"""Quick smoke test for auth endpoints."""
import urllib.request
import urllib.parse
import json
import sys

BASE = "http://localhost:8000"

def post_json(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def post_form(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def get_auth(path, token):
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# ------- Tests -------
all_pass = True

# 1. Health check
try:
    r = urllib.request.urlopen(f"{BASE}/", timeout=5)
    print(f"[PASS] Health: {r.status}")
except Exception as e:
    print(f"[FAIL] Health: {e}")
    sys.exit(1)

# 2. Register Team Lead
status, body = post_json("/auth/register", {
    "name": "Alice TL", "email": "alice@test.com",
    "password": "test123", "role": "team_lead",
})
ok = status == 201
if not ok: all_pass = False
print(f"[{'PASS' if ok else 'FAIL'}] Register TL: {status}")

# 3. Register HR
status, body = post_json("/auth/register", {
    "name": "Bob HR", "email": "bob@test.com",
    "password": "test123", "role": "hr",
})
ok = status == 201
if not ok: all_pass = False
print(f"[{'PASS' if ok else 'FAIL'}] Register HR: {status}")

# 4. Duplicate email
status, body = post_json("/auth/register", {
    "name": "Dup", "email": "alice@test.com",
    "password": "x", "role": "hr",
})
ok = status == 409
if not ok: all_pass = False
print(f"[{'PASS' if ok else 'FAIL'}] Duplicate: {status}")

# 5. Login
status, body = post_form("/auth/login", {
    "username": "alice@test.com", "password": "test123",
})
ok = status == 200 and isinstance(body, dict)
if not ok: all_pass = False
token = body.get("access_token", "") if isinstance(body, dict) else ""
role = body.get("user", {}).get("role", "?") if isinstance(body, dict) else "?"
print(f"[{'PASS' if ok else 'FAIL'}] Login: {status} role={role}")

# 6. /me
status, body = get_auth("/auth/me", token)
ok = status == 200 and isinstance(body, dict)
if not ok: all_pass = False
name = body.get("name", "?") if isinstance(body, dict) else "?"
print(f"[{'PASS' if ok else 'FAIL'}] /me: {status} name={name}")

# 7. Bad token
status, body = get_auth("/auth/me", "bad-token")
ok = status == 401
if not ok: all_pass = False
print(f"[{'PASS' if ok else 'FAIL'}] Bad token: {status}")

print(f"\n=== {'ALL PASS' if all_pass else 'SOME FAILED'} ===")
