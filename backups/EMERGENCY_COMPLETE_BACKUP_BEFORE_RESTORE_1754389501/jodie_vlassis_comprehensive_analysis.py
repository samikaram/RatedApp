import requests
import json
import base64
from datetime import datetime, timedelta
import pytz

# Timezone setup
AEST = pytz.timezone('Australia/Sydney')

# Cliniko API configuration
RAW_API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"

# ✅ WORKING METHOD: Base64 encode the API key
ENCODED_API_KEY = base64.b64encode(f"{RAW_API_KEY}:".encode()).decode()

HEADERS = {
    'Authorization': f'Basic {ENCODED_API_KEY}',
    'Accept': 'application/json',
    'User-Agent': 'RatedApp Jodie Vlassis Analysis'
}

def search_patient_by_name(first_name, last_name):
    """Search for patient by name in Cliniko"""
    
    print(f"🔍 SEARCHING FOR PATIENT: {first_name} {last_name}")
    print("="*60)
    
    # Search using first name and last name filters
    search_params = {
        'q[]': [
            f'first_name:~{first_name}',
            f'last_name:~{last_name}'
        ],
        'per_page': 50
    }
    
    url = f"{BASE_URL}/patients"
    response = requests.get(url, headers=HEADERS, params=search_params)
    
    if response.status_code != 200:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return None
    
    data = response.json()
    patients = data.get('patients', [])
    
    print(f"📋 Found {len(patients)} potential matches")
    
    # Look for exact match
    for patient in patients:
        patient_first = patient.get('first_name', '').lower()
        patient_last = patient.get('last_name', '').lower()
        
        if (patient_first == first_name.lower() and 
            patient_last == last_name.lower()):
            print(f"✅ EXACT MATCH FOUND!")
            print(f"   👤 Name: {patient.get('first_name')} {patient.get('last_name')}")
            print(f"   🆔 ID: {patient.get('id')}")
            print(f"   📧 Email: {patient.get('email', 'N/A')}")
            print(f"   📱 Phone: {patient.get('phone_number', 'N/A')}")
            return patient
    
    # If no exact match, show similar matches
    if patients:
        print(f"⚠️ No exact match found. Similar patients:")
        for i, patient in enumerate(patients[:5], 1):
            print(f"   {i}. {patient.get('first_name')} {patient.get('last_name')} (ID: {patient.get('id')})")
    
    return None

def get_paginated_data(endpoint, params, description):
    """Get all paginated data from Cliniko API"""
    all_data = []
    page = 1
    
    while True:
        current_params = params.copy() if params else {}
        current_params['page'] = page
        current_params['per_page'] = 100
        
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, headers=HEADERS, params=current_params)
        
        if response.status_code != 200:
            print(f"❌ API Error {response.status_code}: {response.text}")
            break
            
        data = response.json()
        
        # Handle different response structures
        if endpoint == 'individual_appointments':
            items = data.get('individual_appointments', [])
        elif endpoint == 'patients':
            items = data.get('patients', [])
        elif endpoint == 'invoices':
            items = data.get('invoices', [])
        else:
            items = data.get('items', [])
        
        print(f"   📄 Page {page}: {len(items)} items")
        all_data.extend(items)
        
        # Check if there are more pages
        if len(items) < 100:
            break
            
        page += 1
    
    print(f"   ✅ Total {description}: {len(all_data)}")
    return all_data

