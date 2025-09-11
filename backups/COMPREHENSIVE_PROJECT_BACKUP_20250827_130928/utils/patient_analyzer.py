import requests
import json
import base64
from datetime import datetime, timedelta
import pytz


# Django model imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from patient_rating.models import ScoringConfiguration# Timezone setup
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
        
        # Get active scoring configuration
        if config is None:
            from patient_rating.models import ScoringConfiguration
            config = ScoringConfiguration.get_active_config()        
        # Get all appointments for this patient (active + cancelled)
        filter_params = {'q[]': [f'patient_id:={patient_id}']}
        active_appointments = get_paginated_data('individual_appointments', filter_params, f'active appointments for {PATIENT_NAME}')
        
        # Get cancelled appointments separately
        cancelled_filter_params = {'q[]': [f'patient_id:={patient_id}', 'cancelled_at:?']}
        cancelled_appointments = get_paginated_data('individual_appointments', cancelled_filter_params, f'cancelled appointments for {PATIENT_NAME}')
        
        # Combine active and cancelled appointments
        all_appointments = active_appointments + cancelled_appointments        
        # Get all invoices for this patient
        filter_params = {'q[]': [f'patient_id:={patient_id}']}
        all_invoices = get_paginated_data('invoices', filter_params, f'invoices for {PATIENT_NAME}')
        
        # BEHAVIOR 1: Future Appointments Booked
        now_utc = datetime.now(pytz.UTC).isoformat()
        future_appointments = [appt for appt in all_appointments if appt.get("starts_at", "") > now_utc]        
        behavior_data['future_appointments'] = {
            'count': len(future_appointments),
            'points': config.future_appointments_weight if len(future_appointments) > 0 else 0,            'description': f"{len(future_appointments)} future appointments"
        }
        
        # BEHAVIOR 2: Age Demographics (DYNAMIC SCORING)
        dob = patient_data.get('date_of_birth')
        age = 0
        if dob:
            birth_date = datetime.strptime(dob, '%Y-%m-%d')
            age = (datetime.now() - birth_date).days // 365
        
        # Find matching age bracket
        matching_bracket = None
        for bracket in config.age_brackets.all():
            if bracket.min_age <= age <= bracket.max_age:
                matching_bracket = bracket
                break
        
        # Calculate points based on bracket percentage
        if matching_bracket:
            points_awarded = int((matching_bracket.percentage / 100) * config.age_demographics_weight)
            bracket_description = f"{matching_bracket.min_age}-{matching_bracket.max_age} ({matching_bracket.percentage}%)"
        else:
            points_awarded = 0
            bracket_description = "No matching bracket"
        
        behavior_data['age_demographics'] = {
            'age': age,
            'points': points_awarded,
            'description': f"Age {age} - {bracket_description}"
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
        raw_points = consecutive_streak * config.points_per_consecutive_attendance
        points_awarded = min(raw_points, config.consecutive_attendance_weight)
        
        behavior_data['consecutive_attendance'] = {
            'streak': consecutive_streak,
            'points': points_awarded,
            'description': f"{consecutive_streak} consecutive attended"
        }
        
        # BEHAVIOR 5: Likability (Manual) - Check database for saved value
        try:
            from patient_rating.models import Patient
            patient_record = Patient.objects.filter(cliniko_patient_id=patient_id).first()
            saved_likability = patient_record.likability if patient_record else 0
        except:
            saved_likability = 0
        
        behavior_data["likability"] = {
            "score": saved_likability,
            "points": saved_likability,
            "description": "Set by practitioner" if saved_likability > 0 else "Manual practitioner input (not set)"
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
            'points': -min(config.points_per_cancellation * cancellation_count, config.cancellations_weight),            'description': f"{cancellation_count} total cancellations"
        }
        
        # BEHAVIOR 9: DNA (Did Not Arrive)
        dna_appointments = [appt for appt in all_appointments if appt.get('did_not_arrive')]
        dna_count = len(dna_appointments)
        
        behavior_data["dna"] = {
            "count": dna_count,
            "points": -min(config.points_per_dna * dna_count, config.dna_weight),
            "description": f"{dna_count} DNA (Did Not Arrive)"
        }
                # BEHAVIOR 10: Unlikability (Manual) - Check database for saved value
        try:
            saved_unlikability = patient_record.unlikability if patient_record else 0
        except:
            saved_unlikability = 0
        
        behavior_data["unlikability"] = {
            "score": saved_unlikability,
            "points": -saved_unlikability,
            "description": "Set by practitioner" if saved_unlikability > 0 else "Manual practitioner input (not set)"
        
        }        # CALCULATE TOTAL SCORE
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
            "patient_name": PATIENT_NAME,
            "patient_data": patient_data,
            "behavior_data": behavior_data,
            "total_score": total_score,
            "letter_grade": letter_grade,
            "insights": insights,
            "analysis_date": datetime.now(AEST).isoformat()
        }        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return None
