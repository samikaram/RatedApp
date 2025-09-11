import requests
import json
from datetime import datetime
import pytz
import base64

# API Configuration
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Create headers
auth_string = f"{API_KEY}:"
encoded_auth = base64.b64encode(auth_string.encode()).decode()
headers = {
    'Authorization': f'Basic {encoded_auth}',
    'Accept': 'application/json',
    'User-Agent': 'RatedApp Patient Search and Extraction'
}

def search_patient_by_name(first_name, last_name):
    """Search for patient by name using official Cliniko filtering"""
    print(f"\n🔍 SEARCHING FOR PATIENT: {first_name} {last_name}")
    
    # Use official Cliniko filtering syntax with proper comparison operators
    search_params = {
        'q[]': [
            f'first_name:={first_name}',
            f'last_name:={last_name}'
        ],
        'per_page': 50
    }
    
    print(f"   📡 Using search filters: {search_params}")
    
    response = requests.get(f"{BASE_URL}/patients", headers=headers, params=search_params)
    
    if response.status_code != 200:
        print(f"   ❌ Search failed: {response.status_code}")
        print(f"   📋 Response: {response.text}")
        return None
    
    data = response.json()
    patients = data.get('patients', [])
    
    print(f"   ✅ Found {len(patients)} matching patients")
    
    if not patients:
        print(f"   ⚠️  No patients found matching '{first_name} {last_name}'")
        return None
    
    # Display all matching patients
    for i, patient in enumerate(patients):
        print(f"   👤 Match {i+1}: {patient.get('first_name', '')} {patient.get('last_name', '')} (ID: {patient.get('id', 'N/A')})")
    
    return patients

def get_filtered_data(endpoint, filter_params, description):
    """Get filtered data using server-side filtering with q[] parameters"""
    print(f"\n📡 Fetching {description} with server-side filtering...")
    all_data = []
    page = 1
    
    while True:
        # Combine filter params with pagination
        params = filter_params.copy()
        params['per_page'] = 100
        params['page'] = page
        
        print(f"   🔍 Requesting {endpoint} page {page} with filters: {filter_params}")
        
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"   ❌ Error on page {page}: {response.status_code}")
            print(f"   📋 Response: {response.text}")
            break
            
        data = response.json()
        items = data.get(endpoint, [])
        
        if not items:
            print(f"   ✅ No more data - completed at page {page-1}")
            break
            
        all_data.extend(items)
        print(f"   📄 Page {page}: {len(items)} {description} retrieved")
        page += 1
    
    print(f"✅ Total {description}: {len(all_data)}")
    return all_data

def convert_to_aest(utc_datetime_str):
    """Convert UTC datetime string to AEST for display"""
    if not utc_datetime_str:
        return "N/A"
    try:
        utc_time = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))
        aest_time = utc_time.astimezone(AEST)
        return aest_time.strftime('%Y-%m-%d %H:%M:%S AEST')
    except:
        return utc_datetime_str

