
import google.generativeai as genai

api_key = "AIzaSyCW7aJCBWLKQkGfBnC8nhC2jC1UWFXPilY" 
genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
