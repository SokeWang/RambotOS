import asyncio
from services.tts import TTSFactory

async def test():
    try:
        engine = TTSFactory.get_tts_engine("edge", voice="zh-CN-XiaoxiaoNeural")
        message = "Rambot is online and ready, sir. All systems are operational."
        b64 = await engine.generate_base64_audio(message)
        print(f"Success, length: {len(b64)}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
