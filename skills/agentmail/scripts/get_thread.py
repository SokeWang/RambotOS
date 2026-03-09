import argparse
import sys
import os
import json
import asyncio

from mail_utils import get_mail_thread

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread_id", required=True)
    args = parser.parse_args()

    results = await get_mail_thread(args.thread_id)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
