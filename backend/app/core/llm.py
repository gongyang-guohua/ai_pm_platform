# from google import genai # Moved to lazy import
from app.core.config import settings
import asyncio

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = None
        self.client = None
        self.tokenizer = None
        
        print(f"Initializing LLM Service with provider: {self.provider}")

        if self.provider == "google":
            self.api_key = settings.GOOGLE_API_KEY
            if not self.api_key:
                print("WARNING: GOOGLE_API_KEY is not set.")
            else:
                try:
                    from google import genai
                    self.client = genai.Client(api_key=self.api_key)
                except ImportError:
                    print("Error: google-genai package not found. Please install it.")
                except Exception as e:
                    print(f"Failed to initialize Google GenAI Client: {e}")
        
        elif self.provider == "local":
            try:
                from llama_cpp import Llama
                
                model_path = settings.MODEL_PATH
                if not model_path:
                    # Default fallback or scan
                    import os
                    if os.path.exists(r"F:\File_Commander\models\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"):
                        model_path = r"F:\File_Commander\models\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
                    else:
                        print("WARNING: MODEL_PATH not set and default not found.")
                
                if model_path:
                    print(f"Loading local model from {model_path}...")
                    # Initialize Llama (GGUF)
                    # n_gpu_layers=-1 attempts to offload all layers to GPU if available
                    self.client = Llama(
                        model_path=model_path,
                        n_gpu_layers=-1, 
                        n_ctx=8192,
                        n_batch=512,
                        verbose=True
                    )
                    print("Local model loaded successfully.")
            except ImportError:
                print("Error: llama-cpp-python not installed. Please run 'uv sync'.")
            except Exception as e:
                print(f"Failed to load local model: {e}")
                
        elif self.provider == "huggingface":
             self.api_key = settings.HUGGINGFACE_API_KEY
             if not self.api_key:
                 print("WARNING: HUGGINGFACE_API_KEY is not set.")

    async def generate_text(self, prompt: str) -> str:
        if self.provider == "google":
            if not self.client:
                return "Error: Google Client not initialized (check API Key)."
            
            # Retry logic for 429 Resource Exhausted
            import re
            
            max_retries = 3
            base_delay = 2
            
            for attempt in range(max_retries):
                try:
                    await asyncio.sleep(1)
                    # Run the synchronous generate_content in a thread pool
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model='gemini-1.5-flash',
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    error_msg = str(e)
                    print(f"DEBUG: LLM Attempt {attempt+1} failed: {error_msg}")
                    
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"DEBUG: Rate limit hit. Waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                            
                    if attempt == max_retries - 1:
                        return f"Error generating content after {max_retries} attempts: {error_msg}"
                    await asyncio.sleep(2)
            
            return "Error: Unknown failure in generate_text."

        elif self.provider == "local":
            if not self.client:
                return "Error: Local model not loaded (check MODEL_PATH)."
            
            try:
                # Run synchronous Llama inference in thread pool
                output = await asyncio.to_thread(
                    self.client.create_chat_completion,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI Project Management Assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                    temperature=0.7
                )
                return output['choices'][0]['message']['content']
            except Exception as e:
                print(f"Local generation error: {e}")
                return f"Error during local generation: {e}"

        elif self.provider == "huggingface":
            return "Hugging Face Remote API not yet implemented."
            
        elif self.provider == "openai":
            return "OpenAI provider not yet implemented."
        else:
            return "Unknown LLM Provider."

    async def generate_json(self, prompt: str) -> dict:
        """
        Generates JSON output from the LLM. 
        Wraps generate_text and attempts to parse the result as JSON.
        """
        import json
        import re

        # Append instruction to force JSON if not already present
        if "json" not in prompt.lower():
            prompt += "\nOutput valid JSON only."

        text_response = await self.generate_text(prompt)
        
        # Clean up markdown code blocks if present
        text_response = text_response.strip()
        if text_response.startswith("```"):
            # Remove first line (```json or ```) and last line (```)
            text_response = re.sub(r"^```\w*\n", "", text_response)
            text_response = re.sub(r"\n```$", "", text_response)
        
        try:
            return json.loads(text_response)
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from LLM: {text_response}")
            # Fallback or retry logic could go here
            return {"error": "Failed to parse JSON", "raw": text_response}

llm_service = LLMService()
