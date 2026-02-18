import requests

api_url = "http://127.0.0.1:8000/api/v1/tasks/1"
data = {
    "status": "in_progress",
    "bogus_field": "ignore me",
    "dependencies": [{"target_id": 2, "relation": "FS", "lag": 0.0}]
}

try:
    # Try updating a task that exists (ID 1 might not exist, let's find one)
    res = requests.get("http://127.0.0.1:8000/api/v1/projects")
    projects = res.json()
    if projects:
        task_id = projects[0]['tasks'][0]['id']
        url = f"http://127.0.0.1:8000/api/v1/tasks/{task_id}"
        print(f"Testing PUT on {url}")
        res = requests.put(url, json=data)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:200]}")
    else:
        print("No projects found to test.")
except Exception as e:
    print(f"Error: {e}")
