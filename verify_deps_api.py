
import requests
import json
import sys

API_URL = "http://127.0.0.1:8000/api/v1"

def test_upload_and_verify():
    # 1. Upload
    files = {'file': ('test_deps.xml', open('test_deps.xml', 'rb'), 'text/xml')}
    print("Uploading test_deps.xml...")
    try:
        r = requests.post(f"{API_URL}/projects/import", files=files)
        if r.status_code != 200:
            print(f"Upload failed: {r.status_code} {r.text}")
            return
        
        project = r.json()
        pid = project['id']
        print(f"Project uploaded. ID: {pid}")
        
        # 2. Verify Dependencies
        tasks = project.get('tasks', [])
        print(f"Found {len(tasks)} tasks.")
        
        task_b = next((t for t in tasks if t['title'] == 'Task B'), None)
        if not task_b:
            print("Task B not found!")
            return

        print(f"Task B Dependencies: {json.dumps(task_b.get('dependencies'), indent=2)}")
        
        deps = task_b.get('dependencies', [])
        if len(deps) > 0 and deps[0]['target_id'] is not None:
             print("SUCCESS: Dependencies found and serialized.")
        else:
             print("FAILURE: Dependencies missing or empty.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload_and_verify()
