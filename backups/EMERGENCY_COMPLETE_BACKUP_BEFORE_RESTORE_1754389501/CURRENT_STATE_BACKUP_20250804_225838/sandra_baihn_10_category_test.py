#!/usr/bin/env python3
"""
🔍 SANDRA BAIHN 10-CATEGORY BEHAVIOR EXTRACTION
✅ Using corrected consecutive attendance logic (DNA OR cancellation breaks streak)
✅ Following Cliniko API documentation
✅ All 10 behavior categories with proven extraction methods
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
        if endpoint == 'individual_appointments':
            items = response_data.get('individual_appointments', [])
        elif endpoint == 'patients':
            items = response_data.get('patients', [])
        elif endpoint == 'invoices':
            items = response_data.get('invoices', [])
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

def search_patient_sandra():
    """Search for Sandra Baihn using WORKING Debbie Macgregor method"""
    print(f"\n🔍 STEP 1: PATIENT SEARCH - SANDRA BAIHN")
    print("="*60)
    
    # Try different name variations using WORKING method
    search_variations = [
        ("Sandra", "Baihn"),
        ("Sandra", ""),
        ("", "Baihn")
    ]
    
    for first_name, last_name in search_variations:
        search_desc = f"Exact match: {first_name} {last_name}".strip()
        print(f"\n🔍 Trying: {search_desc}")
        
        # ✅ WORKING METHOD: Use exact name matching (same as Debbie)
        filter_params = {}
        if first_name:
            filter_params['first_name'] = first_name
        if last_name:
            filter_params['last_name'] = last_name
        
        patients = get_paginated_data(
            'patients',
            filter_params,
            search_desc
        )
        
        if patients:
            print(f"\n✅ FOUND {len(patients)} PATIENT(S):")
            for i, patient in enumerate(patients, 1):
                full_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
                dob = patient.get('date_of_birth', 'N/A')
                age = None
                if dob and dob != 'N/A':
                    try:
                        birth_date = datetime.strptime(dob, '%Y-%m-%d')
                        age = (datetime.now() - birth_date).days // 365
                    except:
                        age = 'N/A'
                
                print(f"\n   {i}. 👤 ID: {patient.get('id')}")
                print(f"      📝 Name: {full_name}")
                print(f"      📅 DOB: {dob}")
                print(f"      📧 Email: {patient.get('email', 'N/A')}")
                print(f"      🎂 Age: {age} years" if age else "      🎂 Age: N/A")
                
                # Return first Sandra Baihn match
                if 'sandra' in full_name.lower() and 'baihn' in full_name.lower():
                    return patient
            
            # If no exact match, return first result
            return patients[0]
    
    print(f"\n❌ Sandra Baihn not found in any search variation")
    return None

def extract_complete_behavior_data(patient_data):
    """Extract all 10 behavior categories using corrected logic"""
    
    PATIENT_ID = patient_data.get('id')
    behavior_data = {}
    
    # BEHAVIOR 1: Appointments Booked (Future Only) - WORKING LOGIC
    print(f"\n🎯 BEHAVIOR 1: Appointments Booked (Future Only) - WORKING LOGIC")
    
    # Get current UTC time for server-side filtering
    now_utc = datetime.now(pytz.UTC)
    now_utc_str = now_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    filter_params = {
        'q[]': [
            f'patient_id:={PATIENT_ID}',
            f'starts_at:>{now_utc_str}'
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
    
    # BEHAVIOR 2: Age Demographics - WORKING LOGIC
    print(f"\n🎯 BEHAVIOR 2: Age Demographics - WORKING LOGIC")
    
    dob = patient_data.get('date_of_birth')
    age = None
    in_target_demographic = False
    
    if dob:
        try:
            birth_date = datetime.strptime(dob, '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
            in_target_demographic = 20 <= age <= 55
        except:
            age = None
    
    behavior_data['age_demographics'] = {
        'age': age,
        'date_of_birth': dob,
        'in_target_demographic': in_target_demographic
    }
    print(f"   ✅ Age: {age} years")
    print(f"   ✅ In target demographic (20-55): {in_target_demographic}")
    
    # BEHAVIOR 3: Yearly Spend (Last 12 months) - WORKING LOGIC
    print(f"\n🎯 BEHAVIOR 3: Yearly Spend (Last 12 months) - WORKING LOGIC")
    
    filter_params = {
        'q[]': f'patient_id:={PATIENT_ID}'
    }
    
    all_invoices = get_paginated_data(
        'invoices',
        filter_params,
        f"all invoices for Patient ID {PATIENT_ID}"
    )
    
    # Client-side filtering for yearly spend (last 12 months)
    twelve_months_ago = datetime.now(AEST) - timedelta(days=365)
    yearly_spend = 0
    paid_invoices_count = 0
    
    for invoice in all_invoices:
        # Check if invoice is paid and within last 12 months
        if invoice.get('closed_at'):  # Invoice is paid
            try:
                closed_date = datetime.fromisoformat(invoice['closed_at'].replace('Z', '+00:00'))
                closed_date_aest = closed_date.astimezone(AEST)
                
                if closed_date_aest >= twelve_months_ago:
                    yearly_spend += float(invoice.get('total_amount', 0))
                    paid_invoices_count += 1
            except:
                continue
    
    behavior_data['yearly_spend'] = {
        'yearly_spend': yearly_spend,
        'paid_invoices_count': paid_invoices_count,
        'total_invoices_checked': len(all_invoices)
    }
    print(f"   ✅ Yearly spend (12 months): ${yearly_spend:.2f}")
    print(f"   ✅ Paid invoices count: {paid_invoices_count}")
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
    
    # ✅ WORKING LOGIC: Count of unpaid invoices (not sum of money)
    unpaid_invoice_count = len(unpaid_invoices)
    unpaid_amount = sum(float(inv.get('total_amount', 0)) for inv in unpaid_invoices)
    
    behavior_data['unpaid_invoices'] = {
        'unpaid_invoice_count': unpaid_invoice_count,
        'unpaid_amount': unpaid_amount
    }
    print(f"   ✅ Unpaid invoice count: {unpaid_invoice_count}")
    print(f"   ✅ Unpaid amount: ${unpaid_amount:.2f}")
    
    # BEHAVIOR 8: Unlikability (Manual Input)
    print(f"\n🎯 BEHAVIOR 8: Unlikability (Manual Input)")
    
    behavior_data['unlikability'] = {
        'unlikability_score': 0,
        'manual_input_required': True
    }
    print(f"   ✅ Unlikability score: 0 (Manual input required)")
    
    # BEHAVIOR 9: Cancellations - PROVEN METHOD
    print(f"\n🎯 BEHAVIOR 9: Cancellations - PROVEN METHOD")
    
    # ✅ PROVEN METHOD: Server-side filtering for cancelled appointments
    filter_params = {
        'q[]': [
            f'patient_id:={PATIENT_ID}',
            'cancelled_at:?'  # Where cancelled_at exists
        ]
    }
    
    cancelled_appointments_for_count = get_paginated_data(
        'individual_appointments',
        filter_params,
        f"cancelled appointments for Patient ID {PATIENT_ID}"
    )
    
    behavior_data['cancellations'] = {
        'total_cancellations': len(cancelled_appointments_for_count),
        'cancelled_appointments': cancelled_appointments_for_count
    }
    print(f"   ✅ Total cancellations: {len(cancelled_appointments_for_count)}")
    
    # BEHAVIOR 10: Did Not Arrive (DNA) - WORKING LOGIC
    print(f"\n🎯 BEHAVIOR 10: Did Not Arrive (DNA) - WORKING LOGIC")
    
    # ✅ WORKING LOGIC: Count DNA appointments from all appointments
    dna_count = sum(1 for apt in all_appointments if apt.get('did_not_arrive') is True)
    
    behavior_data['dna'] = {
        'dna_count': dna_count,
        'dna_appointments': [apt for apt in all_appointments if apt.get('did_not_arrive') is True]
    }
    print(f"   ✅ DNA count: {dna_count}")
    
    return behavior_data

def main():
    """Main function to extract Sandra Baihn's complete behavior data"""
    
    print("🔧 SANDRA BAIHN 10-CATEGORY BEHAVIOR EXTRACTION")
    print("="*80)
    print("✅ Using corrected consecutive attendance logic (DNA OR cancellation breaks streak)")
    print("✅ Following Cliniko API documentation")
    print("✅ All 10 behavior categories with proven extraction methods")
    print("="*80)
    
    try:
        # Step 1: Search for Sandra Baihn
        patient_data = search_patient_sandra()
        
        if not patient_data:
            print("❌ Sandra Baihn not found. Exiting.")
            return None
        
        # Step 2: Extract complete behavior data
        print(f"\n🚀 STEP 2: EXTRACTING COMPLETE BEHAVIOR DATA")
        print("="*80)
        print(f"👤 Patient: {patient_data.get('first_name')} {patient_data.get('last_name')} (ID: {patient_data.get('id')})")
        print(f"📅 Extraction Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S')} AEST")
        print("✅ USING CORRECTED 10-CATEGORY LOGIC")
        print("✅ Fixed consecutive attendance, yearly spend, cancellation detection")
        print("="*80)
        
        behavior_data = extract_complete_behavior_data(patient_data)
        
        # Step 3: Display summary
        print(f"\n🎯 SANDRA BAIHN BEHAVIOR SUMMARY")
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
        print(f"   ❌ Cancellations: {behavior_data['cancellations']['total_cancellations']}")
        print(f"   🚫 DNA: {behavior_data['dna']['dna_count']}")
        
        # Step 4: Save complete data
        complete_data = {
            'extraction_date': datetime.now(AEST).isoformat(),
            'patient_info': patient_data,
            'behavior_data': behavior_data,
            'extraction_method': 'CORRECTED 10-category system',
            'consecutive_attendance_fixed': True,
            'cliniko_api_documentation_followed': True
        }
        
        filename = f"sandra_baihn_complete_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(complete_data, f, indent=2, default=str)
        
        print(f"\n💾 Behavior data saved to: {filename}")
        print(f"✅ SANDRA BAIHN EXTRACTION COMPLETE!")
        print(f"🎯 USING CORRECTED 10-CATEGORY LOGIC")
        print(f"🚀 Ready for accurate A+ through F scoring!")
        
        return complete_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🎯 Starting Sandra Baihn 10-category behavior extraction...")
    print("🔧 APPLYING: Corrected consecutive attendance logic")
    print("📋 Using proven extraction methods from Debbie Macgregor test")
    print("📋 Following Cliniko API documentation")
    
    result = main()
    
    if result:
        print(f"\n🎉 SUCCESS! Sandra Baihn extraction using corrected logic finished!")
        print(f"✅ Applied corrected consecutive attendance logic")
        print(f"✅ UTC timestamp formatting applied")
        print(f"✅ Client-side filtering for complex logic applied")
        print(f"🎯 Ready for accurate A+ through F rating calculation!")
    else:
        print(f"\n❌ Sandra Baihn extraction failed")
