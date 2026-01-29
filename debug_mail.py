import imaplib
import sys
import os

# Add the project root to sys.path to import CFG
sys.path.append('/Users/wangpeidong/Desktop/RAMBOT')

from config.config import CFG

def test_163_mail():
    print(f"Testing IMAP connection for {CFG.MAIL_163_USER}...")
    try:
        mail = imaplib.IMAP4_SSL(CFG.IMAP_SERVER, CFG.IMAP_PORT)
        print("Connected to server.")
        
        rv, data = mail.login(CFG.MAIL_163_USER, CFG.MAIL_163_PASS)
        print(f"Login response: {rv}, {data}")
        
        if rv != 'OK':
            print("Login failed!")
            return

        print("Sending ID command (raw)...")
        try:
            # imaplib.IMAP4.commands['ID'] = ('AUTH', 'NONAUTH')
            # We use xatom which is for vendor-specific commands but ID is standardized enough
            typ, dat = mail.xatom('ID', '("name" "RAMBOT" "version" "1.0.0" "vendor" "test")')
            print(f"ID response: {typ}, {dat}")
        except Exception as e_id:
            print(f"ID command failed: {e_id}")

        print("\nAttempting to select 'INBOX'...")
        rv, data = mail.select("INBOX")
        print(f"Select INBOX response: {rv}, {data}")
        
        if rv == 'OK':
            print("Successfully selected INBOX!")
            status, response = mail.search(None, "ALL")
            print(f"Search ALL response: {status}, count: {len(response[0].split())}")

        mail.logout()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_163_mail()
