import requests
import json

def test_generate_plan():
    url = "http://127.0.0.1:8001/api/v1/projects/generate-plan"
    payload = {
        "description": "Micro-Arc Oxidation (MAO) Pilot Plant Development",
        "industry": "Engineering"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_generate_plan()
