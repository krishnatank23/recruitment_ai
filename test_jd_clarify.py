import requests
import json

BASE_URL = "http://localhost:8000"

def test_clarify():
    print("Testing POST /jd/jd/clarify...")
    payload = {
        "role": "Software Engineer",
        "department": "Engineering",
        "location": "Remote",
        "employment_type": "Full-time",
        "must_have_skills": "Python, FastAPI, React",
        "key_responsibilities": "Build backend APIs, Integrate frontend",
        "experience": "3-5 years"
    }
    try:
        res = requests.post(f"{BASE_URL}/jd/jd/clarify", json=payload)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("Response JSON keys:", res.json().keys())
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"Error Response: {res.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_clarify()