def extract_patient_behavior_data(patient_id, patient_name):
    """Extract complete behavior data for a specific patient"""
    print(f"\n🎯 EXTRACTING COMPLETE BEHAVIOR DATA FOR: {patient_name} (ID: {patient_id})")
    print("="*80)
    
    try:
        # Step 1: Get patient information
        print(f"\n🎯 STEP 1: Getting patient information...")
        patient_response = requests.get(f"{BASE_URL}/patients/{patient_id}", headers=headers)
        
        if patient_response.status_code != 200:
            print(f"❌ Failed to get patient info: {patient_response.status_code}")
            print(f"📋 Response: {patient_response.text}")
            return None
        
        patient_info = patient_response.json()
        print(f"✅ Patient confirmed: {patient_info.get('first_name', '')} {patient_info.get('last_name', '')}")
        
        # Step 2: Get ALL active appointments
        print(f"\n🎯 STEP 2: Getting ALL active appointments for {patient_name}...")
        
        appointment_filter_params = {
            'q[]': f'patient_id:={patient_id}'
        }
        
        active_appointments = get_filtered_data(
            'individual_appointments', 
            appointment_filter_params, 
            f"active appointments for Patient ID {patient_id}"
        )
        
        # Step 3: Get ALL cancelled appointments
        print(f"\n🎯 STEP 3: Getting ALL cancelled appointments for {patient_name}...")
        print("   📋 Using cancelled_at:? method to find cancelled appointments")
        
        cancelled_filter_params = {
            'q[]': [
                'cancelled_at:?',
                f'patient_id:={patient_id}'
            ]
        }
        
        cancelled_appointments = get_filtered_data(
            'individual_appointments', 
            cancelled_filter_params, 
            f"cancelled appointments for Patient ID {patient_id}"
        )
        
        # Step 4: Combine appointments
        print(f"\n🎯 STEP 4: Combining active and cancelled appointments...")
        
        all_appointments = active_appointments.copy()
        
        # Add cancelled appointments that aren't already in active list
        for cancelled_appt in cancelled_appointments:
            cancelled_id = cancelled_appt.get('id')
            if not any(appt.get('id') == cancelled_id for appt in all_appointments):
                all_appointments.append(cancelled_appt)
        
        print(f"✅ Combined appointments:")
        print(f"   📅 Active appointments: {len(active_appointments)}")
        print(f"   ❌ Cancelled appointments: {len(cancelled_appointments)}")
        print(f"   📊 Total unique appointments: {len(all_appointments)}")
        
        # Step 5: Get ALL invoices
        print(f"\n🎯 STEP 5: Getting ALL invoices for {patient_name}...")
        
        invoice_filter_params = {
            'q[]': f'patient_id:={patient_id}'
        }
        
        invoices = get_filtered_data(
            'invoices', 
            invoice_filter_params, 
            f"invoices for Patient ID {patient_id}"
        )
        
        # Step 6: Process and calculate behavior metrics
        print(f"\n🎯 STEP 6: Processing {patient_name}'s complete data with proper cancellation detection...")
        
        # Convert times to AEST
        for appt in all_appointments:
            appt['starts_at_aest'] = convert_to_aest(appt.get('starts_at'))
            appt['cancelled_at_aest'] = convert_to_aest(appt.get('cancelled_at'))
        
        for inv in invoices:
            inv['created_at_aest'] = convert_to_aest(inv.get('created_at'))
            inv['closed_at_aest'] = convert_to_aest(inv.get('closed_at'))
        
        # Calculate comprehensive metrics using corrected attendance logic
        total_appointments = len(all_appointments)
        cancelled = len([a for a in all_appointments if a.get('cancelled_at')])
        dna = len([a for a in all_appointments if a.get('did_not_arrive')])
        attended = len([a for a in all_appointments if not a.get('cancelled_at') and not a.get('did_not_arrive')])
        
        total_invoiced = sum(float(inv.get('total_amount', 0)) for inv in invoices)
        total_paid = sum(float(inv.get('total_amount', 0)) for inv in invoices if inv.get('closed_at'))
        unpaid_amount = total_invoiced - total_paid
        
        attendance_rate = (attended / total_appointments * 100) if total_appointments > 0 else 0
        payment_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
        
        # Step 7: Display comprehensive results
        print(f"\n🎯 STEP 7: COMPREHENSIVE RESULTS - WITH PROPER CANCELLATION DETECTION")
        print("="*80)
        
        print(f"\n👤 PATIENT INFORMATION:")
        print(f"   Name: {patient_info.get('first_name', '')} {patient_info.get('last_name', '')}")
        print(f"   Patient ID: {patient_id}")
        print(f"   Email: {patient_info.get('email', 'N/A')}")
        print(f"   Phone: {patient_info.get('phone_number', 'N/A')}")
        print(f"   Date of Birth: {patient_info.get('date_of_birth', 'N/A')}")
        
        print(f"\n📊 BEHAVIOR METRICS (ALL TIME - WITH PROPER CANCELLATION DETECTION):")
        print(f"   📅 Total Appointments: {total_appointments}")
        print(f"   ✅ Attended: {attended}")
        print(f"   ❌ Cancelled: {cancelled}")
        print(f"   🚫 DNA: {dna}")
        print(f"   📈 Attendance Rate: {attendance_rate:.1f}%")
        print(f"   💰 Total Invoiced: ${total_invoiced:.2f}")
        print(f"   💵 Total Paid: ${total_paid:.2f}")
        print(f"   💳 Unpaid Amount: ${unpaid_amount:.2f}")
        print(f"   📄 Total Invoices: {len(invoices)}")
        print(f"   📊 Payment Rate: {payment_rate:.1f}%")
        
        # Display appointment breakdown
        print(f"\n📋 APPOINTMENT STATUS BREAKDOWN:")
        sorted_appointments = sorted(all_appointments, key=lambda x: x.get('starts_at', ''))
        for appt in sorted_appointments:
            starts_at = appt.get('starts_at_aest', 'N/A')
            if appt.get('cancelled_at'):
                status = f"Cancelled {appt.get('cancellation_reason_description', 'Unknown')}"
            elif appt.get('did_not_arrive'):
                status = "DNA"
            else:
                status = "Attended"
            print(f"   {starts_at} - {status}")
        
        # Compare to Sami Karam's profile
        print(f"\n🔍 COMPARISON TO SAMI KARAM (A/A+ PATIENT):")
        print(f"   Sami: 90.2% attendance, 97.4% payment rate")
        print(f"   {patient_name}: {attendance_rate:.1f}% attendance, {payment_rate:.1f}% payment rate")
        
        # Step 8: Save complete data
        complete_data = {
            'extraction_date': datetime.now(AEST).isoformat(),
            'method': 'NAME SEARCH + INDIVIDUAL EXTRACTION WITH PROPER CANCELLATIONS',
            'patient_id': patient_id,
            'patient_name': patient_name,
            'patient_info': patient_info,
            'appointments': all_appointments,
            'invoices': invoices,
            'metrics': {
                'total_appointments': total_appointments,
                'attended': attended,
                'cancelled': cancelled,
                'dna': dna,
                'attendance_rate': attendance_rate,
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'unpaid_amount': unpaid_amount,
                'payment_rate': payment_rate
            }
        }
        
        filename = f"patient_data_{patient_name.replace(' ', '_').replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(complete_data, f, indent=2, default=str)
        
        print(f"\n💾 Complete data with proper cancellations saved to: {filename}")
        print(f"✅ HIGHLY EFFICIENT EXTRACTION COMPLETE WITH PROPER CANCELLATION DETECTION!")
        print(f"🚀 Used server-side filtering with cancelled_at:? method!")
        
        return complete_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("🚀 HIGHLY EFFICIENT KEVIN EL-AZZI DATA EXTRACTION - WITH PROPER CANCELLATIONS")
    print("="*80)
    print("🎯 Using CORRECT SERVER-SIDE FILTERING with proper string comparison operators")
    print("📋 This mimics the RatedApp UI workflow: Search by name → View behavior profile")
    
    # Search for Kevin El-Azzi
    target_first_name = "Kevin"
    target_last_name = "El-Azzi"
    
    # Step 1: Search for patient by name
    matching_patients = search_patient_by_name(target_first_name, target_last_name)
    
    if not matching_patients:
        print(f"\n❌ No patients found matching '{target_first_name} {target_last_name}'")
        return None
    
    # Step 2: Use the first matching patient (or let user choose)
    target_patient = matching_patients[0]
    patient_id = target_patient.get('id')
    patient_name = f"{target_patient.get('first_name', '')} {target_patient.get('last_name', '')}"
    
    print(f"\n🎯 SELECTED PATIENT: {patient_name} (ID: {patient_id})")
    
    # Step 3: Extract complete behavior data
    extracted_data = extract_patient_behavior_data(patient_id, patient_name)
    
    if extracted_data:
        print(f"\n🎉 SUCCESS! Complete behavior analysis for {patient_name}")
        print(f"📊 Total appointments: {extracted_data['metrics']['total_appointments']}")
        print(f"❌ Cancelled appointments: {extracted_data['metrics']['cancelled']}")
        print(f"💰 Total invoices: {len(extracted_data['invoices'])}")
        print(f"🚀 Method: Server-side filtering with proper cancellation detection")
        print(f"📋 Ready for RatedApp scoring and rating calculation!")
        return extracted_data
    else:
        print(f"\n❌ Extraction failed for {patient_name}")
        return None

if __name__ == "__main__":
    print("🎯 Starting RatedApp patient search and extraction...")
    result = main()
    if result:
        print(f"\n🚀 EXTRACTION COMPLETE - Ready for behavior rating!")
        print(f"🎯 Patient found via name search and complete data extracted!")
        print(f"📊 All behavior metrics calculated and ready for Django integration!")
    else:
        print(f"\n❌ Extraction failed - check error messages above")
        