def extract_comprehensive_behavior_data(patient_data):
    """Extract ALL 10 behavior categories with complete details for Jodie Vlassis"""
    
    PATIENT_ID = patient_data.get('id')
    PATIENT_NAME = f"{patient_data.get('first_name')} {patient_data.get('last_name')}"
    
    print(f"\n🎯 COMPREHENSIVE ANALYSIS: {PATIENT_NAME} (ID: {PATIENT_ID})")
    print("="*80)
    
    behavior_data = {}
    
    # Get all appointments for this patient
    print(f"📡 Fetching all appointments for {PATIENT_NAME}...")
    filter_params = {'q[]': [f'patient_id:={PATIENT_ID}']}
    all_appointments = get_paginated_data('individual_appointments', filter_params, f'appointments for {PATIENT_NAME}')
    
    # Get all invoices for this patient
    print(f"📡 Fetching all invoices for {PATIENT_NAME}...")
    filter_params = {'q[]': [f'patient_id:={PATIENT_ID}']}
    all_invoices = get_paginated_data('invoices', filter_params, f'invoices for {PATIENT_NAME}')
    
    # BEHAVIOR 1: Future Appointments Booked
    print(f"\n🎯 BEHAVIOR 1: Future Appointments Booked")
    print("-" * 50)
    
    now_utc = datetime.now(pytz.UTC).isoformat()
    future_appointments = [appt for appt in all_appointments if appt.get('starts_at', '') > now_utc]
    
    behavior_data['future_appointments'] = {
        'count': len(future_appointments),
        'appointments': future_appointments,
        'scoring_bracket': 'High (3+)' if len(future_appointments) >= 3 else 'Medium (2)' if len(future_appointments) == 2 else 'Low (1)' if len(future_appointments) == 1 else 'None (0)',
        'points_awarded': 20 if len(future_appointments) >= 3 else 15 if len(future_appointments) == 2 else 10 if len(future_appointments) == 1 else 0
    }
    
    print(f"   📅 Future appointments: {len(future_appointments)}")
    print(f"   🎯 Scoring bracket: {behavior_data['future_appointments']['scoring_bracket']}")
    print(f"   ⭐ Points awarded: {behavior_data['future_appointments']['points_awarded']}")
    
    # BEHAVIOR 2: Age Demographics
    print(f"\n🎯 BEHAVIOR 2: Age Demographics")
    print("-" * 50)
    
    dob = patient_data.get('date_of_birth')
    age = 0
    in_target_demographic = False
    if dob:
        birth_date = datetime.strptime(dob, '%Y-%m-%d')
        age = (datetime.now() - birth_date).days // 365
        in_target_demographic = 20 <= age <= 55
    
    behavior_data['age_demographics'] = {
        'age': age,
        'date_of_birth': dob,
        'in_target_demographic': in_target_demographic,
        'target_range': '20-55 years',
        'points_awarded': 10 if in_target_demographic else 0
    }
    
    print(f"   👤 Age: {age} years")
    print(f"   🎯 Target demographic (20-55): {in_target_demographic}")
    print(f"   ⭐ Points awarded: {behavior_data['age_demographics']['points_awarded']}")
    
    # BEHAVIOR 3: Yearly Spend
    print(f"\n🎯 BEHAVIOR 3: Yearly Spend (Rolling 12 months)")
    print("-" * 50)
    
    twelve_months_ago = datetime.now(pytz.UTC) - timedelta(days=365)
    yearly_invoices = [inv for inv in all_invoices if inv.get('created_at') and 
                      datetime.fromisoformat(inv['created_at'].replace('Z', '+00:00')) >= twelve_months_ago]
    yearly_spend = sum(float(inv.get('total_amount', 0)) for inv in yearly_invoices)
    
    # Determine spending bracket
    if yearly_spend >= 1000:
        spending_bracket = 'Excellent ($1000+)'
        points_awarded = 25
    elif yearly_spend >= 500:
        spending_bracket = 'High ($500-999)'
        points_awarded = 20
    elif yearly_spend >= 200:
        spending_bracket = 'Medium ($200-499)'
        points_awarded = 15
    elif yearly_spend >= 100:
        spending_bracket = 'Low ($100-199)'
        points_awarded = 10
    elif yearly_spend > 0:
        spending_bracket = 'Minimal ($1-99)'
        points_awarded = 5
    else:
        spending_bracket = 'None ($0)'
        points_awarded = 0
    
    behavior_data['yearly_spend'] = {
        'amount': yearly_spend,
        'invoice_count': len(yearly_invoices),
        'spending_bracket': spending_bracket,
        'points_awarded': points_awarded
    }
    
    print(f"   💰 Yearly spend: ${yearly_spend:.2f}")
    print(f"   📄 Invoices in period: {len(yearly_invoices)}")
    print(f"   🎯 Spending bracket: {spending_bracket}")
    print(f"   ⭐ Points awarded: {points_awarded}")
    
    # BEHAVIOR 4: Consecutive Attendance
    print(f"\n🎯 BEHAVIOR 4: Consecutive Attendance")
    print("-" * 50)
    
    sorted_appointments = sorted(all_appointments, 
                               key=lambda x: x.get('starts_at', ''), reverse=True)
    
    consecutive_streak = 0
    streak_broken_by = None
    
    for appt in sorted_appointments:
        if appt.get('cancelled_at'):
            streak_broken_by = f"Cancellation on {appt.get('cancelled_at')}"
            break
        elif appt.get('did_not_arrive'):
            streak_broken_by = f"DNA on {appt.get('starts_at')}"
            break
        else:
            consecutive_streak += 1
    
    if consecutive_streak >= 10:
        attendance_bracket = 'Excellent (10+ consecutive)'
        points_awarded = 30
    elif consecutive_streak >= 5:
        attendance_bracket = 'High (5-9 consecutive)'
        points_awarded = 20
    elif consecutive_streak >= 3:
        attendance_bracket = 'Medium (3-4 consecutive)'
        points_awarded = 15
    elif consecutive_streak >= 1:
        attendance_bracket = 'Low (1-2 consecutive)'
        points_awarded = 10
    else:
        attendance_bracket = 'None (0 consecutive)'
        points_awarded = 0
    
    behavior_data['consecutive_attendance'] = {
        'streak': consecutive_streak,
        'attendance_bracket': attendance_bracket,
        'points_awarded': points_awarded,
        'streak_broken_by': streak_broken_by
    }
    
    print(f"   🏃 Consecutive attendance streak: {consecutive_streak}")
    print(f"   🎯 Attendance bracket: {attendance_bracket}")
    print(f"   ⭐ Points awarded: {points_awarded}")
    if streak_broken_by:
        print(f"   ⚠️ Streak broken by: {streak_broken_by}")
    
    # BEHAVIOR 5: Likability (Manual)
    print(f"\n🎯 BEHAVIOR 5: Likability (Manual Input)")
    print("-" * 50)
    
    behavior_data['likability'] = {
        'score': 0,
        'manual_input_required': True,
        'points_awarded': 0
    }
    
    print(f"   😊 Likability score: 0 (Manual input required)")
    print(f"   ⭐ Points awarded: 0")
    
    # BEHAVIOR 6: Open DNA Invoices
    print(f"\n🎯 BEHAVIOR 6: Open DNA Invoices")
    print("-" * 50)
    
    unpaid_invoices = [inv for inv in all_invoices if inv.get('closed_at') is None]
    dna_related_unpaid = []
    for invoice in unpaid_invoices:
        notes = str(invoice.get('notes', '')).lower()
        if any(keyword in notes for keyword in ['dna', 'non-attendance', 'did not arrive', 'no show']):
            dna_related_unpaid.append(invoice)
    
    has_open_dna = len(dna_related_unpaid) > 0
    
    behavior_data['open_dna_invoices'] = {
        'has_open_dna_invoice': has_open_dna,
        'dna_invoice_count': len(dna_related_unpaid),
        'points_deducted': -20 if has_open_dna else 0
    }
    
    print(f"   💸 Has open DNA invoice: {has_open_dna}")
    print(f"   📄 DNA-related unpaid invoices: {len(dna_related_unpaid)}")
    print(f"   ⭐ Points deducted: {behavior_data['open_dna_invoices']['points_deducted']}")
    
    # BEHAVIOR 7: Unpaid Invoices Count
    print(f"\n🎯 BEHAVIOR 7: Unpaid Invoices Count")
    print("-" * 50)
    
    unpaid_count = len(unpaid_invoices)
    
    behavior_data['unpaid_invoices'] = {
        'count': unpaid_count,
        'points_deducted': -5 * unpaid_count,
        'total_unpaid_amount': sum(float(inv.get('total_amount', 0)) for inv in unpaid_invoices)
    }
    
    print(f"   📄 Unpaid invoices count: {unpaid_count}")
    print(f"   💰 Total unpaid amount: ${behavior_data['unpaid_invoices']['total_unpaid_amount']:.2f}")
    print(f"   ⭐ Points deducted: {behavior_data['unpaid_invoices']['points_deducted']}")
    
    # BEHAVIOR 8: Cancellations
    print(f"\n🎯 BEHAVIOR 8: Cancellations")
    print("-" * 50)
    
    cancelled_appointments = [appt for appt in all_appointments if appt.get('cancelled_at')]
    cancellation_count = len(cancelled_appointments)
    
    # Group cancellations by reason if available
    cancellation_reasons = {}
    for appt in cancelled_appointments:
        reason = appt.get('cancellation_reason', 'Unknown')
        cancellation_reasons[reason] = cancellation_reasons.get(reason, 0) + 1
    
    behavior_data['cancellations'] = {
        'count': cancellation_count,
        'appointments': cancelled_appointments,
        'reasons': cancellation_reasons,
        'points_deducted': -2 * cancellation_count,
        'cancellation_rate': (cancellation_count / len(all_appointments) * 100) if all_appointments else 0
    }
    
    print(f"   ❌ Cancellations count: {cancellation_count}")
    print(f"   📊 Cancellation rate: {behavior_data['cancellations']['cancellation_rate']:.1f}%")
    print(f"   📋 Cancellation reasons: {cancellation_reasons}")
    print(f"   ⭐ Points deducted: {behavior_data['cancellations']['points_deducted']}")
    
    # BEHAVIOR 9: DNA (Did Not Arrive)
    print(f"\n🎯 BEHAVIOR 9: DNA (Did Not Arrive)")
    print("-" * 50)
    
    dna_appointments = [appt for appt in all_appointments if appt.get('did_not_arrive')]
    dna_count = len(dna_appointments)
    
    # Calculate DNA rate and patterns
    dna_dates = [appt.get('starts_at') for appt in dna_appointments]
    
    behavior_data['dna'] = {
        'count': dna_count,
        'appointments': dna_appointments,
        'dates': dna_dates,
        'points_deducted': -5 * dna_count,
        'dna_rate': (dna_count / len(all_appointments) * 100) if all_appointments else 0
    }
    
    print(f"   🚫 DNA count: {dna_count}")
    print(f"   📊 DNA rate: {behavior_data['dna']['dna_rate']:.1f}%")
    print(f"   📅 Recent DNA dates: {dna_dates[:5] if dna_dates else 'None'}")
    print(f"   ⭐ Points deducted: {behavior_data['dna']['points_deducted']}")
    
    # BEHAVIOR 10: Unlikability (Manual Input)
    print(f"\n🎯 BEHAVIOR 10: Unlikability (Manual Input)")
    print("-" * 50)
    
    behavior_data['unlikability'] = {
        'score': 0,
        'manual_input_required': True,
        'range': '0-100 points (100 = most unlikable)',
        'points_deducted': 0
    }
    
    print(f"   😠 Unlikability score: 0 (Manual input required)")
    print(f"   📝 Range: 0-100 points (100 = most unlikable)")
    print(f"   ⭐ Points deducted: 0")
    
    # CALCULATE TOTAL SCORE AND GRADE
    print(f"\n🎯 TOTAL SCORE CALCULATION")
    print("-" * 50)
    
    total_score = (
        behavior_data['future_appointments']['points_awarded'] +
        behavior_data['age_demographics']['points_awarded'] +
        behavior_data['yearly_spend']['points_awarded'] +
        behavior_data['consecutive_attendance']['points_awarded'] +
        behavior_data['likability']['points_awarded'] +
        behavior_data['open_dna_invoices']['points_deducted'] +
        behavior_data['unpaid_invoices']['points_deducted'] +
        behavior_data['cancellations']['points_deducted'] +
        behavior_data['dna']['points_deducted'] +
        behavior_data['unlikability']['points_deducted']
    )
    
    # Determine letter grade
    if total_score >= 100:
        letter_grade = 'A+'
    elif total_score >= 80:
        letter_grade = 'A'
    elif total_score >= 60:
        letter_grade = 'B'
    elif total_score >= 40:
        letter_grade = 'C'
    elif total_score >= 20:
        letter_grade = 'D'
    else:
        letter_grade = 'F'
    
    behavior_data['total_score'] = total_score
    behavior_data['letter_grade'] = letter_grade
    
    print(f"   📊 Total Score: {total_score}")
    print(f"   🎯 Letter Grade: {letter_grade}")
    
    # COMPREHENSIVE SUMMARY
    print(f"\n📋 COMPREHENSIVE BEHAVIORAL SUMMARY")
    print("=" * 80)
    print(f"👤 Patient: {PATIENT_NAME} (ID: {PATIENT_ID})")
    print(f"📊 Final Score: {total_score} points")
    print(f"🎯 Grade: {letter_grade}")
    print(f"📅 Total Appointments: {len(all_appointments)}")
    print(f"📄 Total Invoices: {len(all_invoices)}")
    print(f"💰 Yearly Spend: ${behavior_data['yearly_spend']['amount']:.2f}")
    print(f"🏃 Consecutive Attendance: {behavior_data['consecutive_attendance']['streak']}")
    print(f"❌ Cancellations: {behavior_data['cancellations']['count']}")
    print(f"🚫 DNAs: {behavior_data['dna']['count']}")
    print(f"📄 Unpaid Invoices: {behavior_data['unpaid_invoices']['count']}")
    
    # PATIENT CLASSIFICATION
    if letter_grade in ['A+', 'A']:
        classification = "⭐ EXCELLENT PATIENT"
        recommendation = "Maintain engagement, consider loyalty rewards"
    elif letter_grade == 'B':
        classification = "✅ GOOD PATIENT"
        recommendation = "Solid performer, minor improvements possible"
    elif letter_grade == 'C':
        classification = "⚠️ AVERAGE PATIENT"
        recommendation = "Needs attention, focus on engagement"
    elif letter_grade == 'D':
        classification = "🔶 PROBLEMATIC PATIENT"
        recommendation = "Requires intervention, address specific issues"
    else:  # F
        classification = "🚨 HIGH-RISK PATIENT"
        recommendation = "Immediate action required, consider special handling"
    
    print(f"\n{classification}")
    print(f"💡 Recommendation: {recommendation}")
    
    return behavior_data

