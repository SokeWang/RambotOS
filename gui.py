import sys
import os
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot, Signal, QThread, QUrl
import asyncio
import time
import json
from loguru import logger
from services.media_processor import MediaProcessor
from services.wakeword import WakeWordThread
from utils.exceptions import ErrorHandler, MediaProcessingError, ASRError
from utils.concurrency import get_concurrency_manager
import requests
from PySide6.QtCore import QTimer
from services.location_service import start_location_service, get_cached_location

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-features=SkiaGraphite --allow-file-access-from-files --autoplay-policy=no-user-gesture-required --enable-features=Geolocation --unsafely-treat-insecure-origin-as-secure=file://*"
from PySide6.QtCore import Qt

def run_gui():
    # Create App first
    app = QApplication(sys.argv)
    
    # Set Application Icon
    # Handle frozen path for PyInstaller
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    icon_path = os.path.join(base_path, "frontend", "public", "favicon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Configure Logger for less verbosity
    logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])
    
    # Initialize Agent (Proxy for Gateway)
    # We still need mouth and ear for local ASR/TTS
    from services.asr import ASRFactory
    from services.tts import TTSFactory
    
    class RambotClient:
        def __init__(self):
            self.ear = ASRFactory.get_asr_engine()
            self.mouth = TTSFactory.get_tts_engine("edge", voice="zh-CN-XiaoxiaoNeural")
            
    agent_instance = RambotClient()
    logger.info("Backend Client initialized successfully (Gateway Mode).")

    class BackendBridge(QObject):
        chatResponse = Signal(str)
        attachmentSelected = Signal(str)
        speechRecognized = Signal(str)
        audioGenerated = Signal(str)
        controlSignal = Signal(str, str)
        wakeWordDetected = Signal()
        historyLoaded = Signal(str)
        initialized = Signal() # Added for loading animation
        notificationSignal = Signal(str)

        @Slot()
        def frontend_ready(self):
            logger.info("Frontend marked as ready, triggering system initialization...")
            self.initialized.emit()

        def __init__(self):
            super().__init__()
            self.view = None # Will be set later
            self.wake_word_thread = None
            self.email_monitor_thread = None
            # Concurrency manager initialization
            self.concurrency_manager = get_concurrency_manager(max_workers=2, max_queue_size=10)
            self.current_task_id = 0
            self.agent_busy = False
            self.is_listening = False
            
            # Initialize (but don't start) location timer
            self.location_timer = QTimer()
            self.location_timer.timeout.connect(self._poll_location)
            self.location_timer.setSingleShot(False)

        @Slot(float)
        def startNativeLocation(self, timeout=30.0):
            logger.info(f"BackendBridge: On-demand location request received (timeout={timeout})")
            start_location_service(timeout)
            if not self.location_timer.isActive():
                self.location_timer.start(2000)

        def _poll_location(self):
            if not self.view or not self.view.page():
                return
            loc = get_cached_location()
            if loc:
                logger.info(f"BackendBridge: Sending location to frontend: {loc}")
                js = f"window.dispatchEvent(new CustomEvent('NativeLocationUpdate', {{detail: {json.dumps(loc)}}}));"
                self.view.page().runJavaScript(js)
                self.location_timer.stop() # Only need one good fix per request
        @Slot()
        def select_file(self):
            logger.info("Opening file dialog...")
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(None, "Select Attachment", "", "All Files (*)")
            if file_path:
                logger.info(f"File selected: {file_path}")
                self.attachmentSelected.emit(file_path)
            else:
                logger.info("No file selected.")

        @Slot(str, str, str)
        def chat(self, message, attachment_path="", camera_image=""):
            if attachment_path and not os.path.exists(attachment_path):
                logger.warning(f"Attachment path does not exist: {attachment_path}")
            
            if agent_instance:
                # Generate unique task ID
                self.current_task_id += 1
                task_id = f"chat_{self.current_task_id}_{int(time.time())}"
                
                # Use concurrency control manager to submit task
                future = self.concurrency_manager.submit_task(
                    task_id=task_id,
                    func=lambda: self._run_agent(message=message, attachment_path=attachment_path, camera_image=camera_image)
                )
                
                if future is None:
                    logger.warning("Task submission failed or duplicate task running")
                    self.chatResponse.emit(json.dumps({
                        "text": "I'm currently processing another request. Please wait a moment.",
                        "webcam_needed": False
                    }))
            else:
                self.chatResponse.emit(json.dumps({
                    "text": "Error: Agent not initialized.",
                    "webcam_needed": False
                }))

        @Slot(str, str)
        def process_audio(self, base64_audio, camera_image=""):
            logger.debug(f"Slot: process_audio received audio_len={len(base64_audio)}, camera_image_len={len(camera_image) if camera_image else 0}")
            future = self.concurrency_manager.submit_task(
                task_id="voice_chat",
                func=lambda: self._run_agent(message=None, attachment_path=None, camera_image=camera_image, audio_data=base64_audio)
            )
            
            if future is None:
                logger.warning("Audio task submission failed or duplicate task running")

        @Slot()
        def say_welcome(self):
            """Rambot says a welcome message via TTS."""
            message = "Rambot is online and ready, sir. All systems are operational."
            self.concurrency_manager.submit_task(
                task_id="welcome_message",
                func=lambda: asyncio.run(self._do_say_welcome(message))
            )

        async def _do_say_welcome(self, text):
            try:
                # Emit text for visual feedback
                self.chatResponse.emit(json.dumps({
                    "text": text,
                    "webcam_needed": False,
                    "is_welcome": True
                }))
                # Generate and emit audio
                base64_audio = await agent_instance.mouth.generate_base64_audio(text)
                self.audioGenerated.emit(base64_audio)
            except Exception as e:
                import traceback
                logger.error(f"Failed to play welcome message: {e}\n{traceback.format_exc()}")

        def _run_agent(self, message, attachment_path="", camera_image="", audio_data=""):
            self.agent_busy = True
            self._update_wakeword_state()
            
            try:
                self._do_run_agent(message, attachment_path, camera_image, audio_data)
            finally:
                self.agent_busy = False
                self._update_wakeword_state()

        def _do_run_agent(self, message, attachment_path="", camera_image="", audio_data=""):
            logger.debug(f"GUI: _do_run_agent called with message='{message}', camera_image_len={len(camera_image) if camera_image else 0}")
            speech_file = None
            
            # If we have audio, we need to transcribe it first
            if audio_data:
                from services.asr import ASRFactory
                ear = ASRFactory.get_asr_engine()
                speech_file = MediaProcessor.process_incoming_audio(audio_data)
                if speech_file:
                    try:
                        message = ear.transcribe(speech_file)
                        # Emit signal to frontend so user message is added to chat history
                        self.speechRecognized.emit(message)
                    except ASRError as e:
                        logger.warning(f"ASR failed: {e.message}")
                        # Inform frontend to reset UI state
                        self.chatResponse.emit(json.dumps({
                            "text": f"System: {e.message}",
                            "webcam_needed": False
                        }))
                        return # Stop processing, return to wakeword state
                    finally:
                        # Clean up temp file
                        ErrorHandler.safe_cleanup(os.remove, speech_file)
                        speech_file = None # Ensure it's not reused
            
            
            # Webcam is always sent if available, backend will decide if needed
            webcam_needed = bool(camera_image)
            logger.debug(f"GUI: webcam_provided={webcam_needed}")
            
            # Process Attachment if it's a file path
            attachment_b64 = None
            if attachment_path:
                attachment_b64_data, mime = MediaProcessor.get_file_metadata(attachment_path)
                if attachment_b64_data:
                    attachment_b64 = f"data:{mime};base64,{attachment_b64_data}"

            # Speech file is already handled above to get the message
            # We don't need to process audio again here.
            # Passing message to agent_instance.run is enough.

            t_start = time.time()
            # Call Gateway API
            def run_central_chat():
                try:
                    payload = {
                        "message": message,
                        "sender": "os_user",
                        "attachment_base64": attachment_b64,
                        "webcam_base64": camera_image
                    }
                    
                    final_reply = ""
                    with requests.post("http://127.0.0.1:8000/chat", json=payload, timeout=None, stream=True) as resp:
                        if resp.status_code == 200:
                            for line in resp.iter_lines():
                                if line:
                                    try:
                                        brain_response = json.loads(line)
                                        reply_text = brain_response.get("reply", "")
                                        if reply_text:
                                            final_reply = reply_text # Last non-empty reply wins
                                        
                                        frontend_payload = {
                                            "text": reply_text,
                                            "tool_calls": brain_response.get("tool_calls", []),
                                            "webcam_needed": webcam_needed,
                                            "gen_ui": brain_response.get("gen_ui")
                                        }
                                        if brain_response.get("gen_ui"):
                                            logger.info(f"GUI: Emitting gen_ui to frontend. Length: {len(brain_response.get('gen_ui'))}")
                                        self.chatResponse.emit(json.dumps(frontend_payload))
                                    except Exception as je:
                                        logger.error(f"Error parsing stream line: {je}")
                            
                            # Generate and emit audio locally using the final accumulated reply
                            if final_reply:
                                async def play_audio():
                                    try:
                                        audio_b64 = await agent_instance.mouth.generate_base64_audio(final_reply)
                                        self.audioGenerated.emit(audio_b64)
                                    except Exception as ae:
                                        logger.error(f"TTS Error: {ae}")
                                asyncio.run(play_audio())
                        else:
                            logger.error(f"Gateway Error: {resp.status_code}")
                            self.chatResponse.emit(json.dumps({"text": "Gateway connection error."}))
                except Exception as e:
                    logger.error(f"Gateway Chat Failed: {e}")
                    self.chatResponse.emit(json.dumps({"text": f"Error: {e}"}))

            run_central_chat()
            t_end = time.time()
            logger.debug(f"[Performance] Total Agent Execution took {t_end - t_start:.2f}s")
            
            # Cleanup speech file if it exists
            if speech_file and os.path.exists(speech_file):
                ErrorHandler.safe_cleanup(os.remove, speech_file)


                
        # --- Wake Word Control ---
        @Slot(bool)
        def set_agent_busy(self, busy):
            logger.debug(f"Backend: set_agent_busy({busy})")
            self.agent_busy = busy
            self._update_wakeword_state()

        @Slot(bool)
        def set_wakeword_enabled(self, enabled):
            logger.info(f"Backend: set_wakeword_enabled({enabled})")
            if hasattr(self, 'wake_word_thread') and self.wake_word_thread:
                if enabled:
                    self.wake_word_thread.resume()
                else:
                    self.wake_word_thread.pause()

        @Slot(bool)
        def set_listening_state(self, is_listening):
            """
            Called by Frontend to notify recording state.
            is_listening = True -> User is speaking (Pause Wake Word)
            is_listening = False -> User finished (Resume Wake Word)
            """
            logger.debug(f"Backend: set_listening_state({is_listening})")
            self.is_listening = is_listening
            self._update_wakeword_state()

        def _update_wakeword_state(self):
            if hasattr(self, 'wake_word_thread') and self.wake_word_thread:
                if self.is_listening or self.agent_busy:
                    self.wake_word_thread.pause()
                else:
                    self.wake_word_thread.resume()

        historyLoaded = Signal(str)

        @Slot()
        def _on_wake_word_detected(self):
            logger.debug("BackendBridge: Wake word signal received from thread.")
            self.wakeWordDetected.emit()
            logger.debug("BackendBridge: Sent wakeWordDetected signal to frontend.")

        @Slot(str)
        def handle_notification(self, message):
            logger.info(f"BackendBridge: Notification received: {message}")
            self.notificationSignal.emit(message)
            # You might also want to trigger a TTS message here
            # self.concurrency_manager.submit_task("notify_speech", lambda: asyncio.run(agent_instance.mouth.generate_base64_audio(message)))



        # --- Gesture Control ---
        @Slot(float, float)
        def updateCursor(self, x, y):
            """
            Updates the system cursor position based on normalized coordinates (0.0 - 1.0).
            """
            try:
                import pyautogui
                screen_width, screen_height = pyautogui.size()
                
                # Map 0-1 to screen coordinates
                target_x = int(x * screen_width)
                target_y = int(y * screen_height)
                
                # Move mouse (disable fail-safe to prevent corners from raising exceptions)
                pyautogui.FAILSAFE = False
                pyautogui.moveTo(target_x, target_y)
            except ImportError:
                logger.info("pyautogui not installed. Cursor control disabled.")
            except Exception as e:
                logger.info(f"Cursor Error: {e}") # Reduce log spam
                pass

        @Slot(bool)
        def clickMouse(self, is_down):
            """
            Handles mouse clicking.
            is_down: True for press, False for release.
            """
            try:
                import pyautogui
                if is_down:
                    pyautogui.mouseDown()
                else:
                    pyautogui.mouseUp()
            except ImportError:
                pass
            except Exception as e:
                logger.info(f"Click Error: {e}")

        @Slot(str)
        def set_window_state(self, state):
            """
            Changes the window state.
            state: "full" or "mini"
            """
            logger.info(f"Backend: set_window_state({state})")
            if not self.view:
                return
                
            if state == "full":
                self.view.showMaximized()
            elif state == "mini":
                # Shrink to a small orb in the bottom right
                screen = QApplication.primaryScreen().geometry()
                size = 100
                self.view.showNormal()
                self.view.resize(size, size)
                self.view.move(screen.width() - size - 20, screen.height() - size - 40)

        @Slot()
        def close_app(self):
            """Exits the application."""
            logger.info("Backend: close_app called. Exiting...")
            QApplication.quit()

    # --- Setup QWebEngineView ---
    class WebEnginePage(QWebEnginePage):
        def __init__(self, profile, parent=None):
            super().__init__(profile, parent)

        def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
            # Log JS console messages to terminal for debugging
            logger.info(f"FRONTEND [L:{lineNumber}@{sourceID}]: {message}")

    # Configure Persistent Storage for LocalStorage/Settings
    storage_path = os.path.abspath(os.path.expanduser("~/.rambot/web_storage"))
    os.makedirs(storage_path, exist_ok=True)
    
    view = QWebEngineView()
    
    # Create a persistent profile with a unique storage name.
    # Passing 'view' as parent ensures it's cleaned up with the window.
    profile = QWebEngineProfile("RambotProfile", view)
    profile.setPersistentStoragePath(storage_path)
    profile.setCachePath(os.path.join(storage_path, "cache"))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    
    logger.info(f"WebProfile: StorageName={profile.storageName()}")
    logger.info(f"WebProfile: PersistentPath={profile.persistentStoragePath()}")
    logger.info(f"WebProfile: OffTheRecord={profile.isOffTheRecord()}")
    
    # Configure Settings correctly
    # Use QWebEngineSettings.WebAttribute for PySide6 compatibility
    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    
    page = WebEnginePage(profile, view)
    
    page.setBackgroundColor(Qt.black)
    
    view.setPage(page)
    
    view.resize(1200, 900)
    view.setWindowTitle("Rambot")
    if os.path.exists(icon_path):
        view.setWindowIcon(QIcon(icon_path))
    
    # Standard macOS Window Flags (Remove Frameless)
    view.setWindowFlags(
        Qt.Window | 
        Qt.WindowMinMaxButtonsHint | 
        Qt.WindowCloseButtonHint
    )
    
    # Setup WebChannel
    channel = QWebChannel()
    backend_bridge = BackendBridge()
    backend_bridge.view = view # Register view to bridge for control
    channel.registerObject("backendBridge", backend_bridge)
    view.page().setWebChannel(channel)
    
    # Connect Agent UI Callback
    if agent_instance:
        # 1. Background Initialization (Now just for UI ready signal)
        logger.info("Triggering UI Ready Notification...")
        def run_init():
            # In Gateway mode, we don't need to initialize brain here
            # The signal will be emitted when the frontend calls frontend_ready()
            
            # (No monitor notifications bridged directly to GUI anymore, frontend pulls directly or uses SSE if needed)
            pass
            
        backend_bridge.concurrency_manager.submit_task(
            task_id="startup_init",
            func=run_init
        )

        # 2. Define callback wrapper to be called from non-main thread
        def ui_callback_wrapper(action, target):
            logger.debug(f"BackendBridge emitting control signal: {action}, {target}")
            # Signals are thread-safe
            backend_bridge.controlSignal.emit(action, target)
            
        agent_instance.ui_callback = ui_callback_wrapper
        logger.info("Agent UI Callback connected.")

    # Initialize and start WakeWordThread
    wake_word_thread = WakeWordThread()
    backend_bridge.wake_word_thread = wake_word_thread # Pass thread instance to bridge
    wake_word_thread.wakeDetected.connect(backend_bridge._on_wake_word_detected)
    wake_word_thread.start()
    
    # Load index.html
    # Handle frozen path
    if getattr(sys, 'frozen', False):
        current_dir = sys._MEIPASS
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
    index_path = "file://" + os.path.join(current_dir, "frontend", "dist", "index.html")
    view.load(QUrl(index_path))
    
    # Handle permissions (Camera, Microphone, Geolocation)
    def handle_permission_request(permission):
        p_type = permission.permissionType()
        logger.info(f"System Permission Requested: {p_type}")
        
        # In PySide6, Geolocation is often handled via featurePermissionRequested
        # but permissionRequested is also used in newer versions.
        permission.grant()
        logger.info(f"System Permission Granted: {p_type}")

    view.page().permissionRequested.connect(handle_permission_request)
    
    # Also handle Geolocation explicitly for older/other patterns
    def handle_feature_permission(url, feature):
        logger.info(f"Feature Permission Requested for {url}: {feature}")
        view.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
        logger.info(f"Feature Permission Granted: {feature}")

    view.page().featurePermissionRequested.connect(handle_feature_permission)

    view.showMaximized()

    # Hot reload setup
    from PySide6.QtCore import QFileSystemWatcher
    from pathlib import Path
    
    watch_path = Path(current_dir) / "frontend" / "dist" / "index.html"
    watcher = QFileSystemWatcher()
    watcher.addPath(str(watch_path))

    def reload():
        logger.info("Detected change. Reloading Web Page...")
        view.reload()
        if str(watch_path) not in watcher.files():
            watcher.addPath(str(watch_path))

    watcher.fileChanged.connect(reload)
    
    # Cleanup on exit
    def cleanup():
        logger.info("Cleaning up threads...")
        if wake_word_thread.isRunning():
            wake_word_thread.stop()
            wake_word_thread.quit()
            wake_word_thread.wait()
            logger.info("WakeWordThread stopped.")

        # Stop all heartbeats/monitors and bridge via MonitorManager
        logger.info("Cleaning up Service Monitors...")
        if 'monitor_manager' in globals():
            monitor_manager.cleanup()

    app.aboutToQuit.connect(cleanup) # app needs to be defined (QApplication instance)

    exit_code = app.exec()
    return exit_code

if __name__ == "__main__":
    sys.exit(run_gui())