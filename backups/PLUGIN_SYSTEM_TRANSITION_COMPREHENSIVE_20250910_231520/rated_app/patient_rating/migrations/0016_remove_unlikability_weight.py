# Generated migration to remove unlikability_weight field
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('patient_rating', '0015_add_referrer_score_fields'),  # Latest migration
    ]

    operations = [
        migrations.RemoveField(
            model_name='scoringconfiguration',
            name='unlikability_weight',
        ),
    ]
