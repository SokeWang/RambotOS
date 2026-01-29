import edge_tts
import tempfile
import base64
import os
import asyncio
from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """
    Abstract base class for Text-To-Speech providers.
    """
    @abstractmethod
    async def generate_audio(self, text: str, output_file: str = None) -> str:
        """
        Generates audio from text and saves it to a file.
        Returns the path to the generated audio file.
        """
        pass

    async def generate_base64_audio(self, text: str) -> str:
        """
        Generates audio and returns it as a base64 encoded string with data URI scheme.
        Useful for web frontend playback.
        This default implementation uses generate_audio internally.
        """
        file_path = await self.generate_audio(text)
        
        with open(file_path, "rb") as f:
            audio_data = f.read()
            base64_audio = "data:audio/mp3;base64," + base64.b64encode(audio_data).decode('utf-8')
        if os.path.exists(file_path):
            os.remove(file_path)
                
        return base64_audio

class EdgeTTS(TTSProvider):
    """
    TTS provider implementation using edge-tts.
    """
    def __init__(self, voice: str = "en-GB-RyanNeural"):
        self.voice = voice

    async def generate_audio(self, text: str, output_file: str = None) -> str:
        if not output_file:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3:
                output_file = temp_mp3.name

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)
        
        return output_file

class TTSFactory:
    """
    Factory to get TTS providers.
    """
    @staticmethod
    def get_tts_engine(engine_name: str = "edge", **kwargs) -> TTSProvider:
        if engine_name == "edge":
            return EdgeTTS(**kwargs)
        raise ValueError(f"Unknown TTS engine: {engine_name}")

if __name__ == "__main__":
    async def main():
        # Example usage via Factory
        print("Initializing EdgeTTS via Factory...")
        tts_engine = TTSFactory.get_tts_engine("edge")
        
        test_text = "This is a test of the refactored TTS architecture."
        print(f"Generating audio for: '{test_text}'")
        
        # Test File Generation
        output_path = await tts_engine.generate_audio(test_text)
        print(f"Audio file generated at: {output_path}")
        
        # Test Base64 Generation
        base64_audio = await tts_engine.generate_base64_audio(test_text)
        print(f"Base64 generated (length: {len(base64_audio)})")

    asyncio.run(main())
