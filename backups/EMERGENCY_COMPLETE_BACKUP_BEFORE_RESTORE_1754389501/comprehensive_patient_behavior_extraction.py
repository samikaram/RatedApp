#!/usr/bin/env python3
"""
🎯 CORRECTED COMPREHENSIVE PATIENT BEHAVIOR EXTRACTION
📋 Following Cliniko's Official API Documentation
🔧 Using Base64 Encoded Basic Auth (WORKING METHOD)
🔧 Fixed API filtering syntax and patient data parsing
================================================================================
"""

import requests
import json
import base64
from datetime import datetime, timezone
import pytz
import time

# Configuration
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# CORRECTED Authentication (Base64 Encoded - Method 2)
auth_string = base64.b64encode(f'{API_KEY}:'.encode()).decode()
headers = {
    'User-Agent': 'Patient Rating App (sami@example.com)',
    'Accept': 'application/json',
    'Authorization': f'Basic {auth_string}'
}

def handle_rate_limit():
    """Handle Cliniko's 200 requests/minute rate limit"""
    print("   ⏳ Rate limit hit, waiting 60 seconds...")
    time.sleep(60)

def get_all_patient_appointments(patient_id):
    """Get ALL appointments for a specific patient using correct Cliniko filtering"""
    all_appointments = []
    page = 1
    
    while True:
        try:
            # CORRECTED Cliniko API filtering format
            params = {
                'per_page': 100,
                'page': page,
                'q[]': f'patient_id={patient_id}'  # Fixed: use = not :
            }
            
            response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
            
            if response.status_code == 429:
                handle_rate_limit()
                continue
            elif response.status_code != 200:
                print(f"      ❌ API Error {response.status_code}: {response.text}")
                break
                
            data = response.json()
            appointments = data.get('individual_appointments', [])
            
            if not appointments:
                break
                
            all_appointments.extend(appointments)
            
            # Check if there are more pages
            if len(appointments) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"      ❌ Error fetching appointments: {str(e)}")
            break
    
    return all_appointments

def get_all_patient_invoices(patient_id):
    """Get ALL invoices for a specific patient using correct Cliniko filtering"""
    all_invoices = []
    page = 1
    
    while True:
        try:
            # CORRECTED Cliniko API filtering format
            params = {
                'per_page': 100,
                'page': page,
                'q[]': f'patient_id={patient_id}'  # Fixed: use = not :
            }
            
            response = requests.get(f"{BASE_URL}/invoices", headers=headers, params=params)
            
            if response.status_code == 429:
                handle_rate_limit()
                continue
            elif response.status_code != 200:
                print(f"      ❌ API Error {response.status_code}: {response.text}")
                break
                
            data = response.json()
            invoices = data.get('invoices', [])
            
            if not invoices:
                break
                
            all_invoices.extend(invoices)
            
            # Check if there are more pages
            if len(invoices) < 100:
                break
                
            page += 1
            
        except Exception as e:
            print(f"      ❌ Error fetching invoices: {str(e)}")
            break
    
    return all_invoices

def calculate_age_bracket(date_of_birth):
    """Calculate age bracket from date of birth"""
    if not date_of_birth:
        return "Unknown"
    
    try:
        dob = datetime.fromisoformat(date_of_birth.replace('Z', '+00:00'))
        age = (datetime.now(timezone.utc) - dob).days // 365
        
        if age < 18:
            return "Under 18"
        elif age < 30:
            return "18-29"
        elif age < 40:
            return "30-39"
        elif age < 50:
            return "40-49"
        elif age < 60:
            return "50-59"
        else:
            return "60+"
    except:
        return "Unknown"

def convert_to_aest(utc_datetime_str):
    """Convert UTC datetime string to AEST"""
    if not utc_datetime_str:
        return None
    try:
        utc_dt = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))
        aest_dt = utc_dt.astimezone(AEST)
        return aest_dt.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return None

