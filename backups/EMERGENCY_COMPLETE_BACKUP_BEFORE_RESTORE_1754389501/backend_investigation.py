#!/usr/bin/env python3
"""
Backend Investigation: Why was_active_preset_deleted is always false
Investigate active preset detection logic in delete_preset view
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rated_app.settings')
django.setup()

from patient_rating.models import ScoringConfiguration

def investigate_backend_issue():
    print("🔍 BACKEND INVESTIGATION: ACTIVE PRESET DETECTION")
    print("="*60)
    
    # Check current database state
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
        return False
    
    # Check total presets
    total_presets = ScoringConfiguration.objects.count()
    active_presets = ScoringConfiguration.objects.filter(is_active=True).count()
    
    print(f"\n📈 PRESET STATISTICS:")
    print(f"   Total presets: {total_presets}")
    print(f"   Active presets: {active_presets}")
    
    if active_presets == 0:
        print("\n🚨 CRITICAL ISSUE: NO ACTIVE PRESET!")
        print("   The delete_preset logic checks for is_active=True")
        print("   But no preset is marked as active in the database")
        
        # Suggest fix
        print("\n💡 SUGGESTED FIX:")
        print("   1. Mark one preset as active")
        print("   2. Or fix the active preset detection logic")
        
        # Find a preset to make active
        first_preset = ScoringConfiguration.objects.first()
        if first_preset:
            print(f"\n🔧 RECOMMENDED ACTION:")
            print(f"   Make preset '{first_preset.name}' (ID: {first_preset.id}) active")
            return first_preset
    
    elif active_presets > 1:
        print(f"\n⚠️  WARNING: MULTIPLE ACTIVE PRESETS ({active_presets})")
        print("   Only one preset should be active at a time")
        
        active_list = ScoringConfiguration.objects.filter(is_active=True)
        for preset in active_list:
            print(f"   - {preset.name} (ID: {preset.id})")
    
    else:
        print(f"\n✅ ACTIVE PRESET STATE: CORRECT (1 active preset)")
    
    return active_preset

def fix_active_preset_issue():
    print("\n🔧 ACTIVE PRESET FIX OPTIONS:")
    print("="*40)
    
    active_preset = ScoringConfiguration.objects.filter(is_active=True).first()
    
    if not active_preset:
        print("🎯 OPTION 1: MAKE FIRST PRESET ACTIVE")
        first_preset = ScoringConfiguration.objects.first()
        if first_preset:
            print(f"   Preset to activate: {first_preset.name} (ID: {first_preset.id})")
            
            # Ask for confirmation (simulated)
            print(f"\n💡 TO FIX: Run this command in Django shell:")
            print(f"   preset = ScoringConfiguration.objects.get(id={first_preset.id})")
            print(f"   preset.is_active = True")
            print(f"   preset.save()")
            print(f"   print('✅ Made {first_preset.name} active')")
        else:
            print("❌ No presets found to activate")
    
    else:
        print("✅ Active preset already exists - investigating other issues...")
        
        # Check if localStorage and database are in sync
        print("\n🔍 POTENTIAL SYNC ISSUES:")
        print("   1. localStorage shows 'Test 14' as applied")
        print("   2. Database might have different active preset")
        print("   3. Apply button might not update is_active field")
        
        print(f"\n📋 CURRENT ACTIVE PRESET: {active_preset.name} (ID: {active_preset.id})")
        print("   Check if this matches what localStorage shows")

def simulate_delete_logic(preset_id):
    print(f"\n🧪 SIMULATING DELETE LOGIC FOR PRESET ID: {preset_id}")
    print("="*50)
    
    try:
        # Get the preset to delete
        preset = ScoringConfiguration.objects.get(id=preset_id)
        print(f"📋 PRESET TO DELETE: {preset.name} (ID: {preset.id})")
        print(f"   is_active: {preset.is_active}")
        
        # Check if it's active (this is the key logic)
        was_active = preset.is_active
        print(f"\n🔍 ACTIVE CHECK RESULT: was_active = {was_active}")
        
        if was_active:
            print("✅ This preset would be detected as active preset")
            
            # Find fallback
            fallback = ScoringConfiguration.objects.exclude(id=preset_id).first()
            if fallback:
                print(f"🎯 FALLBACK PRESET: {fallback.name} (ID: {fallback.id})")
            else:
                print("❌ NO FALLBACK PRESET AVAILABLE")
        else:
            print("❌ This preset would NOT be detected as active preset")
            print("   This explains why was_active_preset_deleted = false")
        
        return was_active
        
    except ScoringConfiguration.DoesNotExist:
        print(f"❌ PRESET ID {preset_id} NOT FOUND")
        return False

if __name__ == "__main__":
    print("🚀 STARTING BACKEND INVESTIGATION...")
    
    # Main investigation
    result = investigate_backend_issue()
    
    # Suggest fixes
    fix_active_preset_issue()
    
    # Simulate the delete logic for Test 14 (ID: 18)
    print("\n" + "="*60)
    simulate_delete_logic(18)  # Test 14 that was deleted
    
    print("\n🎯 INVESTIGATION COMPLETE!")
    print("\nKey findings will be shown above ☝️")
