import os
from typing import Optional
from google import genai
from google.genai import types
from config import CUSTOM_SYSTEM_PROMPT

# Fetch key from environment or use direct fallback if needed
API_KEY: str = os.getenv("GEMINI_API_KEY", "your_fallback_key_here")

# Initialize the official Google GenAI Client
client = genai.Client(api_key=API_KEY)


def process_news_with_ai(article_content: str) -> Optional[str]:
    """Sends raw article text to Gemini 2.5 Flash for processing and translation."""
    try:
        # Configure system instructions and low temperature for accuracy
        config = types.GenerateContentConfig(
            system_instruction=CUSTOM_SYSTEM_PROMPT,
            temperature=0.3,
        )

        # Call the fast, modern Gemini 2.5 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=article_content,
            config=config,
        )

        # Return the clean processed text output
        if response.text:
            return str(response.text)
        return None

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None
