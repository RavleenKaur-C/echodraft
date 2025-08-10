import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # Safe: only reads local .env if present

@dataclass
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    langsmith_api_key: str | None = os.getenv("LANGSMITH_API_KEY")
    notion_api_key: str | None = os.getenv("NOTION_API_KEY")
    linkedin_token: str | None = os.getenv("LINKEDIN_ACCESS_TOKEN")

settings = Settings()
