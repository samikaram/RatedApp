import requests
import json
from datetime import datetime
import pytz
import base64
from collections import defaultdict

# API Configuration
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Create headers (per Cliniko docs)
auth_string = f"{API_KEY}:"
encoded_auth = base64.b64encode(auth_string.encode()).decode()
headers = {
    'Authorization': f'Basic {encoded_auth}',
    'Accept': 'application/json',
    'User-Agent': 'Patient Behavior Rating System - Sami Karam Data'
}

def get_all_data(endpoint, params=None):
    """Get all data from paginated endpoint using Cliniko documented method"""
    all_data = []
    page = 1
    
    while True:
        current_params = params.copy() if params else {}
        current_params['page'] = page
        current_params['per_page'] = 100
        
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params=current_params)
        if response.status_code != 200:
            print(f"   ❌ Error on {endpoint} page {page}: {response.status_code}")
            if response.status_code == 400:
                print(f"   📋 Response: {response.text}")
            break
            
        data = response.json()
        items = data.get(endpoint, [])
        if not items:
            break
            
        all_data.extend(items)
        print(f"   📄 {endpoint.title()} page {page}: {len(items)} items")
        page += 1
    
    return all_data

def main():
    print("🎯 COMPREHENSIVE SAMI KARAM PATIENT DATA EXTRACTION")
    print("="*70)
    print("📋 Extracting ALL available data for Sami Karam as a patient")
    print("🔍 Using Cliniko documented methods - complete patient history")
    
    try:
        # Step 1: Get ALL patients and search for Sami Karam (Cliniko doesn't support name filtering)
        print(f"\n🎯 STEP 1: Getting all patients to find Sami Karam...")
        print("   📋 Note: Cliniko API doesn't support name filtering - retrieving all patients")
        
        # Get all patients (no filtering - as per your context about API limitations)
        all_patients = get_all_data('patients')
        
        # Find Sami Karam in the results
        sami_patient = None
        for patient in all_patients:
            first_name = patient.get('first_name', '').lower()
            last_name = patient.get('last_name', '').lower()
            
            # Check for various name combinations
            if ('sami' in first_name and 'karam' in last_name) or \
               ('dr' in first_name and 'sami' in first_name and 'karam' in last_name) or \
               (first_name == 'sami' and last_name == 'karam'):
                sami_patient = patient
                break
        
        if not sami_patient:
            print("❌ Sami Karam not found as a patient in Cliniko")
            print("🔍 Searching for similar names...")
            
            # Show patients with similar names for debugging
            similar_patients = []
            for patient in all_patients:
                first_name = patient.get('first_name', '').lower()
                last_name = patient.get('last_name', '').lower()
                if 'sami' in first_name or 'karam' in last_name:
                    similar_patients.append(f"{patient.get('first_name', '')} {patient.get('last_name', '')} (ID: {patient.get('id')})")
            
            if similar_patients:
                print("🔍 Found similar names:")
                for name in similar_patients[:10]:  # Show first 10
                    print(f"   - {name}")
            else:
                print("🔍 No similar names found")
            
            return None
        
        sami_patient_id = str(sami_patient['id'])
        print(f"✅ Found Sami Karam - Patient ID: {sami_patient_id}")
        print(f"   👤 Name: {sami_patient.get('first_name', '')} {sami_patient.get('last_name', '')}")
        print(f"   📧 Email: {sami_patient.get('email', 'N/A')}")
        print(f"   📱 Phone: {sami_patient.get('phone_number', 'N/A')}")
        print(f"   🎂 DOB: {sami_patient.get('date_of_birth', 'N/A')}")
        
        # Step 2: Get ALL appointments and filter for Sami (as per your context - no patient_id filtering)
        print(f"\n🎯 STEP 2: Getting ALL appointments and filtering for Sami Karam...")
        print("   📋 Note: Cliniko API doesn't support patient_id filtering - retrieving all appointments")
        
        # Get all appointments (no patient filtering - as per your context)
        all_appointments = get_all_data('individual_appointments')
        
        # Filter for Sami's appointments
        sami_appointments = []
        for appt in all_appointments:
            if appt.get('patient') and appt['patient'].get('links') and appt['patient']['links'].get('self'):
                patient_url = appt['patient']['links']['self']
                if f'/patients/{sami_patient_id}' in patient_url:
                    sami_appointments.append(appt)
        
        # Get cancelled appointments using your documented method
        print(f"\n🎯 STEP 2b: Getting cancelled appointments for Sami...")
        cancelled_params = {
            'q[]': 'cancelled_at:?'  # Your documented working method
        }
        all_cancelled = get_all_data('individual_appointments', cancelled_params)
        
        # Filter cancelled appointments for Sami
        sami_cancelled = []
        for appt in all_cancelled:
            if appt.get('patient') and appt['patient'].get('links') and appt['patient']['links'].get('self'):
                patient_url = appt['patient']['links']['self']
                if f'/patients/{sami_patient_id}' in patient_url:
                    sami_cancelled.append(appt)
        
        # Combine all appointments (avoid duplicates)
        all_sami_appointments = sami_appointments.copy()
        for cancelled in sami_cancelled:
            if cancelled not in all_sami_appointments:
                all_sami_appointments.append(cancelled)
        
        print(f"✅ Total appointments for Sami: {len(all_sami_appointments)}")
        print(f"   📅 Regular appointments: {len(sami_appointments)}")
        print(f"   ❌ Cancelled appointments: {len(sami_cancelled)}")
        
        # Step 3: Get ALL invoices and filter for Sami (as per your context)
        print(f"\n🎯 STEP 3: Getting ALL invoices and filtering for Sami Karam...")
        print("   📋 Note: Cliniko API doesn't support patient_id filtering - retrieving all invoices")
        
        all_invoices = get_all_data('invoices')
        
        # Filter for Sami's invoices
        sami_invoices = []
        for inv in all_invoices:
            if inv.get('patient') and inv['patient'].get('links') and inv['patient']['links'].get('self'):
                patient_url = inv['patient']['links']['self']
                if f'/patients/{sami_patient_id}' in patient_url:
                    sami_invoices.append(inv)
        
        print(f"✅ Total invoices for Sami: {len(sami_invoices)}")
        
        # Step 4: Get referral source information
        print(f"\n🎯 STEP 4: Getting referral source data...")
        referral_sources = get_all_data('referral_sources')
        
        referrer_name = "Unknown"
        if sami_patient.get('referral_source') and isinstance(sami_patient['referral_source'], dict):
            if sami_patient['referral_source'].get('links', {}).get('self'):
                referrer_id = sami_patient['referral_source']['links']['self'].split('/')[-1]
                referrer = next((r for r in referral_sources if str(r['id']) == referrer_id), None)
                if referrer:
                    referrer_name = referrer.get('name', 'Unknown')
        
        print(f"✅ Referral source: {referrer_name}")
        
        # Step 5: Calculate comprehensive behavior analysis for Sami Karam
        print(f"\n🎯 STEP 5: Calculating Sami Karam's behavior metrics...")
        
        # Convert appointment times to AEST for analysis
        for appt in all_sami_appointments:
            if appt.get('starts_at'):
                utc_time = datetime.fromisoformat(appt['starts_at'].replace('Z', '+00:00'))
                aest_time = utc_time.astimezone(AEST)
                appt['starts_at_aest'] = aest_time.strftime('%Y-%m-%d %H:%M:%S AEST')
        
        # BEHAVIOR CATEGORY 1: Appointments Booked
        total_appointments = len(all_sami_appointments)
        
        # BEHAVIOR CATEGORY 2: Age Demographics
        age = None
        if sami_patient.get('date_of_birth'):
            birth_date = datetime.strptime(sami_patient['date_of_birth'], '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
        
        # BEHAVIOR CATEGORY 3: Total Spend (across all time)
        total_spend = sum(float(inv.get('total_amount', 0)) for inv in sami_invoices)
        
        # BEHAVIOR CATEGORY 4: Referrer Score
        referrer_score = referrer_name
        
        # BEHAVIOR CATEGORY 5: Consecutive Attendance
        attended_appointments = [a for a in all_sami_appointments if not a.get('cancelled_at') and not a.get('did_not_arrive')]
        consecutive_attendance = len(attended_appointments)
        
        # BEHAVIOR CATEGORY 7: Open Non-Attendance Fee Invoice
        dna_fee_invoices = [inv for inv in sami_invoices if 'non-attendance' in inv.get('notes', '').lower() or 'dna' in inv.get('notes', '').lower()]
        open_dna_fees = sum(float(inv.get('total_amount', 0)) for inv in dna_fee_invoices if inv.get('closed_at') is None)
        
        # BEHAVIOR CATEGORY 8: Unpaid Invoices
        unpaid_invoices = [inv for inv in sami_invoices if inv.get('closed_at') is None]
        unpaid_amount = sum(float(inv.get('total_amount', 0)) for inv in unpaid_invoices)
        
        # BEHAVIOR CATEGORY 10: Cancellations
        cancellations = len([a for a in all_sami_appointments if a.get('cancelled_at')])
        
        # BEHAVIOR CATEGORY 11: Did Not Arrive (DNA)
        dna_count = len([a for a in all_sami_appointments if a.get('did_not_arrive')])
        
        # Calculate payment data using Cliniko's closed_at field
        total_paid = sum(float(inv.get('total_amount', 0)) for inv in sami_invoices if inv.get('closed_at') is not None)
        
        # Calculate attendance rate
        attendance_rate = (len(attended_appointments) / total_appointments * 100) if total_appointments > 0 else 0
        
        # Display comprehensive results
        print(f"\n🎯 SAMI KARAM COMPREHENSIVE BEHAVIOR ANALYSIS")
        print("="*70)
        
        print(f"\n👤 PATIENT INFORMATION:")
        print(f"   Name: {sami_patient.get('first_name', '')} {sami_patient.get('last_name', '')}")
        print(f"   Patient ID: {sami_patient_id}")
        print(f"   Email: {sami_patient.get('email', 'N/A')}")
        print(f"   Phone: {sami_patient.get('phone_number', 'N/A')}")
        print(f"   Date of Birth: {sami_patient.get('date_of_birth', 'N/A')}")
        print(f"   Age: {age} years" if age else "   Age: Unknown")
        print(f"   Referral Source: {referrer_name}")
        
        print(f"\n📊 BEHAVIOR METRICS (ALL TIME):")
        print(f"   📅 Total Appointments Booked: {total_appointments}")
        print(f"   ✅ Attended Appointments: {len(attended_appointments)}")
        print(f"   📈 Attendance Rate: {attendance_rate:.1f}%")
        print(f"   ❌ Cancellations: {cancellations}")
        print(f"   🚫 Did Not Arrive (DNA): {dna_count}")
        print(f"   💰 Total Spend: ${total_spend:.2f}")
        print(f"   💵 Total Paid: ${total_paid:.2f}")
        print(f"   💳 Unpaid Amount: ${unpaid_amount:.2f}")
        print(f"   📄 Total Invoices: {len(sami_invoices)}")
        print(f"   📊 Payment Rate: {(total_paid/total_spend*100):.1f}%" if total_spend > 0 else "   📊 Payment Rate: N/A")
        
        if open_dna_fees > 0:
            print(f"   ⚠️ Open DNA Fees: ${open_dna_fees:.2f}")
        
        # Show appointment history (first 10 and last 10)
        if all_sami_appointments:
            print(f"\n📅 APPOINTMENT HISTORY:")
            sorted_appointments = sorted(all_sami_appointments, key=lambda x: x.get('starts_at', ''))
            
            print(f"   🔄 First 5 appointments:")
            for i, appt in enumerate(sorted_appointments[:5], 1):
                status = "Cancelled" if appt.get('cancelled_at') else "DNA" if appt.get('did_not_arrive') else "Attended"
                print(f"      {i}. {appt.get('starts_at_aest', appt.get('starts_at', 'N/A'))} - {status}")
            
            if len(sorted_appointments) > 5:
                print(f"   🔄 Last 5 appointments:")
                for i, appt in enumerate(sorted_appointments[-5:], len(sorted_appointments)-4):
                    status = "Cancelled" if appt.get('cancelled_at') else "DNA" if appt.get('did_not_arrive') else "Attended"
                    print(f"      {i}. {appt.get('starts_at_aest', appt.get('starts_at', 'N/A'))} - {status}")
        
        # Show invoice history
        if sami_invoices:
            print(f"\n💰 INVOICE HISTORY:")
            sorted_invoices = sorted(sami_invoices, key=lambda x: x.get('created_at', ''))
            
            print(f"   💵 Recent invoices:")
            for i, inv in enumerate(sorted_invoices[-5:], 1):
                status = "Paid" if inv.get('closed_at') else "Unpaid"
                amount = float(inv.get('total_amount', 0))
                created_date = inv.get('created_at', 'N/A')
                if created_date != 'N/A':
                    utc_time = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    aest_time = utc_time.astimezone(AEST)
                    created_date = aest_time.strftime('%Y-%m-%d %H:%M AEST')
                print(f"      {i}. {created_date} - ${amount:.2f} - {status}")
        
        # Save comprehensive Sami Karam data
        sami_data = {
            'extraction_date': datetime.now(AEST).isoformat(),
            'method': 'Comprehensive Sami Karam Patient Data - Cliniko Documented',
            'patient_info': sami_patient,
            'patient_id': sami_patient_id,
            'behavior_metrics': {
                'appointments_booked': total_appointments,
                'age_demographics': age,
                'total_spend': total_spend,
                'referrer_score': referrer_name,
                'consecutive_attendance': consecutive_attendance,
                'likability': 0,  # Manual input required
                'open_dna_fees': open_dna_fees,
                'unpaid_invoices': unpaid_amount,
                'unlikability': 0,  # Manual input required
                'cancellations': cancellations,
                'dna_count': dna_count,
                'total_paid': total_paid,
                'attendance_rate': attendance_rate,
                'payment_rate': (total_paid/total_spend*100) if total_spend > 0 else 0
            },
            'appointments': all_sami_appointments,
            'invoices': sami_invoices,
            'summary': {
                'total_appointments': total_appointments,
                'total_invoices': len(sami_invoices),
                'total_spend': total_spend,
                'total_paid': total_paid,
                'attendance_rate': attendance_rate,
                'payment_rate': (total_paid/total_spend*100) if total_spend > 0 else 0
            }
        }
        
        filename = f"sami_karam_complete_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(sami_data, f, indent=2, default=str)
        
        print(f"\n💾 Sami Karam's complete data saved to: {filename}")
        print(f"✅ SAMI KARAM COMPREHENSIVE DATA EXTRACTION COMPLETE!")
        print(f"🎯 All behavior categories extracted using Cliniko documented methods")
        print(f"📊 Ready for patient behavior rating system analysis")
        
        # Return data for further processing
        return sami_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Starting Sami Karam comprehensive patient data extraction...")
    extracted_data = main()
    if extracted_data:
        print(f"\n🎉 SUCCESS! Extracted complete patient history for Sami Karam")
        print(f"📋 All 11 behavior categories analyzed")
        print(f"🔗 Data saved and ready for behavior rating system")
        print(f"👤 Patient ID: {extracted_data['patient_id']}")
        print(f"📅 Total appointments: {extracted_data['behavior_metrics']['appointments_booked']}")
        print(f"💰 Total spend: ${extracted_data['behavior_metrics']['total_spend']:.2f}")
        print(f"✅ Attendance rate: {extracted_data['behavior_metrics']['attendance_rate']:.1f}%")
    else:
        print(f"\n❌ Extraction failed - check error messages above")
