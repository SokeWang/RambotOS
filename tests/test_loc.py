import time
import sys
import CoreLocation
from Foundation import NSRunLoop, NSDate

def test_location(on_background=False):
    import threading
    
    def run_loc():
        print(f"Running location test. Thread: {threading.current_thread().name}")
        from Foundation import NSObject
        class _Delegate(NSObject):
            def locationManager_didUpdateLocations_(self, manager, locations):
                print(f"Update: {locations}")
                manager.stopUpdatingLocation()

            def locationManager_didFailWithError_(self, manager, error):
                print(f"Fail: {error}")

            def locationManagerDidChangeAuthorization_(self, manager):
                print(f"Auth changed: {manager.authorizationStatus()}")

        delegate = _Delegate.alloc().init()
        manager = CoreLocation.CLLocationManager.alloc().init()
        manager.setDelegate_(delegate)
        manager.setDesiredAccuracy_(CoreLocation.kCLLocationAccuracyBest)

        status = CoreLocation.CLLocationManager.authorizationStatus()
        print(f"Initial Status: {status}")
        
        # If not determined, startUpdatingLocation triggers the prompt on macOS
        print("Starting updates...")
        # Note: on macOS, kCLAuthorizationStatusNotDetermined (0)
        manager.startUpdatingLocation()
        
        for _ in range(50):
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
        
        print("Done.")

    if on_background:
        t = threading.Thread(target=run_loc)
        t.start()
        t.join()
    else:
        run_loc()

if __name__ == "__main__":
    if "--bg" in sys.argv:
        test_location(True)
    else:
        test_location(False)
