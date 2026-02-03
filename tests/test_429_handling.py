import re
import asyncio

def test_regex():
    error_str = "Error calling model 'gemini-3-flash-preview' (RESOURCE_EXHAUSTED): 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota... Please retry in 25.795275017s.', ...}}"
    match = re.search(r"retry in (\d+\.?\d*)s", error_str)
    if match:
        retry_wait = float(match.group(1)) + 1
        print(f"SUCCESS: Extracted retry wait: {retry_wait}")
        return retry_wait
    else:
        print("FAILURE: Could not extract retry wait")
        return None

async def test_retry_loop():
    # Simulated execution loop similar to langchain_agent.py
    max_retries = 2
    retry_count = 0
    fail_first = True
    
    print("\nStarting mock retry loop test...")
    while retry_count < max_retries:
        try:
            if fail_first:
                fail_first = False
                raise Exception("RESOURCE_EXHAUSTED: Please retry in 2.5s")
            
            print("Action successful!")
            break
        except Exception as e:
            error_str = str(e)
            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                print(f"Caught expected error: {error_str}")
                match = re.search(r"retry in (\d+\.?\d*)s", error_str)
                retry_wait = float(match.group(1)) + 1 if match else 5
                print(f"Sleeping for {retry_wait}s...")
                await asyncio.sleep(retry_wait)
                continue
            print(f"Unexpected error: {e}")
            break
    print("Test finished.")

if __name__ == "__main__":
    wait = test_regex()
    if wait == 26.795275017:
        print("Regex match is accurate.")
    asyncio.run(test_retry_loop())
