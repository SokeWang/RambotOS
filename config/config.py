import os

class CFG:
    # Path Configuration
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SKILLS_PATH = os.path.join(PROJECT_ROOT, "skills")
    
    chat_model = "gemini-3.1-flash-lite-preview"
    api_key = "AIzaSyC4srhpcQcQUzrGDVGHmG1fexMmPAwnTSg"
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    coder_model = "gemini-3-flash-preview"
    PICOVOICE_ACCESS_KEY = "VyAsogrhUAerN4LVfLEqVxQ1+1mK7Z+w6vlwInN4HHeuG5zluc359g=="
    asr_engine = "fast-whisper"
    embedding_model = "gemini-embedding-001"
    
    # Email Configuration (AgentMail Only)
    MAIL_CHECK_INTERVAL = 30  # Seconds between checks
    AGENTMAIL_API_KEY = "am_63c49fea20c7f00aff60d1954dd072eb37a6772186bcb5a24349fed5fab3d7fd" # Add your AgentMail API key here
    AGENTMAIL_INBOX_ID = "rambotos@agentmail.to" # Optional: specific inbox ID if needed

    # User Identity (For cross-channel recognition)
    USER_EMAIL = "your-email@example.com"  # PLEASE UPDATE THIS TO YOUR ACTUAL EMAIL

    # Telegram Bot Configuration
    TELEGRAM_TOKEN = "7316918741:AAE_N3cg5PNtHCBXvt0W14v3LCZHnakwXOg"
    TELEGRAM_CHECK_INTERVAL = 2 # Seconds

    # Middleware Configuration
    tool_selector_max_tools = 5
    tool_selector_enable_logging = False
    recursion_limit = 50
    
    # MongoDB Configuration
    mongodb_uri = "mongodb://mongodb:27017"