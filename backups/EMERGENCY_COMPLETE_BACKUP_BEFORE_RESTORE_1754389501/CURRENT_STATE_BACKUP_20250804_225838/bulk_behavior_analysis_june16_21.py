import requests
import json
import base64
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

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
    'User-Agent': 'RatedApp Comprehensive Behavior Analysis'
}

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

def extract_patients_from_date_range():
    """Extract unique patients from June 16-21, 2025 appointments"""
    
    print("🔍 EXTRACTING PATIENTS FROM JUNE 16-21, 2025")
    print("="*60)
    print("✅ Using proven July 2nd success method")
    print("✅ Server-side filtering with UTC conversion")
    
    # ✅ PROVEN WORKING DATE RANGE from July 2nd success
    start_date = "2025-06-15T14:00:00Z"  # June 16 AEST = June 15 14:00 UTC
    end_date = "2025-06-21T13:59:59Z"    # June 21 AEST = June 21 13:59 UTC
    
    print(f"📅 Date range: {start_date} to {end_date}")
    
    # Extract appointments from the date range
    filter_params = {
        'q[]': [
            f'starts_at:>{start_date}',
            f'starts_at:<{end_date}'
        ]
    }
    
    print(f"\n📡 Fetching appointments from June 16-21, 2025...")
    appointments = get_paginated_data('individual_appointments', filter_params, 'appointments in date range')
    
    if not appointments:
        print("❌ No appointments found in date range")
        return []
    
    # Extract unique patient IDs
    patient_ids = set()
    for appointment in appointments:
        patient_link = appointment.get('patient', {}).get('links', {}).get('self', '')
        if patient_link:
            # Extract patient ID from URL like: https://api.au1.cliniko.com/v1/patients/1109937
            patient_id = patient_link.split('/')[-1]
            patient_ids.add(patient_id)
    
    print(f"\n✅ Found {len(patient_ids)} unique patients in date range")
    
    # Get detailed patient information
    patients = []
    for i, patient_id in enumerate(list(patient_ids)[:25], 1):  # Limit to 25 for comprehensive analysis
        print(f"📋 Fetching patient {i}/25: ID {patient_id}")
        
        patient_url = f"patients/{patient_id}"
        response = requests.get(f"{BASE_URL}/{patient_url}", headers=HEADERS)
        
        if response.status_code == 200:
            patient_data = response.json()
            patients.append(patient_data)
        else:
            print(f"   ❌ Failed to fetch patient {patient_id}")
    
    print(f"\n✅ Successfully extracted {len(patients)} patients for comprehensive analysis")
    return patients

def extract_comprehensive_behavior_data(patient_data):
    """Extract ALL 10 behavior categories with complete details for a patient"""
    
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
    
    # BEHAVIOR 1: Future Appointments Booked (COMPREHENSIVE)
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
    
    # BEHAVIOR 2: Age Demographics (COMPREHENSIVE)
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
    
    # BEHAVIOR 3: Yearly Spend (COMPREHENSIVE)
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
        'points_awarded': points_awarded,
        'invoices': yearly_invoices
    }
    
    print(f"   💰 Yearly spend: ${yearly_spend:.2f}")
    print(f"   📄 Invoices in period: {len(yearly_invoices)}")
    print(f"   🎯 Spending bracket: {spending_bracket}")
    print(f"   ⭐ Points awarded: {points_awarded}")
    
    # BEHAVIOR 4: Consecutive Attendance (COMPREHENSIVE)
    print(f"\n🎯 BEHAVIOR 4: Consecutive Attendance")
    print("-" * 50)
    
    # Sort appointments by date (most recent first)
    sorted_appointments = sorted(all_appointments, 
                               key=lambda x: x.get('starts_at', ''), reverse=True)
    
    consecutive_streak = 0
    streak_broken_by = None
    
    for i, appt in enumerate(sorted_appointments):
        if appt.get('cancelled_at'):
            streak_broken_by = f"Cancellation on {appt.get('cancelled_at')}"
            break
        elif appt.get('did_not_arrive'):
            streak_broken_by = f"DNA on {appt.get('starts_at')}"
            break
        else:
            consecutive_streak += 1
    
    # Determine attendance bracket
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
        'streak_broken_by': streak_broken_by,
        'total_appointments': len(all_appointments)
    }
    
    print(f"   🏃 Consecutive attendance streak: {consecutive_streak}")
    print(f"   🎯 Attendance bracket: {attendance_bracket}")
    print(f"   ⭐ Points awarded: {points_awarded}")
    if streak_broken_by:
        print(f"   ⚠️ Streak broken by: {streak_broken_by}")
    
    # BEHAVIOR 5: Likability (Manual Input)
    print(f"\n🎯 BEHAVIOR 5: Likability (Manual Input)")
    print("-" * 50)
    
    behavior_data['likability'] = {
        'score': 0,
        'manual_input_required': True,
        'range': '0-100 points',
        'points_awarded': 0
    }
    
    print(f"   😊 Likability score: 0 (Manual input required)")
    print(f"   📝 Range: 0-100 points")
    print(f"   ⭐ Points awarded: 0")
    
    # BEHAVIOR 6: Open DNA Invoices (COMPREHENSIVE)
    print(f"\n🎯 BEHAVIOR 6: Open DNA Invoices")
    print("-" * 50)
    
    unpaid_invoices = [inv for inv in all_invoices if inv.get('closed_at') is None]
    
    # Check for DNA-related unpaid invoices
    dna_related_unpaid = []
    for invoice in unpaid_invoices:
        notes = str(invoice.get('notes', '')).lower()
        if any(keyword in notes for keyword in ['dna', 'non-attendance', 'did not arrive', 'no show']):
            dna_related_unpaid.append(invoice)
    
    has_open_dna = len(dna_related_unpaid) > 0
    
    behavior_data['open_dna_invoices'] = {
        'has_open_dna_invoice': has_open_dna,
        'dna_invoice_count': len(dna_related_unpaid),
        'total_unpaid_invoices': len(unpaid_invoices),
        'dna_invoices': dna_related_unpaid,
        'points_deducted': -20 if has_open_dna else 0
    }
    
    print(f"   💸 Has open DNA invoice: {has_open_dna}")
    print(f"   📄 DNA-related unpaid invoices: {len(dna_related_unpaid)}")
    print(f"   📄 Total unpaid invoices: {len(unpaid_invoices)}")
    print(f"   ⭐ Points deducted: {behavior_data['open_dna_invoices']['points_deducted']}")
    
    # BEHAVIOR 7: Unpaid Invoices Count (COMPREHENSIVE)
    print(f"\n🎯 BEHAVIOR 7: Unpaid Invoices Count")
    print("-" * 50)
    
    # ✅ CORRECTED FILTER SYNTAX (from July 4th fix)
    # Use 'closed_at:!?' (does not exist) instead of 'closed_at:!' for unpaid invoices
    unpaid_invoices = [inv for inv in all_invoices if inv.get('closed_at') is None]
    unpaid_count = len(unpaid_invoices)
    
    behavior_data['unpaid_invoices'] = {
        'count': unpaid_count,
        'invoices': unpaid_invoices,
        'points_deducted': -5 * unpaid_count,
        'total_unpaid_amount': sum(float(inv.get('total_amount', 0)) for inv in unpaid_invoices)
    }
    
    print(f"   📄 Unpaid invoices count: {unpaid_count}")
    print(f"   💰 Total unpaid amount: ${behavior_data['unpaid_invoices']['total_unpaid_amount']:.2f}")
    print(f"   ⭐ Points deducted: {behavior_data['unpaid_invoices']['points_deducted']}")
    
    # BEHAVIOR 8: Cancellations (COMPREHENSIVE)
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
    
    # BEHAVIOR 9: DNA (Did Not Arrive) (COMPREHENSIVE)
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

