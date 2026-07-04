import os

# بارگذاری توکن هوش مصنوعی از متغیرهای سیستم
API_KEY: str = os.getenv("OPENAI_API_KEY", "your_fallback_api_key_here")

# نام فایل دیتابیس
DB_NAME: str = "news_database.db"

# پرامپت اختصاصی شما برای پردازش متن خبر
CUSTOM_SYSTEM_PROMPT: str = """
You are an expert technology journalist. Translate the following news article into Persian (Farsi). 
Provide a catchy headline, a brief 3-sentence summary, and 3 key bullet points. 
Keep the tone professional and engaging.
"""
