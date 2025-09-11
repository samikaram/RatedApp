import requests
import base64
from datetime import datetime
import pytz

def test_cliniko_with_blog_method():
    # Your API key (already includes au1 shard)
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # CORRECT: Basic Authentication (from blog)
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App (sami@sportsmedicineclinic.com.au)'
    }
    
    # CORRECT: Australian shard URL (from blog)
    base_url = "https://api.au1.cliniko.com/v1"
    
    aest = pytz.timezone('Australia/Sydney')
    print(f"🕐 AEST Time: {datetime.now(aest).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🔧 Testing CORRECTED Authentication (Based on Blog)")
    print("="*60)
    
    # Test basic connectivity
    try:
        print("\n🔍 Testing /users/me endpoint...")
        response = requests.get(f"{base_url}/users/me", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authentication successful!")
            print(f"User: {data.get('first_name', '')} {data.get('last_name', '')}")
            print(f"Role: {data.get('role', 'Unknown')}")
            
            # Test patient data access
            print(f"\n🔍 Testing patient data access...")
            patients_response = requests.get(f"{base_url}/patients?per_page=1", headers=headers)
            if patients_response.status_code == 200:
                patients_data = patients_response.json()
                print(f"✅ Patient access: {patients_data.get('total_entries', 0)} patients found")
                return True
            else:
                print(f"❌ Patient access failed: {patients_response.status_code}")
                
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = test_cliniko_with_blog_method()
    if success:
        print("\n🎉 Ready to test your 11 behavior categories with correct authentication!")
    else:
        print("\n❌ Still having authentication issues")

