#!/usr/bin/env python3
"""
🎯 SYSTEMATIC PATIENT BEHAVIOR EXTRACTION - APPOINTMENTS BOOKED & AGE DEMOGRAPHICS
📋 Date Range: 16/06/2025 to 21/06/2025
🔧 Official Cliniko API Compliant Script
================================================================================
"""

import requests
import json
import base64
from datetime import datetime
import pytz

# Configuration
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Authentication headers (Official Cliniko method)
auth_string = base64.b64encode(f"{API_KEY}:".encode()).decode()
headers = {
    'Authorization': f'Basic {auth_string}',
    'Accept': 'application/json',
    'User-Agent': 'PatientRatingApp/1.0'
}

def convert_to_aest(utc_datetime_str):
    """Convert UTC datetime string to AEST"""
    if not utc_datetime_str:
        return None
    utc_dt = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))
    aest_dt = utc_dt.astimezone(AEST)
    return aest_dt.strftime('%d/%m/%Y %H:%M:%S')

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    try:
        birth_date = datetime.fromisoformat(date_of_birth.replace('Z', '+00:00')).date()
        today = datetime.now().date()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age
    except:
        return None

def fetch_appointments_in_date_range():
    """Fetch appointments in specified date range using official API filtering"""
    print("🎯 SYSTEMATIC BEHAVIOR EXTRACTION - APPOINTMENTS BOOKED & AGE DEMOGRAPHICS")
    print("=" * 80)
    print("📅 Date Range: 16/06/2025 to 21/06/2025")
    print("🔧 Using Official Cliniko API Methods")
    print()
    
    # Convert AEST to UTC for API filtering (official method)
    start_aest = AEST.localize(datetime(2025, 6, 16, 0, 0, 0))
    end_aest = AEST.localize(datetime(2025, 6, 21, 23, 59, 59))
    start_utc = start_aest.astimezone(pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_utc = end_aest.astimezone(pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"🕐 UTC Range: {start_utc} to {end_utc}")
    print()
    
    appointments = []
    page = 1
    
    while True:
        print(f"📡 Fetching appointments page {page}...")
        
        # Official Cliniko API filtering method
        params = {
            'per_page': 100,
            'page': page,
            'q[]': [
                f'starts_at:>{start_utc}',
                f'starts_at:<{end_utc}'
            ]
        }
        
        response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            break
            
        data = response.json()
        page_appointments = data.get('individual_appointments', [])
        
        if not page_appointments:
            break
            
        appointments.extend(page_appointments)
        print(f"   ✅ Retrieved {len(page_appointments)} appointments")
        
        # Check if there are more pages
        if len(page_appointments) < 100:
            break
            
        page += 1
    
    print(f"\n🎯 Total appointments retrieved: {len(appointments)}")
    return appointments

def extract_patient_demographics(patient_ids):
    """Extract patient demographics for age calculation"""
    print(f"\n👥 EXTRACTING PATIENT DEMOGRAPHICS")
    print("=" * 50)
    
    patients_data = {}
    
    for i, patient_id in enumerate(patient_ids, 1):
        print(f"📋 Fetching patient {i}/{len(patient_ids)}: ID {patient_id}")
        
        response = requests.get(f"{BASE_URL}/patients/{patient_id}", headers=headers)
        
        if response.status_code == 200:
            patient = response.json()
            patients_data[patient_id] = {
                'name': f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip(),
                'date_of_birth': patient.get('date_of_birth'),
                'age': calculate_age(patient.get('date_of_birth'))
            }
        else:
            print(f"   ❌ Failed to fetch patient {patient_id}: {response.status_code}")
            patients_data[patient_id] = {
                'name': 'Unknown',
                'date_of_birth': None,
                'age': None
            }
    
    return patients_data

def analyze_behaviors(appointments, patients_data):
    """Analyze the two target behaviors: Appointments Booked & Age Demographics"""
    print(f"\n📊 BEHAVIOR ANALYSIS")
    print("=" * 50)
    
    # Behavior 1: Appointments Booked (count per patient)
    appointment_counts = {}
    patient_appointments = {}
    
    for appointment in appointments:
        # Extract patient ID from the appointment
        patient_link = appointment.get('patient', {}).get('links', {}).get('self', '')
        if patient_link:
            patient_id = patient_link.split('/')[-1]
            if patient_id not in appointment_counts:
                appointment_counts[patient_id] = 0
                patient_appointments[patient_id] = []
            
            appointment_counts[patient_id] += 1
            patient_appointments[patient_id].append({
                'id': appointment.get('id'),
                'starts_at': convert_to_aest(appointment.get('starts_at')),
                'status': 'Cancelled' if appointment.get('cancelled_at') else 
                         'DNA' if appointment.get('did_not_arrive') else 'Attended'
            })
    
    # Behavior 2: Age Demographics
    age_demographics = {}
    for patient_id, patient_info in patients_data.items():
        if patient_info['age'] is not None:
            age = patient_info['age']
            age_bracket = f"{(age//10)*10}-{(age//10)*10+9}"
            if age_bracket not in age_demographics:
                age_demographics[age_bracket] = 0
            age_demographics[age_bracket] += 1
    
    return appointment_counts, patient_appointments, age_demographics

def display_results(appointment_counts, patient_appointments, patients_data, age_demographics):
    """Display comprehensive results for both behaviors"""
    print(f"\n🎯 SYSTEMATIC BEHAVIOR EXTRACTION RESULTS")
    print("=" * 80)
    
    print(f"\n📋 BEHAVIOR 1: APPOINTMENTS BOOKED")
    print("-" * 40)
    print(f"Total patients with appointments: {len(appointment_counts)}")
    
    # Sort by appointment count (descending)
    sorted_patients = sorted(appointment_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nTop 10 patients by appointment count:")
    for i, (patient_id, count) in enumerate(sorted_patients[:10], 1):
        patient_name = patients_data.get(patient_id, {}).get('name', 'Unknown')
        print(f"  {i:2d}. {patient_name} ({patient_id}): {count} appointments")
    
    # Appointment count distribution
    count_distribution = {}
    for count in appointment_counts.values():
        if count not in count_distribution:
            count_distribution[count] = 0
        count_distribution[count] += 1
    
    print(f"\nAppointment count distribution:")
    for count in sorted(count_distribution.keys()):
        patients_with_count = count_distribution[count]
        print(f"  {count} appointment{'s' if count != 1 else ''}: {patients_with_count} patient{'s' if patients_with_count != 1 else ''}")
    
    print(f"\n📋 BEHAVIOR 2: AGE DEMOGRAPHICS")
    print("-" * 40)
    
    # Calculate age statistics
    ages = [p['age'] for p in patients_data.values() if p['age'] is not None]
    if ages:
        avg_age = sum(ages) / len(ages)
        min_age = min(ages)
        max_age = max(ages)
        
        print(f"Total patients with age data: {len(ages)}")
        print(f"Average age: {avg_age:.1f} years")
        print(f"Age range: {min_age} - {max_age} years")
        
        print(f"\nAge bracket distribution:")
        for bracket in sorted(age_demographics.keys()):
            count = age_demographics[bracket]
            percentage = (count / len(ages)) * 100
            print(f"  {bracket} years: {count} patients ({percentage:.1f}%)")
    else:
        print("No age data available")
    
    print(f"\n📊 SUMMARY STATISTICS")
    print("-" * 30)
    print(f"Total appointments analyzed: {sum(appointment_counts.values())}")
    print(f"Unique patients: {len(appointment_counts)}")
    print(f"Patients with age data: {len([p for p in patients_data.values() if p['age'] is not None])}")

def main():
    """Main execution function"""
    try:
        # Step 1: Fetch appointments in date range
        appointments = fetch_appointments_in_date_range()
        
        if not appointments:
            print("❌ No appointments found in the specified date range")
            return
        
        # Step 2: Extract unique patient IDs
        patient_ids = set()
        for appointment in appointments:
            patient_link = appointment.get('patient', {}).get('links', {}).get('self', '')
            if patient_link:
                patient_id = patient_link.split('/')[-1]
                patient_ids.add(patient_id)
        
        print(f"🎯 Unique patients found: {len(patient_ids)}")
        
        # Step 3: Extract patient demographics
        patients_data = extract_patient_demographics(list(patient_ids))
        
        # Step 4: Analyze behaviors
        appointment_counts, patient_appointments, age_demographics = analyze_behaviors(appointments, patients_data)
        
        # Step 5: Display results
        display_results(appointment_counts, patient_appointments, patients_data, age_demographics)
        
        # Step 6: Save results to file
        results = {
            'extraction_info': {
                'date_range': '16/06/2025 to 21/06/2025',
                'extraction_time': datetime.now(AEST).strftime('%d/%m/%Y %H:%M:%S AEST'),
                'total_appointments': len(appointments),
                'unique_patients': len(patient_ids)
            },
            'behavior_1_appointments_booked': {
                'patient_appointment_counts': appointment_counts,
                'distribution': dict(sorted([(count, sum(1 for c in appointment_counts.values() if c == count)) 
                                           for count in set(appointment_counts.values())]))
            },
            'behavior_2_age_demographics': {
                'age_brackets': age_demographics,
                'statistics': {
                    'total_with_age_data': len([p for p in patients_data.values() if p['age'] is not None]),
                    'average_age': sum([p['age'] for p in patients_data.values() if p['age'] is not None]) / 
                                 len([p for p in patients_data.values() if p['age'] is not None]) if 
                                 [p for p in patients_data.values() if p['age'] is not None] else 0
                }
            },
            'raw_data': {
                'appointments': appointments,
                'patients': patients_data
            }
        }
        
        filename = f"systematic_behavior_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        print(f"\n✅ SYSTEMATIC EXTRACTION COMPLETE!")
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