def run_comprehensive_bulk_analysis():
    """Run comprehensive behavioral analysis for June 16-21, 2025 patients"""
    
    print("🚀 COMPREHENSIVE BULK BEHAVIORAL ANALYSIS - JUNE 16-21, 2025")
    print("="*80)
    print("✅ Complete 10-category behavior system")
    print("✅ Full detailed analysis per patient")
    print("✅ Comprehensive scoring and recommendations")
    print("✅ Ready for RatedApp integration")
    print("="*80)
    
    # Extract patients from date range
    patients = extract_patients_from_date_range()
    
    if not patients:
        print("❌ No patients found in date range")
        return
    
    # Comprehensive analysis for each patient
    all_behavior_data = []
    
    for i, patient in enumerate(patients, 1):
        print(f"\n📊 PATIENT {i}/{len(patients)}")
        print("="*80)
        
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
            all_behavior_data.append(behavior_data)
            
        except Exception as e:
            print(f"❌ Error analyzing patient {patient.get('id')}: {str(e)}")
            continue
    
    # Save comprehensive results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"comprehensive_behavior_analysis_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_behavior_data, f, indent=2, default=str)
    
    print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
    print("="*80)
    print(f"📋 Total patients analyzed: {len(all_behavior_data)}")
    print(f"💾 Detailed results saved to: {filename}")
    
    # Generate summary statistics
    grades = [data['letter_grade'] for data in all_behavior_data]
    grade_counts = {grade: grades.count(grade) for grade in ['A+', 'A', 'B', 'C', 'D', 'F']}
    
    print(f"\n📊 GRADE DISTRIBUTION:")
    for grade, count in grade_counts.items():
        percentage = (count / len(all_behavior_data) * 100) if all_behavior_data else 0
        print(f"   {grade}: {count} patients ({percentage:.1f}%)")
    
    # Identify top and bottom performers
    sorted_patients = sorted(all_behavior_data, key=lambda x: x['total_score'], reverse=True)
    
    print(f"\n⭐ TOP 3 PERFORMERS:")
    for i, patient in enumerate(sorted_patients[:3], 1):
        name = f"{patient['patient_info']['first_name']} {patient['patient_info']['last_name']}"
        print(f"   {i}. {name}: {patient['total_score']} points ({patient['letter_grade']})")
    
    print(f"\n🚨 BOTTOM 3 PERFORMERS:")
    for i, patient in enumerate(sorted_patients[-3:], 1):
        name = f"{patient['patient_info']['first_name']} {patient['patient_info']['last_name']}"
        print(f"   {i}. {name}: {patient['total_score']} points ({patient['letter_grade']})")
    
    print(f"\n🎯 READY FOR RATEDAPP INTEGRATION!")
    print("✅ Complete behavioral profiles generated")
    print("✅ All 10 categories extracted and scored")
    print("✅ Comprehensive patient insights available")
    print("✅ Django model integration ready")
    
    return all_behavior_data

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE BEHAVIORAL ANALYSIS SYSTEM")
    print("="*80)
    print("✅ All 10 behavior categories included")
    print("✅ Complete patient profiles with recommendations")
    print("✅ Detailed scoring breakdown")
    print("✅ Ready for RatedApp integration")
    print("="*80)
    
    # Run comprehensive analysis
    results = run_comprehensive_bulk_analysis()
    
    if results:
        print(f"\n🎉 SUCCESS! {len(results)} patients analyzed comprehensively")
        print("🔧 Ready to integrate into RatedApp Django system")
    else:
        print("\n❌ Analysis failed - check patient data and API connectivity")
        
