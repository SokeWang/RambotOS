from abc import ABC, abstractmethod
from loguru import logger
from utils.exceptions import ASRError

class ASR(ABC):
    @abstractmethod
    def transcribe(self, audio_data) -> str:
        pass

class GoogleWebSpeechASR(ASR):
    def __init__(self):
        import speech_recognition as sr
        self.sr = sr
        self.recognizer = sr.Recognizer()

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes audio file at the given path using Google Web Speech API.
        """
        try:
            with self.sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Google ASR Output: {text}")
            return text
        except self.sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio (likely silent)")
            raise ASRError("No speech detected in audio")
        except self.sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            raise ASRError(f"ASR Service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected ASR error: {type(e).__name__}: {str(e)}")
            raise ASRError(f"Unexpected ASR error: {str(e)}")

class FasterWhisperASR(ASR):
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        from faster_whisper import WhisperModel
        logger.info(f"Initializing Faster Whisper model: {model_size} on {device}")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes audio file at the given path using Faster Whisper.
        """
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            text = "".join([segment.text for segment in segments]).strip()
            logger.info(f"Faster Whisper Output: {text} (language: {info.language}, probability: {info.language_probability:.2f})")
            if not text:
                raise ASRError("No speech detected in audio")
            return text
        except Exception as e:
            logger.error(f"Faster Whisper ASR error: {type(e).__name__}: {str(e)}")
            raise ASRError(f"Faster Whisper ASR error: {str(e)}")

class ASRFactory:
    _instances = {}

    @staticmethod
    def get_asr_engine(engine_type=None):
        from config.config import CFG
        if engine_type is None:
            engine_type = getattr(CFG, "asr_engine", "google")
            
        if engine_type in ASRFactory._instances:
            return ASRFactory._instances[engine_type]

        if engine_type == "google":
            engine = GoogleWebSpeechASR()
        elif engine_type == "fast-whisper":
            engine = FasterWhisperASR()
        else:
            raise ValueError(f"Unknown ASR engine: {engine_type}")
        
        ASRFactory._instances[engine_type] = engine
        return engine