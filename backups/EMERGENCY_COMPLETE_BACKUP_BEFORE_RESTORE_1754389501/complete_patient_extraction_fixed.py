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
    'User-Agent': 'Patient Behavior Rating System'
}

def get_all_data(endpoint, description):
    """Get all data from any Cliniko endpoint"""
    print(f"\n📡 Fetching ALL {description}...")
    all_data = []
    page = 1
    
    while True:
        params = {'per_page': 100, 'page': page}
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"   ❌ Error on page {page}: {response.status_code}")
            break
            
        data = response.json()
        items = data.get(endpoint, [])
        
        if not items:
            break
            
        all_data.extend(items)
        print(f"   📄 Page {page}: {len(items)} {description}")
        page += 1
        
        # Safety limit for testing
        if page > 50:
            print(f"   🛑 Reached page limit for testing")
            break
    
    print(f"✅ Total {description}: {len(all_data)}")
    return all_data

def main():
    print("🎯 COMPLETE PATIENT BEHAVIOR EXTRACTION - FIXED APPROACH")
    print("="*80)
    print("🔧 Using proven method: Get ALL data, then group by patients")
    
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
        
        print(f"✅ Target period: {len(target_patient_ids)} patients from {len(target_appointments)} appointments")
        
        # Step 2: Get ALL clinic data
        all_appointments = get_all_data('individual_appointments', 'appointments')
        all_invoices = get_all_data('invoices', 'invoices')
        all_patients = get_all_data('patients', 'patients')
        
        # Step 3: Process patient behaviors
        print(f"\n🎯 STEP 3: Analyzing patient behaviors...")
        patient_behaviors = {}
        
        # Group appointments by patient
        for appt in all_appointments:
            if appt.get('patient', {}).get('links', {}).get('self'):
                patient_id = appt['patient']['links']['self'].split('/')[-1]
                if patient_id in target_patient_ids:
                    if patient_id not in patient_behaviors:
                        patient_behaviors[patient_id] = {
                            'appointments': [],
                            'invoices': [],
                            'patient_data': None
                        }
                    patient_behaviors[patient_id]['appointments'].append(appt)
        
        # Group invoices by patient
        for invoice in all_invoices:
            if invoice.get('patient', {}).get('links', {}).get('self'):
                patient_id = invoice['patient']['links']['self'].split('/')[-1]
                if patient_id in patient_behaviors:
                    patient_behaviors[patient_id]['invoices'].append(invoice)
        
        # Add patient demographic data
        for patient in all_patients:
            patient_id = str(patient.get('id'))
            if patient_id in patient_behaviors:
                patient_behaviors[patient_id]['patient_data'] = patient
        
        # Step 4: Calculate behavior metrics
        print(f"\n🎯 STEP 4: Calculating behavior metrics...")
        results = []
        
        for patient_id, data in patient_behaviors.items():
            appointments = data['appointments']
            invoices = data['invoices']
            patient_info = data['patient_data']
            
            if not patient_info:
                continue
                
            # Calculate metrics using CORRECT field names
            total_appointments = len(appointments)
            attended = len([a for a in appointments if a.get('patient_arrived')])
            dna = len([a for a in appointments if a.get('did_not_arrive')])
            cancelled = len([a for a in appointments if a.get('cancelled_at')])
            
            # Financial metrics
            total_invoiced = sum(float(inv.get('total_amount', 0)) for inv in invoices)
            paid_invoices = [inv for inv in invoices if inv.get('status') == 'paid']
            total_paid = sum(float(inv.get('total_amount', 0)) for inv in paid_invoices)
            
            # Demographics
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
        
        # Step 5: Display results
        print(f"\n🎯 STEP 5: COMPREHENSIVE RESULTS")
        print("="*60)
        print(f"📊 Successfully analyzed {len(results)} patients")
        
        # Summary statistics
        if results:
            avg_attendance = sum(r['attendance_rate'] for r in results) / len(results)
            avg_appointments = sum(r['total_appointments'] for r in results) / len(results)
            total_revenue = sum(r['total_paid'] for r in results)
            
            print(f"\n📈 CLINIC STATISTICS:")
            print(f"   👥 Patients analyzed: {len(results)}")
            print(f"   📅 Average appointments per patient: {avg_appointments:.1f}")
            print(f"   ✅ Average attendance rate: {avg_attendance:.1f}%")
            print(f"   💰 Total revenue: ${total_revenue:.2f}")
        
        # Top 10 patients by appointments
        print(f"\n🏆 TOP PATIENTS BY ACTIVITY:")
        top_patients = sorted(results, key=lambda x: x['total_appointments'], reverse=True)[:10]
        for i, patient in enumerate(top_patients, 1):
            print(f"   {i}. {patient['name']}: {patient['total_appointments']} appointments "
                  f"({patient['attendance_rate']:.1f}% attendance)")
        
        # Save results
        filename = f"complete_patient_behaviors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'extraction_date': datetime.now(AEST).isoformat(),
                'target_period': 'June 16-21, 2025',
                'total_patients': len(results),
                'patient_behaviors': results
            }, f, indent=2, default=str)
        
        print(f"\n💾 Complete results saved to: {filename}")
        print(f"✅ EXTRACTION COMPLETE - Ready for Django integration!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

