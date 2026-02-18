import requests
import json

BASE_URL = "http://localhost:8000"

def test_save_form():
    print("Testing POST /jd/jd/forms...")
    payload = {
        "role": "Test Role",
        "department": "Engineering",
        "location": "Remote",
        "employment_type": "Full-time"
    }
    try:
        res = requests.post(f"{BASE_URL}/jd/jd/forms", json=payload)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
        if res.status_code == 200:
            return res.json()["id"]
    except Exception as e:
        print(f"Error: {e}")
    return None

def test_get_forms():
    print("\nTesting GET /jd/jd/forms...")
    try:
        res = requests.get(f"{BASE_URL}/jd/jd/forms")
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    form_id = test_save_form()
    if form_id:
        test_get_forms()
