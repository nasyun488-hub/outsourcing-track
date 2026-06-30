"""Test audit summary fix for primary_admin 500 bug."""
import requests
import json

s = requests.Session()
s.trust_env = False

BASE = 'http://localhost:8000'

def login(phone):
    r = s.post(f'{BASE}/api/auth/send-sms', json={'phone': phone})
    assert r.status_code == 200, f'send-sms {r.status_code}: {r.text}'
    sms_code = r.json()['code']
    r = s.post(f'{BASE}/api/auth/login', json={'phone': phone, 'code': sms_code})
    assert r.status_code == 200, f'login {r.status_code}: {r.text}'
    return r.json()['access_token']

# Enterprise admin
token_e = login('13800138000')
r = s.get(f'{BASE}/api/audit/summary', headers={'Authorization': f'Bearer {token_e}'})
print('=== Enterprise admin audit summary ===')
print(f'Status: {r.status_code}')
j = r.json()
if r.status_code == 200:
    print(f'total_logs: {j.get("total_logs")}')
    print(f'action_types: {json.dumps(j.get("action_type_counts"), ensure_ascii=False)}')
    print(f'user_count: {len(j.get("user_counts", []))}')
else:
    print(j)

# Primary admin (was returning 500 before fix)
token_p = login('13800138001')
r = s.get(f'{BASE}/api/audit/summary', headers={'Authorization': f'Bearer {token_p}'})
print()
print('=== Primary admin audit summary ===')
print(f'Status: {r.status_code}')
j = r.json()
if r.status_code == 200:
    print(f'total_logs: {j.get("total_logs")}')
    print(f'action_types: {json.dumps(j.get("action_type_counts"), ensure_ascii=False)}')
    print(f'user_count: {len(j.get("user_counts", []))}')
else:
    print(json.dumps(j, ensure_ascii=False))

print()
if r.status_code == 200:
    print('FIX CONFIRMED: primary_admin audit summary no longer returns 500')
else:
    print(f'FIX FAILED: status {r.status_code}')