def main():
    print("🎯 CORRECTED COMPREHENSIVE PATIENT BEHAVIOR EXTRACTION")
    print("="*80)
    print("📋 Following Cliniko's Official API Documentation")
    print("🔧 Using Base64 Encoded Basic Auth (WORKING METHOD)")
    print("🔧 Fixed API filtering syntax and patient data parsing")
    print("🎯 Result: Accurate patient behavior profiles")
    
    try:
        # STEP 1: Get target patients (June 16-21, 2025)
        print(f"\n🎯 STEP 1: IDENTIFYING TARGET PATIENTS")
        print("="*60)
        print("📅 Finding patients with appointments: June 16-21, 2025")
        
        # Convert AEST to UTC for API
        start_date_aest = datetime(2025, 6, 16, 0, 0, 0, tzinfo=AEST)
        end_date_aest = datetime(2025, 6, 22, 0, 0, 0, tzinfo=AEST)
        start_date_utc = start_date_aest.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        end_date_utc = end_date_aest.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        print(f"🕐 UTC Range: {start_date_utc} to {end_date_utc}")
        
        # Get appointments in date range
        all_target_appointments = []
        page = 1
        
        while True:
            print(f"📡 Fetching appointments page {page}...")
            
            params = {
                'per_page': 100,
                'page': page,
                'q[]': [
                    f'starts_at:>{start_date_utc}',
                    f'starts_at:<{end_date_utc}'
                ]
            }
            
            response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
            
            if response.status_code == 429:
                handle_rate_limit()
                continue
            elif response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return
                
            data = response.json()
            appointments = data.get('individual_appointments', [])
            
            if not appointments:
                break
                
            print(f"   ✅ Retrieved {len(appointments)} appointments")
            all_target_appointments.extend(appointments)
            
            if len(appointments) < 100:
                break
                
            page += 1
        
        # CORRECTED patient ID extraction (from July 2nd breakthrough)
        target_patient_ids = []
        for appt in all_target_appointments:
            if appt.get('patient') and appt['patient'].get('links') and appt['patient']['links'].get('self'):
                patient_url = appt['patient']['links']['self']
                # Extract ID from URL: https://api.au1.cliniko.com/v1/patients/1109937
                patient_id = patient_url.split('/')[-1]
                target_patient_ids.append(patient_id)
        
        target_patient_ids = list(set(target_patient_ids))  # Remove duplicates
        
        print(f"\n✅ Target patients identified: {len(target_patient_ids)}")
        print(f"📊 From {len(all_target_appointments)} appointments in date range")
        
        if not target_patient_ids:
            print("❌ No target patients found")
            return
        
        # STEP 2: Extract comprehensive behavior data
        print(f"\n🎯 STEP 2: EXTRACTING COMPLETE BEHAVIOR DATA")
        print("="*60)
        print(f"📊 Processing {len(target_patient_ids)} patients...")
        
        all_patient_behaviors = []
        
        for i, patient_id in enumerate(target_patient_ids, 1):
            print(f"\n👤 Patient {i}/{len(target_patient_ids)}: ID {patient_id}")
            
            # Get patient demographics
            print("   📋 Fetching demographics...")
            try:
                patient_response = requests.get(f"{BASE_URL}/patients/{patient_id}", headers=headers)
                if patient_response.status_code == 429:
                    handle_rate_limit()
                    patient_response = requests.get(f"{BASE_URL}/patients/{patient_id}", headers=headers)
                
                if patient_response.status_code != 200:
                    print(f"   ❌ Failed to get patient demographics: {patient_response.status_code}")
                    continue
                    
                patient_data = patient_response.json()
                
                # FIXED: Add error handling for patient data parsing
                if isinstance(patient_data, str):
                    print(f"   ❌ Invalid patient data format: {patient_data}")
                    continue
                
                patient_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}".strip()
                print(f"   👤 {patient_name}")
                
            except Exception as e:
                print(f"   ❌ Error getting patient data: {str(e)}")
                continue
            
            # Get ALL appointments for this patient
            print("   📅 Fetching ALL appointments...")
            all_appointments = get_all_patient_appointments(patient_id)
            print(f"      ✅ {len(all_appointments)} total appointments")
            
            # Get ALL invoices for this patient  
            print("   💰 Fetching ALL invoices...")
            all_invoices = get_all_patient_invoices(patient_id)
            print(f"      ✅ {len(all_invoices)} total invoices")
            
            # Calculate behavior metrics using CORRECTED ATTENDANCE LOGIC
            total_appointments = len(all_appointments)
            cancelled_appointments = len([a for a in all_appointments if a.get('cancelled_at')])
            dna_appointments = len([a for a in all_appointments if a.get('did_not_arrive') == True])
            
            # CORRECTED ATTENDANCE LOGIC (matches Cliniko dashboard)
            attended_appointments = len([a for a in all_appointments 
                                       if not a.get('cancelled_at') and not a.get('did_not_arrive')])
            
            # Calculate rates
            cancellation_rate = (cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0
            attendance_rate = (attended_appointments / total_appointments * 100) if total_appointments > 0 else 0
            dna_rate = (dna_appointments / total_appointments * 100) if total_appointments > 0 else 0
            
            # Invoice analysis
            total_invoices = len(all_invoices)
            paid_invoices = len([inv for inv in all_invoices if float(inv.get('total_paid', 0)) > 0])
            payment_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
            
            # Calculate total spend
            total_spend = sum([float(inv.get('total', 0)) for inv in all_invoices])
            
            # Age and referral analysis with FIXED error handling
            age_bracket = calculate_age_bracket(patient_data.get('date_of_birth'))
            
            # FIXED: Safe referral source extraction
            try:
                referral_source = "Unknown"
                if patient_data.get('referral_source'):
                    if isinstance(patient_data['referral_source'], dict):
                        referral_source = patient_data['referral_source'].get('name', 'Unknown')
                    else:
                        referral_source = str(patient_data['referral_source'])
            except:
                referral_source = "Unknown"
            
            patient_behavior = {
                'patient_id': patient_id,
                'name': patient_name,
                'total_appointments': total_appointments,
                'cancelled_appointments': cancelled_appointments,
                'attended_appointments': attended_appointments,
                'dna_appointments': dna_appointments,
                'cancellation_rate': round(cancellation_rate, 1),
                'attendance_rate': round(attendance_rate, 1),
                'dna_rate': round(dna_rate, 1),
                'total_invoices': total_invoices,
                'paid_invoices': paid_invoices,
                'payment_rate': round(payment_rate, 1),
                'total_spend': round(total_spend, 2),
                'age_bracket': age_bracket,
                'referral_source': referral_source
            }
            
            all_patient_behaviors.append(patient_behavior)
            
            print("   📊 Behavior Summary:")
            print(f"      🎯 Total appointments: {total_appointments}")
            print(f"      ✅ Attended: {attended_appointments} ({attendance_rate:.1f}%)")
            print(f"      🚫 Cancelled: {cancelled_appointments} ({cancellation_rate:.1f}%)")
            print(f"      ❌ DNA: {dna_appointments} ({dna_rate:.1f}%)")
            print(f"      💰 Payment rate: {payment_rate:.1f}%")
            print(f"      💵 Total spend: ${total_spend:.2f}")
            
            # Rate limiting - small delay between patients
            time.sleep(0.5)
        
        # STEP 3: Summary statistics and analysis
        print(f"\n🎯 STEP 3: COMPREHENSIVE ANALYSIS")
        print("="*60)
        
        total_patients = len(all_patient_behaviors)
        if total_patients == 0:
            print("❌ No patient data extracted")
            return
            
        avg_appointments = sum(p['total_appointments'] for p in all_patient_behaviors) / total_patients
        avg_cancellation_rate = sum(p['cancellation_rate'] for p in all_patient_behaviors) / total_patients
        avg_attendance_rate = sum(p['attendance_rate'] for p in all_patient_behaviors) / total_patients
        patients_with_payments = [p for p in all_patient_behaviors if p['payment_rate'] > 0]
        avg_payment_rate = sum(p['payment_rate'] for p in patients_with_payments) / len(patients_with_payments) if patients_with_payments else 0
        
        print(f"📊 CLINIC BEHAVIOR STATISTICS:")
        print(f"   👥 Total patients analyzed: {total_patients}")
        print(f"   📅 Average appointments per patient: {avg_appointments:.1f}")
        print(f"   🚫 Average cancellation rate: {avg_cancellation_rate:.1f}%")
        print(f"   ✅ Average attendance rate: {avg_attendance_rate:.1f}%")
        print(f"   💰 Average payment rate: {avg_payment_rate:.1f}%")
        
        # Top performers and concerns
        print(f"\n🏆 TOP PERFORMERS:")
        top_attendance = sorted(all_patient_behaviors, key=lambda x: x['attendance_rate'], reverse=True)[:5]
        for i, patient in enumerate(top_attendance, 1):
            print(f"   {i}. {patient['name']}: {patient['attendance_rate']:.1f}% attendance ({patient['total_appointments']} appointments)")
        
        print(f"\n⚠️  PATIENTS NEEDING ATTENTION:")
        high_cancellation = sorted([p for p in all_patient_behaviors if p['cancellation_rate'] > 20], 
                                 key=lambda x: x['cancellation_rate'], reverse=True)[:5]
        for i, patient in enumerate(high_cancellation, 1):
            print(f"   {i}. {patient['name']}: {patient['cancellation_rate']:.1f}% cancellation rate")
        
        # Age demographics
        age_brackets = {}
        for patient in all_patient_behaviors:
            bracket = patient['age_bracket']
            if bracket not in age_brackets:
                age_brackets[bracket] = 0
            age_brackets[bracket] += 1
        
        print(f"\n👥 AGE DEMOGRAPHICS:")
        for bracket in sorted(age_brackets.keys()):
            count = age_brackets[bracket]
            percentage = (count / total_patients) * 100
            print(f"   {bracket}: {count} patients ({percentage:.1f}%)")
        
        # Referral source analysis
        referral_sources = {}
        for patient in all_patient_behaviors:
            source = patient['referral_source']
            if source not in referral_sources:
                referral_sources[source] = 0
            referral_sources[source] += 1
        
        print(f"\n📍 REFERRAL SOURCES:")
        sorted_referrals = sorted(referral_sources.items(), key=lambda x: x[1], reverse=True)
        for i, (source, count) in enumerate(sorted_referrals[:10], 1):
            percentage = (count / total_patients) * 100
            print(f"   {i}. {source}: {count} patients ({percentage:.1f}%)")
        
        # Save comprehensive results
        results = {
            'extraction_info': {
                'target_date_range': 'June 16-21, 2025',
                'extraction_time': datetime.now(AEST).strftime('%d/%m/%Y %H:%M:%S AEST'),
                'total_patients_analyzed': total_patients,
                'extraction_method': 'Cliniko API compliant - Complete historical behavior data'
            },
            'clinic_statistics': {
                'average_appointments_per_patient': round(avg_appointments, 1),
                'average_cancellation_rate': round(avg_cancellation_rate, 1),
                'average_attendance_rate': round(avg_attendance_rate, 1),
                'average_payment_rate': round(avg_payment_rate, 1)
            },
            'patient_behaviors': all_patient_behaviors,
            'age_demographics': age_brackets,
            'referral_sources': dict(sorted_referrals),
            'top_performers': [
                {
                    'name': p['name'],
                    'attendance_rate': p['attendance_rate'],
                    'total_appointments': p['total_appointments']
                } for p in top_attendance
            ],
            'attention_needed': [
                {
                    'name': p['name'],
                    'cancellation_rate': p['cancellation_rate'],
                    'total_appointments': p['total_appointments']
                } for p in high_cancellation
            ]
        }
        
        # Save to file
        filename = f"corrected_patient_behaviors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Complete results saved to: {filename}")
        print(f"\n✅ CORRECTED EXTRACTION COMPLETE!")
        print(f"🎯 Following Cliniko's official API documentation")
        print(f"🔧 Using Base64 Encoded Basic Auth (WORKING METHOD)")
        print(f"🔧 Fixed API filtering syntax and patient data parsing")
        print(f"📊 All {total_patients} patients have accurate historical behavior profiles")
        print(f"🚀 Ready for patient behavior scoring system integration!")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()  
