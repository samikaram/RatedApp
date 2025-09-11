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
            bracket_description = f"[{matching_bracket.min_age}-{matching_bracket.max_age}] ({matching_bracket.percentage}%)"
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
        
        # Dynamic bracket-based calculation with fallback logic
        spend_brackets = config.spend_brackets.all().order_by('order')
        bracket_percentage = 0  # Default
        
        # Find matching bracket
        for bracket in spend_brackets:
            if bracket.min_spend <= yearly_spend <= bracket.max_spend:
                bracket_percentage = bracket.percentage / 100
                break
        
        # FALLBACK LOGIC: If no bracket matched and amount > 0
        if bracket_percentage == 0 and yearly_spend > 0 and spend_brackets.exists():
            # Get the highest bracket's percentage for amounts above highest bracket
            highest_bracket = spend_brackets.order_by('-max_spend').first()
            if yearly_spend > highest_bracket.max_spend:
                bracket_percentage = highest_bracket.percentage / 100
        
        # Apply config weight to bracket percentage
        points_awarded = config.yearly_spend_weight * bracket_percentage
        
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
            # Check if invoice is linked to a DNA appointment
            if 'appointment' in invoice and invoice['appointment']:
                appointment_link = invoice['appointment']['links']['self']
                appointment_id = appointment_link.split('/')[-1]
                
                # Find the matching appointment in our appointments data
                for appointment in all_appointments:
                    if str(appointment.get('id')) == appointment_id:
                        # Check if this appointment is a DNA (did_not_arrive = True)
                        if appointment.get('did_not_arrive', False):
                            dna_related_unpaid.append(invoice)
                        break
        
        has_open_dna = len(dna_related_unpaid) > 0
        
        behavior_data['open_dna_invoices'] = {
            'has_open_dna': has_open_dna,
            'count': len(dna_related_unpaid),
            'points': -config.open_dna_invoice_weight if has_open_dna else 0,
            'description': f"{len(dna_related_unpaid)} open DNA invoices"
        }
        
        # BEHAVIOR 7: Unpaid Invoices Count
        unpaid_count = len(unpaid_invoices)
        behavior_data['unpaid_invoices'] = {
            'count': unpaid_count,
            'points': -min(config.points_per_unpaid_invoice * unpaid_count, config.unpaid_invoices_weight),
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

        # BEHAVIOR 11: Referrer Score - Calculate how many patients this patient has referred
        print(f"🎯 Calculating referrer score for Patient ID: {patient_id}")
        try:
            referrer_url = "https://api.cliniko.com/v1/referral_sources"
            referrer_params = {
                'q[]': f'referrer_id:={patient_id}',
                'per_page': 50
            }
            referrer_response = requests.get(referrer_url, headers=HEADERS, params=referrer_params)
            
            if referrer_response.status_code == 200:
                referrer_data = referrer_response.json()
                referral_count = len(referrer_data.get('referral_sources', []))
                print(f"📊 Found {referral_count} patients referred by this patient")
                
                # Calculate score using slider max and points per referral
                # Raw points = referral_count × points_per_referral
                raw_points = referral_count * config.points_per_referral
                
                # Final score = min(raw_points, slider_max)
                referrer_points = min(raw_points, config.referrer_score_weight)
                
                # Status based on referral count only
                if referral_count >= 10:
                    referrer_level = "EXCELLENT REFERRER"
                elif referral_count >= 5:
                    referrer_level = "VERY GOOD REFERRER"
                elif referral_count >= 3:
                    referrer_level = "GOOD REFERRER"
                elif referral_count >= 1:
                    referrer_level = "SOME REFERRALS"
                else:
                    referrer_level = "NO REFERRALS"
                
                referrer_description = f"{referral_count} patient{'s' if referral_count != 1 else ''} referred"
            else:
                print(f"⚠️ Referrer API error: {referrer_response.status_code}")
                referrer_points = 0
                referrer_description = "Unable to calculate referrals"
                referrer_level = "ERROR"
                referral_count = 0
        except Exception as e:
            print(f"❌ Referrer calculation error: {e}")
            referrer_points = 0
            referrer_description = f"Error calculating referrals: {str(e)}"
            referrer_level = "ERROR"
            referral_count = 0

        behavior_data["referrer_score"] = {
            "points": referrer_points,
            "description": referrer_description,
            "level": referrer_level,
            "count": referral_count
        }
        print(f"✅ Referrer Score: {referrer_points} points (placeholder)")
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
            behavior_data['referrer_score']['points']
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

    
    # Referrer Score Calculation (Added August 2025)
    def calculate_patient_referrer_score(patient_id, config):
        """
        Calculate referrer score using Paula's new API filter.
        
        Args:
            patient_id (str): Cliniko patient ID
            config: ScoringConfiguration object
            
        Returns:
            int: Referrer score (capped by slider maximum)
        """
        try:
            referrer_score = calculate_referrer_score(
                patient_id=patient_id,
                points_per_referral=config.points_per_referral,
                max_points=config.referrer_score_weight
            )
            return referrer_score
        except Exception as e:
            print(f"❌ Error calculating referrer score for patient {patient_id}: {e}")
            return 0
    