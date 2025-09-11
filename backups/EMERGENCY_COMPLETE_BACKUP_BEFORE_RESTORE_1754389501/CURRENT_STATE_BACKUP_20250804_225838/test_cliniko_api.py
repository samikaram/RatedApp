import requests
import base64

API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"

print("🔍 CLINIKO API CONNECTIVITY DIAGNOSTIC")
print("="*50)
print("🎯 Testing different authentication methods...")

# Method 1: Direct Basic auth (current method in script)
print("\n📡 Method 1: Direct Basic Auth")
headers1 = {
    'User-Agent': 'Patient Rating App (sami@example.com)',
    'Accept': 'application/json',
    'Authorization': f'Basic {API_KEY}:'
}

response1 = requests.get("https://api.au1.cliniko.com/v1/patients?per_page=1", headers=headers1)
print(f"   Status Code: {response1.status_code}")
if response1.status_code == 200:
    print("   ✅ SUCCESS - Method 1 works!")
    data = response1.json()
    print(f"   📊 Found {len(data.get('patients', []))} patients")
else:
    print(f"   ❌ FAILED - {response1.text[:200]}")

# Method 2: Base64 encoded Basic auth
print("\n📡 Method 2: Base64 Encoded Basic Auth")
auth_string = base64.b64encode(f'{API_KEY}:'.encode()).decode()
headers2 = {
    'User-Agent': 'Patient Rating App (sami@example.com)',
    'Accept': 'application/json',
    'Authorization': f'Basic {auth_string}'
}

response2 = requests.get("https://api.au1.cliniko.com/v1/patients?per_page=1", headers=headers2)
print(f"   Status Code: {response2.status_code}")
if response2.status_code == 200:
    print("   ✅ SUCCESS - Method 2 works!")
    data = response2.json()
    print(f"   📊 Found {len(data.get('patients', []))} patients")
else:
    print(f"   ❌ FAILED - {response2.text[:200]}")

# Method 3: Test individual appointments endpoint specifically
print("\n📡 Method 3: Testing Individual Appointments Endpoint")
response3 = requests.get("https://api.au1.cliniko.com/v1/individual_appointments?per_page=1", headers=headers1)
print(f"   Status Code: {response3.status_code}")
if response3.status_code == 200:
    print("   ✅ SUCCESS - Individual appointments endpoint works!")
    data = response3.json()
    print(f"   📊 Found {len(data.get('individual_appointments', []))} appointments")
else:
    print(f"   ❌ FAILED - {response3.text[:200]}")

# Method 4: Test with requests auth parameter
print("\n📡 Method 4: Using requests.auth parameter")
headers4 = {
    'User-Agent': 'Patient Rating App (sami@example.com)',
    'Accept': 'application/json'
}

response4 = requests.get(
    "https://api.au1.cliniko.com/v1/patients?per_page=1", 
    headers=headers4,
    auth=(API_KEY, '')
)
print(f"   Status Code: {response4.status_code}")
if response4.status_code == 200:
    print("   ✅ SUCCESS - requests.auth method works!")
    data = response4.json()
    print(f"   📊 Found {len(data.get('patients', []))} patients")
else:
    print(f"   ❌ FAILED - {response4.text[:200]}")

print("\n🎯 DIAGNOSTIC COMPLETE")
print("="*50)
