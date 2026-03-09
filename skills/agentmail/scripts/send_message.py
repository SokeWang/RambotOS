import argparse
import sys
import os
import asyncio

from mail_utils import send_mail_message

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--thread_id", default=None)
    args = parser.parse_args()

    result = await send_mail_message(
        message=args.message,
        to=args.to,
        subject=args.subject,
        thread_id=args.thread_id
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
