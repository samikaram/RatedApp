import requests
import base64

# Test different authentication methods
RAW_API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"

def test_basic_endpoint():
    """Test the most basic endpoint - users"""
    print("🔐 TESTING BASIC API AUTHENTICATION")
    print("="*50)
    
    # Method 1: Direct API key (what worked July 3)
    print("\n🧪 Method 1: Direct API key")
    headers1 = {
        'Authorization': f'Basic {RAW_API_KEY}',
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Test'
    }
    
    try:
        response1 = requests.get(f"{BASE_URL}/users", headers=headers1)
        print(f"   Status: {response1.status_code}")
        if response1.status_code == 200:
            print("   ✅ SUCCESS - Direct API key works!")
            return True
        else:
            print(f"   ❌ FAILED - {response1.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {str(e)}")
    
    # Method 2: Base64 encoded API key
    print("\n🧪 Method 2: Base64 encoded API key")
    encoded_key = base64.b64encode(f"{RAW_API_KEY}:".encode()).decode()
    headers2 = {
        'Authorization': f'Basic {encoded_key}',
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Test'
    }
    
    try:
        response2 = requests.get(f"{BASE_URL}/users", headers=headers2)
        print(f"   Status: {response2.status_code}")
        if response2.status_code == 200:
            print("   ✅ SUCCESS - Base64 encoded works!")
            return True
        else:
            print(f"   ❌ FAILED - {response2.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {str(e)}")
    
    # Method 3: Try patients endpoint directly
    print("\n🧪 Method 3: Test patients endpoint with Method 1")
    try:
        response3 = requests.get(f"{BASE_URL}/patients", headers=headers1, params={'per_page': 1})
        print(f"   Status: {response3.status_code}")
        if response3.status_code == 200:
            print("   ✅ SUCCESS - Patients endpoint accessible!")
            return True
        else:
            print(f"   ❌ FAILED - {response3.text}")
    except Exception as e:
        print(f"   ❌ ERROR - {str(e)}")
    
    return False

if __name__ == "__main__":
    print("🔍 DIAGNOSING API AUTHENTICATION ISSUE")
    print("🗓️ API was working July 3, 2025")
    print("🗓️ Now failing July 7, 2025")
    print("🎯 Testing basic authentication...")
    
    if test_basic_endpoint():
        print("\n✅ AUTHENTICATION WORKS!")
        print("🔧 Issue is likely in the search syntax")
    else:
        print("\n❌ AUTHENTICATION FAILED!")
        print("🔑 API key may have expired or changed")
        print("💡 Need to generate new API key from Cliniko")
