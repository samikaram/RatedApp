import requests
import base64
from datetime import datetime, timedelta
import pytz
import json

def debug_first_10_patients():
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Debug First 10 Patients'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    
    # Date range: 16/06/2025 to 21/06/2025 (inclusive) in AEST
    start_date_aest = aest.localize(datetime(2025, 6, 16, 0, 0, 0))
    end_date_aest = aest.localize(datetime(2025, 6, 21, 23, 59, 59))
    
    print(f"🔧 DEBUG: FIRST 10 PATIENTS EXTRACTION")
    print(f"📅 Date Range: 16/06/2025 - 21/06/2025 (AEST)")
    print(f"🕐 Start: {start_date_aest.strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print(f"🕐 End: {end_date_aest.strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("="*80)
    
    # Step 1: Get appointments and examine structure
    print(f"\n🔍 STEP 1: Getting appointments and examining structure")
    appointments_in_range = []
    
    try:
        appointments_url = f"{base_url}/individual_appointments?per_page=50&page=1"
        response = requests.get(appointments_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            appointments = data.get('individual_appointments', [])
            
            print(f"✅ Retrieved {len(appointments)} appointments from first page")
            
            # Examine first appointment structure
            if appointments:
                print(f"\n🔍 EXAMINING FIRST APPOINTMENT STRUCTURE:")
                first_apt = appointments[0]
                print(f"   Keys in appointment: {list(first_apt.keys())}")
                
                # Look for patient information
                if 'patient' in first_apt:
                    print(f"   Patient field: {first_apt['patient']}")
                if 'patient_id' in first_apt:
                    print(f"   Patient ID field: {first_apt['patient_id']}")
                if 'links' in first_apt:
                    print(f"   Links field: {first_apt['links']}")
                
                print(f"   Appointment starts_at: {first_apt.get('starts_at')}")
            
            # Filter appointments within date range
            for apt in appointments:
                if apt.get('starts_at'):
                    apt_utc = datetime.fromisoformat(apt['starts_at'].replace('Z', '+00:00'))
                    apt_aest = apt_utc.astimezone(aest)
                    
                    if start_date_aest <= apt_aest <= end_date_aest:
                        apt['starts_at_aest'] = apt_aest
                        appointments_in_range.append(apt)
            
            print(f"✅ Found {len(appointments_in_range)} appointments in date range")
            
        else:
            print(f"❌ Failed to get appointments: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Exception getting appointments: {str(e)}")
        return
    
    # Step 2: Extract patient IDs and debug the extraction
    print(f"\n🔍 STEP 2: Extracting patient IDs from appointments")
    patient_ids = set()
    
    for i, apt in enumerate(appointments_in_range[:20]):  # Look at first 20 appointments
        print(f"\n   📅 Appointment {i+1}: {apt['starts_at_aest'].strftime('%d/%m/%Y %H:%M AEST')}")
        
        # Try different ways to extract patient ID
        patient_id = None
        
        # Method 1: Direct patient.id
        if apt.get('patient') and isinstance(apt['patient'], dict) and apt['patient'].get('id'):
            patient_id = apt['patient']['id']
            print(f"      ✅ Found patient ID via patient.id: {patient_id}")
        
        # Method 2: Direct patient_id field
        elif apt.get('patient_id'):
            patient_id = apt['patient_id']
            print(f"      ✅ Found patient ID via patient_id: {patient_id}")
        
        # Method 3: Links field
        elif apt.get('links') and apt['links'].get('patient'):
            patient_link = apt['links']['patient']
            # Extract ID from URL if it's a link
            if isinstance(patient_link, str) and '/patients/' in patient_link:
                patient_id = patient_link.split('/patients/')[-1].split('?')[0]
                print(f"      ✅ Found patient ID via links: {patient_id}")
            else:
                print(f"      🔍 Patient link format: {patient_link}")
        
        else:
            print(f"      ❌ No patient ID found in appointment")
            print(f"      🔍 Available fields: {list(apt.keys())}")
        
        if patient_id:
            patient_ids.add(patient_id)
    
    print(f"\n✅ Extracted {len(patient_ids)} unique patient IDs")
    
    # Step 3: Get detailed patient data for first 10 patients
    print(f"\n🔍 STEP 3: Getting detailed patient data (first 10)")
    successful_patients = {}
    failed_patients = []
    
    for i, patient_id in enumerate(list(patient_ids)[:10], 1):
        print(f"\n   👤 Patient {i}: ID {patient_id}")
        
        try:
            patient_url = f"{base_url}/patients/{patient_id}"
            patient_response = requests.get(patient_url, headers=headers)
            
            print(f"      📡 API call: {patient_url}")
            print(f"      📊 Status: {patient_response.status_code}")
            
            if patient_response.status_code == 200:
                patient_data = patient_response.json()
                successful_patients[patient_id] = patient_data
                
                name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
                print(f"      ✅ SUCCESS: {name}")
                
                # Show key patient data
                if patient_data.get('date_of_birth'):
                    birth_date = datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d')
                    age = (datetime.now() - birth_date).days // 365
                    print(f"      🎂 Age: {age} years")
                
            elif patient_response.status_code == 404:
                print(f"      ❌ Patient not found (404)")
                failed_patients.append((patient_id, "Not found"))
                
            elif patient_response.status_code == 401:
                print(f"      ❌ Authentication failed (401)")
                failed_patients.append((patient_id, "Auth failed"))
                
            else:
                print(f"      ❌ Error {patient_response.status_code}: {patient_response.text[:100]}")
                failed_patients.append((patient_id, f"Error {patient_response.status_code}"))
                
        except Exception as e:
            print(f"      ❌ Exception: {str(e)}")
            failed_patients.append((patient_id, f"Exception: {str(e)}"))
    
    # Step 4: Summary report
    print(f"\n" + "="*80)
    print(f"📋 DEBUG SUMMARY REPORT")
    print(f"="*80)
    
    print(f"\n📊 EXTRACTION RESULTS:")
    print(f"   📅 Appointments in range: {len(appointments_in_range)}")
    print(f"   🔢 Unique patient IDs found: {len(patient_ids)}")
    print(f"   ✅ Successful patient extractions: {len(successful_patients)}")
    print(f"   ❌ Failed patient extractions: {len(failed_patients)}")
    
    if successful_patients:
        print(f"\n✅ SUCCESSFUL PATIENTS:")
        for patient_id, patient_data in successful_patients.items():
            name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
            print(f"   • {patient_id}: {name}")
    
    if failed_patients:
        print(f"\n❌ FAILED PATIENTS:")
        for patient_id, error in failed_patients:
            print(f"   • {patient_id}: {error}")
    
    print(f"\n🔍 NEXT STEPS:")
    if successful_patients:
        print(f"   ✅ Patient extraction is working!")
        print(f"   🚀 Ready to scale up to full dataset")
    else:
        print(f"   ❌ Need to investigate patient ID extraction method")
        print(f"   🔧 Check appointment structure and API permissions")

if __name__ == "__main__":
    debug_first_10_patients()
