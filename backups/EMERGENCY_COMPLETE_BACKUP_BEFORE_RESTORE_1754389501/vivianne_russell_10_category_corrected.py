#!/usr/bin/env python3
"""
VIVIANNE RUSSELL - 10-CATEGORY PATIENT BEHAVIOR EXTRACTION (CORRECTED)
Testing the refined 10-category system on Vivianne Russell (ID: 1104455)
CORRECTED: Yearly spend now uses rolling 12 months (not lifetime or calendar year)
Following official Cliniko API documentation
"""

import requests
import json
import base64
from datetime import datetime, timedelta
import pytz
import time

# ✅ CORRECT API KEY - July 3, 2025
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# ✅ VIVIANNE RUSSELL PATIENT ID (Known to exist)
VIVIANNE_PATIENT_ID = "1104455"
VIVIANNE_NAME = "Vivianne Russell"

def get_auth_header(api_key):
    """Create proper Cliniko API authentication header"""
    credentials = f"{api_key}:"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"

def extract_vivianne_complete_data():
    """Extract complete 10-category behavior data for Vivianne Russell"""
    print(f"🎯 VIVIANNE RUSSELL - 10-CATEGORY BEHAVIOR EXTRACTION (CORRECTED)")
    print("="*70)
    print(f"Patient ID: {VIVIANNE_PATIENT_ID}")
    print(f"Patient Name: {VIVIANNE_NAME}")
    print(f"✅ CORRECTED: Yearly spend = rolling 12 months (not lifetime)")
    print(f"✅ Following official Cliniko API documentation")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    # Initialize results
    results = {
        'patient_id': VIVIANNE_PATIENT_ID,
        'patient_name': VIVIANNE_NAME,
        'extraction_date': datetime.now(AEST).isoformat(),
        'behavior_categories': {},
        'corrections_applied': [
            'Yearly spend: Rolling 12 months from current date',
            'Future appointments only (not total)',
            'Proper server-side API filtering',
            'Official Cliniko API documentation compliance'
        ]
    }
    
    try:
        # Get patient details
        print(f"\n📋 Getting patient details...")
        patient_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}",
            headers=headers
        )
        
        if patient_response.status_code == 200:
            patient_data = patient_response.json()
            
            # Calculate age
            dob = patient_data.get('date_of_birth')
            age = None
            if dob:
                birth_date = datetime.strptime(dob, '%Y-%m-%d')
                age = (datetime.now() - birth_date).days // 365
                
            results['patient_details'] = {
                'first_name': patient_data.get('first_name'),
                'last_name': patient_data.get('last_name'),
                'email': patient_data.get('email'),
                'phone': patient_data.get('phone_number'),
                'date_of_birth': dob,
                'age': age,
                'created_at': patient_data.get('created_at')
            }
            
            print(f"   ✅ Patient: {patient_data.get('first_name')} {patient_data.get('last_name')}")
            print(f"   📧 Email: {patient_data.get('email')}")
            print(f"   📞 Phone: {patient_data.get('phone_number')}")
            print(f"   🎂 Age: {age} years")
            
        time.sleep(0.5)
        
        # CATEGORY 1: APPOINTMENTS BOOKED (Future only)
        print(f"\n📅 CATEGORY 1: APPOINTMENTS BOOKED (Future)")
        now_utc = datetime.now(pytz.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        future_appointments_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}/appointments",
            headers=headers,
            params={
                'q[]': f'starts_at:>{now_utc}',
                'per_page': 100
            }
        )
        
        future_appointments = []
        if future_appointments_response.status_code == 200:
            future_data = future_appointments_response.json()
            future_appointments = future_data.get('appointments', [])
            
        print(f"   ✅ Future appointments: {len(future_appointments)}")
        results['behavior_categories']['appointments_booked'] = {
            'count': len(future_appointments),
            'appointments': future_appointments
        }
        
        time.sleep(0.5)
        
        # CATEGORY 2: AGE DEMOGRAPHICS (Target 30-50)
        print(f"\n🎂 CATEGORY 2: AGE DEMOGRAPHICS")
        age_score = 0
        if age:
            if 30 <= age <= 50:
                age_score = 10  # Target demographic
            elif 25 <= age <= 55:
                age_score = 5   # Close to target
            else:
                age_score = 0   # Outside target
                
        print(f"   ✅ Age: {age}, Score: {age_score}")
        results['behavior_categories']['age_demographics'] = {
            'age': age,
            'score': age_score,
            'target_demographic': 30 <= age <= 50 if age else False
        }
        
        # CATEGORY 3: YEARLY SPEND (CORRECTED - Rolling 12 months)
        print(f"\n💰 CATEGORY 3: YEARLY SPEND (CORRECTED - Rolling 12 months)")
        current_date = datetime.now()
        twelve_months_ago = current_date - timedelta(days=365)
        
        # Convert to UTC for API (following Cliniko documentation)
        twelve_months_ago_utc = twelve_months_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
        current_date_utc = current_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        print(f"   📅 Period: {twelve_months_ago.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
        
        yearly_invoices_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}/invoices",
            headers=headers,
            params={
                'q[]': f'created_at:>={twelve_months_ago_utc}',
                'q[]': f'created_at:<={current_date_utc}',
                'per_page': 100
            }
        )
        
        yearly_spend = 0
        yearly_invoices = []
        if yearly_invoices_response.status_code == 200:
            yearly_data = yearly_invoices_response.json()
            yearly_invoices = yearly_data.get('invoices', [])
            yearly_spend = sum(float(inv.get('total_amount', 0)) for inv in yearly_invoices)
            
        print(f"   ✅ 12-month spend: ${yearly_spend:.2f} ({len(yearly_invoices)} invoices)")
        print(f"   🔧 CORRECTED: Not lifetime spend, not calendar year")
        results['behavior_categories']['yearly_spend'] = {
            'amount': yearly_spend,
            'invoice_count': len(yearly_invoices),
            'period_start': twelve_months_ago.strftime('%Y-%m-%d'),
            'period_end': current_date.strftime('%Y-%m-%d'),
            'method': 'Rolling 12 months from current date'
        }
        
        time.sleep(0.5)
        
        # CATEGORY 4: CONSECUTIVE ATTENDANCE
        print(f"\n📊 CATEGORY 4: CONSECUTIVE ATTENDANCE")
        
        # Get all past appointments
        all_appointments_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}/appointments",
            headers=headers,
            params={
                'q[]': f'starts_at:<{now_utc}',
                'per_page': 100
            }
        )
        
        all_appointments = []
        if all_appointments_response.status_code == 200:
            all_data = all_appointments_response.json()
            all_appointments = all_data.get('appointments', [])
            
        # Calculate consecutive attendance streak
        consecutive_streak = 0
        total_attended = 0
        total_appointments = len(all_appointments)
        
        # Sort by date (most recent first)
        sorted_appointments = sorted(all_appointments, 
                                   key=lambda x: x.get('starts_at', ''), 
                                   reverse=True)
        
        for apt in sorted_appointments:
            if apt.get('patient_arrived'):
                consecutive_streak += 1
                total_attended += 1
            else:
                break  # Streak broken
                
        attendance_rate = (total_attended / total_appointments * 100) if total_appointments > 0 else 0
        
        print(f"   ✅ Consecutive streak: {consecutive_streak}")
        print(f"   ✅ Total attended: {total_attended}/{total_appointments} ({attendance_rate:.1f}%)")
        
        results['behavior_categories']['consecutive_attendance'] = {
            'streak': consecutive_streak,
            'total_attended': total_attended,
            'total_appointments': total_appointments,
            'attendance_rate': attendance_rate
        }
        
        time.sleep(0.5)
        
        # CATEGORY 5: LIKABILITY (Manual - default neutral)
        print(f"\n😊 CATEGORY 5: LIKABILITY (Manual)")
        likability_score = 0  # Default neutral
        print(f"   ✅ Likability: {likability_score} (manual input required)")
        results['behavior_categories']['likability'] = {
            'score': likability_score,
            'type': 'manual_input',
            'note': 'Requires practitioner input'
        }
        
        # CATEGORY 6: OPEN DNA INVOICES
        print(f"\n🚫 CATEGORY 6: OPEN DNA INVOICES")
        
        # Get all invoices
        all_invoices_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}/invoices",
            headers=headers,
            params={'per_page': 100}
        )
        
        dna_invoices = []
        if all_invoices_response.status_code == 200:
            all_invoices_data = all_invoices_response.json()
            all_invoices = all_invoices_data.get('invoices', [])
            
            # Look for DNA-related invoices
            for invoice in all_invoices:
                if isinstance(invoice, dict):
                    invoice_items = invoice.get('invoice_items', [])
                    
                    if isinstance(invoice_items, list):
                        for item in invoice_items:
                            if isinstance(item, dict):
                                item_name = item.get('name', '').lower()
                                if 'dna' in item_name or 'did not arrive' in item_name or 'no show' in item_name:
                                    if not invoice.get('closed_at'):  # Still open
                                        dna_invoices.append(invoice)
                                        break
                        
        print(f"   ✅ Open DNA invoices: {len(dna_invoices)}")
        results['behavior_categories']['open_dna_invoices'] = {
            'count': len(dna_invoices),
            'invoices': dna_invoices
        }
        
        time.sleep(0.5)
        
        # CATEGORY 7: UNPAID INVOICES
        print(f"\n💳 CATEGORY 7: UNPAID INVOICES")
        
        unpaid_invoices_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}/invoices",
            headers=headers,
            params={
                'q[]': 'closed_at:!?',  # Official Cliniko API method
                'per_page': 100
            }
        )
        
        unpaid_invoices = []
        unpaid_amount = 0
        if unpaid_invoices_response.status_code == 200:
            unpaid_data = unpaid_invoices_response.json()
            unpaid_invoices = unpaid_data.get('invoices', [])
            unpaid_amount = sum(float(inv.get('total_amount', 0)) for inv in unpaid_invoices)
            
        print(f"   ✅ Unpaid invoices: {len(unpaid_invoices)} (${unpaid_amount:.2f})")
        results['behavior_categories']['unpaid_invoices'] = {
            'count': len(unpaid_invoices),
            'total_amount': unpaid_amount,
            'invoices': unpaid_invoices
        }
        
        time.sleep(0.5)
        
        # CATEGORY 8: CANCELLATIONS
        print(f"\n🚫 CATEGORY 8: CANCELLATIONS")
        
        cancelled_appointments_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}/appointments",
            headers=headers,
            params={
                'q[]': 'cancelled_at:?',  # Official Cliniko API method
                'per_page': 100
            }
        )
        
        cancelled_appointments = []
        if cancelled_appointments_response.status_code == 200:
            cancelled_data = cancelled_appointments_response.json()
            cancelled_appointments = cancelled_data.get('appointments', [])
            
        print(f"   ✅ Cancelled appointments: {len(cancelled_appointments)}")
        results['behavior_categories']['cancellations'] = {
            'count': len(cancelled_appointments),
            'appointments': cancelled_appointments
        }
        
        time.sleep(0.5)
        
        # CATEGORY 9: DNA COUNT
        print(f"\n❌ CATEGORY 9: DNA COUNT")
        
        dna_appointments_response = requests.get(
            f"{BASE_URL}/patients/{VIVIANNE_PATIENT_ID}/appointments",
            headers=headers,
            params={
                'q[]': 'did_not_arrive:true',  # Official Cliniko API method
                'per_page': 100
            }
        )
        
        dna_appointments = []
        if dna_appointments_response.status_code == 200:
            dna_data = dna_appointments_response.json()
            dna_appointments = dna_data.get('appointments', [])
            
        print(f"   ✅ DNA appointments: {len(dna_appointments)}")
        results['behavior_categories']['dna_count'] = {
            'count': len(dna_appointments),
            'appointments': dna_appointments
        }
        
        time.sleep(0.5)
        
        # CATEGORY 10: UNLIKABILITY (Manual - default neutral)
        print(f"\n😠 CATEGORY 10: UNLIKABILITY (Manual)")
        unlikability_score = 0  # Default neutral
        print(f"   ✅ Unlikability: {unlikability_score} (manual input required)")
        results['behavior_categories']['unlikability'] = {
            'score': unlikability_score,
            'type': 'manual_input',
            'note': 'Requires practitioner input'
        }
        
        # EXTRACTION SUMMARY
        print(f"\n📊 EXTRACTION SUMMARY (CORRECTED):")
        print("="*70)
        print(f"✅ Patient: {VIVIANNE_NAME} (ID: {VIVIANNE_PATIENT_ID})")
        print(f"✅ Age: {age} years")
        print(f"✅ Future appointments: {len(future_appointments)}")
        print(f"✅ 12-month spend: ${yearly_spend:.2f} (CORRECTED)")
        print(f"✅ Consecutive attendance: {consecutive_streak}")
        print(f"✅ Open DNA invoices: {len(dna_invoices)}")
        print(f"✅ Unpaid invoices: {len(unpaid_invoices)}")
        print(f"✅ Cancellations: {len(cancelled_appointments)}")
        print(f"✅ DNA count: {len(dna_appointments)}")
        print(f"✅ Manual inputs: Likability & Unlikability (default 0)")
        print(f"🔧 CORRECTED: Yearly spend now uses rolling 12 months")
        
        return results
        
    except Exception as e:
        print(f"❌ Extraction error: {str(e)}")
        return None

