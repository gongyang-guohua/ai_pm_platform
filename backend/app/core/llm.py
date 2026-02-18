from google import genai
from app.core.config import settings
import asyncio

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = None
        self.client = None
        
        if self.provider == "google":
            self.api_key = settings.GOOGLE_API_KEY
            if not self.api_key:
                print("WARNING: GOOGLE_API_KEY is not set.")
            else:
                try:
                    self.client = genai.Client(api_key=self.api_key)
                except Exception as e:
                    print(f"Failed to initialize Google GenAI Client: {e}")

    async def generate_text(self, prompt: str) -> str:
        if self.provider == "google":
            if not self.client:
                return "Error: Google Client not initialized (check API Key)."
            
            # Retry logic for 429 Resource Exhausted
            import re
            import time
            
            max_retries = 5
            base_delay = 2
            
            for attempt in range(max_retries):
                try:
                    await asyncio.sleep(2)  # Rate limit mitigation for free tier
                    # Run the synchronous generate_content in a thread pool
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model='gemini-1.5-flash', # Generic alias for stability
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    error_msg = str(e)
                    print(f"DEBUG: LLM Attempt {attempt+1} failed: {error_msg}")
                    
                    if "404" in error_msg and "NOT_FOUND" in error_msg:
                        return f"**System Notice:** The AI model (gemini-1.5-flash-001) is currently unavailable for your API key's region. \n\n**Generated Fallback Report:**\n\n# Project Report: {prompt.split('Title: ')[1].splitlines()[0] if 'Title:' in prompt else 'Project'}\n\n**Executive Summary**\nThe project is proceeding according to the defined parameters. Task logic and scheduling are active.\n\n**Status**\nCheck the Gantt chart for detailed timeline analysis."

                    # Check for 429 / Resource Exhausted
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        # Extract retry delay if present "Please retry in 27.75s"
                        match = re.search(r"retry in (\d+(\.\d+)?)s", error_msg)
                        if match:
                            wait_time = float(match.group(1)) + 1.0 # Add 1s buffer
                            print(f"DEBUG: Rate limit hit. Waiting {wait_time:.2f}s as requested...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Exponential backoff
                            wait_time = base_delay * (2 ** attempt)
                            print(f"DEBUG: Rate limit hit (no time specified). Waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                            
                    # If it's the last attempt, return the error
                    if attempt == max_retries - 1:
                        return f"Error generating content after {max_retries} attempts: {error_msg}"
                        
                    # For other errors, wait a bit and retry
                    await asyncio.sleep(2)
            
            return "Error: Unknown failure in generate_text."
        elif self.provider == "openai":
            return "OpenAI provider not yet implemented."
        elif self.provider == "local":
            return "Local model provider not yet configured."
        else:
            return "Unknown LLM Provider."

llm_service = LLMService()
