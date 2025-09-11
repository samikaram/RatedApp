import requests
import base64
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Any

class PatientBehaviorAnalyzer:
    def __init__(self):
        self.RAW_API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
        self.ENCODED_API_KEY = base64.b64encode(f"{self.RAW_API_KEY}:".encode()).decode()
        self.BASE_URL = "https://api.au1.cliniko.com/v1"
        self.HEADERS = {
            'Authorization': f'Basic {self.ENCODED_API_KEY}',
            'Accept': 'application/json',
            'User-Agent': 'RatedApp Behavior Analysis (sami@sportsmedicineclinic.com.au)'
        }
        self.AEST = pytz.timezone('Australia/Sydney')
    
    def analyze_patient(self, patient_id: int) -> Dict[str, Any]:
        """Complete 10-category behavioral analysis for a patient"""
        try:
            # Get patient info
            patient_info = self._get_patient_info(patient_id)
            if not patient_info:
                return {'error': 'Patient not found'}
            
            # Extract all behavioral data
            appointments = self._get_patient_appointments(patient_id)
            invoices = self._get_patient_invoices(patient_id)
            
            # Calculate 10 behavioral categories
            behavior_scores = self._calculate_behavior_scores(patient_info, appointments, invoices)
            
            # Calculate total score and grade
            total_score = sum(score for score in behavior_scores.values() if isinstance(score, (int, float)))
            letter_grade = self._get_letter_grade(total_score)
            
            # Generate insights
            insights = self._generate_insights(behavior_scores, total_score, letter_grade)
            
            return {
                'patient_info': patient_info,
                'behavior_scores': behavior_scores,
                'total_score': total_score,
                'letter_grade': letter_grade,
                'insights': insights,
                'appointments_count': len(appointments),
                'invoices_count': len(invoices)
            }
            
        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _get_patient_info(self, patient_id: int) -> Dict[str, Any]:
        """Get basic patient information"""
        try:
            url = f"{self.BASE_URL}/patients/{patient_id}"
            response = requests.get(url, headers=self.HEADERS)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def _get_patient_appointments(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all appointments for patient"""
        try:
            url = f"{self.BASE_URL}/appointments"
            params = {'q[]': f'patient_id:={patient_id}', 'per_page': 100}
            response = requests.get(url, headers=self.HEADERS, params=params)
            response.raise_for_status()
            return response.json().get('appointments', [])
        except:
            return []
    
    def _get_patient_invoices(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get all invoices for patient"""
        try:
            url = f"{self.BASE_URL}/invoices"
            params = {'q[]': f'patient_id:={patient_id}', 'per_page': 100}
            response = requests.get(url, headers=self.HEADERS, params=params)
            response.raise_for_status()
            return response.json().get('invoices', [])
        except:
            return []
    
    def _calculate_behavior_scores(self, patient_info: Dict, appointments: List, invoices: List) -> Dict[str, Any]:
        """Calculate all 10 behavioral categories"""
        now = datetime.now(self.AEST)
        one_year_ago = now - timedelta(days=365)
        
        # 1. Appointments Booked (future appointments)
        future_appointments = [apt for apt in appointments 
                             if apt.get('starts_at') and 
                             datetime.fromisoformat(apt['starts_at'].replace('Z', '+00:00')).astimezone(self.AEST) > now]
        appointments_booked_score = min(len(future_appointments) * 5, 20)  # Max 20 points
        
        # 2. Age Demographics (30-50 target)
        age_score = 0
        if patient_info.get('date_of_birth'):
            try:
                dob = datetime.fromisoformat(patient_info['date_of_birth']).date()
                age = (now.date() - dob).days // 365
                if 30 <= age <= 50:
                    age_score = 10
            except:
                pass
        
        # 3. Yearly Spend (last 12 months)
        recent_invoices = []
        for invoice in invoices:
            if invoice.get('created_at'):
                try:
                    invoice_date = datetime.fromisoformat(invoice['created_at'].replace('Z', '+00:00')).astimezone(self.AEST)
                    if invoice_date >= one_year_ago:
                        recent_invoices.append(invoice)
                except:
                    pass
        
        yearly_spend = sum(float(inv.get('total', 0)) for inv in recent_invoices)
        if yearly_spend >= 2000:
            yearly_spend_score = 25
        elif yearly_spend >= 1000:
            yearly_spend_score = 20
        elif yearly_spend >= 500:
            yearly_spend_score = 15
        elif yearly_spend >= 200:
            yearly_spend_score = 10
        elif yearly_spend > 0:
            yearly_spend_score = 5
        else:
            yearly_spend_score = 0
        
        # 4. Consecutive Attendance (current streak)
        attended_appointments = [apt for apt in appointments 
                               if apt.get('attended') == True]
        consecutive_attendance = len(attended_appointments)  # Simplified for now
        consecutive_score = min(consecutive_attendance * 2, 30)  # Max 30 points
        
        # 5. Likability (manual input - default 0)
        likability_score = 0
        
        # 6. Open DNA Invoices (penalty)
        dna_invoices = [inv for inv in invoices 
                       if 'DNA' in str(inv.get('invoice_items', [])) and 
                       inv.get('status') != 'paid']
        open_dna_penalty = len(dna_invoices) * -20
        
        # 7. Unpaid Invoices (penalty)
        unpaid_invoices = [inv for inv in invoices 
                          if inv.get('status') not in ['paid', 'cancelled']]
        unpaid_penalty = len(unpaid_invoices) * -5
        
        # 8. Cancellations (penalty)
        cancelled_appointments = [apt for apt in appointments 
                                if apt.get('cancelled_at')]
        cancellation_penalty = len(cancelled_appointments) * -2
        
        # 9. DNA (penalty)
        dna_appointments = [apt for apt in appointments 
                          if apt.get('did_not_arrive') == True]
        dna_penalty = len(dna_appointments) * -5
        
        # 10. Unlikability (manual input - default 0)
        unlikability_penalty = 0
        
        return {
            'appointments_booked': appointments_booked_score,
            'age_demographics': age_score,
            'yearly_spend': yearly_spend_score,
            'consecutive_attendance': consecutive_score,
            'likability': likability_score,
            'open_dna_invoices': open_dna_penalty,
            'unpaid_invoices': unpaid_penalty,
            'cancellations': cancellation_penalty,
            'dna': dna_penalty,
            'unlikability': unlikability_penalty,
            # Additional data for display
            'yearly_spend_amount': yearly_spend,
            'future_appointments_count': len(future_appointments),
            'total_appointments': len(appointments),
            'total_invoices': len(invoices),
            'cancelled_count': len(cancelled_appointments),
            'dna_count': len(dna_appointments),
            'unpaid_count': len(unpaid_invoices)
        }
    
    def _get_letter_grade(self, total_score: float) -> str:
        """Convert total score to letter grade"""
        if total_score >= 100:
            return 'A+'
        elif total_score >= 80:
            return 'A'
        elif total_score >= 60:
            return 'B'
        elif total_score >= 40:
            return 'C'
        elif total_score >= 20:
            return 'D'
        else:
            return 'F'
    
    def _generate_insights(self, scores: Dict, total_score: float, grade: str) -> Dict[str, Any]:
        """Generate actionable insights based on behavior analysis"""
        insights = {
            'classification': '',
            'recommendation': '',
            'priority': '',
            'behavioral_profile': ''
        }
        
        if grade in ['A+', 'A']:
            insights['classification'] = 'Excellent Patient'
            insights['recommendation'] = 'Maintain relationship, consider VIP treatment'
            insights['priority'] = 'High Value'
            insights['behavioral_profile'] = 'Ideal Patient'
        elif grade == 'B':
            insights['classification'] = 'Good Patient'
            insights['recommendation'] = 'Encourage continued engagement'
            insights['priority'] = 'Standard'
            insights['behavioral_profile'] = 'Reliable Patient'
        elif grade == 'C':
            insights['classification'] = 'Average Patient'
            insights['recommendation'] = 'Needs attention, focus on engagement'
            insights['priority'] = 'Monitor'
            insights['behavioral_profile'] = 'Moderate Engagement'
        elif grade == 'D':
            insights['classification'] = 'Below Average Patient'
            insights['recommendation'] = 'Requires intervention and support'
            insights['priority'] = 'Attention Needed'
            insights['behavioral_profile'] = 'Engagement Issues'
        else:  # F
            insights['classification'] = 'Problematic Patient'
            insights['recommendation'] = 'Special handling required, consider discharge'
            insights['priority'] = 'High Risk'
            insights['behavioral_profile'] = 'Significant Issues'
        
        return insights
