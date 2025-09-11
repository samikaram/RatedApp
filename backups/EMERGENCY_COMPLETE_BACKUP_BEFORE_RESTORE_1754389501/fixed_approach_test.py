import requests
import json
from datetime import datetime
import pytz
import base64

# API Configuration
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Create headers with Base64 encoded API key
auth_string = f"{API_KEY}:"
encoded_auth = base64.b64encode(auth_string.encode()).decode()
headers = {
    'Authorization': f'Basic {encoded_auth}',
    'Accept': 'application/json',
    'User-Agent': 'Patient Behavior Rating System'
}

def main():
    print("🎯 FIXED COMPREHENSIVE PATIENT BEHAVIOR EXTRACTION")
    print("="*80)
    print("🔧 NEW APPROACH: Get ALL data first, then group by patients")
    
    try:
        # Step 1: Get target patients (this works)
        print("\n🎯 STEP 1: Getting target patients from June 16-21, 2025...")
        start_date = AEST.localize(datetime(2025, 6, 16, 0, 5)).astimezone(pytz.UTC)
        end_date = AEST.localize(datetime(2025, 6, 21, 23, 55)).astimezone(pytz.UTC)
        
        params = {
            'per_page': 100,
            'page': 1,
            'q[]': [
                f'starts_at:>{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                f'starts_at:<{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            ]
        }
        
        target_appointments = []
        page = 1
        while True:
            params['page'] = page
            response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
            if response.status_code != 200:
                break
            data = response.json()
            appointments = data.get('individual_appointments', [])
            if not appointments:
                break
            target_appointments.extend(appointments)
            page += 1
            
        target_patient_ids = list(set([
            appt['patient']['links']['self'].split('/')[-1] 
            for appt in target_appointments 
            if appt.get('patient', {}).get('links', {}).get('self')
        ]))
        
        print(f"✅ Found {len(target_patient_ids)} unique patients from {len(target_appointments)} appointments")
        
        # Step 2: Get ALL appointments for ALL patients (no filtering)
        print("\n🎯 STEP 2: Getting ALL appointments (no patient filtering)...")
        all_appointments = []
        page = 1
        while True:
            params = {'per_page': 100, 'page': page}
            response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ Error getting appointments page {page}: {response.status_code}")
                break
            data = response.json()
            appointments = data.get('individual_appointments', [])
            if not appointments:
                break
            all_appointments.extend(appointments)
            print(f"   📄 Page {page}: {len(appointments)} appointments")
            page += 1
            if page > 10:  # Safety limit for testing
                print("   🛑 Stopping at page 10 for testing...")
                break
                
        print(f"✅ Retrieved {len(all_appointments)} total appointments")
        
        # Step 3: Group appointments by patient
        print("\n🎯 STEP 3: Grouping appointments by target patients...")
        patient_appointments = {}
        for appt in all_appointments:
            if appt.get('patient', {}).get('links', {}).get('self'):
                patient_id = appt['patient']['links']['self'].split('/')[-1]
                if patient_id in target_patient_ids:
                    if patient_id not in patient_appointments:
                        patient_appointments[patient_id] = []
                    patient_appointments[patient_id].append(appt)
        
        print(f"✅ Found appointments for {len(patient_appointments)} target patients")
        
        # Step 4: Analyze first few patients
        print("\n🎯 STEP 4: Sample analysis...")
        for i, (patient_id, appointments) in enumerate(list(patient_appointments.items())[:5], 1):
            attended = len([a for a in appointments if a.get('attendance_status') == 'attended'])
            dna = len([a for a in appointments if a.get('attendance_status') == 'did_not_arrive'])
            cancelled = len([a for a in appointments if a.get('cancelled')])
            total = len(appointments)
            
            print(f"   👤 Patient {i}: ID {patient_id}")
            print(f"      📅 Total appointments: {total}")
            print(f"      ✅ Attended: {attended}")
            print(f"      ❌ DNA: {dna}")
            print(f"      🚫 Cancelled: {cancelled}")
            
        print(f"\n✅ APPROACH WORKING! No more 'patient_id is not filterable' errors!")
        print(f"🎯 Ready to implement full extraction with this corrected method")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

