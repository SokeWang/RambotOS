import time
import struct
import pyaudio
import pvporcupine
import sys
from PySide6.QtCore import QThread, Signal
from loguru import logger
from config.config import CFG

class WakeWordThread(QThread):
    wakeDetected = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._paused = False
        self.access_key = CFG.PICOVOICE_ACCESS_KEY
        
    def run(self):
        if not self.access_key:
            logger.info("PICOVOICE_ACCESS_KEY not found. Wake word disabled.")
            return

        while self._running:
            try:
                # Handle frozen path for PyInstaller
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS
                else:
                    import os
                    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                # Custom wake word model path
                import os
                keyword_path = os.path.join(base_path, "resources", "wakewords", "Rambo.ppn")
                logger.info(f"Loading wake word model from: {keyword_path}")
                
                porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=[keyword_path]
                )
                
                pa = pyaudio.PyAudio()
                audio_stream = pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length
                )
                
                logger.info(f"Wake Word Listener Started (Rambo)")
                
                loop_count = 0
                while self._running:
                    try:
                        # Always read to keep the buffer clean and stream active
                        pcm_bytes = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                        
                        if self._paused:
                            # If paused, we just discard the data to stay in sync
                            continue
                            
                        # Logging heartbeat every 100 frames (~3 seconds)
                        loop_count += 1
                        if loop_count % 100 == 0:
                            # logger.debug("WakeWordThread heartbeat: listening...")
                            loop_count = 0

                        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm_bytes)
                        keyword_index = porcupine.process(pcm)
                        
                        if keyword_index >= 0:
                            logger.info("Wake Word Detected!")
                            self.wakeDetected.emit()
                            # Auto-pause to prevent multiple triggers
                            self._paused = True 
                    except (IOError, struct.error) as e:
                        logger.warning(f"Wake Word Audio Read Error: {e}")
                        time.sleep(0.1)
                        continue
                
                audio_stream.close()
                pa.terminate()
                porcupine.delete()
                
            except Exception as e:
                logger.error(f"Wake Word Fatal Error: {e}. Retrying in 3 seconds...")
                time.sleep(3)

    def pause(self):
        logger.info("WakeWordThread paused")
        self._paused = True
    
    def resume(self):
        logger.info("WakeWordThread resumed")
        self._paused = False
        
    def stop(self):
        self._running = False
