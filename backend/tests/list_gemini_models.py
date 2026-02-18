
import asyncio
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from google import genai

async def list_models():
    print(f"Listing available models for key: {settings.GOOGLE_API_KEY[:5]}...")
    
    if not settings.GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY is not set.")
        return

    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        print("\n--- Available Models ---")
        try:
            # The list operation is synchronous in the new SDK unless using AsyncClient
            for model in client.models.list():
                print(f"- {model.name} (DisplayName: {model.display_name})")
        except Exception as e:
            print(f"Error listing models: {e}")

    except Exception as e:
        print(f"\nClient Initialization Failed: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
