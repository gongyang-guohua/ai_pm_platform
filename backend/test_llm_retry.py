
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'app'))
sys.path.append(os.getcwd())

from app.core.llm import llm_service

async def test_llm():
    print("Testing LLM generation with retry logic...")
    try:
        response = await llm_service.generate_text("Hello, say 'Test Successful' if you can hear me.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
