import requests
import base64
from datetime import datetime, timedelta
import pytz
import json

def extract_complete_data_june_16_21():
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Complete Data Extraction'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    
    # Date range: 16/06/2025 to 21/06/2025 (inclusive) in AEST
    start_date_aest = aest.localize(datetime(2025, 6, 16, 0, 0, 0))
    end_date_aest = aest.localize(datetime(2025, 6, 21, 23, 59, 59))
    
    # Convert to UTC for API filtering
    start_date_utc = start_date_aest.astimezone(pytz.UTC)
    end_date_utc = end_date_aest.astimezone(pytz.UTC)
    
    print(f"🚀 COMPLETE DATA EXTRACTION")
    print(f"📅 Date Range: 16/06/2025 - 21/06/2025 (AEST)")
    print(f"🕐 Start: {start_date_aest.strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print(f"🕐 End: {end_date_aest.strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print(f"🏥 Sports Medicine Clinic - Parramatta & Peakhurst")
    print("="*80)
    
    # Data containers
    all_appointments = []
    all_patients = {}
    all_invoices = []
    all_referral_sources = {}
    
    # Step 1: Extract ALL appointments in date range
    print(f"\n🔍 STEP 1: Extracting ALL appointments (16/06/2025 - 21/06/2025)")
    page = 1
    while True:
        try:
            appointments_url = f"{base_url}/individual_appointments?per_page=100&page={page}"
            response = requests.get(appointments_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                appointments = data.get('individual_appointments', [])
                
                if not appointments:
                    break
                
                # Filter appointments within date range
                for apt in appointments:
                    if apt.get('starts_at'):
                        apt_utc = datetime.fromisoformat(apt['starts_at'].replace('Z', '+00:00'))
                        apt_aest = apt_utc.astimezone(aest)
                        
                        if start_date_aest <= apt_aest <= end_date_aest:
                            apt['starts_at_aest'] = apt_aest
                            all_appointments.append(apt)
                
                print(f"   📄 Processed page {page}, found {len([a for a in appointments if a.get('starts_at_aest')])} appointments in range")
                page += 1
                
            else:
                print(f"❌ Error fetching appointments page {page}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Exception on appointments page {page}: {str(e)}")
            break
    
    print(f"✅ Total appointments in range: {len(all_appointments)}")
    
    # Step 2: Extract ALL patients from appointments
    print(f"\n🔍 STEP 2: Extracting ALL patients from appointments")
    patient_ids = set()
    for apt in all_appointments:
        if apt.get('patient', {}).get('id'):
            patient_ids.add(apt['patient']['id'])
    
    print(f"   📊 Found {len(patient_ids)} unique patients with appointments")
    
    # Get detailed patient data
    for patient_id in patient_ids:
        try:
            patient_response = requests.get(f"{base_url}/patients/{patient_id}", headers=headers)
            if patient_response.status_code == 200:
                patient_data = patient_response.json()
                all_patients[patient_id] = patient_data
        except Exception as e:
            print(f"❌ Error fetching patient {patient_id}: {str(e)}")
    
    print(f"✅ Retrieved detailed data for {len(all_patients)} patients")
    
    # Step 3: Extract ALL invoices in date range
    print(f"\n🔍 STEP 3: Extracting ALL invoices (16/06/2025 - 21/06/2025)")
    page = 1
    while True:
        try:
            invoices_url = f"{base_url}/invoices?per_page=100&page={page}"
            response = requests.get(invoices_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                invoices = data.get('invoices', [])
                
                if not invoices:
                    break
                
                # Filter invoices within date range
                for inv in invoices:
                    if inv.get('created_at'):
                        inv_utc = datetime.fromisoformat(inv['created_at'].replace('Z', '+00:00'))
                        inv_aest = inv_utc.astimezone(aest)
                        
                        if start_date_aest <= inv_aest <= end_date_aest:
                            inv['created_at_aest'] = inv_aest
                            all_invoices.append(inv)
                
                print(f"   📄 Processed page {page}, found {len([i for i in invoices if i.get('created_at_aest')])} invoices in range")
                page += 1
                
            else:
                print(f"❌ Error fetching invoices page {page}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Exception on invoices page {page}: {str(e)}")
            break
    
    print(f"✅ Total invoices in range: {len(all_invoices)}")
    
    # Step 4: Extract ALL referral sources
    print(f"\n🔍 STEP 4: Extracting ALL referral sources")
    page = 1
    while True:
        try:
            referrals_url = f"{base_url}/referral_sources?per_page=100&page={page}"
            response = requests.get(referrals_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                referrals = data.get('referral_sources', [])
                
                if not referrals:
                    break
                
                for ref in referrals:
                    all_referral_sources[ref['id']] = ref
                
                print(f"   📄 Processed page {page}, found {len(referrals)} referral sources")
                page += 1
                
            else:
                print(f"❌ Error fetching referrals page {page}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Exception on referrals page {page}: {str(e)}")
            break
    
    print(f"✅ Total referral sources: {len(all_referral_sources)}")
    
    # Step 5: Generate comprehensive report
    print(f"\n" + "="*80)
    print(f"📋 COMPREHENSIVE DATA EXTRACTION REPORT")
    print(f"📅 Period: 16/06/2025 - 21/06/2025 (AEST)")
    print(f"="*80)
    
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"   👥 Patients with activity: {len(all_patients)}")
    print(f"   📅 Appointments in period: {len(all_appointments)}")
    print(f"   💰 Invoices in period: {len(all_invoices)}")
    print(f"   📍 Total referral sources: {len(all_referral_sources)}")
    
    # Detailed patient breakdown
    print(f"\n👥 PATIENT BREAKDOWN:")
    for i, (patient_id, patient) in enumerate(all_patients.items(), 1):
        print(f"\n{'-'*50}")
        print(f"👤 PATIENT {i}: {patient.get('first_name', '')} {patient.get('last_name', '')} (ID: {patient_id})")
        
        # Demographics
        if patient.get('date_of_birth'):
            birth_date = datetime.strptime(patient['date_of_birth'], '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
            print(f"   🎂 Age: {age} years")
        
        # Referral source
        referral_source_id = patient.get('referral_source', {}).get('id') if patient.get('referral_source') else None
        if referral_source_id and referral_source_id in all_referral_sources:
            referral_name = all_referral_sources[referral_source_id].get('name', 'Unknown')
            print(f"   📍 Referral: {referral_name}")
        
        # Appointments for this patient
        patient_appointments = [apt for apt in all_appointments if apt.get('patient', {}).get('id') == patient_id]
        print(f"   📅 Appointments in period: {len(patient_appointments)}")
        
        for apt in patient_appointments:
            status = "✅ Attended" if apt.get('patient_arrived') else "❌ DNA" if apt.get('did_not_arrive') else "📅 Scheduled"
            if apt.get('cancelled_at'):
                status = f"🚫 Cancelled"
            print(f"      • {apt['starts_at_aest'].strftime('%d/%m/%Y %H:%M AEST')}: {status}")
        
        # Invoices for this patient
        patient_invoices = [inv for inv in all_invoices if inv.get('patient', {}).get('id') == patient_id]
        if patient_invoices:
            total_amount = sum(float(inv.get('total_amount', 0)) for inv in patient_invoices)
            print(f"   💰 Invoices in period: {len(patient_invoices)}, Total: ${total_amount:.2f}")
            
            for inv in patient_invoices:
                print(f"      • {inv['created_at_aest'].strftime('%d/%m/%Y AEST')}: ${float(inv.get('total_amount', 0)):.2f} ({inv.get('status', 'unknown')})")
    
    print(f"\n" + "="*80)
    print(f"✅ COMPLETE DATA EXTRACTION FINISHED")
    print(f"🔍 Ready for manual verification against Cliniko interface")
    print(f"="*80)

if __name__ == "__main__":
    extract_complete_data_june_16_21()

