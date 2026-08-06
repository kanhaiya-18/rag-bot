from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings

model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=settings.GOOGLE_API_KEY
)