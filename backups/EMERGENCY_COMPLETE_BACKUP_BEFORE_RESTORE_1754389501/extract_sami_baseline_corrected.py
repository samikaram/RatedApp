#!/usr/bin/env python3
"""
SAMI KARAM BASELINE EXTRACTION - CORRECTED API METHODS
- Uses proper Cliniko API filtering based on official documentation
- Corrected patient search using q[] parameter format
- Ensures cancelled appointments are included in extraction
"""

import requests
import base64
from datetime import datetime
import pytz
import json

def extract_sami_baseline_corrected():
    # API Configuration (using working API key with full access)
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication (proven working method)
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Sami Baseline Extraction (Corrected)'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    utc = pytz.UTC
    
    print("👤 SAMI KARAM BASELINE EXTRACTION - CORRECTED API METHODS")
    print("🎯 Goal: Extract all current appointment data using proper Cliniko API filtering")
    print("📋 Based on: Official Cliniko API documentation")
    print("="*80)
    
    # Step 1: Find Sami Karam's patient record using correct API filtering
    print("🔍 STEP 1: Finding Sami Karam's patient record (corrected method)...")
    
    url = f"{base_url}/patients"
    params = {
        'q[]': [
            'first_name:~Sami',
            'last_name:~Karam'
        ],
        'per_page': 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"   📡 API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error searching for patient: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
            
        data = response.json()
        patients = data.get('patients', [])
        print(f"   🔍 Found {len(patients)} patients matching search")
        
        sami_patient = None
        for patient in patients:
            first_name = patient.get('first_name', '').lower()
            last_name = patient.get('last_name', '').lower()
            print(f"   👤 Patient: {patient.get('first_name')} {patient.get('last_name')} (ID: {patient.get('id')})")
            
            if 'sami' in first_name and 'karam' in last_name:
                sami_patient = patient
                break
        
        if not sami_patient:
            print("❌ Sami Karam not found in patient records")
            # Try alternative search without filtering
            print("🔍 Trying alternative search method...")
            
            url = f"{base_url}/patients"
            params = {'per_page': 100}
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                patients = data.get('patients', [])
                
                for patient in patients:
                    full_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".lower()
                    if 'sami' in full_name and 'karam' in full_name:
                        sami_patient = patient
                        print(f"   ✅ Found via alternative search: {patient.get('first_name')} {patient.get('last_name')}")
                        break
            
            if not sami_patient:
                return None
            
        patient_id = sami_patient.get('id')
        print(f"✅ Found Sami Karam - Patient ID: {patient_id}")
        print(f"   📝 Full Name: {sami_patient.get('first_name')} {sami_patient.get('last_name')}")
        print(f"   📧 Email: {sami_patient.get('email', 'Not provided')}")
        print(f"   📱 Phone: {sami_patient.get('phone_number', 'Not provided')}")
        
    except Exception as e:
        print(f"❌ Error finding patient: {str(e)}")
        return None
    
    # Step 2: Get ALL appointments for Sami Karam using correct API filtering
    print(f"\n🔍 STEP 2: Extracting ALL appointments for Sami Karam (including cancelled)...")
    
    all_appointments = []
    page = 1
    
    while True:
        url = f"{base_url}/individual_appointments"
        params = {
            'q[]': f'patient_id:={patient_id}',
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
                
            print(f"   📄 Page {page}: {len(appointments)} appointments")
            all_appointments.extend(appointments)
            
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching appointments: {str(e)}")
            break
    
    print(f"✅ Total appointments found for Sami: {len(all_appointments)}")
    
    # Step 3: Analyze appointment statuses (including cancelled)
    print(f"\n📊 STEP 3: Analyzing appointment statuses (focus on cancelled)...")
    
    attended_count = 0
    dna_count = 0
    cancelled_count = 0
    scheduled_count = 0
    
    appointment_details = []
    
    for apt in all_appointments:
        apt_id = apt.get('id')
        starts_at_str = apt.get('starts_at')
        
        # Convert to AEST for display
        starts_at_aest = "Unknown"
        if starts_at_str:
            try:
                starts_at_utc = datetime.strptime(starts_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc)
                starts_at_aest = starts_at_utc.astimezone(aest).strftime('%d/%m/%Y %H:%M AEST')
            except:
                pass
        
        # Check cancellation status first (priority)
        cancelled_at = apt.get('cancelled_at')
        cancellation_reason = apt.get('cancellation_reason')
        
        # Determine status
        status = "Unknown"
        if cancelled_at:
            status = "Cancelled"
            cancelled_count += 1
        elif apt.get('patient_arrived'):
            status = "Attended"
            attended_count += 1
        elif apt.get('did_not_arrive'):
            status = "DNA"
            dna_count += 1
        else:
            status = "Scheduled"
            scheduled_count += 1
        
        appointment_details.append({
            'id': apt_id,
            'starts_at': starts_at_aest,
            'status': status,
            'cancelled_at': cancelled_at,
            'cancellation_reason': cancellation_reason,
            'patient_arrived': apt.get('patient_arrived'),
            'did_not_arrive': apt.get('did_not_arrive'),
            'created_at': apt.get('created_at'),
            'updated_at': apt.get('updated_at')
        })
    
    # Results
    print(f"\n📊 SAMI'S APPOINTMENT STATUS BREAKDOWN:")
    print(f"="*50)
    print(f"   ✅ Attended: {attended_count}")
    print(f"   ❌ DNA: {dna_count}")
    print(f"   🚫 Cancelled: {cancelled_count}")
    print(f"   ⏳ Scheduled: {scheduled_count}")
    print(f"   🧮 Total: {len(all_appointments)}")
    
    # Show cancelled appointments specifically (this is what we're testing)
    cancelled_appointments = [apt for apt in appointment_details if apt['status'] == 'Cancelled']
    if cancelled_appointments:
        print(f"\n🚫 CANCELLED APPOINTMENTS FOUND:")
        print(f"="*50)
        for i, apt in enumerate(cancelled_appointments, 1):
            print(f"{i}. 📅 Scheduled: {apt['starts_at']}")
            print(f"   🚫 Cancelled at: {apt['cancelled_at']}")
            print(f"   📝 Reason: {apt['cancellation_reason'] or 'No reason provided'}")
            print(f"   🆔 ID: {apt['id']}")
    else:
        print(f"\n🚫 NO CANCELLED APPOINTMENTS FOUND (Current Baseline)")
        print(f"   This is expected before you add the test cancelled appointment")
    
    # Show recent appointments for context
    if appointment_details:
        print(f"\n📅 RECENT APPOINTMENTS (Last 5):")
        print(f"="*50)
        
        # Sort by start time (most recent first)
        sorted_appointments = sorted(appointment_details, 
                                   key=lambda x: x.get('starts_at', ''), 
                                   reverse=True)
        
        for i, apt in enumerate(sorted_appointments[:5], 1):
            print(f"{i:2d}. 📅 {apt['starts_at']} | Status: {apt['status']} | ID: {apt['id']}")
    
    # Save baseline data
    baseline_data = {
        'extraction_date': datetime.now(aest).isoformat(),
        'patient_info': sami_patient,
        'total_appointments': len(all_appointments),
        'status_breakdown': {
            'attended': attended_count,
            'dna': dna_count,
            'cancelled': cancelled_count,
            'scheduled': scheduled_count
        },
        'appointment_details': appointment_details,
        'cancelled_appointments': cancelled_appointments
    }
    
    try:
        with open('sami_baseline_data.json', 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)
        print(f"\n📄 Baseline data saved to: sami_baseline_data.json")
    except Exception as e:
        print(f"❌ Failed to save baseline: {str(e)}")
    
    print(f"\n" + "="*80)
    print(f"✅ BASELINE EXTRACTION COMPLETE!")
    print(f"🎯 Next Step: Add a cancelled appointment in Cliniko")
    print(f"📋 Then run this script again to see what changes in the API")
    print(f"="*80)
    
    return baseline_data

if __name__ == "__main__":
    baseline = extract_sami_baseline_corrected()

