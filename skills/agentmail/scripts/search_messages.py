import argparse
import sys
import os
import json
import asyncio

# Logic is now in mail_utils.py within the same directory
from mail_utils import search_mail

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="ALL")
    args = parser.parse_args()

    results = await search_mail(args.query)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
