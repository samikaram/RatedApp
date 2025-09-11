import requests
import json
from datetime import datetime
import pytz
import base64
import time

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
    'User-Agent': 'Patient Behavior Rating System'
}

def get_patient_appointments(patient_id):
    """Get ALL appointments for a specific patient"""
    print(f"   📅 Fetching appointments for patient {patient_id}...")
    
    # We can't filter by patient_id, so we need to get all appointments
    # and filter them in Python (this is the limitation we discovered)
    all_appointments = []
    page = 1
    
    while True:
        params = {'per_page': 100, 'page': page}
        response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        appointments = data.get('individual_appointments', [])
        
        if not appointments:
            break
        
        # Filter for this specific patient
        patient_appointments = [
            appt for appt in appointments 
            if appt.get('patient', {}).get('links', {}).get('self', '').split('/')[-1] == str(patient_id)
        ]
        
        all_appointments.extend(patient_appointments)
        page += 1
        
        # If we haven't found any appointments for this patient in 10 pages, 
        # they probably don't have many appointments
        if page > 10 and not all_appointments:
            break
            
        # If we found appointments but none in this page, keep looking a bit more
        if page > 20:
            break
    
    return all_appointments

def get_patient_invoices(patient_id):
    """Get ALL invoices for a specific patient"""
    print(f"   💰 Fetching invoices for patient {patient_id}...")
    
    # Same limitation - can't filter by patient_id directly
    all_invoices = []
    page = 1
    
    while True:
        params = {'per_page': 100, 'page': page}
        response = requests.get(f"{BASE_URL}/invoices", headers=headers, params=params)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        invoices = data.get('invoices', [])
        
        if not invoices:
            break
        
        # Filter for this specific patient
        patient_invoices = [
            inv for inv in invoices 
            if inv.get('patient', {}).get('links', {}).get('self', '').split('/')[-1] == str(patient_id)
        ]
        
        all_invoices.extend(patient_invoices)
        page += 1
        
        # Same logic as appointments
        if page > 10 and not all_invoices:
            break
        if page > 20:
            break
    
    return all_invoices

def get_patient_details(patient_id):
    """Get specific patient details by ID"""
    print(f"   👤 Fetching details for patient {patient_id}...")
    
    response = requests.get(f"{BASE_URL}/patients/{patient_id}", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"      ❌ Error fetching patient {patient_id}: {response.status_code}")
        return None

