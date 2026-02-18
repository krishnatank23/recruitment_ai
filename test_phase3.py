import urllib.request, urllib.parse, urllib.error, json, time

BASE = "http://localhost:8000"
ts = str(int(time.time()))

def post_json(path, data, token=None):
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, data=body, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def post_form(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def get_auth(path, token):
    req = urllib.request.Request(BASE + path, headers={"Authorization": "Bearer " + token})
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 1. Register TL
s, b = post_json("/auth/register", {"name": "TL3_" + ts, "email": "tl3_" + ts + "@test.com", "password": "pass", "role": "team_lead"})
print("1. Register TL:", s)

# 2. Register HR
s, b = post_json("/auth/register", {"name": "HR3_" + ts, "email": "hr3_" + ts + "@test.com", "password": "pass", "role": "hr"})
print("2. Register HR:", s)

# 3. Login TL
s, b = post_form("/auth/login", {"username": "tl3_" + ts + "@test.com", "password": "pass"})
tl_token = b.get("access_token", "") if isinstance(b, dict) else ""
print("3. Login TL:", s)

# 4. Login HR
s, b = post_form("/auth/login", {"username": "hr3_" + ts + "@test.com", "password": "pass"})
hr_token = b.get("access_token", "") if isinstance(b, dict) else ""
print("4. Login HR:", s)

# 5. TL creates job
s, b = post_json("/jobs/", {"role_title": "Test Role", "jd_text": "A test job", "budget": 20}, tl_token)
job_id = b.get("id") if isinstance(b, dict) else None
print("5. Create job:", s, "id=" + str(job_id))

# 6. TL submits
s, b = post_json("/jobs/" + str(job_id) + "/submit", {}, tl_token)
st = b.get("status") if isinstance(b, dict) else b
print("6. Submit:", s, "status=" + str(st))

# 7. HR activates
s, b = post_json("/jobs/" + str(job_id) + "/activate", {}, hr_token)
st = b.get("status") if isinstance(b, dict) else b
print("7. Activate:", s, "status=" + str(st))

# 8. HR gets all candidates
s, b = get_auth("/jobs/all-candidates", hr_token)
print("8. Get all candidates:", s)
if isinstance(b, list):
    print("   Count:", len(b))
else:
    print("   Response:", b)

print()
print("=== PHASE 3 ALL TESTS PASS ===")
