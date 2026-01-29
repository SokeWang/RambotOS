import os
import base64
import tempfile
import subprocess
import mimetypes
from loguru import logger
from utils.exceptions import MediaProcessingError, ErrorHandler

class MediaProcessor:
    @staticmethod
    def process_incoming_audio(audio_base64: str) -> str:
        """
        Converts incoming base64 audio (likely WebM/WAV from browser) to structural WAV for ASR.
        Returns the path to the converted temporary WAV file.
        
        Raises:
            MediaProcessingError: If audio processing fails
        """
        webm_path = None
        wav_path = None
        
        try:
            # Strip data URI header if present
            header_split = audio_base64.split(',')
            audio_data = header_split[1] if len(header_split) > 1 else audio_base64
            
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                raise MediaProcessingError(
                    "Failed to decode base64 audio",
                    {"error": str(e)}
                )

            # Create temp file (likely WebM from browser)
            try:
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp.flush()
                    webm_path = tmp.name
            except Exception as e:
                raise MediaProcessingError(
                    "Failed to create temporary audio file",
                    {"error": str(e)}
                )

            # Convert to WAV for SpeechRecognition
            wav_path = webm_path.replace(".webm", ".wav")
            
            try:
                result = subprocess.run(
                    ["ffmpeg", "-i", webm_path, "-ac", "1", "-ar", "16000", "-y", wav_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    raise MediaProcessingError(
                        "FFmpeg conversion failed",
                        {
                            "returncode": result.returncode,
                            "stderr": result.stderr[:200]  # Limit error message length
                        }
                    )
            except subprocess.TimeoutExpired:
                raise MediaProcessingError(
                    "FFmpeg conversion timeout",
                    {"timeout": "10s"}
                )
            except FileNotFoundError:
                raise MediaProcessingError(
                    "FFmpeg not found. Please install FFmpeg to process audio.",
                    {"command": "ffmpeg"}
                )

            if os.path.exists(wav_path):
                # Remove original webm
                ErrorHandler.safe_cleanup(os.remove, webm_path)
                logger.debug(f"Successfully converted audio to {wav_path}")
                return wav_path
            else:
                raise MediaProcessingError(
                    "WAV file was not created after conversion",
                    {"expected_path": wav_path}
                )
                
        except MediaProcessingError:
            # Clean up temp files
            ErrorHandler.safe_cleanup(os.remove, webm_path)
            ErrorHandler.safe_cleanup(os.remove, wav_path)
            raise
        except Exception as e:
            # Clean up temp files
            ErrorHandler.safe_cleanup(os.remove, webm_path)
            ErrorHandler.safe_cleanup(os.remove, wav_path)
            raise MediaProcessingError(
                "Unexpected error processing audio",
                {"error": str(e), "type": type(e).__name__}
            )

    @staticmethod
    def get_file_metadata(file_path: str):
        """
        Reads a file and returns its base64 content and mime type.
        
        Returns:
            tuple: (base64_string, mime_type) or (None, None) on error
        """
        try:
            if not os.path.exists(file_path):
                raise MediaProcessingError(
                    f"File not found: {file_path}",
                    {"path": file_path}
                )
            
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
                logger.debug(f"Unknown mime type for {file_path}, using {mime_type}")
            
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                    b64_str = base64.b64encode(file_bytes).decode('utf-8')
                    return b64_str, mime_type
            except PermissionError:
                raise MediaProcessingError(
                    f"Permission denied reading file: {file_path}",
                    {"path": file_path}
                )
            except Exception as e:
                raise MediaProcessingError(
                    f"Failed to read file: {file_path}",
                    {"error": str(e), "type": type(e).__name__}
                )
                
        except MediaProcessingError as e:
            logger.error(f"{e.message} | Details: {e.details}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {type(e).__name__}: {e}")
            return None, None

    @staticmethod
    def parse_multimodal_input(message: str, attachment_base64: str = None, webcam_base64: str = None) -> list:
        """
        Parses various inputs into the format required by the agent.
        Normalizes into a common multimodal format for LangChain/Agent consistency.
        """
        inputs = []
        logger.debug(f"MediaProcessor: input msg={bool(message)}, attach={bool(attachment_base64)}, webcam={bool(webcam_base64)}")
        if message:
            inputs.append({"type": "text", "text": message})
        
        # Helper for adding media
        def add_media(b64_with_header, source=None):
            if not b64_with_header:
                return
            
            # OpenAI/LangChain standard multimodal format
            image_obj = {
                "type": "image_url",
                "image_url": {"url": b64_with_header}
            }
            if source:
                image_obj["media_source"] = source
                
            inputs.append(image_obj)

        if attachment_base64:
            add_media(attachment_base64, source="attachment")
        
        if webcam_base64:
            add_media(webcam_base64, source="webcam")

        if inputs:
            types = [item.get("type") for item in inputs]
            logger.debug(f"Parsed multimodal input with {len(inputs)} blocks: {types}")
        return inputs
