import sys
import os
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot, Signal, QThread, QUrl
import threading
import asyncio
import time
import json
from datetime import datetime
from config.config import CFG
from ultron import Ultron
from loguru import logger
from services.media_processor import MediaProcessor
from services.wakeword import WakeWordThread
from services.email_monitor import EmailMonitorThread
from utils.exceptions import ErrorHandler, MediaProcessingError, ASRError
from utils.concurrency import get_concurrency_manager

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-features=SkiaGraphite"
from PySide6.QtCore import Qt

if __name__ == "__main__":
    # Create App first
    app = QApplication(sys.argv)
    
    # Set Application Icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "public", "favicon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Configure Logger for less verbosity
    logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])
    
    # Initialize Agent
    agent_instance = Ultron()
    logger.info("Backend Agent initialized successfully.")

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

        def __init__(self):
            super().__init__()
            self.view = None # Will be set later
            self.wake_word_thread = None
            self.email_monitor_thread = None
            # 初始化并发控制管理器
            self.concurrency_manager = get_concurrency_manager(max_workers=2, max_queue_size=10)
            self.current_task_id = 0
            self.agent_busy = False
            self.is_listening = False

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
                # 生成唯一任务 ID
                self.current_task_id += 1
                task_id = f"chat_{self.current_task_id}_{int(time.time())}"
                
                # 使用并发控制管理器提交任务
                future = self.concurrency_manager.submit_task(
                    task_id=task_id,
                    func=lambda: self._run_agent(message=message, attachment_path=attachment_path, camera_image=camera_image)
                )
                
                if future is None:
                    logger.warning("Task submission failed or duplicate task running")
                    self.chatResponse.emit(json.dumps({
                        "text": "I'm currently processing another request. Please wait a moment.",
                        "ui": None,
                        "webcam_needed": False
                    }))
            else:
                self.chatResponse.emit(json.dumps({
                    "text": "Error: Agent not initialized.",
                    "ui": None,
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
                    "ui": None,
                    "webcam_needed": False
                }))
                # Generate and emit audio
                base64_audio = await agent_instance.mouth.generate_base64_audio(text)
                self.audioGenerated.emit(base64_audio)
            except Exception as e:
                logger.error(f"Failed to play welcome message: {e}")

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
                    except ASRError as e:
                        logger.warning(f"ASR failed: {e.message}")
                        # Inform frontend to reset UI state
                        self.chatResponse.emit(json.dumps({
                            "text": f"System: {e.message}",
                            "ui": None,
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
            # Call agent with new arguments
            async def run_sequence():
                audio_emitted = False
                async for response_payload in agent_instance.run(
                    message=message,
                    speech=None, # Already transcribed
                    attachment_base64=attachment_b64,
                    webcam_base64=camera_image
                ):
                    audio_response = response_payload.get("audio")
                    brain_response = response_payload.get("text")
                    
                    if brain_response:
                        if isinstance(brain_response, dict):
                            reply_text = brain_response.get("reply", "")
                            ui_content = brain_response.get("ui_component", None)
                        else:
                            reply_text = str(brain_response)

                        frontend_payload = {
                            "text": reply_text,
                            "ui": ui_content,
                            "webcam_needed": webcam_needed  # Tell frontend if camera image should be shown
                        }
                        self.chatResponse.emit(json.dumps(frontend_payload))
                    
                    if audio_response:
                        self.audioGenerated.emit(audio_response)

            asyncio.run(run_sequence())
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
        def requestHistory(self):
            if not agent_instance:
                logger.debug("Agent not ready, cannot get history.")
                return

            logger.debug("Fetching chat history...")

            import json
            messages = agent_instance.brain.short_memory_manager.get(limit=20, with_time=True)
            formatted_history = []
            
            for msg in messages:
                # Handle message content
                content = msg["content"]
                # If it's a list (Multimodal/Structured), keep it as is. 
                # The Frontend should handle rendering of [{"type": "text", ...}]
                # Previous logic flattened it, but User request explicitly wants aligned object storage.
                if msg["role"] == "ai":
                    raw_text = content[0]["text"] if isinstance(content, list) and content else str(content)
                    try:
                        # Try to parse as the old JSON format
                        parsed = json.loads(raw_text)
                        if isinstance(parsed, dict) and "reply" in parsed:
                            content = parsed["reply"]
                        else:
                            content = raw_text
                    except:
                        # If not JSON, it's already the raw text we want
                        content = raw_text

                formatted_history.append({
                    "type": msg["role"],
                    "content": content,
                    "time": msg["time"]
                })
            json_history = json.dumps(formatted_history)
            self.historyLoaded.emit(json_history)
            logger.debug(f"Sent {len(formatted_history)} historical messages to frontend.")

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
        def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
            # Suppress messages to reduce verbosity as requested.
            pass

    view = QWebEngineView()
    page = WebEnginePage(view)
    
    # Configure Settings for React/CDN loading
    settings = page.settings()
    settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(settings.WebAttribute.LocalStorageEnabled, True)
    
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
        # 1. Background Initialization
        logger.info("Triggering Background Agent Initialization...")
        def run_init():
            asyncio.run(agent_instance.initialize())
            backend_bridge.initialized.emit() # Signal frontend that loading is finished
            
            # Start Email Monitor after brain is ready
            logger.info("Starting Email Monitor...")
            backend_bridge.email_monitor_thread = EmailMonitorThread(agent_instance.brain)
            backend_bridge.email_monitor_thread.notificationReceived.connect(backend_bridge.handle_notification)
            backend_bridge.email_monitor_thread.start()
            
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = "file://" + os.path.join(current_dir, "frontend", "dist", "index.html")
    view.load(QUrl(index_path))
    
    # Handle permissions (Camera, Microphone)
    def handle_permission_request(permission):
        logger.debug(f"Permission requested: {permission.permissionType()}")
        permission.grant()

    view.page().permissionRequested.connect(handle_permission_request)

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

        if hasattr(backend_bridge, 'email_monitor_thread') and backend_bridge.email_monitor_thread:
            backend_bridge.email_monitor_thread.stop()
            logger.info("EmailMonitorThread stopped.")

    app.aboutToQuit.connect(cleanup)

    exit_code = app.exec()
    sys.exit(exit_code)