import requests
import json
from datetime import datetime
import pytz

def verify_cliniko_behavior_mapping():
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # AEST timezone setup
    aest = pytz.timezone('Australia/Sydney')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Behavior Mapping Verification'
    }
    
    base_url = "https://api.cliniko.com/v1"
    
    print(f"🕐 AEST Time: {datetime.now(aest).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🔍 VERIFYING BEHAVIOR CATEGORY DATA MAPPING")
    print("🏥 Sports Medicine Clinic - Parramatta & Peakhurst")
    print("="*70)
    
    # Test specific endpoints for your 11 behavior categories
    behavior_tests = {
        'patients': {
            'endpoint': '/patients?per_page=2',
            'behaviors': ['Age Demographics'],
            'key_fields': ['date_of_birth', 'referral_source', 'created_at']
        },
        'appointments': {
            'endpoint': '/appointments?per_page=3',
            'behaviors': ['Appointments Booked', 'Cancellations', 'DNA', 'Consecutive Attendance'],
            'key_fields': ['starts_at', 'ends_at', 'cancelled_at', 'did_not_arrive', 'patient_arrived', 'cancellation_reason']
        },
        'invoices': {
            'endpoint': '/invoices?per_page=3',
            'behaviors': ['Yearly Spend', 'Unpaid Invoices', 'Non-Attendance Fees'],
            'key_fields': ['total_amount', 'status', 'issue_date', 'closed_at', 'patient_id']
        },
        'referral_sources': {
            'endpoint': '/referral_sources?per_page=3',
            'behaviors': ['Referrer Score'],
            'key_fields': ['name', 'patients']
        }
    }
    
    results = {}
    
    for endpoint_name, config in behavior_tests.items():
        print(f"\n🔍 Testing {endpoint_name.upper()} for behaviors: {', '.join(config['behaviors'])}")
        
        try:
            response = requests.get(f"{base_url}{config['endpoint']}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                total_records = data.get('total_entries', 0)
                
                # Get sample record
                sample_record = {}
                if data.get(endpoint_name) and len(data[endpoint_name]) > 0:
                    sample_record = data[endpoint_name][0]
                
                # Check if key fields exist
                available_fields = list(sample_record.keys()) if sample_record else []
                missing_fields = [field for field in config['key_fields'] if field not in available_fields]
                found_fields = [field for field in config['key_fields'] if field in available_fields]
                
                results[endpoint_name] = {
                    'status': 'SUCCESS ✅',
                    'total_records': total_records,
                    'behaviors_supported': config['behaviors'],
                    'found_fields': found_fields,
                    'missing_fields': missing_fields,
                    'sample_data': {field: sample_record.get(field) for field in found_fields[:3]} if sample_record else {}
                }
                
                print(f"✅ {total_records} records found")
                print(f"   Found fields: {', '.join(found_fields)}")
                if missing_fields:
                    print(f"   ⚠️  Missing fields: {', '.join(missing_fields)}")
                
                # Show sample data with AEST conversion for timestamps
                if sample_record:
                    print("   Sample data:")
                    for field in found_fields[:3]:
                        value = sample_record.get(field)
                        if field in ['starts_at', 'ends_at', 'cancelled_at', 'created_at', 'issue_date', 'closed_at'] and value:
                            # Convert to AEST if it's a timestamp
                            try:
                                utc_dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                aest_dt = utc_dt.astimezone(aest)
                                print(f"     {field}: {aest_dt.strftime('%Y-%m-%d %H:%M:%S AEST')}")
                            except:
                                print(f"     {field}: {value}")
                        else:
                            print(f"     {field}: {value}")
                
            else:
                results[endpoint_name] = {
                    'status': f'ERROR ❌ - {response.status_code}',
                    'message': response.text[:200],
                    'behaviors_supported': config['behaviors']
                }
                print(f"❌ Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            results[endpoint_name] = {
                'status': f'EXCEPTION ❌',
                'message': str(e),
                'behaviors_supported': config['behaviors']
            }
            print(f"❌ Exception: {str(e)}")
    
    return results

if __name__ == "__main__":
    print("🚀 CLINIKO API BEHAVIOR MAPPING VERIFICATION")
    print("📊 Testing Data Availability for 11 Patient Behavior Categories")
    
    results = verify_cliniko_behavior_mapping()
    
    print("\n" + "="*70)
    print("📋 BEHAVIOR MAPPING VERIFICATION SUMMARY")
    print("="*70)
    
    all_behaviors = []
    successful_behaviors = []
    
    for endpoint, result in results.items():
        print(f"\n{endpoint.upper()}:")
        print(f"  Status: {result['status']}")
        print(f"  Behaviors: {', '.join(result['behaviors_supported'])}")
        
        all_behaviors.extend(result['behaviors_supported'])
        if 'SUCCESS' in result['status']:
            successful_behaviors.extend(result['behaviors_supported'])
            
        if 'total_records' in result:
            print(f"  Records Available: {result['total_records']}")
            if result.get('found_fields'):
                print(f"  Data Fields: ✅ {len(result['found_fields'])}/{len(result['found_fields']) + len(result.get('missing_fields', []))}")
    
    print(f"\n🎯 OVERALL BEHAVIOR COVERAGE:")
    print(f"   Total Behaviors: {len(set(all_behaviors))}")
    print(f"   Supported Behaviors: {len(set(successful_behaviors))}")
    print(f"   Coverage: {len(set(successful_behaviors))/len(set(all_behaviors))*100:.1f}%")
    
    print(f"\n🕐 Verification completed: {datetime.now(pytz.timezone('Australia/Sydney')).strftime('%Y-%m-%d %H:%M:%S AEST')}")

