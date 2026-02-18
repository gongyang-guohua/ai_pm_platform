
import asyncio
import os
import sys

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.llm import LLMService
# Use `google.genai` in the test import to confirm correct package usage
from google import genai 

async def test_connection():
    print(f"Testing LLM Conneciton...")
    print(f"Provider: {settings.LLM_PROVIDER}")
    
    if not settings.GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY is not set in .env file.")
        print("Please add your key to d:\\ai_pm_platform\\backend\\.env")
        return

    service = LLMService()
    try:
        if service.provider == "google":
            # Simple generation test
            print("Sending request to Google Gemini (via google-genai SDK)...")
            
            # Use generate_text method instead of direct model access for abstraction
            response_text = await service.generate_text("Hello, confirm you are working with the new SDK.")
            
            print("\nResponse from Gemini:")
            print("-" * 20)
            print(response_text)
            print("-" * 20)
            
            if "Error" not in response_text:
                print("Connection Successful!")
            else:
                print("Connection Failed (API Error).")

    except Exception as e:
        print(f"\nConnection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
