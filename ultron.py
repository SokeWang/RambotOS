from agents.langchain_agent import UltronBrain
from services.tts import TTSFactory
import asyncio
from services.asr import ASRFactory
from loguru import logger
from utils.exceptions import ASRError

class Ultron:
    def __init__(self):
        self.ear = ASRFactory.get_asr_engine()
        self.brain = UltronBrain()
        self.mouth = TTSFactory.get_tts_engine("edge", voice="en-GB-SoniaNeural")

    async def initialize(self):
        """Pre-load brain components"""
        await self.brain.initialize()

    async def run(self, message: str, speech: str = None, attachment_base64: str = None, webcam_base64: str = None):
        from services.media_processor import MediaProcessor
        
        if speech:
            try:
                message = self.ear.transcribe(speech)
            except ASRError as e:
                logger.warning(f"ASR failed in Ultron: {e.message}")
                message = None # Treat as empty
        
        inputs = MediaProcessor.parse_multimodal_input(message, attachment_base64, webcam_base64)
        
        if inputs:
            audio_task = None
            async for response in self.brain.run(inputs):
                # Always yield text immediately
                yield {
                    "text": response,
                    "audio": None
                }
                
                # Start audio generation in background if we have a reply and haven't started yet
                if response.get("reply") and not audio_task:
                    audio_task = asyncio.create_task(self.mouth.generate_base64_audio(response["reply"]))

            # Once all brain/designer steps are done, if we have an audio task, wait for it and yield
            if audio_task:
                try:
                    base64_audio = await audio_task
                    yield {
                        "text": None, # Signal that this is just for audio
                        "audio": base64_audio
                    }
                except Exception as e:
                    logger.error(f"TTS generation failed: {type(e).__name__}: {e}")
        else:
            yield {
                "text": {"reply": "I couldn't hear you."},
                "audio": None
            }

if __name__ == "__main__":
    async def test():
        ultron = Ultron()
        async for response in ultron.run("what's the time"):
            print(f"Response: {response['text']}")
    
    asyncio.run(test())
