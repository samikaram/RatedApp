#!/usr/bin/env python3
"""
Safe Frontend Fix: Add action parameter to Apply button
"""

def add_apply_button_action():
    print("🔧 ADDING ACTION PARAMETER TO APPLY BUTTON...")
    
    # Read current template
    with open('./templates/patient_rating/unified_dashboard.html', 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if 'formData.append(\'action\', \'apply_preset\')' in content:
        print("✅ Apply button already has action parameter - skipping")
        return True
    
    # Find the Apply button FormData line (line 1623)
    lines = content.split('\n')
    target_line = None
    
    for i, line in enumerate(lines):
        if 'const formData = new FormData(form);' in line and i > 1500:  # Apply button context
            target_line = i
            break
    
    if target_line is None:
        print("❌ Could not find Apply button FormData line")
        return False
    
    print(f"📍 Found Apply button FormData at line {target_line + 1}")
    
    # Insert action parameter after FormData line
    action_code = [
        "",
        "    // Add action parameter for backend handling",
        "    formData.append('action', 'apply_preset');",
        "    formData.append('preset_id', selectedValue);"
    ]
    
    # Insert the lines
    for i, code_line in enumerate(action_code):
        lines.insert(target_line + 1 + i, code_line)
    
    # Write back to file
    with open('./templates/patient_rating/unified_dashboard.html', 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ Frontend action parameter added successfully!")
    return True

if __name__ == "__main__":
    add_apply_button_action()
