import requests
import base64
from datetime import datetime
import pytz

def test_official_cliniko_api():
    # Your API key (includes au1 shard)
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # OFFICIAL: Basic Authentication (API key as username, no password)
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    # OFFICIAL: Required headers
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App (sami@sportsmedicineclinic.com.au)'
    }
    
    # OFFICIAL: Base URL with shard
    base_url = "https://api.au1.cliniko.com/v1"
    
    aest = pytz.timezone('Australia/Sydney')
    print(f"🕐 AEST Time: {datetime.now(aest).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🔧 Testing OFFICIAL Cliniko API Requirements")
    print("="*60)
    
    # Test endpoints from your behavior mapping
    test_endpoints = [
        ('/patients', 'Age Demographics'),
        ('/individual_appointments', 'Appointments, Cancellations, DNA, Attendance'),
        ('/invoices', 'Yearly Spend, Unpaid Invoices, Fees'),
        ('/referral_sources', 'Referrer Score')
    ]
    
    successful_endpoints = []
    
    for endpoint, behaviors in test_endpoints:
        try:
            print(f"\n🔍 Testing {endpoint} for: {behaviors}")
            response = requests.get(f"{base_url}{endpoint}?per_page=1", headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total_entries', 0)
                print(f"✅ SUCCESS! {total} records available")
                successful_endpoints.append((endpoint, behaviors, total))
                
                # Show sample data structure for first record
                endpoint_key = endpoint.replace('/', '').replace('_', '_')
                if endpoint_key in data and data[endpoint_key]:
                    sample = data[endpoint_key][0]
                    print(f"   Sample fields: {list(sample.keys())[:5]}...")
                
            elif response.status_code == 401:
                print(f"❌ 401 - Authentication failed")
            elif response.status_code == 404:
                print(f"❌ 404 - Endpoint not found")
            else:
                print(f"❌ {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    return successful_endpoints

if __name__ == "__main__":
    print("🚀 OFFICIAL CLINIKO API VERIFICATION")
    print("📊 Testing Your 11 Behavior Categories")
    
    successful = test_official_cliniko_api()
    
    print(f"\n" + "="*60)
    print(f"📋 RESULTS SUMMARY")
    print(f"="*60)
    
    if successful:
        print(f"✅ {len(successful)} endpoints working successfully!")
        for endpoint, behaviors, total in successful:
            print(f"   {endpoint}: {total} records ({behaviors})")
        print(f"\n🎉 Ready to build your patient behavior rating system!")
    else:
        print(f"❌ No endpoints working - need to investigate API key permissions")