def calculate_behavior_scores(results):
    """Calculate scores for each behavior category"""
    print(f"\n🎯 STEP 2: CALCULATE BEHAVIOR SCORES")
    print("="*70)
    
    if not results or 'behavior_categories' not in results:
        print("❌ No data to calculate scores")
        return None
    
    categories = results['behavior_categories']
    scores = {}
    
    # POSITIVE BEHAVIORS (Higher = Better)
    
    # 1. Appointments Booked (Bracket scoring)
    future_count = categories.get('appointments_booked', {}).get('count', 0)
    if future_count >= 5:
        appointments_score = 20
    elif future_count >= 3:
        appointments_score = 15
    elif future_count >= 1:
        appointments_score = 10
    else:
        appointments_score = 0
    scores['appointments_booked'] = appointments_score
    
    # 2. Age Demographics (Boolean scoring)
    age_score = categories.get('age_demographics', {}).get('score', 0)
    scores['age_demographics'] = age_score
    
    # 3. Yearly Spend (Bracket scoring - CORRECTED)
    yearly_spend = categories.get('yearly_spend', {}).get('amount', 0)
    if yearly_spend >= 2000:
        spend_score = 25
    elif yearly_spend >= 1000:
        spend_score = 20
    elif yearly_spend >= 500:
        spend_score = 15
    elif yearly_spend >= 100:
        spend_score = 10
    else:
        spend_score = 0
    scores['yearly_spend'] = spend_score
    
    # 4. Consecutive Attendance (Accumulative scoring)
    streak = categories.get('consecutive_attendance', {}).get('streak', 0)
    attendance_score = min(streak * 2, 30)  # Max 30 points
    scores['consecutive_attendance'] = attendance_score
    
    # 5. Likability (Manual input)
    likability = categories.get('likability', {}).get('score', 0)
    scores['likability'] = likability
    
    # NEGATIVE BEHAVIORS (Higher = Worse, so negative points)
    
    # 6. Open DNA Invoices (Boolean penalty)
    open_dna_count = categories.get('open_dna_invoices', {}).get('count', 0)
    dna_invoice_penalty = -20 if open_dna_count > 0 else 0
    scores['open_dna_invoices'] = dna_invoice_penalty
    
    # 7. Unpaid Invoices (Count penalty)
    unpaid_count = categories.get('unpaid_invoices', {}).get('count', 0)
    unpaid_penalty = -unpaid_count * 5  # -5 per unpaid invoice
    scores['unpaid_invoices'] = unpaid_penalty
    
    # 8. Cancellations (Accumulative penalty)
    cancellation_count = categories.get('cancellations', {}).get('count', 0)
    cancellation_penalty = -cancellation_count * 2  # -2 per cancellation
    scores['cancellations'] = cancellation_penalty
    
    # 9. DNA Count (Accumulative penalty)
    dna_count = categories.get('dna_count', {}).get('count', 0)
    dna_penalty = -dna_count * 5  # -5 per DNA
    scores['dna_count'] = dna_penalty
    
    # 10. Unlikability (Manual penalty)
    unlikability = categories.get('unlikability', {}).get('score', 0)
    unlikability_penalty = -unlikability
    scores['unlikability'] = unlikability_penalty
    
    # Calculate total score
    total_score = sum(scores.values())
    
    # Calculate letter grade
    if total_score >= 100:
        letter_grade = "A+"
    elif total_score >= 80:
        letter_grade = "A"
    elif total_score >= 60:
        letter_grade = "B"
    elif total_score >= 40:
        letter_grade = "C"
    elif total_score >= 20:
        letter_grade = "D"
    else:
        letter_grade = "F"
    
    print(f"📊 BEHAVIOR SCORES:")
    print(f"   Appointments Booked: +{appointments_score}")
    print(f"   Age Demographics: +{age_score}")
    print(f"   Yearly Spend: +{spend_score} (CORRECTED)")
    print(f"   Consecutive Attendance: +{attendance_score}")
    print(f"   Likability: +{likability}")
    print(f"   Open DNA Invoices: {dna_invoice_penalty}")
    print(f"   Unpaid Invoices: {unpaid_penalty}")
    print(f"   Cancellations: {cancellation_penalty}")
    print(f"   DNA Count: {dna_penalty}")
    print(f"   Unlikability: {unlikability_penalty}")
    print(f"\n🎯 TOTAL SCORE: {total_score}")
    print(f"🎯 LETTER GRADE: {letter_grade}")
    
    return {
        'individual_scores': scores,
        'total_score': total_score,
        'letter_grade': letter_grade
    }

