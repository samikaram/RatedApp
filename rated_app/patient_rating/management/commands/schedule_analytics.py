from django.core.management.base import BaseCommand
from django_cron import CronJobBase, Schedule
from patient_rating.models import AnalyticsJob


class AnalyticsCronJob(CronJobBase):
    """
    Cron job to check and run scheduled analytics
    """
    RUN_EVERY_MINS = 5  # Run every 5 minutes
    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'patient_rating.analytics_cron'
    
    def do(self):
        """Check for and run pending analytics jobs"""
        from django.core.management import call_command
        call_command('process_analytics')


class Command(BaseCommand):
    help = 'Manually trigger analytics cron job'
    
    def handle(self, *args, **options):
        """Manually run the analytics cron job"""
        self.stdout.write('Manually triggering analytics cron job...')
        
        job = AnalyticsCronJob()
        job.do()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully triggered analytics cron job')
        )