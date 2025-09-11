import requests
import json
from datetime import datetime
import pytz
import base64

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
    'User-Agent': 'Patient Behavior Rating System'
}

def main():
    print("🎯 CLINIKO API DOCUMENTED METHOD ONLY")
    print("="*60)
    print("📋 Following EXACT Cliniko API documentation")
    
    try:
        # Step 1: Get appointments (EXACT as July 2nd success)
        print("\n🎯 STEP 1: Getting appointments (June 16-21, 2025)...")
        start_date = AEST.localize(datetime(2025, 6, 16, 0, 5)).astimezone(pytz.UTC)
        end_date = AEST.localize(datetime(2025, 6, 21, 23, 55)).astimezone(pytz.UTC)
        
        # Cliniko documented filtering format
        params = {
            'per_page': 100,
            'page': 1,
            'q[]': [
                f'starts_at:>{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                f'starts_at:<{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            ]
        }
        
        all_appointments = []
        page = 1
        while True:
            params['page'] = page
            response = requests.get(f"{BASE_URL}/individual_appointments", headers=headers, params=params)
            if response.status_code != 200:
                print(f"   ❌ Error on page {page}: {response.status_code}")
                break
            data = response.json()
            appointments = data.get('individual_appointments', [])
            if not appointments:
                break
            all_appointments.extend(appointments)
            print(f"   📄 Page {page}: {len(appointments)} appointments")
            page += 1
            
        print(f"✅ Total appointments: {len(all_appointments)}")
        
        # Step 2: Get patient IDs
        patient_ids = list(set([
            appt['patient']['links']['self'].split('/')[-1] 
            for appt in all_appointments 
            if appt.get('patient', {}).get('links', {}).get('self')
        ]))
        print(f"✅ Unique patients: {len(patient_ids)}")
        
        # Step 3: Get invoices using Cliniko documented date filtering
        print(f"\n🎯 STEP 2: Getting invoices (CLINIKO DOCUMENTED METHOD)...")
        
        # Use same date range for invoices (Cliniko documented approach)
        invoice_params = {
            'per_page': 100,
            'page': 1,
            'q[]': [
                f'created_at:>{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                f'created_at:<{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            ]
        }
        
        all_invoices = []
        page = 1
        while True:
            invoice_params['page'] = page
            response = requests.get(f"{BASE_URL}/invoices", headers=headers, params=invoice_params)
            if response.status_code != 200:
                print(f"   ❌ Invoice error on page {page}: {response.status_code}")
                break
            data = response.json()
            invoices = data.get('invoices', [])
            if not invoices:
                break
            all_invoices.extend(invoices)
            print(f"   📄 Invoice page {page}: {len(invoices)} invoices")
            page += 1
            
        print(f"✅ Total invoices in date range: {len(all_invoices)}")
        
        # Step 4: Get patient data
        print(f"\n🎯 STEP 3: Getting patient demographics...")
        patients_data = {}
        for i, patient_id in enumerate(patient_ids, 1):
            try:
                response = requests.get(f"{BASE_URL}/patients/{patient_id}", headers=headers)
                if response.status_code == 200:
                    patient_data = response.json()
                    patients_data[patient_id] = patient_data
                    if i <= 5:
                        name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
                        print(f"   👤 Patient {i}: {name.strip()}")
            except Exception as e:
                print(f"   ❌ Error getting patient {patient_id}: {e}")
        
        print(f"✅ Retrieved {len(patients_data)} patient records")
        
        # Step 5: Calculate metrics using ACTUAL invoice fields
        print(f"\n🎯 STEP 4: Calculating behaviors (ACTUAL FIELDS ONLY)...")
        
        # First, examine actual invoice structure
        if all_invoices:
            sample_invoice = all_invoices[0]
            print(f"📋 Sample invoice fields: {list(sample_invoice.keys())}")
        
        results = []
        total_revenue = 0
        total_invoiced = 0
        
        for patient_id in patient_ids:
            patient_info = patients_data.get(patient_id)
            if not patient_info:
                continue
                
            # Get patient appointments
            patient_appointments = [
                appt for appt in all_appointments 
                if appt.get('patient', {}).get('links', {}).get('self') and 
                appt['patient']['links']['self'].split('/')[-1] == patient_id
            ]
            
            # Get patient invoices
            patient_invoices = [
                inv for inv in all_invoices 
                if inv.get('patient', {}).get('links', {}).get('self') and
                inv['patient']['links']['self'].split('/')[-1] == patient_id
            ]
            
            # Calculate attendance (July 2nd proven logic)
            total_appointments = len(patient_appointments)
            attended = len([a for a in patient_appointments if not a.get('cancelled_at') and not a.get('did_not_arrive')])
            dna = len([a for a in patient_appointments if a.get('did_not_arrive')])
            
            # Calculate financial using ACTUAL invoice fields only
            patient_invoiced = sum(float(inv.get('total_amount', 0)) for inv in patient_invoices)
            
            # Use ONLY the fields that actually exist in invoices
            patient_paid = 0
            for inv in patient_invoices:
                # Check what payment fields actually exist
                if 'outstanding_amount' in inv and inv['outstanding_amount'] is not None:
                    outstanding = float(inv['outstanding_amount'])
                    total = float(inv.get('total_amount', 0))
                    if outstanding == 0 and total > 0:
                        patient_paid += total
                elif 'status' in inv:
                    # Use status field if it indicates payment
                    status = inv.get('status')
                    if status in ['paid', 'closed', 1]:  # Common paid status values
                        patient_paid += float(inv.get('total_amount', 0))
            
            total_invoiced += patient_invoiced
            total_revenue += patient_paid
            
            # Demographics
            name = f"{patient_info.get('first_name', '')} {patient_info.get('last_name', '')}"
            dob = patient_info.get('date_of_birth')
            age = None
            if dob:
                birth_date = datetime.strptime(dob, '%Y-%m-%d')
                age = (datetime.now() - birth_date).days // 365
            
            results.append({
                'patient_id': patient_id,
                'name': name.strip(),
                'age': age,
                'total_appointments': total_appointments,
                'attended': attended,
                'dna': dna,
                'attendance_rate': (attended / total_appointments * 100) if total_appointments > 0 else 0,
                'total_invoiced': patient_invoiced,
                'total_paid': patient_paid,
                'invoice_count': len(patient_invoices)
            })
        
        # Display results
        print(f"\n🎯 RESULTS (CLINIKO DOCUMENTED METHOD)")
        print("="*50)
        print(f"📊 Successfully analyzed {len(results)} patients")
        print(f"📅 Total appointments: {len(all_appointments)}")
        print(f"📄 Total invoices in date range: {len(all_invoices)}")
        
        if results:
            avg_attendance = sum(r['attendance_rate'] for r in results) / len(results)
            avg_age = sum(r['age'] for r in results if r['age']) / len([r for r in results if r['age']])
            
            print(f"\n📈 CLINIC STATISTICS:")
            print(f"   👥 Patients: {len(results)}")
            print(f"   ✅ Avg attendance rate: {avg_attendance:.1f}%")
            print(f"   👤 Average age: {avg_age:.1f} years")
            print(f"   💰 Total invoiced: ${total_invoiced:.2f}")
            print(f"   💵 Total revenue: ${total_revenue:.2f}")
        
        # Save results
        filename = f"cliniko_documented_method_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'extraction_date': datetime.now(AEST).isoformat(),
                'method': 'Cliniko API Documented Method Only',
                'target_period': 'June 16-21, 2025',
                'results': results,
                'summary': {
                    'total_patients': len(results),
                    'total_appointments': len(all_appointments),
                    'total_invoices': len(all_invoices),
                    'clinic_revenue': total_revenue,
                    'clinic_invoiced': total_invoiced
                }
            }, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        print(f"✅ CLINIKO DOCUMENTED METHOD COMPLETE!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

