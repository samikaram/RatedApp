import requests
import base64
from datetime import datetime, timedelta
import pytz
import json
import time

def complete_extraction_both_locations():
    api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
    
    # Authentication
    auth_string = f"{api_key}:"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Patient Rating App - Complete Extraction Fixed'
    }
    
    base_url = "https://api.au1.cliniko.com/v1"
    aest = pytz.timezone('Australia/Sydney')
    utc = pytz.UTC
    
    # Date range: 16/06/2025 to 21/06/2025 in AEST
    start_date_aest = aest.localize(datetime(2025, 6, 16, 0, 0, 0))
    end_date_aest = aest.localize(datetime(2025, 6, 21, 23, 59, 59))
    
    # Convert to UTC for API filtering
    start_date_utc = start_date_aest.astimezone(utc)
    end_date_utc = end_date_aest.astimezone(utc)
    
    # Format for Cliniko API
    start_utc_str = start_date_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_utc_str = end_date_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"🏥 COMPLETE EXTRACTION - BOTH LOCATIONS (FIXED)")
    print(f"📍 Parramatta (10 Alma Street) & Peakhurst (144 Boundary Road)")
    print(f"📅 Date Range: 16/06/2025 - 21/06/2025 (AEST)")
    print(f"🌍 UTC Range: {start_utc_str} - {end_utc_str}")
    print("="*80)
    
    # Data containers
    all_appointments = []
    all_patients = {}
    all_invoices = []
    all_referral_sources = {}
    all_businesses = {}
    
    # Step 1: Get ALL appointments across both locations
    print(f"\n🔍 STEP 1: Extracting ALL appointments (both locations)")
    page = 1
    while True:
        try:
            appointments_url = (
                f"{base_url}/individual_appointments?"
                f"q[]=starts_at:>{start_utc_str}&"
                f"q[]=starts_at:<{end_utc_str}&"
                f"per_page=100&page={page}"
            )
            
            response = requests.get(appointments_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                appointments = data.get('individual_appointments', [])
                
                if not appointments:
                    break
                
                # Add AEST conversion for each appointment
                for apt in appointments:
                    if apt.get('starts_at'):
                        apt_utc = datetime.fromisoformat(apt['starts_at'].replace('Z', '+00:00'))
                        apt['starts_at_aest'] = apt_utc.astimezone(aest)
                        all_appointments.append(apt)
                
                print(f"   📄 Page {page}: {len(appointments)} appointments")
                page += 1
                
            elif response.status_code == 429:
                print(f"   ⏳ Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                continue
                
            else:
                print(f"❌ Error on page {page}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Exception on page {page}: {str(e)}")
            break
    
    print(f"✅ Total appointments extracted: {len(all_appointments)}")
    
    # Step 2: Extract ALL unique patient IDs
    print(f"\n🔍 STEP 2: Extracting ALL patient IDs")
    patient_ids = set()
    
    for apt in all_appointments:
        if apt.get('patient') and apt['patient'].get('links') and apt['patient']['links'].get('self'):
            patient_url = apt['patient']['links']['self']
            if '/patients/' in patient_url:
                patient_id = patient_url.split('/patients/')[-1].split('?')[0]
                patient_ids.add(patient_id)
    
    print(f"✅ Found {len(patient_ids)} unique patients")
    
    # Step 3: Get detailed data for ALL patients
    print(f"\n🔍 STEP 3: Getting detailed data for ALL {len(patient_ids)} patients")
    successful_patients = 0
    failed_patients = 0
    
    for i, patient_id in enumerate(patient_ids, 1):
        try:
            patient_response = requests.get(f"{base_url}/patients/{patient_id}", headers=headers)
            
            if patient_response.status_code == 200:
                patient_data = patient_response.json()
                all_patients[patient_id] = patient_data
                successful_patients += 1
                
                if i % 10 == 0:  # Progress update every 10 patients
                    print(f"   📊 Processed {i}/{len(patient_ids)} patients...")
                    
            elif patient_response.status_code == 429:
                print(f"   ⏳ Rate limit hit at patient {i}, waiting 60 seconds...")
                time.sleep(60)
                continue
                
            else:
                failed_patients += 1
                
        except Exception as e:
            failed_patients += 1
    
    print(f"✅ Successfully extracted {successful_patients} patients")
    print(f"❌ Failed to extract {failed_patients} patients")
    
    # Step 4: Get ALL invoices for the date range
    print(f"\n🔍 STEP 4: Extracting ALL invoices for date range")
    page = 1
    while True:
        try:
            invoices_url = (
                f"{base_url}/invoices?"
                f"q[]=created_at:>{start_utc_str}&"
                f"q[]=created_at:<{end_utc_str}&"
                f"per_page=100&page={page}"
            )
            
            response = requests.get(invoices_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                invoices = data.get('invoices', [])
                
                if not invoices:
                    break
                
                # Add AEST conversion for each invoice
                for inv in invoices:
                    if inv.get('created_at'):
                        inv_utc = datetime.fromisoformat(inv['created_at'].replace('Z', '+00:00'))
                        inv['created_at_aest'] = inv_utc.astimezone(aest)
                        all_invoices.append(inv)
                
                print(f"   📄 Page {page}: {len(invoices)} invoices")
                page += 1
                
            elif response.status_code == 429:
                print(f"   ⏳ Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                continue
                
            else:
                print(f"❌ Error on invoices page {page}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Exception on invoices page {page}: {str(e)}")
            break
    
    print(f"✅ Total invoices extracted: {len(all_invoices)}")
    
    # Step 5: Get ONLY referral sources used by our patients (FIXED LOGIC)
    print(f"\n🔍 STEP 5: Extracting referral sources for our {len(all_patients)} patients")
    
    # Collect unique referral source IDs from our patients
    referral_ids_needed = set()
    string_referrals = set()
    
    for patient_data in all_patients.values():
        if patient_data.get('referral_source'):
            if isinstance(patient_data['referral_source'], dict):
                ref_id = patient_data['referral_source'].get('id')
                if ref_id:
                    referral_ids_needed.add(ref_id)
            elif isinstance(patient_data['referral_source'], str):
                # Handle string referral sources
                string_referrals.add(patient_data['referral_source'])
    
    print(f"📊 Found {len(referral_ids_needed)} unique referral source IDs to fetch")
    print(f"📊 Found {len(string_referrals)} string-based referral sources")
    
    # Fetch only the referral sources we actually need
    successful_referrals = 0
    for ref_id in referral_ids_needed:
        try:
            ref_response = requests.get(f"{base_url}/referral_sources/{ref_id}", headers=headers)
            if ref_response.status_code == 200:
                ref_data = ref_response.json()
                all_referral_sources[ref_id] = ref_data
                successful_referrals += 1
            elif ref_response.status_code == 429:
                print(f"   ⏳ Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                continue
        except Exception as e:
            print(f"❌ Failed to get referral source {ref_id}: {str(e)}")
    
    # Add string referrals as simple entries
    for string_ref in string_referrals:
        all_referral_sources[f"string_{len(all_referral_sources)}"] = {
            'id': f"string_{len(all_referral_sources)}",
            'name': string_ref,
            'type': 'string_based'
        }
    
    print(f"✅ Successfully extracted {successful_referrals} referral source objects")
    print(f"✅ Added {len(string_referrals)} string-based referral sources")
    print(f"✅ Total referral sources: {len(all_referral_sources)}")
    
    # Step 6: Get business/location data (with rate limit handling)
    print(f"\n🔍 STEP 6: Getting business/location data")
    try:
        businesses_response = requests.get(f"{base_url}/businesses", headers=headers)
        if businesses_response.status_code == 200:
            businesses_data = businesses_response.json()
            businesses = businesses_data.get('businesses', [])
            for business in businesses:
                all_businesses[business['id']] = business
            print(f"✅ Found {len(all_businesses)} business locations")
        elif businesses_response.status_code == 429:
            print(f"⏳ Rate limit hit on businesses, skipping for now...")
        else:
            print(f"❌ Failed to get businesses: {businesses_response.status_code}")
    except Exception as e:
        print(f"❌ Exception getting businesses: {str(e)}")
    
    # Step 7: Generate comprehensive report
    print(f"\n" + "="*80)
    print(f"📋 COMPREHENSIVE EXTRACTION REPORT (FIXED)")
    print(f"🏥 Sports Medicine Clinic - Both Locations")
    print(f"📅 Period: 16/06/2025 - 21/06/2025 (AEST)")
    print(f"="*80)
    
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"   👥 Total patients: {len(all_patients)}")
    print(f"   📅 Total appointments: {len(all_appointments)}")
    print(f"   💰 Total invoices: {len(all_invoices)}")
    print(f"   📍 Total referral sources: {len(all_referral_sources)} (FIXED - was 5,900!)")
    print(f"   🏢 Business locations: {len(all_businesses)}")
    
    # Location breakdown
    print(f"\n🏢 LOCATION BREAKDOWN:")
    location_stats = {}
    for apt in all_appointments:
        business_id = apt.get('business', {}).get('id') if apt.get('business') else None
        if business_id:
            if business_id not in location_stats:
                business_name = all_businesses.get(business_id, {}).get('name', f'Location {business_id}')
                location_stats[business_id] = {'name': business_name, 'appointments': 0}
            location_stats[business_id]['appointments'] += 1
    
    for business_id, stats in location_stats.items():
        print(f"   🏥 {stats['name']}: {stats['appointments']} appointments")
    
    # Behavior categories data summary
    print(f"\n📊 BEHAVIOR DATA SUMMARY:")
    attended_count = sum(1 for apt in all_appointments if apt.get('patient_arrived'))
    dna_count = sum(1 for apt in all_appointments if apt.get('did_not_arrive'))
    cancelled_count = sum(1 for apt in all_appointments if apt.get('cancelled_at'))
    
    print(f"   ✅ Attended appointments: {attended_count}")
    print(f"   ❌ DNA appointments: {dna_count}")
    print(f"   🚫 Cancelled appointments: {cancelled_count}")
    
    # Invoice summary
    if all_invoices:
        total_invoice_amount = sum(float(inv.get('total_amount', 0)) for inv in all_invoices)
        paid_invoices = sum(1 for inv in all_invoices if inv.get('status') == 'paid')
        unpaid_invoices = sum(1 for inv in all_invoices if inv.get('status') != 'paid')
        
        print(f"   💰 Total invoice amount: ${total_invoice_amount:.2f}")
        print(f"   ✅ Paid invoices: {paid_invoices}")
        print(f"   ❌ Unpaid invoices: {unpaid_invoices}")
    
    # Age demographics
    ages = []
    for patient_data in all_patients.values():
        if patient_data.get('date_of_birth'):
            birth_date = datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
            ages.append(age)
    
    if ages:
        print(f"   🎂 Age range: {min(ages)} - {max(ages)} years")
        print(f"   📊 Average age: {sum(ages) // len(ages)} years")
    
    # Referral source breakdown (FIXED - now showing actual referrals)
    referral_usage = {}
    for patient_data in all_patients.values():
        if patient_data.get('referral_source'):
            if isinstance(patient_data['referral_source'], dict):
                ref_id = patient_data['referral_source'].get('id')
                if ref_id and ref_id in all_referral_sources:
                    ref_name = all_referral_sources[ref_id].get('name', 'Unknown')
                    referral_usage[ref_name] = referral_usage.get(ref_name, 0) + 1
            elif isinstance(patient_data['referral_source'], str):
                # Handle string referral sources
                ref_name = patient_data['referral_source']
                referral_usage[ref_name] = referral_usage.get(ref_name, 0) + 1
    
    if referral_usage:
        print(f"\n📍 REFERRAL SOURCE BREAKDOWN:")
        sorted_referrals = sorted(referral_usage.items(), key=lambda x: x[1], reverse=True)
        for i, (ref_name, count) in enumerate(sorted_referrals, 1):
            print(f"   {i}. {ref_name}: {count} patients")
    
    # Patient-by-patient detailed breakdown
    print(f"\n" + "="*80)
    print(f"👥 DETAILED PATIENT BREAKDOWN (ALL {len(all_patients)} PATIENTS)")
    print(f"="*80)
    
    for i, (patient_id, patient_data) in enumerate(all_patients.items(), 1):
        name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
        print(f"\n{i}. 👤 {name} (ID: {patient_id})")
        
        # Demographics
        if patient_data.get('date_of_birth'):
            birth_date = datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
            print(f"   🎂 Age: {age} years")
        
        # Referral source (FIXED)
        if patient_data.get('referral_source'):
            if isinstance(patient_data['referral_source'], dict):
                ref_id = patient_data['referral_source'].get('id')
                if ref_id and ref_id in all_referral_sources:
                    ref_name = all_referral_sources[ref_id].get('name', 'Unknown')
                    print(f"   📍 Referral: {ref_name}")
            elif isinstance(patient_data['referral_source'], str):
                print(f"   📍 Referral: {patient_data['referral_source']}")
        
        # Find appointments for this patient
        patient_appointments = []
        for apt in all_appointments:
            if apt.get('patient') and apt['patient'].get('links'):
                apt_patient_url = apt['patient']['links']['self']
                if f'/patients/{patient_id}' in apt_patient_url:
                    apt_aest = apt['starts_at_aest']
                    
                    status = "✅ Attended" if apt.get('patient_arrived') else "❌ DNA" if apt.get('did_not_arrive') else "📅 Scheduled"
                    if apt.get('cancelled_at'):
                        status = "🚫 Cancelled"
                    
                    patient_appointments.append({
                        'date': apt_aest,
                        'status': status,
                        'business': apt.get('business', {}).get('id')
                    })
        
        # Sort appointments by date
        patient_appointments.sort(key=lambda x: x['date'])
        
        # Show appointments
        for apt in patient_appointments:
            business_name = all_businesses.get(apt['business'], {}).get('name', 'Unknown Location')
            print(f"   📅 {apt['date'].strftime('%d/%m/%Y %H:%M AEST')}: {apt['status']} ({business_name})")
        
        # Find invoices for this patient
        patient_invoices = []
        for inv in all_invoices:
            if inv.get('patient') and inv['patient'].get('links'):
                inv_patient_url = inv['patient']['links']['self']
                if f'/patients/{patient_id}' in inv_patient_url:
                    patient_invoices.append(inv)
        
        if patient_invoices:
            total_amount = sum(float(inv.get('total_amount', 0)) for inv in patient_invoices)
            paid_amount = sum(float(inv.get('total_amount', 0)) for inv in patient_invoices if inv.get('status') == 'paid')
            print(f"   💰 Total invoices: ${total_amount:.2f} (Paid: ${paid_amount:.2f})")
    
    print(f"\n" + "="*80)
    print(f"✅ COMPLETE EXTRACTION FINISHED (FIXED)")
    print(f"📊 Ready for patient behavior scoring system")
    print(f"🔍 All data extracted with proper referral source logic")
    print(f"="*80)
    
    # Save summary to file for reference
    summary_data = {
        'extraction_date': datetime.now(aest).isoformat(),
        'date_range': '16/06/2025 - 21/06/2025',
        'total_patients': len(all_patients),
        'total_appointments': len(all_appointments),
        'total_invoices': len(all_invoices),
        'total_referral_sources': len(all_referral_sources),
        'location_stats': location_stats,
        'behavior_stats': {
            'attended': attended_count,
            'dna': dna_count,
            'cancelled': cancelled_count
        }
    }
    
    # Write summary to JSON file
    try:
        with open('extraction_summary_fixed.json', 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        print(f"📄 Summary saved to: extraction_summary_fixed.json")
    except Exception as e:
        print(f"❌ Failed to save summary: {str(e)}")
    
    # Return all extracted data for further processing
    return {
        'patients': all_patients,
        'appointments': all_appointments,
        'invoices': all_invoices,
        'referral_sources': all_referral_sources,
        'businesses': all_businesses,
        'summary': summary_data
    }

if __name__ == "__main__":
    extracted_data = complete_extraction_both_locations()
    print(f"\n🎯 EXTRACTION COMPLETE!")
    print(f"📊 All data ready for patient behavior rating system")

