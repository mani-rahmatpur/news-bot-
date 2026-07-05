import os

# کلید دائمی و رایگان Gemini شما که مستقیماً در کد جایگذاری شده است
API_KEY: str = "AQ.Ab8RN6LOiwb0ZjXdYI13vooUhpyqslFHolMer-3Ev_5tT74UBg"

# تنظیم متغیر محیطی سیستم به صورت خودکار توسط خود پایتون
os.environ["GEMINI_API_KEY"] = API_KEY

# نام فایل دیتابیس
DB_NAME: str = "news_database.db"

# پرامپت اختصاصی شما برای پردازش متن خبر
CUSTOM_SYSTEM_PROMPT: str = """
You are an expert technology journalist. Translate the following news article into Persian (Farsi). 
Provide a catchy headline, a brief 3-sentence summary, and 3 key bullet points. 
Keep the tone professional and engaging.
"""
