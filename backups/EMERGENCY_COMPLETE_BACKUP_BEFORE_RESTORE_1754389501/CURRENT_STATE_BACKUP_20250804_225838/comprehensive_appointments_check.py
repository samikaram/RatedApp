#!/usr/bin/env python3
"""
COMPREHENSIVE APPOINTMENTS CHECK - ALL TYPES & CANCELLATIONS
- Checks Individual Appointments (done: 157 found)
- Checks Group Appointments (new)
- Checks Attendees (new - likely where cancelled appointments are hiding)
- Finds all cancellation statuses across all appointment types
"""

import requests
import base64
from datetime import datetime
import pytz
import time

def comprehensive_appointments_check():
    # API Configuration (using working API key from breakthrough)
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication (proven working method)
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Comprehensive Appointments Check'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    utc = pytz.UTC
    
    print("🔍 COMPREHENSIVE APPOINTMENTS CHECK - ALL TYPES")
    print("📅 Target Range: 16/06/2025 - 21/06/2025 (AEST)")
    print("🎯 Goal: Find ALL appointments including cancelled ones across all endpoints")
    print("💡 Focus: Individual Appointments + Group Appointments + Attendees")
    print("="*80)
    
    # Same date range as breakthrough extraction
    target_start_aest = aest.localize(datetime(2025, 6, 16, 0, 0, 0))
    target_end_aest = aest.localize(datetime(2025, 6, 21, 23, 59, 59))
    
    # Convert to UTC
    target_start_utc = target_start_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    target_end_utc = target_end_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"🎯 Date Range:")
    print(f"   📅 AEST: {target_start_aest.strftime('%d/%m/%Y %H:%M')} - {target_end_aest.strftime('%d/%m/%Y %H:%M')}")
    print(f"   🌍 UTC: {target_start_utc} - {target_end_utc}")
    
    # Results storage
    all_results = {
        'individual_appointments': [],
        'group_appointments': [],
        'attendees': [],
        'cancelled_individual': [],
        'cancelled_group': [],
        'cancelled_attendees': []
    }
    
    # 1. CHECK INDIVIDUAL APPOINTMENTS (we know this works)
    print(f"\n📡 STEP 1: INDIVIDUAL APPOINTMENTS")
    print(f"="*50)
    
    page = 1
    while True:
        url = f"{base_url}/individual_appointments"
        params = {
            'q[]': [
                f'starts_at:>{target_start_utc}',
                f'starts_at:<{target_end_utc}'
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
            all_results['individual_appointments'].extend(appointments)
            
            # Count cancelled individual appointments
            for apt in appointments:
                if apt.get('cancelled_at'):
                    all_results['cancelled_individual'].append(apt)
            
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching individual appointments: {str(e)}")
            break
    
    print(f"✅ Individual Appointments: {len(all_results['individual_appointments'])}")
    print(f"🚫 Cancelled Individual: {len(all_results['cancelled_individual'])}")
    
    # 2. CHECK GROUP APPOINTMENTS (new check)
    print(f"\n📡 STEP 2: GROUP APPOINTMENTS")
    print(f"="*50)
    
    page = 1
    while True:
        url = f"{base_url}/group_appointments"
        params = {
            'q[]': [
                f'starts_at:>{target_start_utc}',
                f'starts_at:<{target_end_utc}'
            ],
            'per_page': 100,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 404:
                print(f"   ℹ️  Group appointments endpoint not available or no data")
                break
            elif response.status_code != 200:
                print(f"❌ Error on page {page}: {response.status_code}")
                break
                
            data = response.json()
            appointments = data.get('group_appointments', [])
            
            if not appointments:
                break
                
            print(f"   📄 Page {page}: {len(appointments)} group appointments")
            all_results['group_appointments'].extend(appointments)
            
            # Count cancelled group appointments
            for apt in appointments:
                if apt.get('cancelled_at'):
                    all_results['cancelled_group'].append(apt)
            
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching group appointments: {str(e)}")
            break
    
    print(f"✅ Group Appointments: {len(all_results['group_appointments'])}")
    print(f"🚫 Cancelled Group: {len(all_results['cancelled_group'])}")
    
    # 3. CHECK ATTENDEES (your key suggestion!)
    print(f"\n📡 STEP 3: ATTENDEES (Key Check - Likely Where Cancelled Appointments Are)")
    print(f"="*50)
    
    # For attendees, we need to check a broader range since they're linked to appointments
    # We'll look for attendees with appointments in our target range
    page = 1
    attendees_found = 0
    
    while True:
        url = f"{base_url}/attendees"
        params = {
            'per_page': 100,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 404:
                print(f"   ℹ️  Attendees endpoint not available")
                break
            elif response.status_code != 200:
                print(f"❌ Error on page {page}: {response.status_code}")
                break
                
            data = response.json()
            attendees = data.get('attendees', [])
            
            if not attendees:
                break
            
            # Filter attendees by appointment date
            relevant_attendees = []
            for attendee in attendees:
                # Check if attendee's appointment is in our target range
                if attendee.get('group_appointment') and attendee['group_appointment'].get('links'):
                    # We'll need to check the group appointment date
                    # For now, collect all attendees and filter later
                    relevant_attendees.append(attendee)
            
            print(f"   📄 Page {page}: {len(attendees)} attendees ({len(relevant_attendees)} potentially relevant)")
            all_results['attendees'].extend(relevant_attendees)
            attendees_found += len(attendees)
            
            # Count cancelled attendees
            for attendee in relevant_attendees:
                if attendee.get('cancelled_at'):
                    all_results['cancelled_attendees'].append(attendee)
            
            if len(attendees) < 100:
                break
                
            page += 1
            
            # Limit attendees check to avoid too much data
            if attendees_found > 1000:
                print(f"   ⚠️  Limiting attendees check to avoid excessive data")
                break
            
        except Exception as e:
            print(f"❌ Error fetching attendees: {str(e)}")
            break
        
        # Rate limiting
        time.sleep(0.1)
    
    print(f"✅ Attendees Checked: {len(all_results['attendees'])}")
    print(f"🚫 Cancelled Attendees: {len(all_results['cancelled_attendees'])}")
    
    # 4. ANALYSIS AND RESULTS
    print(f"\n📊 COMPREHENSIVE ANALYSIS RESULTS")
    print(f"="*80)
    
    total_individual = len(all_results['individual_appointments'])
    total_group = len(all_results['group_appointments'])
    total_attendees = len(all_results['attendees'])
    
    total_cancelled_individual = len(all_results['cancelled_individual'])
    total_cancelled_group = len(all_results['cancelled_group'])
    total_cancelled_attendees = len(all_results['cancelled_attendees'])
    
    print(f"📋 APPOINTMENT COUNTS:")
    print(f"   📅 Individual Appointments: {total_individual}")
    print(f"   👥 Group Appointments: {total_group}")
    print(f"   🎫 Attendees: {total_attendees}")
    print(f"   🧮 Total Appointments Found: {total_individual + total_group}")
    
    print(f"\n🚫 CANCELLATION BREAKDOWN:")
    print(f"   🚫 Cancelled Individual: {total_cancelled_individual}")
    print(f"   🚫 Cancelled Group: {total_cancelled_group}")
    print(f"   🚫 Cancelled Attendees: {total_cancelled_attendees}")
    print(f"   🧮 Total Cancelled: {total_cancelled_individual + total_cancelled_group + total_cancelled_attendees}")
    
    # Show cancelled appointment details
    if total_cancelled_individual > 0:
        print(f"\n🚫 CANCELLED INDIVIDUAL APPOINTMENTS:")
        for i, apt in enumerate(all_results['cancelled_individual'], 1):
            cancelled_at = apt.get('cancelled_at', 'Unknown')
            starts_at = apt.get('starts_at', 'Unknown')
            print(f"   {i}. ID: {apt.get('id')} | Scheduled: {starts_at} | Cancelled: {cancelled_at}")
    
    if total_cancelled_group > 0:
        print(f"\n🚫 CANCELLED GROUP APPOINTMENTS:")
        for i, apt in enumerate(all_results['cancelled_group'], 1):
            cancelled_at = apt.get('cancelled_at', 'Unknown')
            starts_at = apt.get('starts_at', 'Unknown')
            print(f"   {i}. ID: {apt.get('id')} | Scheduled: {starts_at} | Cancelled: {cancelled_at}")
    
    if total_cancelled_attendees > 0:
        print(f"\n🚫 CANCELLED ATTENDEES:")
        for i, attendee in enumerate(all_results['cancelled_attendees'], 1):
            cancelled_at = attendee.get('cancelled_at', 'Unknown')
            print(f"   {i}. Attendee ID: {attendee.get('id')} | Cancelled: {cancelled_at}")
    
    # Final calculation
    print(f"\n" + "="*80)
    print(f"📋 FINAL COMPREHENSIVE ANALYSIS")
    print(f"="*80)
    
    total_appointments_found = total_individual + total_group
    rescheduled_forward = 3  # From previous analysis
    
    print(f"🎯 Individual Appointments: {total_individual}")
    print(f"👥 Group Appointments: {total_group}")
    print(f"🔄 Previously found rescheduled forward: {rescheduled_forward}")
    print(f"🧮 Total accounted for: {total_appointments_found + rescheduled_forward}")
    print(f"📊 Expected total (Cliniko dashboard): 172")
    
    still_missing = 172 - (total_appointments_found + rescheduled_forward)
    print(f"🔍 Still missing: {still_missing} appointments")
    
    if still_missing <= 0:
        print(f"🎉 ✅ SUCCESS! All appointments found!")
    else:
        print(f"\n💡 NEXT STEPS TO FIND REMAINING {still_missing} APPOINTMENTS:")
        print(f"   1. 🔍 Check attendees more thoroughly (filter by appointment dates)")
        print(f"   2. 📅 Check for appointments spanning midnight")
        print(f"   3. 🏥 Check different business locations separately")
        print(f"   4. 📊 Verify dashboard counting methodology")
    
    print(f"\n🎯 COMPREHENSIVE APPOINTMENTS CHECK COMPLETE!")
    
    return all_results

if __name__ == "__main__":
    results = comprehensive_appointments_check()

