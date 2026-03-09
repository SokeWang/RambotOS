import argparse
import sys
import os
import asyncio

from mail_utils import update_mail_state

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message_id", required=True)
    parser.add_argument("--status", required=True) # "read" or "unread"
    args = parser.parse_args()

    remove_labels = ["UNREAD"] if args.status == "read" else []
    add_labels = ["UNREAD"] if args.status == "unread" else []

    result = await update_mail_state(
        message_id=args.message_id,
        add_label_ids=add_labels,
        remove_label_ids=remove_labels
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
