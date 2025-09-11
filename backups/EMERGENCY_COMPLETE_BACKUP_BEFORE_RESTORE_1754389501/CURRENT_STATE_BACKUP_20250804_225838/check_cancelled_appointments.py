#!/usr/bin/env python3
"""
CANCELLED APPOINTMENTS DIAGNOSTIC SCRIPT
- Uses same working extraction parameters from July 2 breakthrough
- Focuses on finding appointments with cancelled_at field populated
- Explains the missing 15 appointments (172 expected - 157 found = 15)
"""

import requests
import base64
from datetime import datetime
import pytz

def check_cancelled_appointments():
    # API Configuration (using working API key from breakthrough)
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication (proven working method)
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Cancelled Appointments Diagnostic'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    utc = pytz.UTC
    
    print("🔍 CANCELLED APPOINTMENTS DIAGNOSTIC")
    print("📅 Target Range: 16/06/2025 - 21/06/2025 (AEST)")
    print("🎯 Goal: Find cancelled appointments that explain missing 15 appointments")
    print("📊 Context: Breakthrough showed 0 cancelled appointments, but 15 are missing")
    print("="*80)
    
    # Same date range as breakthrough extraction
    target_start_aest = aest.localize(datetime(2025, 6, 16, 0, 0, 0))
    target_end_aest = aest.localize(datetime(2025, 6, 21, 23, 59, 59))
    
    # Convert to UTC (same as working extraction)
    target_start_utc = target_start_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    target_end_utc = target_end_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"🎯 Using same parameters as breakthrough extraction:")
    print(f"   📅 AEST Range: {target_start_aest.strftime('%d/%m/%Y %H:%M')} - {target_end_aest.strftime('%d/%m/%Y %H:%M')}")
    print(f"   🌍 UTC Range: {target_start_utc} - {target_end_utc}")
    
    # Extract ALL appointments using same method as breakthrough
    print(f"\n📡 EXTRACTING ALL APPOINTMENTS (including cancelled)...")
    all_appointments = []
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
            all_appointments.extend(appointments)
            
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching appointments: {str(e)}")
            break
    
    print(f"✅ Total appointments extracted: {len(all_appointments)}")
    
    # Analyze appointment statuses with focus on cancelled appointments
    print(f"\n🔍 ANALYZING APPOINTMENT STATUSES...")
    
    attended_appointments = []
    dna_appointments = []
    cancelled_appointments = []
    scheduled_appointments = []
    
    for apt in all_appointments:
        apt_id = apt.get('id')
        starts_at_str = apt.get('starts_at')
        
        # Convert start time to AEST for display
        starts_at_aest = "Unknown"
        if starts_at_str:
            try:
                starts_at_utc = datetime.strptime(starts_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc)
                starts_at_aest = starts_at_utc.astimezone(aest).strftime('%d/%m/%Y %H:%M AEST')
            except:
                pass
        
        # Check for cancellation
        cancelled_at = apt.get('cancelled_at')
        if cancelled_at:
            try:
                cancelled_at_utc = datetime.strptime(cancelled_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc)
                cancelled_at_aest = cancelled_at_utc.astimezone(aest).strftime('%d/%m/%Y %H:%M AEST')
            except:
                cancelled_at_aest = cancelled_at
            
            cancelled_appointments.append({
                'id': apt_id,
                'starts_at': starts_at_aest,
                'cancelled_at': cancelled_at_aest,
                'patient_arrived': apt.get('patient_arrived'),
                'did_not_arrive': apt.get('did_not_arrive'),
                'cancellation_reason': apt.get('cancellation_reason', 'No reason provided')
            })
        
        # Categorize based on attendance (same logic as breakthrough)
        elif apt.get('patient_arrived'):
            attended_appointments.append({
                'id': apt_id,
                'starts_at': starts_at_aest
            })
        elif apt.get('did_not_arrive'):
            dna_appointments.append({
                'id': apt_id,
                'starts_at': starts_at_aest
            })
        else:
            scheduled_appointments.append({
                'id': apt_id,
                'starts_at': starts_at_aest
            })
    
    # Results breakdown
    print(f"\n📊 APPOINTMENT STATUS BREAKDOWN:")
    print(f"="*80)
    print(f"   ✅ Attended: {len(attended_appointments)}")
    print(f"   ❌ DNA: {len(dna_appointments)}")
    print(f"   🚫 Cancelled: {len(cancelled_appointments)}")
    print(f"   ⏳ Scheduled: {len(scheduled_appointments)}")
    print(f"   🧮 Total: {len(all_appointments)}")
    
    # Compare with breakthrough results
    print(f"\n🔍 COMPARISON WITH BREAKTHROUGH RESULTS:")
    print(f"   📊 Breakthrough (July 2): 146 attended, 11 DNA, 0 cancelled = 157 total")
    print(f"   📊 Current analysis: {len(attended_appointments)} attended, {len(dna_appointments)} DNA, {len(cancelled_appointments)} cancelled = {len(all_appointments)} total")
    
    # Show cancelled appointments details
    if cancelled_appointments:
        print(f"\n🚫 DETAILED BREAKDOWN OF CANCELLED APPOINTMENTS:")
        print(f"="*80)
        
        for i, apt in enumerate(cancelled_appointments, 1):
            print(f"\n{i}. 📅 Appointment ID: {apt['id']}")
            print(f"   📅 Scheduled for: {apt['starts_at']}")
            print(f"   🚫 Cancelled at: {apt['cancelled_at']}")
            print(f"   📝 Reason: {apt['cancellation_reason']}")
            
            # Check if it was marked as attended or DNA after cancellation
            if apt['patient_arrived']:
                print(f"   ⚠️  Note: Marked as attended despite cancellation")
            elif apt['did_not_arrive']:
                print(f"   ⚠️  Note: Marked as DNA despite cancellation")
    else:
        print(f"\n🚫 NO CANCELLED APPOINTMENTS FOUND")
        print(f"   This confirms the breakthrough results showing 0 cancelled appointments")
    
    # Final calculation
    print(f"\n" + "="*80)
    print(f"📋 FINAL ANALYSIS")
    print(f"="*80)
    
    current_total = len(all_appointments)
    rescheduled_forward = 3  # From previous analysis
    calculated_total = current_total + rescheduled_forward
    
    print(f"🎯 Current extraction: {current_total} appointments")
    print(f"🔄 Previously found rescheduled forward: {rescheduled_forward} appointments")
    print(f"🧮 Total accounted for: {calculated_total}")
    print(f"📊 Expected total (Cliniko dashboard): 172")
    
    still_missing = 172 - calculated_total
    print(f"🔍 Still missing: {still_missing} appointments")
    
    if still_missing > 0:
        print(f"\n💡 POSSIBLE EXPLANATIONS FOR MISSING {still_missing} APPOINTMENTS:")
        print(f"   1. 📅 Different appointment types (group appointments, blocked time)")
        print(f"   2. 🏥 Different appointment endpoints (not individual_appointments)")
        print(f"   3. 🔄 Appointments rescheduled backward (to earlier dates)")
        print(f"   4. 📊 Dashboard counting logic differs from API extraction")
        print(f"   5. 🗓️  Appointments spanning midnight (timezone edge cases)")
    elif still_missing == 0:
        print(f"🎉 ✅ PERFECT MATCH! All appointments accounted for!")
    
    print(f"\n🎯 CANCELLED APPOINTMENTS DIAGNOSTIC COMPLETE!")
    
    return {
        'total_appointments': len(all_appointments),
        'attended': len(attended_appointments),
        'dna': len(dna_appointments),
        'cancelled': len(cancelled_appointments),
        'scheduled': len(scheduled_appointments),
        'cancelled_details': cancelled_appointments
    }

if __name__ == "__main__":
    results = check_cancelled_appointments()