def run_jodie_vlassis_analysis():
    """Run comprehensive behavioral analysis for Jodie Vlassis"""
    
    print("🚀 JODIE VLASSIS COMPREHENSIVE BEHAVIORAL ANALYSIS")
    print("="*80)
    print("✅ Complete 10-category behavior system")
    print("✅ Full detailed analysis")
    print("✅ Comprehensive scoring and recommendations")
    print("="*80)
    
    # Search for Jodie Vlassis
    patient = search_patient_by_name("Jodie", "Vlassis")
    
    if not patient:
        print("❌ Jodie Vlassis not found in database")
        return None
    
    # Run comprehensive analysis
    try:
        behavior_data = extract_comprehensive_behavior_data(patient)
        behavior_data['patient_info'] = {
            'id': patient.get('id'),
            'first_name': patient.get('first_name'),
            'last_name': patient.get('last_name'),
            'email': patient.get('email'),
            'phone': patient.get('phone_number'),
            'date_of_birth': patient.get('date_of_birth')
        }
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"jodie_vlassis_comprehensive_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(behavior_data, f, indent=2, default=str)
        
        print(f"\n🎉 JODIE VLASSIS ANALYSIS COMPLETE!")
        print("="*80)
        print(f"💾 Detailed results saved to: {filename}")
        print(f"🎯 Ready for RatedApp integration!")
        
        return behavior_data
        
    except Exception as e:
        print(f"❌ Error analyzing Jodie Vlassis: {str(e)}")
        return None

if __name__ == "__main__":
    print("🎯 JODIE VLASSIS BEHAVIORAL ANALYSIS SYSTEM")
    print("="*80)
    print("✅ All 10 behavior categories included")
    print("✅ Complete patient profile with recommendations")
    print("✅ Detailed scoring breakdown")
    print("✅ Ready for RatedApp integration")
    print("="*80)
    
    # Run Jodie Vlassis analysis
    result = run_jodie_vlassis_analysis()
    
    if result:
        print(f"\n🎉 SUCCESS! Jodie Vlassis analyzed comprehensively")
        print("🔧 Ready to integrate into RatedApp Django system")
    else:
        print("\n❌ Analysis failed - check patient data and API connectivity")
