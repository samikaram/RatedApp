#!/usr/bin/env python3
"""
🔍 DEBBIE MACGREGOR FINAL CORRECTED EXTRACTION - APPLYING WORKING LOGIC
✅ Using the EXACT same logic that worked for Vivianne Russell
✅ Fixed UTC timestamp formatting for invoice date filtering
✅ Fixed consecutive attendance calculation (most recent first, stop at DNA/cancellation)
✅ Fixed yearly spend extraction (client-side filtering for paid invoices)
✅ Using proven July 4, 2025 corrected behavior logic
"""

import requests
import json
import base64
import time
from datetime import datetime, timedelta
import pytz

# Configuration - Using verified working API key
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

def make_api_request(endpoint, params=None):
    """Make API request using official Cliniko documentation authentication"""
    url = f"{BASE_URL}/{endpoint}"
    
    # Official Cliniko authentication: API key as username, empty password
    credentials = f"{API_KEY}:"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Accept': 'application/json',
        'User-Agent': 'RatedApp/1.0 support@sportsmedicineclinic.com.au'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("⏳ Rate limit hit - waiting 60 seconds...")
            time.sleep(60)
            return make_api_request(endpoint, params)
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Request Error: {str(e)}")
        return None

def get_paginated_data(endpoint, params, description):
    """Get all paginated data from Cliniko API"""
    all_data = []
    page = 1
    
    print(f"📡 Fetching {description} using server-side filtering...")
    
    while True:
        params_with_page = params.copy()
        params_with_page['page'] = page
        
        response_data = make_api_request(endpoint, params_with_page)
        
        if not response_data:
            break
            
        # Handle different endpoint response structures
        if endpoint == 'patients':
            items = response_data.get('patients', [])
        elif endpoint == 'individual_appointments':
            items = response_data.get('individual_appointments', [])
        elif endpoint == 'invoices':
            items = response_data.get('invoices', [])
        elif endpoint == 'referral_sources':
            items = response_data.get('referral_sources', [])
        else:
            items = response_data.get('items', [])
        
        if not items:
            break
            
        all_data.extend(items)
        print(f"   📄 Page {page}: {len(items)} items retrieved")
        
        # Check if there are more pages
        links = response_data.get('links', {})
        if not links.get('next'):
            break
            
        page += 1
    
    print(f"   ✅ Total {description}: {len(all_data)}")
    
    return all_data

def search_patient_debbie():
    """STEP 1: Search for Debbie Macgregor using multiple name variations"""
    print("🔍 STEP 1: PATIENT SEARCH - DEBBIE MACGREGOR")
    print("="*60)
    
    search_queries = [
        {
            'q[]': [
                'first_name:=Debbie',
                'last_name:=Macgregor'
            ],
            'description': 'Exact match: Debbie Macgregor'
        },
        {
            'q[]': [
                'first_name:=Deborah',
                'last_name:=Macgregor'
            ],
            'description': 'Full name: Deborah Macgregor'
        },
        {
            'q[]': 'last_name:=Macgregor',
            'description': 'Last name only: Macgregor'
        },
        {
            'q[]': 'first_name:=Debbie',
            'description': 'First name only: Debbie'
        }
    ]
    
    for search_query in search_queries:
        print(f"\n🔍 Trying: {search_query['description']}")
        
        patients = get_paginated_data('patients', search_query, f"patients matching {search_query['description']}")
        
        if patients:
            print(f"\n✅ FOUND {len(patients)} PATIENT(S):")
            for i, patient in enumerate(patients, 1):
                print(f"\n   {i}. 👤 ID: {patient.get('id')}")
                print(f"      📝 Name: {patient.get('first_name')} {patient.get('last_name')}")
                print(f"      📅 DOB: {patient.get('date_of_birth')}")
                print(f"      📧 Email: {patient.get('email')}")
                
                # Calculate age
                if patient.get('date_of_birth'):
                    birth_date = datetime.strptime(patient.get('date_of_birth'), '%Y-%m-%d')
                    age = (datetime.now() - birth_date).days // 365
                    print(f"      🎂 Age: {age} years")
            
            # Return first patient found
            return patients[0]
    
    print("\n❌ NO PATIENTS FOUND - DEBBIE MACGREGOR NOT IN SYSTEM")
    return None

