import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rated_app.settings')
django.setup()

from patient_rating.models import ScoringConfiguration

print("🔍 BACKEND INVESTIGATION: ACTIVE PRESET DETECTION")
print("=" * 60)

# Check all presets
print("📊 CURRENT DATABASE STATE:")
presets = ScoringConfiguration.objects.all().order_by('id')
for preset in presets:
    status = "🟢 ACTIVE" if preset.is_active else "⚪ INACTIVE"
    print(f"   ID: {preset.id:2d} | {status} | Name: {preset.name}")

# Find active preset
active_preset = ScoringConfiguration.objects.filter(is_active=True).first()
if active_preset:
    print(f"\n🎯 ACTIVE PRESET FOUND:")
    print(f"   ID: {active_preset.id}")
    print(f"   Name: {active_preset.name}")
    print(f"   Active: {active_preset.is_active}")
else:
    print("\n❌ NO ACTIVE PRESET FOUND!")
    print("   This explains why was_active_preset_deleted is always false")

# Statistics
total_presets = ScoringConfiguration.objects.count()
active_presets = ScoringConfiguration.objects.filter(is_active=True).count()

print(f"\n📈 PRESET STATISTICS:")
print(f"   Total presets: {total_presets}")
print(f"   Active presets: {active_presets}")

# Simulate delete logic for Test 14 (ID: 18)
print(f"\n🧪 SIMULATING DELETE LOGIC FOR PRESET ID: 18")
print("=" * 50)

try:
    preset = ScoringConfiguration.objects.get(id=18)
    print(f"📋 PRESET TO DELETE: {preset.name} (ID: {preset.id})")
    print(f"   is_active: {preset.is_active}")
    
    was_active = preset.is_active
    print(f"\n🔍 ACTIVE CHECK RESULT: was_active = {was_active}")
    
    if was_active:
        print("✅ This preset would be detected as active preset")
        fallback = ScoringConfiguration.objects.exclude(id=18).first()
        if fallback:
            print(f"🎯 FALLBACK PRESET: {fallback.name} (ID: {fallback.id})")
        else:
            print("❌ NO FALLBACK PRESET AVAILABLE")
    else:
        print("❌ This preset would NOT be detected as active preset")
        print("   This explains why was_active_preset_deleted = false")
        
except ScoringConfiguration.DoesNotExist:
    print("❌ PRESET ID 18 NOT FOUND (already deleted)")

print("\n🎯 INVESTIGATION COMPLETE!")
