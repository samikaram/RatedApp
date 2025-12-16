import logging
import time
import pytz
from patient_rating.views import send_analytics_email_log
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from patient_rating.models import (
    RatedAppSettings, 
    ScoringConfiguration,
    AnalyticsJob,
    Patient
)
from patient_rating.integrations.factory import IntegrationFactory
from patient_rating.behavioral_processor import BehavioralProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process analytics jobs for patient rating'
    
    def __init__(self):
        super().__init__()
        self.current_job = None
        self.client = None
        self.normalizer = None
        self.processor = None
        self.settings = None
        
    def handle(self, *args, **options):
        """Main entry point for the management command"""
        try:
            # Find jobs that need processing
            jobs = AnalyticsJob.objects.filter(
                status__in=['pending', 'running']
            ).order_by('created_at')
            
            for job in jobs:
                # Process manual jobs immediately if pending
                if job.frequency == 'manual' and job.status == 'pending':
                    self.process_job(job)
                # Process scheduled jobs if it's time
                elif job.should_run_now():
                    self.process_job(job)
                # Resume running jobs (recovery from crash)
                elif job.status == 'running':
                    self.process_job(job)
                    
        except Exception as e:
            logger.error(f"Error in analytics processor: {e}")
            
    def process_job(self, job: AnalyticsJob):
        """Process a single analytics job"""
        self.current_job = job
        
        try:
            logger.info(f"Starting analytics job {job.id}")
            
            # Update job status
            job.status = 'running'
            job.last_run_started = timezone.now()
            job.save()
            
            # Initialize components
            self.initialize_components(job)
            
            # Get date range
            start_date, end_date = self.get_date_range_utc(job)
            
            # Get patients with appointments in range
            logger.info(f"Fetching patients with appointments from {start_date} to {end_date}")
            patient_details = self.get_patients_in_range(start_date, end_date)
            
            if not patient_details:
                logger.warning("No patients found in date range")
                job.status = 'completed'
                job.last_run_completed = timezone.now()
                job.patients_processed = 0
                job.save()
                return
            
            # Update job with total patients
            job.total_patients = len(patient_details)
            job.save()
            
            logger.info(f"Found {len(patient_details)} unique patients to process")
            
            # Process patients in batches
            self.process_patients_batch(patient_details, job)
            
            # Mark job as completed
            if job.cancel_requested:
                job.status = 'cancelled'
            elif job.patients_failed > 0:
                job.status = 'partial'
            else:
                job.status = 'completed'
                
            job.last_run_completed = timezone.now()
            
            # Calculate next run if recurring
            if job.frequency in ['daily', 'weekly'] and not job.cancel_requested:
                job.calculate_next_run()
                job.status = 'pending'  # Ready for next run
                
            job.save()
            # Send email log if completed successfully
            if job.status in ['completed', 'partial']:
                try:
                    send_analytics_email_log(job, self.settings)
                except Exception as e:
                    logger.error(f"Failed to send analytics email log: {e}")
            
            logger.info(f"Analytics job {job.id} completed: {job.patients_processed}/{job.total_patients} processed")
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            job.mark_failed(str(e))
            
    def initialize_components(self, job: AnalyticsJob):
        """Initialize plugin components and settings"""
        self.settings = RatedAppSettings.objects.first()
        if not self.settings:
            raise ValueError("No clinic settings configured")
        
        # Initialize plugin components
        self.client = IntegrationFactory.get_client(self.settings)
        self.normalizer = IntegrationFactory.get_normalizer(self.settings)
        self.processor = BehavioralProcessor()
        
        # Get rate limits for this integration
        self.rate_limits = self.client.get_rate_limits()
        
    def get_date_range_utc(self, job: AnalyticsJob) -> tuple:
        """Convert job date range to UTC timestamps"""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        import pytz
        
        # Use clinic timezone
        clinic_tz = pytz.timezone(self.settings.clinic_timezone or 'Australia/Sydney')
        
        # For "1 day", use the current time as end and exactly 24 hours back as start
        if job.date_range == '1d':
            # Current moment in clinic timezone
            end_date = datetime.now(clinic_tz)
            # Exactly 24 hours (1 day) back
            start_date = end_date - timedelta(hours=24)
        else:
            # For other ranges, use end of today and calculate back
            end_date = datetime.now(clinic_tz).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            
            # Handle different date range formats
            if job.date_range == '3':
                # 3 months
                start_date = end_date - relativedelta(months=3)
            elif job.date_range == '6':
                # 6 months  
                start_date = end_date - relativedelta(months=6)
            elif job.date_range == '1y':
                # 1 year
                start_date = end_date - relativedelta(years=1)
            elif job.date_range == '2y':
                # 2 years
                start_date = end_date - relativedelta(years=2)
            elif job.date_range == '5y':
                # 5 years
                start_date = end_date - relativedelta(years=5)
            elif job.date_range == '10y':
                # 10 years
                start_date = end_date - relativedelta(years=10)
            else:
                # Default to 3 months if unrecognized
                start_date = end_date - relativedelta(months=3)
            
            # Set to beginning of day for non-1-day ranges
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Convert to UTC
        start_utc = start_date.astimezone(pytz.UTC)
        end_utc = end_date.astimezone(pytz.UTC)
        
        # Format for API
        start_str = start_utc.strftime('%Y-%m-%dT%H:%M:%S')
        end_str = end_utc.strftime('%Y-%m-%dT%H:%M:%S')
        
        logger.info(f"Date range for {job.date_range}: {start_str} to {end_str}")
        
        return start_str, end_str
    
    def get_patients_in_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get unique patients with appointments in date range"""
        try:
            return self.client.get_patients_with_appointments_in_range(
                start_date, 
                end_date
            )
        except Exception as e:
            logger.error(f"Error fetching patients: {e}")
            return []
    
    def process_patients_batch(
        self, 
        patient_details: List[Dict], 
        job: AnalyticsJob
    ):
        """Process patients in batches with rate limiting"""
        batch_size = min(10, self.rate_limits.get('batch_size', 10))
        delay_between_patients = self.rate_limits.get('recommended_delay', 0.5)
        delay_between_batches = 30  # Normal pause between batches
        
        processed = 0
        failed = 0
        test_results = []
        
        # Clear existing patient records only if NOT test mode
        if not job.is_test_mode:
            Patient.objects.all().delete()
            logger.info("Cleared existing patient records")
        else:
            logger.info("[TEST MODE] Skipping patient record clearing")
        
        for i in range(0, len(patient_details), batch_size):
            # Check for cancellation before each batch
            job.refresh_from_db()
            if job.cancel_requested:
                logger.info(f"Job {job.id} cancelled by user")
                break
            
            batch = patient_details[i:i + batch_size]
            
            for patient_info in batch:
                # Check cancellation before EACH patient (more responsive)
                job.refresh_from_db()
                if job.cancel_requested:
                    logger.info(f"Job {job.id} cancelled by user (mid-batch)")
                    break
                    
                patient_id = patient_info['patient_id']
                patient_name = patient_info.get('name', f'Patient {patient_id}')
                
                try:
                    # Process single patient with test mode flag
                    success = self.process_single_patient(
                        patient_id, 
                        patient_name,
                        job.preset,
                        is_test_mode=job.is_test_mode
                    )
                    
                    if success:
                        processed += 1
                        job.processed_patient_ids.append(patient_id)
                        if job.is_test_mode:
                            test_results.append({
                                'id': patient_id,
                                'name': patient_name,
                                'status': 'success'
                            })
                    else:
                        failed += 1
                        job.failed_patient_ids.append({
                            'id': patient_id,
                            'name': patient_name,
                            'error': 'Processing failed'
                        })
                        if job.is_test_mode:
                            test_results.append({
                                'id': patient_id,
                                'name': patient_name,
                                'status': 'failed'
                            })
                    
                except Exception as e:
                    logger.error(f"Error processing {patient_name}: {e}")
                    failed += 1
                    job.failed_patient_ids.append({
                        'id': patient_id,
                        'name': patient_name,
                        'error': str(e)
                    })
                    if job.is_test_mode:
                        test_results.append({
                            'id': patient_id,
                            'name': patient_name,
                            'status': 'error',
                            'error': str(e)
                        })
                
                # Update job progress
                job.patients_processed = processed
                job.patients_failed = failed
                if job.is_test_mode:
                    job.test_results = {'patients': test_results}
                job.save()
                
                # Rate limiting between patients
                time.sleep(delay_between_patients)
                
                # If cancellation requested, use shorter delay
                if job.cancel_requested:
                    break
            
            # If cancellation requested, exit immediately
            if job.cancel_requested:
                break
                
            # Pause between batches (shorter if cancellation pending)
            if i + batch_size < len(patient_details):
                if job.cancel_requested:
                    logger.info(f"Cancellation requested, exiting...")
                    break
                else:
                    logger.info(f"Processed {processed}/{len(patient_details)} patients. Pausing...")
                    time.sleep(delay_between_batches)
    
    def process_single_patient(
        self, 
        patient_id: str, 
        patient_name: str,
        config: ScoringConfiguration,
        is_test_mode: bool = False
    ) -> bool:
        """Process a single patient and update their rating"""
        try:
            # Get patient data
            patients = self.client.get_patients(filters={'id': patient_id})
            
            if not patients:
                logger.warning(f"No patient found for ID: {patient_id}")
                return False
            
            raw_patient = patients[0]
            normalized_patient = self.normalizer.normalize_patient(raw_patient)
            
            # Get appointments, invoices, referrals
            appointments = self.client.get_appointments(patient_id)
            invoices = self.client.get_invoices(patient_id)
            referral_data = self.client.get_referrals(patient_id)
            
            # Prepare data for behavioral processor
            patient_data = {
                'id': patient_id,
                'date_of_birth': normalized_patient['date_of_birth'],
                'appointments': appointments,
                'invoices': invoices,
                'referrals': referral_data.get('referred_patient_ids', []) 
                            if isinstance(referral_data, dict) else []
            }
            
            # Process behavior
            result = self.processor.process_patient_behavior(
                patient_data, 
                config, 
                self.settings
            )
            result['patient_name'] = patient_name
            
            # Save to database
            patient_obj, created = Patient.objects.update_or_create(
                cliniko_patient_id=patient_id,
                defaults={
                    'patient_name': patient_name,
                    'total_score': result['total_score'],
                    'calculated_rating': result['letter_grade'],
                    'last_calculated': timezone.now()
                }
            )
            
            logger.info(
                f"{'[TEST MODE] ' if is_test_mode else ''}"
                f"Patient: {patient_name}, "
                f"Score: {result['total_score']}, "
                f"Rating: {result['letter_grade']}"
            )
            
            # Update appointment notes in Cliniko (skip if test mode)
            if not is_test_mode:
                rating_text = f"Rated {result['letter_grade']}"
                update_result = self.client.update_patient_appointment_notes(
                    patient_id, 
                    rating_text
                )
                
                if update_result:
                    logger.info(f"Successfully updated notes for {patient_name}")
                    return True
                else:
                    logger.error(f"Failed to update notes for {patient_name}")
                    return False
            else:
                logger.info(f"[TEST MODE] Would update notes for {patient_name} with rating {result['letter_grade']}")
                return True
                
        except Exception as e:
            logger.error(f"Error processing patient {patient_id}: {e}")
            return False
