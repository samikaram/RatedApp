from django.db import migrations, models
from django.core.validators import MinValueValidator, MaxValueValidator

class Migration(migrations.Migration):

    dependencies = [
        ('patient_rating', '0011_add_spend_bracket_model'),  # Update this to your latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name='scoringconfiguration',
            name='points_per_consecutive_attendance',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='scoringconfiguration',
            name='points_per_cancellation',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='scoringconfiguration',
            name='points_per_dna',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='scoringconfiguration',
            name='points_per_unpaid_invoice',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]),
        ),
    ]
