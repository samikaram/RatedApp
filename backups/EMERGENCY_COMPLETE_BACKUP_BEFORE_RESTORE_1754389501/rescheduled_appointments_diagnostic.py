#!/usr/bin/env python3
"""
RESCHEDULED APPOINTMENTS DIAGNOSTIC SCRIPT
- Finds appointments updated during June 16-21 but scheduled after June 21
- Identifies the missing 15 appointments from rescheduling activity
"""

import requests
import base64
from datetime import datetime, timedelta
import pytz
import json

def rescheduled_appointments_diagnostic():
    # API Configuration (using your working API key)
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication (same as working script)
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Rescheduled Appointments Diagnostic'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    utc = pytz.UTC
    
    print("🔍 RESCHEDULED APPOINTMENTS DIAGNOSTIC")
    print("📅 Target Range: 16/06/2025 - 21/06/2025 (AEST)")
    print("🎯 Goal: Find appointments UPDATED during June 16-21 but SCHEDULED after June 21")
    print("🎯 Expected: 15 missing appointments (172 total - 157 found = 15)")
    print("="*80)
    
    # Target date range (when rescheduling activity happened)
    target_start_aest = aest.localize(datetime(2025, 6, 16, 0, 0, 0))
    target_end_aest = aest.localize(datetime(2025, 6, 21, 23, 59, 59))
    
    # Extended search range (where rescheduled appointments might be)
    search_start_aest = aest.localize(datetime(2025, 6, 22, 0, 0, 0))  # Day after target range
    search_end_aest = aest.localize(datetime(2025, 8, 31, 23, 59, 59))   # Extended forward range
    
    # Convert to UTC for API
    search_start_utc = search_start_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    search_end_utc = search_end_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"🔍 Searching appointments from {search_start_aest.strftime('%d/%m/%Y')} to {search_end_aest.strftime('%d/%m/%Y')}")
    print(f"🎯 Looking for updates during {target_start_aest.strftime('%d/%m/%Y')} to {target_end_aest.strftime('%d/%m/%Y')}")
    
    # Get appointments in the extended range
    print(f"\n📡 STEP 1: Extracting appointments from extended range...")
    all_appointments = []
    page = 1
    
    while True:
        url = f"{base_url}/individual_appointments"
        params = {
            'q[]': [
                f'starts_at:>{search_start_utc}',
                f'starts_at:<{search_end_utc}'
            ],
            'per_page': 100,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ Error on page {page}: {response.status_code}")
                break
                
            data = response.json()
            appointments = data.get('individual_appointments', [])
            
            if not appointments:
                break
                
            print(f"   📄 Page {page}: {len(appointments)} appointments")
            all_appointments.extend(appointments)
            
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching appointments: {str(e)}")
            break
    
    print(f"✅ Total appointments in extended range: {len(all_appointments)}")
    
    # Analyze appointments for rescheduling patterns
    print(f"\n🔍 STEP 2: Analyzing appointments for rescheduling patterns...")
    
    rescheduled_appointments = []
    
    for apt in all_appointments:
        try:
            # Parse timestamps
            starts_at_str = apt.get('starts_at')
            created_at_str = apt.get('created_at')
            updated_at_str = apt.get('updated_at')
            
            if not all([starts_at_str, created_at_str, updated_at_str]):
                continue
            
            # Convert to datetime objects
            starts_at_utc = datetime.strptime(starts_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc)
            created_at_utc = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc)
            updated_at_utc = datetime.strptime(updated_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc)
            
            # Convert to AEST
            starts_at_aest = starts_at_utc.astimezone(aest)
            created_at_aest = created_at_utc.astimezone(aest)
            updated_at_aest = updated_at_utc.astimezone(aest)
            
            # CORRECTED LOGIC: Find appointments that were:
            # 1. Updated during June 16-21 (rescheduling activity in target period)
            # 2. Currently scheduled after June 21 (moved forward)
            # 3. Updated significantly after creation (indicating a reschedule, not just a minor edit)
            
            update_in_target_range = target_start_aest <= updated_at_aest <= target_end_aest
            scheduled_after_target = starts_at_aest > target_end_aest
            significant_update = (updated_at_aest - created_at_aest).total_seconds() > 3600  # More than 1 hour difference
            
            if update_in_target_range and scheduled_after_target and significant_update:
                # Get patient info
                patient_name = "Unknown"
                patient_id = None
                
                if apt.get('patient') and apt['patient'].get('links'):
                    patient_url = apt['patient']['links']['self']
                    patient_id = patient_url.split('/')[-1]
                    
                    # Try to get patient name from a separate API call
                    try:
                        patient_response = requests.get(patient_url, headers=headers)
                        if patient_response.status_code == 200:
                            patient_data = patient_response.json()
                            first_name = patient_data.get('first_name', '')
                            last_name = patient_data.get('last_name', '')
                            patient_name = f"{first_name} {last_name}".strip()
                    except:
                        pass
                
                rescheduled_appointments.append({
                    'appointment_id': apt.get('id'),
                    'patient_id': patient_id,
                    'patient_name': patient_name,
                    'created_at_aest': created_at_aest,
                    'updated_at_aest': updated_at_aest,
                    'starts_at_aest': starts_at_aest,
                    'days_moved_forward': (starts_at_aest.date() - target_end_aest.date()).days,
                    'update_gap_hours': (updated_at_aest - created_at_aest).total_seconds() / 3600,
                    'attendance_status': {
                        'patient_arrived': apt.get('patient_arrived'),
                        'did_not_arrive': apt.get('did_not_arrive'),
                        'cancelled_at': apt.get('cancelled_at')
                    }
                })
                
        except Exception as e:
            print(f"❌ Error processing appointment {apt.get('id')}: {str(e)}")
            continue
    
    # Results
    print(f"\n📊 RESCHEDULING ANALYSIS RESULTS:")
    print(f"="*80)
    print(f"🎯 Expected missing appointments: 15")
    print(f"✅ Found rescheduled appointments: {len(rescheduled_appointments)}")
    
    if len(rescheduled_appointments) == 15:
        print(f"🎉 PERFECT MATCH! Found exactly the missing 15 appointments!")
    elif len(rescheduled_appointments) > 0:
        print(f"🔍 Found {len(rescheduled_appointments)} rescheduled appointments")
        print(f"📊 Still need to find: {15 - len(rescheduled_appointments)} more appointments")
    else:
        print(f"❌ No rescheduled appointments found with current criteria")
        print(f"💡 May need to adjust search criteria or look for other patterns")
    
    # Detailed breakdown
    if rescheduled_appointments:
        print(f"\n🔍 DETAILED BREAKDOWN OF RESCHEDULED APPOINTMENTS:")
        print(f"="*80)
        
        for i, apt in enumerate(rescheduled_appointments, 1):
            print(f"\n{i}. 📅 Appointment ID: {apt['appointment_id']}")
            print(f"   👤 Patient: {apt['patient_name']} (ID: {apt['patient_id']})")
            print(f"   📝 Created: {apt['created_at_aest'].strftime('%d/%m/%Y %H:%M AEST')}")
            print(f"   ✏️  Updated: {apt['updated_at_aest'].strftime('%d/%m/%Y %H:%M AEST')} ← Rescheduling activity")
            print(f"   📅 Current time: {apt['starts_at_aest'].strftime('%d/%m/%Y %H:%M AEST')}")
            print(f"   ➡️  Moved forward by: {apt['days_moved_forward']} days")
            print(f"   ⏱️  Update gap: {apt['update_gap_hours']:.1f} hours after creation")
            
            # Attendance status
            status = apt['attendance_status']
            if status['cancelled_at']:
                print(f"   🚫 Status: Cancelled")
            elif status['patient_arrived']:
                print(f"   ✅ Status: Attended")
            elif status['did_not_arrive']:
                print(f"   ❌ Status: DNA")
            else:
                print(f"   ⏳ Status: Scheduled")
    
    # Summary calculation
    print(f"\n" + "="*80)
    print(f"📋 FINAL SUMMARY")
    print(f"="*80)
    print(f"🎯 Original extraction: 157 appointments in June 16-21 range")
    print(f"🔄 Rescheduled forward: {len(rescheduled_appointments)} appointments")
    print(f"🧮 Total appointments that were in target period: {157 + len(rescheduled_appointments)}")
    print(f"📊 Expected total (Cliniko dashboard): 172")
    
    if 157 + len(rescheduled_appointments) == 172:
        print(f"🎉 ✅ PERFECT MATCH! Mystery solved!")
    else:
        remaining = 172 - (157 + len(rescheduled_appointments))
        print(f"🔍 Still missing: {remaining} appointments")
        if remaining > 0:
            print(f"💡 These might be: cancelled appointments, different appointment types, or other patterns")
    
    # Save results
    results = {
        'analysis_date': datetime.now(aest).isoformat(),
        'target_range': '16/06/2025 - 21/06/2025',
        'search_range': f'{search_start_aest.strftime("%d/%m/%Y")} - {search_end_aest.strftime("%d/%m/%Y")}',
        'summary': {
            'original_extraction': 157,
            'rescheduled_forward': len(rescheduled_appointments),
            'calculated_total': 157 + len(rescheduled_appointments),
            'expected_total': 172,
            'perfect_match': 157 + len(rescheduled_appointments) == 172
        },
        'rescheduled_appointments': rescheduled_appointments
    }
    
    try:
        with open('rescheduled_appointments_analysis.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Analysis saved to: rescheduled_appointments_analysis.json")
    except Exception as e:
        print(f"❌ Failed to save analysis: {str(e)}")
    
    print(f"\n🎯 RESCHEDULED APPOINTMENTS DIAGNOSTIC COMPLETE!")
    
    return results

if __name__ == "__main__":
    results = rescheduled_appointments_diagnostic()
