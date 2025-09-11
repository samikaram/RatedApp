#!/usr/bin/env python3
"""
Phase 1 Enhancement: Enhance Delete Preset Response Handling
Safe replacement of lines 645-671 in unified_dashboard.html
"""

def enhance_delete_preset_response():
    template_path = "./templates/patient_rating/unified_dashboard.html"
    
    print("🚀 PHASE 1: ENHANCING DELETE PRESET RESPONSE HANDLING")
    print("="*60)
    
    # Read the current file
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"📄 File loaded: {len(content)} characters")
    except FileNotFoundError:
        print(f"❌ File not found: {template_path}")
        return False
    
    # Define the old code block to replace
    old_code = """                console.log('Preset deleted successfully:', data);
                alert('Preset deleted successfully');

                // Remove deleted preset from dropdown
                const dropdown = document.getElementById('preset-dropdown');
                const deletedPresetId = presetId;

                // Find and remove the option
                for (let i = 0; i < dropdown.options.length; i++) {
                    if (dropdown.options[i].value === deletedPresetId) {
                        dropdown.remove(i);
                        console.log('Removed preset option:', deletedPresetId);
                        break;
                    }
                }

                // Handle dropdown selection after deletion
                if (dropdown.options.length > 0) {
                    dropdown.selectedIndex = 0;  // Select first remaining preset
                    console.log('Selected first remaining preset');
                } else {
                    console.log('No presets remaining in dropdown');
                    // Could add logic to create default preset or disable UI
                }"""
    
    # Define the new enhanced code
    new_code = """                console.log('Preset deleted successfully:', data);
                
                // 🆕 PHASE 1: Enhanced response detection
                const wasActivePresetDeleted = data.was_active_preset_deleted || false;
                const deletedPresetName = data.deleted_preset_name || 'Unknown';
                const fallbackPreset = data.fallback_preset || null;

                console.log('🔍 Enhanced delete response:', {
                    wasActivePresetDeleted,
                    deletedPresetName,
                    fallbackPreset
                });

                // 🆕 PHASE 1: Enhanced success message
                if (wasActivePresetDeleted && fallbackPreset) {
                    alert(`Preset "${deletedPresetName}" deleted successfully.\\n\\nNote: This was your applied preset. The system has automatically selected "${fallbackPreset.name}" as the new active preset.`);
                } else {
                    alert(`Preset "${deletedPresetName}" deleted successfully`);
                }

                // Remove deleted preset from dropdown (existing logic enhanced)
                const dropdown = document.getElementById('preset-dropdown');
                const deletedPresetId = presetId;

                // Find and remove the option
                for (let i = 0; i < dropdown.options.length; i++) {
                    if (dropdown.options[i].value === deletedPresetId) {
                        dropdown.remove(i);
                        console.log('Removed preset option:', deletedPresetId);
                        break;
                    }
                }

                // 🆕 PHASE 1: Enhanced dropdown selection
                if (fallbackPreset) {
                    // Select the fallback preset in dropdown
                    for (let i = 0; i < dropdown.options.length; i++) {
                        if (dropdown.options[i].value == fallbackPreset.id) {
                            dropdown.selectedIndex = i;
                            console.log('🎯 Selected fallback preset in dropdown:', fallbackPreset.name);
                            break;
                        }
                    }
                } else if (dropdown.options.length > 0) {
                    dropdown.selectedIndex = 0;  // Select first remaining preset
                    console.log('Selected first remaining preset');
                } else {
                    console.log('No presets remaining in dropdown');
                    // Could add logic to create default preset or disable UI
                }

                // 🆕 PHASE 1: Prepare for Phase 2 (localStorage cleanup)
                if (wasActivePresetDeleted) {
                    console.log('🧹 Applied preset was deleted - localStorage cleanup needed in Phase 2');
                }

                // 🆕 PHASE 1: Prepare for Phase 3 (auto-apply fallback)
                if (wasActivePresetDeleted && fallbackPreset) {
                    console.log('🎛️ Auto-apply fallback preset needed in Phase 3:', fallbackPreset.name);
                }"""
    
    # Check if old code exists
    if old_code not in content:
        print("❌ Target code block not found in file")
        print("🔍 Searching for partial matches...")
        
        # Try to find the start line
        if "console.log('Preset deleted successfully:', data);" in content:
            print("✅ Found start line - but full block doesn't match")
            print("📝 Manual replacement may be needed")
        else:
            print("❌ Start line not found - file may have been modified")
        return False
    
    # Perform the replacement
    new_content = content.replace(old_code, new_code)
    
    # Verify the replacement worked
    if new_content == content:
        print("❌ No replacement made - content unchanged")
        return False
    
    # Write the enhanced file
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ File successfully updated!")
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return False
    
    # Verification
    print("\n🔍 VERIFICATION:")
    verification_markers = [
        "🆕 PHASE 1: Enhanced response detection",
        "wasActivePresetDeleted",
        "fallbackPreset",
        "🎯 Selected fallback preset in dropdown"
    ]
    
    for marker in verification_markers:
        if marker in new_content:
            print(f"✅ Found: {marker}")
        else:
            print(f"❌ Missing: {marker}")
    
    print(f"\n📊 Original size: {len(content)} characters")
    print(f"📊 Enhanced size: {len(new_content)} characters")
    print(f"📊 Size change: {len(new_content) - len(content):+d} characters")
    
    print("\n🎯 PHASE 1 ENHANCEMENT COMPLETE!")
    print("Next steps:")
    print("1. python manage.py runserver")
    print("2. Open http://127.0.0.1:8000/patients/dashboard/")
    print("3. Open browser console (F12) and test delete preset")
    print("4. Look for enhanced logs and improved messages")
    
    return True

if __name__ == "__main__":
    success = enhance_delete_preset_response()
    if not success:
        print("\n❌ ENHANCEMENT FAILED")
        print("💡 Try manual replacement or check file contents")
    else:
        print("\n✅ ENHANCEMENT SUCCESSFUL")
