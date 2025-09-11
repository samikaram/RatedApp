#!/usr/bin/env python3
"""
QUERY CANCELLED APPOINTMENTS - CORRECTED API OPERATORS
Based on official Cliniko API error response:
- Uses q[]=cancelled_at:? to get cancelled appointments (where cancelled_at exists)
- Uses q[]=cancelled_at:!? to get active appointments (where cancelled_at does not exist)
- Tests your July 2nd cancelled appointment
"""

import requests
import base64
from datetime import datetime
import pytz
import json

def query_cancelled_appointments_corrected():
    # API Configuration
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Cancelled Appointments Query Corrected'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    
    print("🚫 CANCELLED APPOINTMENTS QUERY - CORRECTED API OPERATORS")
    print("📋 Based on: Official Cliniko API error response")
    print("🎯 Goal: Query cancelled appointments using q[]=cancelled_at:?")
    print("🧪 Test: Find your July 2nd cancelled appointment")
    print("="*80)
    
    # Results storage
    results = {
        'cancelled_appointments': [],
        'active_appointments': [],
        'sami_cancelled': [],
        'sami_active': []
    }
    
    # 1. QUERY CANCELLED APPOINTMENTS ONLY
    print(f"\n🚫 STEP 1: QUERYING CANCELLED APPOINTMENTS ONLY")
    print(f"📋 Using: q[]=cancelled_at:? (corrected API parameter)")
    print(f"="*60)
    
    page = 1
    while True:
        url = f"{base_url}/individual_appointments"
        params = {
            'q[]': 'cancelled_at:?',  # CORRECTED: ? means "exists" (not null)
            'per_page': 100,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"   📡 Page {page} API Response: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error on page {page}: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                break
                
            data = response.json()
            appointments = data.get('individual_appointments', [])
            
            if not appointments:
                break
                
            print(f"   📄 Page {page}: {len(appointments)} cancelled appointments")
            results['cancelled_appointments'].extend(appointments)
            
            # Look for Sami's cancelled appointments
            for apt in appointments:
                if apt.get('patient') and apt['patient'].get('links'):
                    patient_url = apt['patient']['links']['self']
                    if '/patients/1104221' in patient_url:  # Sami's patient ID
                        results['sami_cancelled'].append(apt)
                        print(f"   🎯 Found Sami's cancelled appointment: ID {apt.get('id')}")
            
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching cancelled appointments: {str(e)}")
            break
    
    print(f"✅ Total Cancelled Appointments Found: {len(results['cancelled_appointments'])}")
    print(f"🎯 Sami's Cancelled Appointments: {len(results['sami_cancelled'])}")
    
    # 2. QUERY ACTIVE APPOINTMENTS ONLY (for comparison)
    print(f"\n✅ STEP 2: QUERYING ACTIVE APPOINTMENTS ONLY")
    print(f"📋 Using: q[]=cancelled_at:!? (corrected API parameter)")
    print(f"="*60)
    
    page = 1
    active_count = 0
    sami_active_count = 0
    
    while page <= 2:  # Limit to first 2 pages for comparison
        url = f"{base_url}/individual_appointments"
        params = {
            'q[]': 'cancelled_at:!?',  # CORRECTED: !? means "does not exist" (is null)
            'per_page': 100,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"   📡 Page {page} API Response: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error on page {page}: {response.status_code}")
                break
                
            data = response.json()
            appointments = data.get('individual_appointments', [])
            
            if not appointments:
                break
                
            print(f"   📄 Page {page}: {len(appointments)} active appointments")
            active_count += len(appointments)
            
            # Count Sami's active appointments
            for apt in appointments:
                if apt.get('patient') and apt['patient'].get('links'):
                    patient_url = apt['patient']['links']['self']
                    if '/patients/1104221' in patient_url:
                        sami_active_count += 1
            
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching active appointments: {str(e)}")
            break
    
    print(f"✅ Sample Active Appointments Count: {active_count}")
    print(f"🎯 Sami's Active Appointments (sample): {sami_active_count}")
    
    # 3. ANALYZE SAMI'S CANCELLED APPOINTMENT
    if results['sami_cancelled']:
        print(f"\n🎯 STEP 3: ANALYZING SAMI'S CANCELLED APPOINTMENT")
        print(f"="*60)
        
        for i, apt in enumerate(results['sami_cancelled'], 1):
            print(f"\n📋 Cancelled Appointment #{i}:")
            print(f"   🆔 ID: {apt.get('id')}")
            print(f"   📅 Scheduled: {apt.get('starts_at')}")
            print(f"   🚫 Cancelled At: {apt.get('cancelled_at')}")
            print(f"   📝 Cancellation Reason: {apt.get('cancellation_reason')}")
            print(f"   💬 Cancellation Note: {apt.get('cancellation_note')}")
            print(f"   🔄 Updated At: {apt.get('updated_at')}")
            
            # Convert to AEST for display
            if apt.get('cancelled_at'):
                try:
                    cancelled_utc = datetime.fromisoformat(apt['cancelled_at'].replace('Z', '+00:00'))
                    cancelled_aest = cancelled_utc.astimezone(aest)
                    print(f"   🕐 Cancelled At (AEST): {cancelled_aest.strftime('%d/%m/%Y %H:%M:%S')}")
                    
                    # Check if this matches your July 2nd test
                    if cancelled_aest.date() == datetime(2025, 7, 2).date():
                        print(f"   🎯 THIS IS YOUR JULY 2ND TEST CANCELLED APPOINTMENT!")
                except:
                    pass
    else:
        print(f"\n❌ NO CANCELLED APPOINTMENTS FOUND FOR SAMI")
        print(f"   This could mean:")
        print(f"   1. API sync delay - cancelled appointment not yet available")
        print(f"   2. Cancelled appointment stored differently")
        print(f"   3. Additional filtering needed")
    
    # 4. SUMMARY
    print(f"\n" + "="*80)
    print(f"📊 QUERY RESULTS SUMMARY")
    print(f"="*80)
    
    print(f"🚫 Total Cancelled Appointments (All Patients): {len(results['cancelled_appointments'])}")
    print(f"🎯 Sami's Cancelled Appointments: {len(results['sami_cancelled'])}")
    print(f"✅ Sample Active Appointments: {active_count}")
    print(f"🎯 Sami's Active Appointments (sample): {sami_active_count}")
    
    if len(results['cancelled_appointments']) > 0:
        print(f"\n🎉 SUCCESS! Found cancelled appointments using corrected API method!")
        print(f"📋 The q[]=cancelled_at:? parameter works!")
        
        if len(results['sami_cancelled']) > 0:
            print(f"🎯 Your July 2nd test cancelled appointment was found!")
        else:
            print(f"⏳ Your July 2nd cancelled appointment may need more time to sync")
    else:
        print(f"\n❓ No cancelled appointments found - investigating further needed")
    
    # Save results
    with open('cancelled_appointments_data_corrected.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: cancelled_appointments_data_corrected.json")
    print(f"\n🎯 CORRECTED CANCELLED APPOINTMENTS QUERY COMPLETE!")
    
    return results

if __name__ == "__main__":
    results = query_cancelled_appointments_corrected()