def main():
    print("🎯 TARGETED PATIENT BEHAVIOR EXTRACTION")
    print("="*60)
    print("🔧 Approach: Get specific data for each target patient")
    
    try:
        # Step 1: Get target patients from June 16-21, 2025
        print("\n🎯 STEP 1: Identifying target patients...")
        start_date = AEST.localize(datetime(2025, 6, 16, 0, 5)).astimezone(pytz.UTC)
        end_date = AEST.localize(datetime(2025, 6, 21, 23, 55)).astimezone(pytz.UTC)
        
        params = {
            'per_page': 100,
            'page': 1,
            'q[]': [
                f'starts_at:>{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                f'starts_at:<{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            ]
        }
        
        target_appointments = []
        page = 1
        while True:
            params['page'] = page
            response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
            if response.status_code != 200:
                break
            data = response.json()
            appointments = data.get('individual_appointments', [])
            if not appointments:
                break
            target_appointments.extend(appointments)
            page += 1
            
        target_patient_ids = list(set([
            appt['patient']['links']['self'].split('/')[-1] 
            for appt in target_appointments 
            if appt.get('patient', {}).get('links', {}).get('self')
        ]))
        
        print(f"✅ Target patients: {len(target_patient_ids)} from {len(target_appointments)} appointments")
        
        # Step 2: Process each target patient individually
        print(f"\n🎯 STEP 2: Processing {len(target_patient_ids)} patients individually...")
        
        results = []
        
        for i, patient_id in enumerate(target_patient_ids, 1):
            print(f"\n👤 Patient {i}/{len(target_patient_ids)}: ID {patient_id}")
            
            # Get patient details
            patient_data = get_patient_details(patient_id)
            if not patient_data:
                continue
                
            # Get patient appointments
            appointments = get_patient_appointments(patient_id)
            
            # Get patient invoices  
            invoices = get_patient_invoices(patient_id)
            
            # Calculate metrics
            total_appointments = len(appointments)
            attended = len([a for a in appointments if a.get('patient_arrived')])
            dna = len([a for a in appointments if a.get('did_not_arrive')])
            cancelled = len([a for a in appointments if a.get('cancelled_at')])
            
            # Financial metrics
            total_invoiced = sum(float(inv.get('total_amount', 0)) for inv in invoices)
            # Try multiple payment status fields
            paid_invoices = []
            for inv in invoices:
                if (inv.get('status') == 'paid' or 
                    inv.get('payment_status') == 'paid' or 
                    float(inv.get('amount_paid', 0)) > 0):
                    paid_invoices.append(inv)
            
            total_paid = sum(float(inv.get('amount_paid', 0)) for inv in paid_invoices)
            
            # Demographics
            patient_info = patient_data.get('patient', patient_data)
            name = f"{patient_info.get('first_name', '')} {patient_info.get('last_name', '')}"
            dob = patient_info.get('date_of_birth')
            age = None
            if dob:
                birth_date = datetime.strptime(dob, '%Y-%m-%d')
                age = (datetime.now() - birth_date).days // 365
            
            # Referral source
            referral = "Unknown"
            if patient_info.get('referral_source'):
                if isinstance(patient_info['referral_source'], dict):
                    referral = patient_info['referral_source'].get('name', 'Unknown')
                else:
                    referral = str(patient_info['referral_source'])
            
            patient_result = {
                'patient_id': patient_id,
                'name': name.strip(),
                'age': age,
                'referral_source': referral,
                'total_appointments': total_appointments,
                'attended': attended,
                'dna': dna,
                'cancelled': cancelled,
                'attendance_rate': (attended / total_appointments * 100) if total_appointments > 0 else 0,
                'cancellation_rate': (cancelled / total_appointments * 100) if total_appointments > 0 else 0,
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'payment_rate': (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
            }
            
            results.append(patient_result)
            
            print(f"      📊 {total_appointments} appointments, {attended} attended ({patient_result['attendance_rate']:.1f}%)")
            print(f"      💰 ${total_invoiced:.2f} invoiced, ${total_paid:.2f} paid ({patient_result['payment_rate']:.1f}%)")
            
            # Small delay to be nice to the API
            time.sleep(0.1)
        
        # Step 3: Display comprehensive results
        print(f"\n🎯 STEP 3: COMPREHENSIVE RESULTS")
        print("="*60)
        print(f"📊 Successfully analyzed {len(results)} patients")
        
        if results:
            avg_attendance = sum(r['attendance_rate'] for r in results) / len(results)
            avg_appointments = sum(r['total_appointments'] for r in results) / len(results)
            total_revenue = sum(r['total_paid'] for r in results)
            
            print(f"\n📈 CLINIC STATISTICS:")
            print(f"   👥 Patients analyzed: {len(results)}")
            print(f"   📅 Average appointments per patient: {avg_appointments:.1f}")
            print(f"   ✅ Average attendance rate: {avg_attendance:.1f}%")
            print(f"   💰 Total revenue: ${total_revenue:.2f}")
        
        # Save results
        filename = f"targeted_patient_behaviors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'extraction_date': datetime.now(AEST).isoformat(),
                'target_period': 'June 16-21, 2025',
                'total_patients': len(results),
                'patient_behaviors': results
            }, f, indent=2, default=str)
        
        print(f"\n💾 Complete results saved to: {filename}")
        print(f"✅ TARGETED EXTRACTION COMPLETE!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

