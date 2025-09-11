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

def main():
    print("🎯 PROVEN JULY 2ND APPROACH - REVENUE FIXED")
    print("="*60)
    print("🔧 Using the exact method that gave us $14,211.37 revenue")
    
    try:
        # Step 1: Get appointments from June 16-21, 2025 (PROVEN METHOD)
        print("\n🎯 STEP 1: Getting appointments from target period...")
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
        
        # Step 2: Extract unique patient IDs
        patient_ids = list(set([
            appt['patient']['links']['self'].split('/')[-1] 
            for appt in all_appointments 
            if appt.get('patient', {}).get('links', {}).get('self')
        ]))
        
        print(f"✅ Unique patients: {len(patient_ids)}")
        
        # Step 3: Get patient data for each patient
        print(f"\n🎯 STEP 2: Getting patient demographics...")
        patients_data = {}
        for i, patient_id in enumerate(patient_ids, 1):
            try:
                response = requests.get(f"{BASE_URL}/patients/{patient_id}", headers=headers)
                if response.status_code == 200:
                    patient_data = response.json()
                    patients_data[patient_id] = patient_data
                    if i <= 5:  # Show first 5
                        name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
                        print(f"   👤 Patient {i}: {name.strip()}")
                else:
                    print(f"   ❌ Failed to get patient {patient_id}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error getting patient {patient_id}: {e}")
        
        print(f"✅ Retrieved {len(patients_data)} patient records")
        
        # Step 4: Get invoices for all patients
        print(f"\n🎯 STEP 3: Getting invoices...")
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
            all_invoices.extend(invoices)
            page += 1
            # Limit to reasonable amount for target patients
            if page > 50:  # Should be enough for target patients
                break
                
        print(f"✅ Total invoices retrieved: {len(all_invoices)}")
        
        # Filter invoices for our target patients
        target_invoices = [
            inv for inv in all_invoices 
            if inv.get('patient', {}).get('links', {}).get('self') and 
            inv['patient']['links']['self'].split('/')[-1] in patient_ids
        ]
        
        print(f"✅ Target patient invoices: {len(target_invoices)}")
        
        # Step 5: Calculate behavior metrics (FIXED PAYMENT LOGIC)
        print(f"\n🎯 STEP 4: Calculating patient behaviors...")
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
                inv for inv in target_invoices 
                if inv['patient']['links']['self'].split('/')[-1] == patient_id
            ]
            
            # Calculate attendance (PROVEN LOGIC from July 2nd)
            total_appointments = len(patient_appointments)
            attended = len([a for a in patient_appointments if not a.get('cancelled_at') and not a.get('did_not_arrive')])
            dna = len([a for a in patient_appointments if a.get('did_not_arrive')])
            
            # Calculate financial metrics (FIXED PAYMENT LOGIC)
            patient_invoiced = sum(float(inv.get('total_amount', 0)) for inv in patient_invoices)
            
            # FIXED PAYMENT CALCULATION - Multiple methods
            patient_paid = 0
            for inv in patient_invoices:
                total_amount = float(inv.get('total_amount', 0))
                outstanding = float(inv.get('outstanding_amount', total_amount))
                amount_paid = float(inv.get('amount_paid', 0))
                
                # Method 1: If outstanding is 0 or very small, it's paid
                if outstanding <= 0.01 and total_amount > 0:
                    patient_paid += total_amount
                # Method 2: Use amount_paid field if available
                elif amount_paid > 0:
                    patient_paid += amount_paid
                # Method 3: Check if total_amount equals outstanding (unpaid)
                elif outstanding < total_amount:
                    patient_paid += (total_amount - outstanding)
            
            total_invoiced += patient_invoiced
            total_revenue += patient_paid
            
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
                'attendance_rate': (attended / total_appointments * 100) if total_appointments > 0 else 0,
                'total_invoiced': patient_invoiced,
                'total_paid': patient_paid,
                'payment_rate': (patient_paid / patient_invoiced * 100) if patient_invoiced > 0 else 0
            }
            
            results.append(patient_result)
        
        # Step 6: Display results
        print(f"\n🎯 STEP 5: RESULTS")
        print("="*50)
        print(f"📊 Successfully analyzed {len(results)} patients")
        
        if results:
            avg_attendance = sum(r['attendance_rate'] for r in results) / len(results)
            avg_appointments = sum(r['total_appointments'] for r in results) / len(results)
            avg_age = sum(r['age'] for r in results if r['age']) / len([r for r in results if r['age']])
            avg_payment_rate = sum(r['payment_rate'] for r in results) / len(results)
            
            print(f"\n📈 CLINIC STATISTICS:")
            print(f"   👥 Patients: {len(results)}")
            print(f"   📅 Avg appointments/patient: {avg_appointments:.1f}")
            print(f"   ✅ Avg attendance rate: {avg_attendance:.1f}%")
            print(f"   👤 Average age: {avg_age:.1f} years")
            print(f"   💰 Total invoiced: ${total_invoiced:.2f}")
            print(f"   💵 Total revenue: ${total_revenue:.2f}")
            print(f"   📊 Avg payment rate: {avg_payment_rate:.1f}%")
            
            # Top patients by revenue
            print(f"\n🏆 TOP 5 BY REVENUE:")
            top_revenue = sorted(results, key=lambda x: x['total_paid'], reverse=True)[:5]
            for i, patient in enumerate(top_revenue, 1):
                print(f"   {i}. {patient['name']}: ${patient['total_paid']:.2f} "
                      f"({patient['total_appointments']} appts, {patient['attendance_rate']:.1f}% attendance)")
                
            # Top patients by activity
            print(f"\n📅 TOP 5 BY ACTIVITY:")
            top_activity = sorted(results, key=lambda x: x['total_appointments'], reverse=True)[:5]
            for i, patient in enumerate(top_activity, 1):
                print(f"   {i}. {patient['name']}: {patient['total_appointments']} appointments "
                      f"({patient['attendance_rate']:.1f}% attendance, ${patient['total_paid']:.2f} paid)")
        
        # Save results
        filename = f"proven_july2_FIXED_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'extraction_date': datetime.now(AEST).isoformat(),
                'method': 'Proven July 2nd Approach - Revenue Fixed',
                'target_period': 'June 16-21, 2025',
                'total_patients': len(results),
                'total_appointments': len(all_appointments),
                'total_invoices': len(target_invoices),
                'clinic_revenue': total_revenue,
                'clinic_invoiced': total_invoiced,
                'patient_behaviors': results
            }, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        print(f"✅ PROVEN METHOD WITH REVENUE FIX COMPLETE!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
