
import requests
import json
import sys

def test_project_planning():
    url = "http://localhost:8000/api/v1/projects/generate-plan"
    
    payload = {
        "description": "A web application for tracking personal finances, including income, expenses, and budget planning. It should have a dashboard and report generation.",
        "industry": "FinTech"
    }
    
    print(f"Sending request to {url}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("\nSuccess! Response:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"\nFailed with status code {response.status_code}:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Is it running?")

if __name__ == "__main__":
    test_project_planning()
