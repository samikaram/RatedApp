from datetime import datetime, timedelta
import pytz

class BehavioralProcessor:
    @staticmethod
    def process_patient_behavior(patient_data, config, settings):
        """
        Process patient behavioral metrics using the latest scoring logic
        
        :param patient_data: Normalized patient data dictionary
        :param config: Active scoring configuration
        :param settings: RatedAppSettings with clinic timezone
        :return: Dictionary of behavioral metrics
        """
        # Use clinic timezone from settings
        clinic_tz = pytz.timezone(settings.clinic_timezone or 'Australia/Sydney')
        now_utc = datetime.now(pytz.UTC)
        
        behavior_data = {}
        
        # 1. FUTURE APPOINTMENTS
        future_appointments = [
            appt for appt in patient_data.get('appointments', []) 
            if datetime.fromisoformat(appt.get('starts_at', '').replace('Z', '+00:00')) > now_utc
        ]
        behavior_data['future_appointments'] = {
            'count': len(future_appointments),
            'points': config.future_appointments_weight if len(future_appointments) > 0 else 0,
            'description': f"{len(future_appointments)} future appointments"
        }
        
        # 2. AGE DEMOGRAPHICS
        dob = patient_data.get('date_of_birth')
        age = 0
        if dob:
            # Handle multiple date formats
            for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    birth_date = datetime.strptime(dob, date_format)
                    today = datetime.now(clinic_tz).date()
                    age = (today - birth_date.date()).days // 365
                    break
                except ValueError:
                    continue
            
            if age == 0 and dob:
                print(f"Warning: Could not parse date of birth: {dob}")
        
        # Find matching age bracket
        matching_bracket = next(
            (bracket for bracket in config.age_brackets.all() 
             if bracket.min_age <= age <= bracket.max_age), 
            None
        )
        
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
        
        # 3. YEARLY SPEND
        twelve_months_ago = now_utc - timedelta(days=365)
        yearly_invoices = [
            inv for inv in patient_data.get('invoices', []) 
            if inv.get('created_at') and 
               datetime.fromisoformat(inv['created_at'].replace('Z', '+00:00')) >= twelve_months_ago
        ]
        yearly_spend = sum(float(inv.get('total_amount', 0)) for inv in yearly_invoices)
        
        # Dynamic spend bracket calculation
        spend_brackets = config.spend_brackets.all().order_by('order')
        bracket_percentage = 0
        
        for bracket in spend_brackets:
            if bracket.min_spend <= yearly_spend <= bracket.max_spend:
                bracket_percentage = bracket.percentage / 100
                break
        
        # Fallback for amounts above highest bracket
        if bracket_percentage == 0 and yearly_spend > 0 and spend_brackets.exists():
            highest_bracket = spend_brackets.order_by('-max_spend').first()
            if yearly_spend > highest_bracket.max_spend:
                bracket_percentage = highest_bracket.percentage / 100
        
        points_awarded = round(config.yearly_spend_weight * bracket_percentage)
        
        behavior_data['yearly_spend'] = {
            'amount': yearly_spend,
            'points': points_awarded,
            'description': f"${yearly_spend:.2f} in last 12 months"
        }
        
        # 4. CONSECUTIVE ATTENDANCE
        sorted_appointments = sorted(
            patient_data.get('appointments', []), 
            key=lambda x: x.get('starts_at', ''), 
            reverse=True
        )
        
        consecutive_streak = 0
        for appt in sorted_appointments:
            if appt.get('cancelled_at') or appt.get('did_not_arrive'):
                break
            consecutive_streak += 1
        
        raw_points = consecutive_streak * config.points_per_consecutive_attendance
        points_awarded = min(raw_points, config.consecutive_attendance_weight)
        
        behavior_data['consecutive_attendance'] = {
            'streak': consecutive_streak,
            'points': points_awarded,
            'description': f"{consecutive_streak} consecutive attended"
        }
        
        # 5. REFERRER SCORE
        referrals = patient_data.get('referrals', [])
        referral_count = len(referrals)
        
        # Calculate referrer points with dynamic weighting
        raw_points = referral_count * config.points_per_referral
        referrer_points = min(raw_points, config.referrer_score_weight)
        
        behavior_data['referrer_score'] = {
            'points': referrer_points,
            'description': f"{referral_count} patients referred",
            'count': referral_count
        }
        
        # 6. OPEN DNA INVOICES
        unpaid_invoices = [
            inv for inv in patient_data.get('invoices', []) 
            if inv.get('closed_at') is None
        ]
        
        # Check for DNA-related unpaid invoices by linking to appointments
        dna_related_unpaid = []
        for invoice in unpaid_invoices:
            # Check if invoice is linked to a DNA appointment
            if 'appointment' in invoice and invoice['appointment']:
                appointment_link = invoice['appointment']['links']['self']
                appointment_id = appointment_link.split('/')[-1]
                
                # Find the matching appointment in our appointments data
                for appointment in patient_data.get('appointments', []):
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
        
        # 7. UNPAID INVOICES
        unpaid_count = len(unpaid_invoices)
        behavior_data['unpaid_invoices'] = {
            'count': unpaid_count,
            'points': -min(config.points_per_unpaid_invoice * unpaid_count, config.unpaid_invoices_weight),
            'description': f"{unpaid_count} unpaid invoices"
        }
        
        # 8. CANCELLATIONS
        cancelled_appointments = [
            appt for appt in patient_data.get('appointments', []) 
            if appt.get('cancelled_at')
        ]
        cancellation_count = len(cancelled_appointments)
        
        behavior_data['cancellations'] = {
            'count': cancellation_count,
            'points': -min(config.points_per_cancellation * cancellation_count, config.cancellations_weight),
            'description': f"{cancellation_count} total cancellations"
        }
        
        # 9. DNA APPOINTMENTS
        dna_appointments = [
            appt for appt in patient_data.get('appointments', []) 
            if appt.get('did_not_arrive')
        ]
        dna_count = len(dna_appointments)
        
        behavior_data['dna'] = {
            'count': dna_count,
            'points': -min(config.points_per_dna * dna_count, config.dna_weight),
            'description': f"{dna_count} DNA (Did Not Arrive)"
        }
        
        # 10. LIKABILITY (Manual)
        # Check for saved likability in Patient model
        try:
            from patient_rating.models import Patient
            patient_record = Patient.objects.filter(cliniko_patient_id=patient_data.get('id')).first()
            saved_likability = patient_record.likability if patient_record else 0
        except:
            saved_likability = 0
        
        behavior_data['likability'] = {
            'score': saved_likability,
            'points': saved_likability,
            'description': "Set by practitioner" if saved_likability != 0 else "Manual practitioner input (not set)"
        }
        
        # Calculate Total Score
        total_score = round(sum(category.get('points', 0) for category in behavior_data.values()))
        
        # Calculate Letter Grade
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
        
        return {
            'behavior_data': behavior_data,
            'total_score': total_score,
            'letter_grade': letter_grade,
            'analysis_date': datetime.now(clinic_tz).isoformat()
        }
