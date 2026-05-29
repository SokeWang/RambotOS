import threading
import time
import CoreLocation
from Foundation import NSObject, NSRunLoop, NSDate
from loguru import logger

# This allows the Python process (which can request system location permission)
# to bridge coordinates to the frontend.

# These will be set once we have a location
_location: dict | None = None
_location_lock = threading.Lock()
_location_fix_obtained = threading.Event()

def get_cached_location() -> dict | None:
    """Return the last known location dict {lat, lng} or None."""
    with _location_lock:
        return _location

def start_location_service(timeout: float = 30.0) -> None:
    """
    Spawns a thread to request a one-time location fix from CoreLocation.
    The result will be cached and can be retrieved via get_cached_location().
    """
    def run_loc():
        global _location
        
        class _Delegate(NSObject):
            def locationManager_didUpdateLocations_(self, manager, locations):  # noqa: N802
                global _location
                if not locations:
                    return
                loc = locations[-1]
                lat = loc.coordinate().latitude
                lng = loc.coordinate().longitude
                
                with _location_lock:
                    _location = {"lat": lat, "lng": lng}
                
                logger.info(f"LocationService: Obtained fix {lat}, {lng}")
                _location_fix_obtained.set()

            def locationManager_didFailWithError_(self, manager, error):  # noqa: N802
                logger.error(f"LocationService: Failed with error: {error}")
                # We don't set fix_obtained on error to allow retries/waiting

            def locationManagerDidChangeAuthorization_(self, manager):  # noqa: N802
                status = manager.authorizationStatus()
                logger.info(f"LocationService: Auth status changed: {status}")
                # We just log it, the loop continues to wait for locations

        delegate = _Delegate.alloc().init()
        manager = CoreLocation.CLLocationManager.alloc().init()
        manager.setDelegate_(delegate)
        manager.setDesiredAccuracy_(CoreLocation.kCLLocationAccuracyBest)

        logger.info("LocationService: Requesting location update...")
        manager.startUpdatingLocation()
        
        # Run loop until fix is obtained or timeout
        start_time = time.time()
        while not _location_fix_obtained.is_set() and (time.time() - start_time < timeout):
            # Process events for 0.5 seconds
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.5))
        
        manager.stopUpdatingLocation()
        if _location_fix_obtained.is_set():
            logger.info("LocationService: Successfully obtained location fix.")
        else:
            logger.warning("LocationService: Timed out waiting for location fix.")

    _location_fix_obtained.clear()
    t = threading.Thread(target=run_loc, name="LocationServiceThread", daemon=True)
    t.start()