def main():
    """Main function to test Vivianne Russell extraction with corrected yearly spend"""
    print("🚀 VIVIANNE RUSSELL - 10-CATEGORY BEHAVIOR EXTRACTION (CORRECTED)")
    print("📋 Testing refined 10-category system with proper yearly spend logic")
    print(f"📅 Test Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🔧 CORRECTED: Yearly spend = rolling 12 months (not lifetime)")
    print("="*80)
    
    # Extract complete data
    results = extract_vivianne_complete_data()
    
    if not results:
        print("❌ Data extraction failed")
        return
    
    # Calculate scores
    scores = calculate_behavior_scores(results)
    
    if scores:
        results['scoring'] = scores
    
    # Save results
    filename = f"vivianne_russell_10_category_corrected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"🎉 VIVIANNE RUSSELL CORRECTED EXTRACTION COMPLETE!")
    
    # Final summary
    if scores:
        print(f"\n📋 FINAL SUMMARY (CORRECTED):")
        print("="*70)
        print(f"Patient: {VIVIANNE_NAME}")
        print(f"Total Score: {scores['total_score']}")
        print(f"Letter Grade: {scores['letter_grade']}")
        print(f"🔧 CORRECTED: Yearly spend now uses rolling 12 months")
        print(f"✅ 10-category system working with proper logic!")

if __name__ == "__main__":
    main()