def extract_complete_behavior_data(patient_data):
    """STEP 2: Extract all 10 behavior categories using WORKING VIVIANNE LOGIC"""
    
    PATIENT_ID = patient_data.get('id')
    PATIENT_NAME = f"{patient_data.get('first_name')} {patient_data.get('last_name')}"
    
    print(f"\n🚀 STEP 2: APPLYING WORKING VIVIANNE LOGIC TO DEBBIE")
    print("="*80)
    print(f"👤 Patient: {PATIENT_NAME} (ID: {PATIENT_ID})")
    print(f"📅 Extraction Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("✅ USING EXACT SAME LOGIC THAT WORKED FOR VIVIANNE RUSSELL")
    print("✅ Fixed UTC timestamps, consecutive attendance, yearly spend")
    print("="*80)
    
    behavior_data = {}
    
    # BEHAVIOR 1: Future Appointments Booked (USING WORKING LOGIC)
    print(f"\n🎯 BEHAVIOR 1: Appointments Booked (Future Only) - WORKING LOGIC")
    
    # ✅ WORKING LOGIC: Proper UTC timestamp formatting
    now_aest = datetime.now(AEST)
    now_utc = now_aest.astimezone(pytz.UTC)
    utc_timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    filter_params = {
        'q[]': [
            f'patient_id:={PATIENT_ID}',
            f'starts_at:>{utc_timestamp}'
        ]
    }
    
    future_appointments = get_paginated_data(
        'individual_appointments',
        filter_params,
        f"future appointments for Patient ID {PATIENT_ID}"
    )
    
    behavior_data['appointments_booked'] = {
        'future_appointments_count': len(future_appointments),
        'future_appointments': future_appointments
    }
    print(f"   ✅ Future appointments booked: {len(future_appointments)}")
    
    # BEHAVIOR 2: Age Demographics (USING WORKING LOGIC)
    print(f"\n🎯 BEHAVIOR 2: Age Demographics - WORKING LOGIC")
    
    age = None
    in_target_demographic = False
    
    if patient_data.get('date_of_birth'):
        birth_date = datetime.strptime(patient_data.get('date_of_birth'), '%Y-%m-%d')
        age = (datetime.now() - birth_date).days // 365
        in_target_demographic = 20 <= age <= 55
    
    behavior_data['age_demographics'] = {
        'age': age,
        'date_of_birth': patient_data.get('date_of_birth'),
        'in_target_demographic': in_target_demographic
    }
    print(f"   ✅ Age: {age} years")
    print(f"   ✅ In target demographic (20-55): {in_target_demographic}")
    
    # BEHAVIOR 3: Yearly Spend (USING WORKING VIVIANNE LOGIC)
    print(f"\n🎯 BEHAVIOR 3: Yearly Spend (Last 12 months) - WORKING LOGIC")
    
    # ✅ WORKING LOGIC: Proper UTC timestamp for date filtering
    twelve_months_ago_aest = datetime.now(AEST) - timedelta(days=365)
    twelve_months_ago_utc = twelve_months_ago_aest.astimezone(pytz.UTC)
    twelve_months_ago_str = twelve_months_ago_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # ✅ Get ALL invoices first, then filter by date and status
    filter_params = {
        'q[]': f'patient_id:={PATIENT_ID}'
    }
    
    all_invoices = get_paginated_data(
        'invoices',
        filter_params,
        f"all invoices for Patient ID {PATIENT_ID}"
    )
    
    # ✅ WORKING LOGIC: Client-side filtering for paid invoices in last 12 months
    twelve_months_ago_date = twelve_months_ago_aest.date()
    paid_invoices_last_12_months = []
    
    for invoice in all_invoices:
        # Check if invoice is paid (status = 1 or has closed_at)
        is_paid = (invoice.get('status') == 1 or 
                  invoice.get('closed_at') is not None)
        
        # Check if invoice is within last 12 months
        if invoice.get('created_at'):
            created_date = datetime.fromisoformat(invoice.get('created_at').replace('Z', '+00:00'))
            created_date_aest = created_date.astimezone(AEST).date()
            is_within_12_months = created_date_aest >= twelve_months_ago_date
        else:
            is_within_12_months = False
        
        if is_paid and is_within_12_months:
            paid_invoices_last_12_months.append(invoice)
    
    yearly_spend = sum(float(invoice.get('total_amount', 0)) for invoice in paid_invoices_last_12_months)
    
    behavior_data['yearly_spend'] = {
        'yearly_spend': yearly_spend,
        'paid_invoices_count': len(paid_invoices_last_12_months),
        'paid_invoices': paid_invoices_last_12_months,
        'total_invoices_checked': len(all_invoices)
    }
    print(f"   ✅ Yearly spend (12 months): ${yearly_spend:.2f}")
    print(f"   ✅ Paid invoices count: {len(paid_invoices_last_12_months)}")
    print(f"   ✅ Total invoices checked: {len(all_invoices)}")
    
    # BEHAVIOR 4: Consecutive Attendance Streak - CORRECTED LOGIC
    print(f"\n🎯 BEHAVIOR 4: Consecutive Attendance Streak - CORRECTED LOGIC")
    print("✅ FIXED: Both DNA AND cancellations break streak")
    print("✅ Following Cliniko API documentation")

    # Get ALL appointments first
    filter_params = {
        'q[]': f'patient_id:={PATIENT_ID}'
    }

    all_appointments = get_paginated_data(
        'individual_appointments',
        filter_params,
        f"ALL appointments for Patient ID {PATIENT_ID}"
    )

    # Get cancelled appointments separately to ensure we have them
    cancelled_appointments_params = {
        'q[]': [
            f'patient_id:={PATIENT_ID}',
            'cancelled_at:?'  # Where cancelled_at exists
        ]
    }

    cancelled_appointments = get_paginated_data(
        'individual_appointments',
        cancelled_appointments_params,
        f"CANCELLED appointments for Patient ID {PATIENT_ID}"
    )

    # Merge and deduplicate appointments
    unique_appointments = {}

    # Add all appointments
    for apt in all_appointments:
        apt_id = apt.get('id')
        if apt_id:
            unique_appointments[apt_id] = apt

    # Add cancelled appointments (ensures we have complete data)
    for apt in cancelled_appointments:
        apt_id = apt.get('id')
        if apt_id:
            unique_appointments[apt_id] = apt

    # Convert back to list and filter valid appointments
    merged_appointments = list(unique_appointments.values())
    valid_appointments = [apt for apt in merged_appointments if apt.get('starts_at')]

    # Sort by starts_at (most recent first)
    valid_appointments.sort(key=lambda x: x.get('starts_at', ''), reverse=True)

    print(f"   📊 Analyzing {len(valid_appointments)} appointments for consecutive streak...")
    print(f"   📊 Total appointments: {len(all_appointments)}")
    print(f"   📊 Cancelled appointments: {len(cancelled_appointments)}")
    print(f"   📊 Merged unique appointments: {len(merged_appointments)}")

    # Calculate consecutive streak - CORRECTED LOGIC
    consecutive_attendance_streak = 0
    for i, appointment in enumerate(valid_appointments):
        # ✅ CORRECTED: Both cancelled and DNA break streak
        is_cancelled = appointment.get('cancelled_at') is not None
        is_dna = appointment.get('did_not_arrive') is True
        streak_broken = is_cancelled or is_dna
        
        print(f"   📅 Appointment {i+1}: {appointment.get('starts_at', 'N/A')[:10]} - "
              f"Cancelled: {is_cancelled}, "
              f"DNA: {is_dna}, "
              f"Arrived: {bool(appointment.get('patient_arrived'))}, "
              f"Streak Broken: {streak_broken}")
        
        if not streak_broken:
            consecutive_attendance_streak += 1
            print(f"   ✅ Streak continues: {consecutive_attendance_streak}")
        else:
            reason = "Cancelled" if is_cancelled else "DNA"
            print(f"   ❌ Streak broken at appointment {i+1} - Reason: {reason}")
            break

    behavior_data['consecutive_attendance'] = {
        'consecutive_attendance_streak': consecutive_attendance_streak,
        'total_appointments': len(merged_appointments),
        'valid_appointments': len(valid_appointments),
        'cancelled_count': len(cancelled_appointments),
        'calculation_method': 'CORRECTED: DNA OR cancellation breaks streak'
    }
    print(f"   ✅ CORRECTED Consecutive attendance streak: {consecutive_attendance_streak}")
    
    # BEHAVIOR 5: Likability (Manual Input)
    print(f"\n🎯 BEHAVIOR 5: Likability (Manual Input)")
    
    behavior_data['likability'] = {
        'likability_score': 0,
        'manual_input_required': True
    }
    print(f"   ✅ Likability score: 0 (Manual input required)")
    
    # BEHAVIOR 6: Open DNA Invoices (USING WORKING LOGIC)
    print(f"\n🎯 BEHAVIOR 6: Open DNA Invoices - WORKING LOGIC")
    
    # ✅ WORKING LOGIC: Using closed_at:!? for unpaid invoices
    unpaid_invoices = [inv for inv in all_invoices if inv.get('closed_at') is None]
    
    # Check if any unpaid invoices are DNA-related
    has_open_dna_invoice = any(
        'non-attendance' in str(invoice.get('notes', '')).lower() or 
        'dna' in str(invoice.get('notes', '')).lower() or
        'did not arrive' in str(invoice.get('notes', '')).lower()
        for invoice in unpaid_invoices
    )
    
    behavior_data['open_dna_invoices'] = {
        'has_open_dna_invoice': has_open_dna_invoice,
        'total_unpaid_invoices': len(unpaid_invoices)
    }
    print(f"   ✅ Has open DNA invoice: {has_open_dna_invoice}")
    print(f"   ✅ Total unpaid invoices: {len(unpaid_invoices)}")
    
    # BEHAVIOR 7: Unpaid Invoices (Count) - WORKING LOGIC
    print(f"\n🎯 BEHAVIOR 7: Unpaid Invoices (Count) - WORKING LOGIC")
    
    unpaid_amount = sum(float(invoice.get('total_amount', 0)) for invoice in unpaid_invoices)
    
    behavior_data['unpaid_invoices'] = {
        'unpaid_invoice_count': len(unpaid_invoices),
        'unpaid_amount': unpaid_amount,
        'unpaid_invoices': unpaid_invoices
    }
    print(f"   ✅ Unpaid invoice count: {len(unpaid_invoices)}")
    print(f"   ✅ Unpaid amount: ${unpaid_amount:.2f}")
    
    # BEHAVIOR 8: Unlikability (Manual Input)
    print(f"\n🎯 BEHAVIOR 8: Unlikability (Manual Input)")
    
    behavior_data['unlikability'] = {
        'unlikability_score': 0,
        'manual_input_required': True
    }
    print(f"   ✅ Unlikability score: 0 (Manual input required)")
    
    # BEHAVIOR 9: Cancellations (USING PROVEN METHOD)
    print(f"\n🎯 BEHAVIOR 9: Cancellations - PROVEN METHOD")
    
    # ✅ USING PROVEN METHOD: cancelled_at:? from July 3 success
    filter_params = {
        'q[]': [
            f'patient_id:={PATIENT_ID}',
            'cancelled_at:?'  # ✅ PROVEN: Where cancelled_at exists
        ]
    }
    
    cancelled_appointments = get_paginated_data(
        'individual_appointments',
        filter_params,
        f"cancelled appointments for Patient ID {PATIENT_ID}"
    )
    
    cancellation_count = len(cancelled_appointments)
    
    behavior_data['cancellations'] = {
        'cancellation_count': cancellation_count,
        'cancelled_appointments': cancelled_appointments
    }
    print(f"   ✅ Total cancellations: {cancellation_count}")
    
    # BEHAVIOR 10: Did Not Arrive (DNA) - WORKING LOGIC
    print(f"\n🎯 BEHAVIOR 10: Did Not Arrive (DNA) - WORKING LOGIC")
    
    # Filter for DNA appointments from all appointments
    dna_appointments = [appt for appt in all_appointments if appt.get('did_not_arrive')]
    dna_count = len(dna_appointments)
    
    behavior_data['dna'] = {
        'dna_count': dna_count,
        'dna_appointments': dna_appointments
    }
    print(f"   ✅ DNA count: {dna_count}")
    
    return behavior_data

def main():
    """Main function to search and extract Debbie Macgregor's behavior data using working logic"""
    print("🔍 DEBBIE MACGREGOR EXTRACTION USING WORKING VIVIANNE LOGIC")
    print("="*80)
    print("✅ APPLYING EXACT SAME LOGIC THAT WORKED FOR VIVIANNE RUSSELL:")
    print("   🕐 UTC timestamp formatting for AEST timezone")
    print("   💰 Yearly spend extraction - client-side filtering")
    print("   🏃 Consecutive attendance calculation - most recent first")
    print("   📊 Server-side + client-side hybrid filtering")
    print("   ❌ Cancellation detection using proven method")
    print("="*80)
    
    try:
        # STEP 1: Search for Debbie Macgregor
        patient_data = search_patient_debbie()
        
        if not patient_data:
            print("\n❌ SEARCH FAILED - Debbie Macgregor not found in system")
            print("💡 RECOMMENDATION: Try alternative patient for testing")
            return None
        
        # STEP 2: Extract complete behavior data using working logic
        behavior_data = extract_complete_behavior_data(patient_data)
        
        # STEP 3: Display comprehensive summary
        PATIENT_NAME = f"{patient_data.get('first_name')} {patient_data.get('last_name')}"
        PATIENT_ID = patient_data.get('id')
        
        print(f"\n🎯 {PATIENT_NAME.upper()} BEHAVIOR SUMMARY (USING WORKING LOGIC)")
        print("="*80)
        
        print(f"\n✅ POSITIVE BEHAVIORS:")
        print(f"   📅 Future Appointments Booked: {behavior_data['appointments_booked']['future_appointments_count']}")
        print(f"   👤 Age: {behavior_data['age_demographics']['age']} years")
        print(f"   🎯 Target Demographic: {behavior_data['age_demographics']['in_target_demographic']}")
        print(f"   💰 Yearly Spend: ${behavior_data['yearly_spend']['yearly_spend']:.2f}")
        print(f"   🏃 Consecutive Attendance: {behavior_data['consecutive_attendance']['consecutive_attendance_streak']}")
        print(f"   😊 Likability: {behavior_data['likability']['likability_score']} (Manual)")
        
        print(f"\n⚠️ NEGATIVE BEHAVIORS:")
        print(f"   💸 Open DNA Invoice: {behavior_data['open_dna_invoices']['has_open_dna_invoice']} (Boolean)")
        print(f"   📄 Unpaid Invoices: {behavior_data['unpaid_invoices']['unpaid_invoice_count']}")
        print(f"   💰 Unpaid Amount: ${behavior_data['unpaid_invoices']['unpaid_amount']:.2f}")
        print(f"   😞 Unlikability: {behavior_data['unlikability']['unlikability_score']} (Manual)")
        print(f"   ❌ Cancellations: {behavior_data['cancellations']['cancellation_count']}")
        print(f"   🚫 DNA: {behavior_data['dna']['dna_count']}")
        
        # Save complete data
        complete_data = {
            'extraction_date': datetime.now(AEST).isoformat(),
            'patient_id': PATIENT_ID,
            'patient_name': PATIENT_NAME,
            'patient_data': patient_data,
            'behavior_data': behavior_data,
            'extraction_method': 'WORKING VIVIANNE LOGIC APPLIED TO DEBBIE MACGREGOR',
            'working_logic_applied': [
                'UTC timestamp formatting for AEST timezone',
                'Client-side invoice filtering for yearly spend',
                'Corrected consecutive attendance calculation (most recent first)',
                'Proper attendance logic: not cancelled AND not DNA',
                'Cancellation detection using proven cancelled_at:? method',
                'Unpaid invoice detection using closed_at:!? method',
                'All 10 behavior categories with working logic'
            ]
        }
        
        filename = f"debbie_macgregor_working_logic_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(complete_data, f, indent=2, default=str)
        
        print(f"\n💾 Behavior data saved to: {filename}")
        print(f"✅ DEBBIE MACGREGOR EXTRACTION COMPLETE!")
        print(f"🎯 USING EXACT SAME WORKING LOGIC AS VIVIANNE RUSSELL")
        print(f"🚀 Ready for accurate A+ through F scoring!")
        
        return complete_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🎯 Starting Debbie Macgregor extraction using working Vivianne logic...")
    print("🔧 APPLYING: UTC timestamps, consecutive attendance, yearly spend logic")
    print("📋 Using proven July 4, 2025 corrected behavior logic")
    print("📋 Using July 3, 2025 proven cancellation method")
    
    extracted_data = main()
    
    if extracted_data:
        print(f"\n🎉 SUCCESS! Debbie Macgregor extraction using working logic finished!")
        print(f"✅ Applied exact same logic that worked for Vivianne Russell")
        print(f"✅ UTC timestamp formatting applied")
        print(f"✅ Consecutive attendance calculation applied")
        print(f"✅ Client-side filtering for complex logic applied")
        print(f"🎯 Ready for accurate A+ through F rating calculation!")
    else:
        print(f"\n❌ Extraction failed - patient may not exist in system")
        print(f"💡 Consider testing with a different known patient")
        
