class CFG:
    chat_model = "gemini-3-flash-preview"
    api_key = "AIzaSyC4srhpcQcQUzrGDVGHmG1fexMmPAwnTSg"
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    coder_model = "gemini-3-flash-preview"
    PICOVOICE_ACCESS_KEY = "VyAsogrhUAerN4LVfLEqVxQ1+1mK7Z+w6vlwInN4HHeuG5zluc359g=="
    asr_engine = "fast-whisper"
    embedding_model = "gemini-embedding-001"
    
    # Email Configuration (Default: 163 Mail)
    MAIL_PROVIDER = "163"  # "163", "gmail", "outlook", "generic"
    MAIL_USER = "rambotai@163.com"
    MAIL_PASS = "LQJbifKjyyK8CwtW"
    IMAP_SERVER = "imap.163.com"
    SMTP_SERVER = "smtp.163.com"
    IMAP_PORT = 993
    SMTP_PORT = 465
    MAIL_CHECK_INTERVAL = 30  # Seconds between checks

    # Middleware Configuration
    tool_selector_max_tools = 5
    tool_selector_enable_logging = False
    