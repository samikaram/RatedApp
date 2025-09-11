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

# Base64 encode the API key
ENCODED_API_KEY = base64.b64encode(f"{RAW_API_KEY}:".encode()).decode()

HEADERS = {
    'Authorization': f'Basic {ENCODED_API_KEY}',
    'Accept': 'application/json',
    'User-Agent': 'RatedApp Django Analysis'
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
        
        all_data.extend(items)
        
        # Check if there are more pages
        if len(items) < 100:
            break
            
        page += 1
    
    return all_data

def analyze_patient_behavior(patient_id, config=None):
    """Complete 10-category behavioral analysis using proven extraction logic"""
    
    try:
        print(f"🎯 Starting analysis for Patient ID: {patient_id}")
        
        # Get patient data
        url = f"{BASE_URL}/patients/{patient_id}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        patient_data = response.json()
        
        PATIENT_NAME = f"{patient_data.get('first_name')} {patient_data.get('last_name')}"
        print(f"📊 Analyzing: {PATIENT_NAME}")
        
        behavior_data = {}
        
        # Get all appointments for this patient
        filter_params = {'q[]': [f'patient_id:={patient_id}']}
        all_appointments = get_paginated_data('individual_appointments', filter_params, f'appointments for {PATIENT_NAME}')
        
        # Get all invoices for this patient
        filter_params = {'q[]': [f'patient_id:={patient_id}']}
        all_invoices = get_paginated_data('invoices', filter_params, f'invoices for {PATIENT_NAME}')
        
        # BEHAVIOR 1: Future Appointments Booked
        now_utc = datetime.now(pytz.UTC).isoformat()
        future_appointments = [appt for appt in all_appointments if appt.get('starts_at', '') > now_utc]
        
        behavior_data['future_appointments'] = {
            'count': len(future_appointments),
            'points': 20 if len(future_appointments) >= 3 else 15 if len(future_appointments) == 2 else 10 if len(future_appointments) == 1 else 0,
            'description': f"{len(future_appointments)} future appointments"
        }
        
        # BEHAVIOR 2: Age Demographics
        dob = patient_data.get('date_of_birth')
        age = 0
        in_target_demographic = False
        if dob:
            birth_date = datetime.strptime(dob, '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
            in_target_demographic = 20 <= age <= 55
        
        behavior_data['age_demographics'] = {
            'age': age,
            'in_target_demographic': in_target_demographic,
            'points': 10 if in_target_demographic else 0,
            'description': f"Age {age} ({'target demographic' if in_target_demographic else 'outside target'})"
        }
        
        # BEHAVIOR 3: Yearly Spend
        twelve_months_ago = datetime.now(pytz.UTC) - timedelta(days=365)
        yearly_invoices = [inv for inv in all_invoices if inv.get('created_at') and 
                          datetime.fromisoformat(inv['created_at'].replace('Z', '+00:00')) >= twelve_months_ago]
        yearly_spend = sum(float(inv.get('total_amount', 0)) for inv in yearly_invoices)
        
        if yearly_spend >= 1000:
            points_awarded = 25
        elif yearly_spend >= 500:
            points_awarded = 20
        elif yearly_spend >= 200:
            points_awarded = 15
        elif yearly_spend >= 100:
            points_awarded = 10
        elif yearly_spend > 0:
            points_awarded = 5
        else:
            points_awarded = 0
        
        behavior_data['yearly_spend'] = {
            'amount': yearly_spend,
            'points': points_awarded,
            'description': f"${yearly_spend:.2f} in last 12 months"
        }
        
        # BEHAVIOR 4: Consecutive Attendance
        sorted_appointments = sorted(all_appointments, key=lambda x: x.get('starts_at', ''), reverse=True)
        
        consecutive_streak = 0
        for appt in sorted_appointments:
            if appt.get('cancelled_at') or appt.get('did_not_arrive'):
                break
            else:
                consecutive_streak += 1
        
        # Use dynamic weight: 2 points per consecutive appointment, capped at slider max
        raw_points = consecutive_streak * 2
        points_awarded = min(raw_points, config.consecutive_attendance_weight)
        
        behavior_data['consecutive_attendance'] = {
            'streak': consecutive_streak,
            'points': points_awarded,
            'description': f"{consecutive_streak} consecutive attended"
        }
        
        # BEHAVIOR 5: Likability (Manual)
        behavior_data['likability'] = {
            'score': 0,
            'points': config.likability_weight,
            'description': "Manual practitioner input (not set)"
        }
        
        # BEHAVIOR 6: Open DNA Invoices
        unpaid_invoices = [inv for inv in all_invoices if inv.get('closed_at') is None]
        dna_related_unpaid = []
        for invoice in unpaid_invoices:
            notes = str(invoice.get('notes', '')).lower()
            if any(keyword in notes for keyword in ['dna', 'non-attendance', 'did not arrive', 'no show']):
                dna_related_unpaid.append(invoice)
        
        has_open_dna = len(dna_related_unpaid) > 0
        
        behavior_data['open_dna_invoices'] = {
            'has_open_dna': has_open_dna,
            'count': len(dna_related_unpaid),
            'points': -20 if has_open_dna else 0,
            'description': f"{len(dna_related_unpaid)} open DNA invoices"
        }
        
        # BEHAVIOR 7: Unpaid Invoices Count
        unpaid_count = len(unpaid_invoices)
        behavior_data['unpaid_invoices'] = {
            'count': unpaid_count,
            'points': -5 * unpaid_count,
            'description': f"{unpaid_count} unpaid invoices"
        }
        
        # BEHAVIOR 8: Cancellations
        cancelled_appointments = [appt for appt in all_appointments if appt.get('cancelled_at')]
        cancellation_count = len(cancelled_appointments)
        
        behavior_data['cancellations'] = {
            'count': cancellation_count,
            'points': -2 * cancellation_count,
            'description': f"{cancellation_count} total cancellations"
        }
        
        # BEHAVIOR 9: DNA (Did Not Arrive)
        dna_appointments = [appt for appt in all_appointments if appt.get('did_not_arrive')]
        dna_count = len(dna_appointments)
        
        behavior_data['dna'] = {
            'count': dna_count,
            'points': -5 * dna_count,
            'description': f"{dna_count} DNA (Did Not Arrive)"
        }
        
        # BEHAVIOR 10: Unlikability (Manual)
        behavior_data['unlikability'] = {
            'score': 0,
            'points': -config.unlikability_weight,
            'description': "Manual practitioner input (not set)"
        }
        
        # CALCULATE TOTAL SCORE
        total_score = (
            behavior_data['future_appointments']['points'] +
            behavior_data['age_demographics']['points'] +
            behavior_data['yearly_spend']['points'] +
            behavior_data['consecutive_attendance']['points'] +
            behavior_data['likability']['points'] +
            behavior_data['open_dna_invoices']['points'] +
            behavior_data['unpaid_invoices']['points'] +
            behavior_data['cancellations']['points'] +
            behavior_data['dna']['points'] +
            behavior_data['unlikability']['points']
        )
        
        # Calculate letter grade
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
        
        # Generate insights
        insights = []
        if letter_grade in ['A+', 'A']:
            insights.append("⭐ Excellent patient - prioritize for VIP treatment")
        elif letter_grade == 'B':
            insights.append("✅ Good patient - maintain engagement")
        elif letter_grade == 'C':
            insights.append("⚠️ Average patient - needs attention, focus on engagement")
        elif letter_grade in ['D', 'F']:
            insights.append("🚨 Problematic patient - requires special handling")
        
        if behavior_data['cancellations']['count'] > 10:
            insights.append("📅 High cancellation rate - consider booking policies")
        
        if behavior_data['dna']['count'] > 5:
            insights.append("❌ Multiple DNAs - implement confirmation system")
        
        if behavior_data['yearly_spend']['amount'] == 0:
            insights.append("💰 No recent spending - re-engagement needed")
        
        print(f"✅ Analysis complete - Score: {total_score}, Grade: {letter_grade}")
        
        return {
            'patient_data': patient_data,
            'behavior_data': behavior_data,
            'total_score': total_score,
            'letter_grade': letter_grade,
            'insights': insights,
            'analysis_date': datetime.now(AEST).isoformat()
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return None
