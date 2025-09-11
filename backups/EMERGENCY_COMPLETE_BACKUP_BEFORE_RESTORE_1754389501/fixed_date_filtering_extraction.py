import requests
import base64
from datetime import datetime, timedelta
import pytz
import json

def fixed_date_filtering_extraction():
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Fixed Date Filtering'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    utc = pytz.UTC
    
    # Date range: 16/06/2025 to 21/06/2025 in AEST
    start_date_aest = aest.localize(datetime(2025, 6, 16, 0, 0, 0))
    end_date_aest = aest.localize(datetime(2025, 6, 21, 23, 59, 59))
    
    # Convert to UTC for API filtering (CRITICAL FIX)
    start_date_utc = start_date_aest.astimezone(utc)
    end_date_utc = end_date_aest.astimezone(utc)
    
    # Format for Cliniko API (ISO format with Z)
    start_utc_str = start_date_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_utc_str = end_date_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"🔧 FIXED DATE FILTERING EXTRACTION")
    print(f"📅 AEST Range: 16/06/2025 00:00:00 - 21/06/2025 23:59:59")
    print(f"🌍 UTC Range: {start_utc_str} - {end_utc_str}")
    print("="*80)
    
    # Step 1: Get appointments using PROPER API filtering
    print(f"\n🔍 STEP 1: Using proper Cliniko API date filtering")
    
    # CRITICAL FIX: Use q[] parameters for server-side filtering
    appointments_url = (
        f"{base_url}/individual_appointments?"
        f"q[]=starts_at:>{start_utc_str}&"
        f"q[]=starts_at:<{end_utc_str}&"
        f"per_page=100"
    )
    
    print(f"🔗 API URL: {appointments_url}")
    
    try:
        response = requests.get(appointments_url, headers=headers)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            appointments = data.get('individual_appointments', [])
            total_entries = data.get('total_entries', 0)
            
            print(f"✅ SUCCESS: Found {len(appointments)} appointments on this page")
            print(f"📊 Total appointments in date range: {total_entries}")
            
            if appointments:
                print(f"\n🔍 SAMPLE APPOINTMENTS (showing first 3):")
                for i, apt in enumerate(appointments[:3], 1):
                    # Convert UTC back to AEST for display
                    apt_utc = datetime.fromisoformat(apt['starts_at'].replace('Z', '+00:00'))
                    apt_aest = apt_utc.astimezone(aest)
                    
                    print(f"   {i}. {apt_aest.strftime('%d/%m/%Y %H:%M AEST')} - Patient: {apt.get('patient_name', 'Unknown')}")
                    
                    # Show patient field structure
                    if apt.get('patient'):
                        print(f"      Patient field: {apt['patient']}")
            
            # Step 2: Extract patient IDs using correct method
            print(f"\n🔍 STEP 2: Extracting patient IDs from filtered appointments")
            patient_ids = set()
            
            for apt in appointments:
                patient_id = None
                
                # Extract patient ID from links field (based on debug findings)
                if apt.get('patient') and apt['patient'].get('links') and apt['patient']['links'].get('self'):
                    patient_url = apt['patient']['links']['self']
                    # Extract ID from URL: https://api.au1.cliniko.com/v1/patients/1109937
                    if '/patients/' in patient_url:
                        patient_id = patient_url.split('/patients/')[-1].split('?')[0]
                        patient_ids.add(patient_id)
            
            print(f"✅ Extracted {len(patient_ids)} unique patient IDs")
            
            # Step 3: Get detailed patient data (limit to first 10)
            print(f"\n🔍 STEP 3: Getting detailed patient data (first 10)")
            successful_patients = {}
            
            for i, patient_id in enumerate(list(patient_ids)[:10], 1):
                try:
                    patient_url = f"{base_url}/patients/{patient_id}"
                    patient_response = requests.get(patient_url, headers=headers)
                    
                    if patient_response.status_code == 200:
                        patient_data = patient_response.json()
                        successful_patients[patient_id] = patient_data
                        
                        name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
                        print(f"   ✅ Patient {i}: {name} (ID: {patient_id})")
                        
                        # Show demographics
                        if patient_data.get('date_of_birth'):
                            birth_date = datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d')
                            age = (datetime.now() - birth_date).days // 365
                            print(f"      🎂 Age: {age} years")
                        
                        # Show referral source
                        if patient_data.get('referral_source'):
                            print(f"      📍 Referral: {patient_data['referral_source']}")
                    
                    else:
                        print(f"   ❌ Patient {i}: Failed to get data (Status: {patient_response.status_code})")
                        
                except Exception as e:
                    print(f"   ❌ Patient {i}: Exception - {str(e)}")
            
            # Step 4: Show appointments for successful patients
            print(f"\n🔍 STEP 4: Showing appointments for extracted patients")
            for patient_id, patient_data in successful_patients.items():
                name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
                print(f"\n👤 {name} (ID: {patient_id}):")
                
                # Find appointments for this patient
                patient_appointments = []
                for apt in appointments:
                    if apt.get('patient') and apt['patient'].get('links'):
                        apt_patient_url = apt['patient']['links']['self']
                        if f'/patients/{patient_id}' in apt_patient_url:
                            apt_utc = datetime.fromisoformat(apt['starts_at'].replace('Z', '+00:00'))
                            apt_aest = apt_utc.astimezone(aest)
                            
                            status = "✅ Attended" if apt.get('patient_arrived') else "❌ DNA" if apt.get('did_not_arrive') else "📅 Scheduled"
                            if apt.get('cancelled_at'):
                                status = "🚫 Cancelled"
                            
                            patient_appointments.append({
                                'date': apt_aest,
                                'status': status
                            })
                
                patient_appointments.sort(key=lambda x: x['date'])
                for apt in patient_appointments:
                    print(f"   📅 {apt['date'].strftime('%d/%m/%Y %H:%M AEST')}: {apt['status']}")
        
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print(f"\n" + "="*80)
    print(f"🎯 FIXED DATE FILTERING RESULTS")
    print(f"✅ Used proper q[] parameter filtering to avoid 2012 data")
    print(f"📅 Filtered server-side for exact date range: 16/06/2025 - 21/06/2025")
    print(f"🌍 Converted AEST to UTC for API, back to AEST for display")
    print(f"="*80)

if __name__ == "__main__":
    fixed_date_filtering_extraction()

