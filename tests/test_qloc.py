import sys
import threading
import CoreLocation
from Foundation import NSRunLoop, NSDate, NSObject
from PySide6.QtWidgets import QApplication, QWidget

_man = None
_del = None

def test_location(on_background=False):
    global _man, _del
    def run_loc():
        global _man, _del
        print(f"Running location test. Thread: {threading.current_thread().name}")
        class _Delegate(NSObject):
            def locationManager_didUpdateLocations_(self, manager, locations):
                print(f"Update: {locations}")
                manager.stopUpdatingLocation()

            def locationManager_didFailWithError_(self, manager, error):
                print(f"Fail: {error}")

            def locationManagerDidChangeAuthorization_(self, manager):
                print(f"Auth changed: {manager.authorizationStatus()}")

        _del = _Delegate.alloc().init()
        _man = CoreLocation.CLLocationManager.alloc().init()
        _man.setDelegate_(_del)
        _man.setDesiredAccuracy_(CoreLocation.kCLLocationAccuracyBest)

        status = CoreLocation.CLLocationManager.authorizationStatus()
        print(f"Initial Status: {status}")
        
        print("Starting updates...")
        _man.startUpdatingLocation()
        
        if threading.current_thread().name != 'MainThread':
            import time
            deadline = time.time() + 5
            while time.time() < deadline:
                NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
            print("Done bg loop.")

    if on_background:
        t = threading.Thread(target=run_loc)
        t.start()
    else:
        run_loc()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = QWidget()
    w.show()
    
    if "--bg" in sys.argv:
        import PySide6.QtCore as QtCore
        QtCore.QTimer.singleShot(1000, lambda: test_location(True))
    else:
        import PySide6.QtCore as QtCore
        QtCore.QTimer.singleShot(1000, lambda: test_location(False))
        
    QtCore.QTimer.singleShot(6000, app.quit)
    sys.exit(app.exec())
