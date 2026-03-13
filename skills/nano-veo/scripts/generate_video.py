#!/usr/bin/env python3
"""
基于 Gemini Veo 3.1 的视频生成脚本 (nano-veo)

支持功能：
- 文生视频 (Text-to-Video)
- 图生视频 (Image-to-Video): 将图片作为首帧
- 视频扩展 (Extend Video)
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

# 尝试集成 RambotOS 的配置系统
try:
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if project_root.exists() and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from config.config import CFG
except ImportError:
    CFG = None

def get_api_key(args_key=None):
    if args_key: return args_key
    if CFG and hasattr(CFG, "api_key") and CFG.api_key:
        return CFG.api_key
    return os.environ.get("GOOGLE_API_KEY")

def generate_video(prompt, output_path, input_image=None, input_video=None, aspect_ratio="16:9", api_key=None):
    api_key = get_api_key(api_key)
    if not api_key:
        print("Error: No API Key found.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    model_id = "veo-3.1-generate-preview"

    print(f"Starting video generation...")
    print(f"Prompt: {prompt}")

    # TODO: Implement full image/video input logic for Veo options
    # Current SDK simplified logic
    try:
        operation = client.models.generate_videos(
            model=model_id,
            prompt=prompt,
            # config=types.GenerateVideoConfig(aspect_ratio=aspect_ratio)
        )

        while not operation.done:
            print("Waiting for video generation to complete... (Polling every 10s)")
            time.sleep(10)
            operation = client.operations.get(operation)

        if operation.response and operation.response.generated_videos:
            generated_video = operation.response.generated_videos[0]
            print(f"Generation complete. Downloading video...")
            
            # Fetching video bytes from the URI/object
            print(f"Generation complete. Downloading video...")
            
            # Assuming generated_video.video.uri exists or is accessible
            # We use requests to fetch the content if it's a URL
            import requests
            
            # Using the uri if available, otherwise trying generic access
            video_uri = getattr(generated_video.video, 'uri', None)
            
            if video_uri:
                response = requests.get(video_uri, stream=True)
                response.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✓ Video successfully saved to: {output_path}")
                return output_path
            else:
                # Fallback to original logic if no URI
                print("Warning: No URI found. Attempting direct save.")
                generated_video.video.save(output_path)
                return output_path
        else:
            print(f"Error: Operation failed or no video generated.")
            print(f"Response: {operation}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Gemini Veo 3.1 Video Generation Tool")
    parser.add_argument("--prompt", "-p", required=True, help="Text prompt for video generation")
    parser.add_argument("--input-image", "-i", help="Path to input image (first frame)")
    parser.add_argument("--input-video", "-v", help="Path to input video (for extension)")
    parser.add_argument("--aspect-ratio", "-a", default="16:9", help="Aspect ratio (e.g., 16:9)")
    parser.add_argument("--filename", "-f", help="Output filename")
    parser.add_argument("--api-key", "-k", help="API Key")

    args = parser.parse_args()

    # Determine default storage
    if CFG:
        storage_root = Path(CFG.PROJECT_ROOT)
    else:
        storage_root = Path(__file__).resolve().parent.parent.parent.parent
    
    video_dir = storage_root / "generated_video"
    video_dir.mkdir(parents=True, exist_ok=True)

    if not args.filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.filename = str(video_dir / f"video_{timestamp}.mp4")
    elif not Path(args.filename).is_absolute():
        args.filename = str(video_dir / args.filename)

    generate_video(
        prompt=args.prompt,
        output_path=args.filename,
        input_image=args.input_image,
        input_video=args.input_video,
        aspect_ratio=args.aspect_ratio,
        api_key=args.api_key
    )

if __name__ == "__main__":
    main()
