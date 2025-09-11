print('🔧 FIXING INSERTION WITH PROPER INDENTATION...')
print('='*70)

# Read the current views.py
with open('patient_rating/views.py', 'r') as f:
    content = f.read()

# Create a backup first
with open('patient_rating/views.py.pre_fix', 'w') as f:
    f.write(content)

print('✅ Created backup: views.py.pre_fix')

# Find a safer insertion point - look for the end of add_spend_bracket
import re

# Look for the complete add_spend_bracket block ending
safer_pattern = r'(elif action == \'add_spend_bracket\'.*?return JsonResponse${[^}]+}$)(.*?)(except)'

match = re.search(safer_pattern, content, re.DOTALL)

if match:
    print('✅ Found safer insertion point after add_spend_bracket')
    
    before_except = match.group(1)
    whitespace = match.group(2)
    except_clause = match.group(3)
    
    # Create the missing handlers with proper indentation
    missing_handlers = '''
            elif action == 'update_cancellations_points':
                points = request.POST.get('points_per_cancellation')
                if points:
                    active_config.points_per_cancellation = int(points)
                    active_config.save()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": f"Cancellations points updated to {points}"})

            elif action == 'update_dna_points':
                points = request.POST.get('points_per_dna')
                if points:
                    active_config.points_per_dna = int(points)
                    active_config.save()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": f"DNA points updated to {points}"})

            elif action == 'update_unpaid_invoices_points':
                points = request.POST.get('points_per_unpaid_invoice')
                if points:
                    active_config.points_per_unpaid_invoice = int(points)
                    active_config.save()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": f"Unpaid invoices points updated to {points}"})

            elif action == 'update_weights':
                # Update all weight fields
                weight_fields = ['appointments_booked_weight', 'age_demographics_weight', 'yearly_spend_weight', 'consecutive_attendance_weight', 'cancellations_weight', 'dna_weight', 'unpaid_invoices_weight', 'open_dna_invoice_weight']
                
                for field in weight_fields:
                    if field in request.POST:
                        setattr(active_config, field, int(request.POST.get(field, 0)))
                
                # Update points fields
                points_fields = ['points_per_consecutive_attendance', 'points_per_cancellation', 'points_per_dna', 'points_per_unpaid_invoice']
                
                for field in points_fields:
                    if field in request.POST:
                        setattr(active_config, field, int(request.POST.get(field, 2)))
                
                active_config.save()
                
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": True, "message": "All weights updated successfully!"})
'''
    
    # Insert the handlers
    new_content = content.replace(
        before_except + whitespace + except_clause,
        before_except + missing_handlers + whitespace + except_clause
    )
    
    # Write and verify
    with open('patient_rating/views.py', 'w') as f:
        f.write(new_content)
    
    try:
        compile(new_content, 'patient_rating/views.py', 'exec')
        print('✅ ALL MISSING HANDLERS ADDED SUCCESSFULLY')
        print('✅ Python syntax is valid')
        
        print('\n📋 FIXED BACKEND PROCESSING:')
        print('   ✅ update_cancellations_points')
        print('   ✅ update_dna_points') 
        print('   ✅ update_unpaid_invoices_points')
        print('   ✅ update_weights (all 8 weight fields)')
        
        print('\n🔄 RESTART DJANGO AND TEST THE FIX')
        
    except SyntaxError as e:
        print(f'🚨 SYNTAX ERROR: {e}')
        with open('patient_rating/views.py.pre_fix', 'r') as f:
            original = f.read()
        with open('patient_rating/views.py', 'w') as f:
            f.write(original)
        print('🔧 RESTORED FROM BACKUP')
        
else:
    print('❌ Could not find add_spend_bracket insertion point')
    
    # Show what patterns we can find
    print('\n🔍 AVAILABLE PATTERNS:')
    if 'add_spend_bracket' in content:
        print('   ✅ add_spend_bracket found')
    if 'except' in content:
        print('   ✅ except clauses found')
    
    # Try simpler approach - find any except block after POST
    simple_pattern = r'(elif action == \'update_consecutive_points\'.*?return JsonResponse.*?\n)(.*?)(except)'
    simple_match = re.search(simple_pattern, content, re.DOTALL)
    
    if simple_match:
        print('   ✅ Found alternative insertion point after update_consecutive_points')
        print('   🔧 Using alternative approach...')
        
        # Use the alternative insertion point
        before_except = simple_match.group(1)
        whitespace = simple_match.group(2)
        except_clause = simple_match.group(3)
        
        # Same missing handlers code
        missing_handlers = '''
            elif action == 'update_cancellations_points':
                points = request.POST.get('points_per_cancellation')
                if points:
                    active_config.points_per_cancellation = int(points)
                    active_config.save()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": f"Cancellations points updated to {points}"})

            elif action == 'update_dna_points':
                points = request.POST.get('points_per_dna')
                if points:
                    active_config.points_per_dna = int(points)
                    active_config.save()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": f"DNA points updated to {points}"})

            elif action == 'update_unpaid_invoices_points':
                points = request.POST.get('points_per_unpaid_invoice')
                if points:
                    active_config.points_per_unpaid_invoice = int(points)
                    active_config.save()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True, "message": f"Unpaid invoices points updated to {points}"})

            elif action == 'update_weights':
                # Update all weight fields
                weight_fields = ['appointments_booked_weight', 'age_demographics_weight', 'yearly_spend_weight', 'consecutive_attendance_weight', 'cancellations_weight', 'dna_weight', 'unpaid_invoices_weight', 'open_dna_invoice_weight']
                
                for field in weight_fields:
                    if field in request.POST:
                        setattr(active_config, field, int(request.POST.get(field, 0)))
                
                # Update points fields  
                points_fields = ['points_per_consecutive_attendance', 'points_per_cancellation', 'points_per_dna', 'points_per_unpaid_invoice']
                
                for field in points_fields:
                    if field in request.POST:
                        setattr(active_config, field, int(request.POST.get(field, 2)))
                
                active_config.save()
                
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": True, "message": "All weights updated successfully!"})
'''
        
        # Insert using alternative approach
        new_content = content.replace(
            before_except + whitespace + except_clause,
            before_except + missing_handlers + whitespace + except_clause
        )
        
        # Write and verify
        with open('patient_rating/views.py', 'w') as f:
            f.write(new_content)
        
        try:
            compile(new_content, 'patient_rating/views.py', 'exec')
            print('✅ ALTERNATIVE INSERTION SUCCESSFUL')
            print('✅ Python syntax is valid')
            print('\n📋 ALL MISSING HANDLERS ADDED')
        except SyntaxError as e:
            print(f'🚨 SYNTAX ERROR: {e}')
            with open('patient_rating/views.py.pre_fix', 'r') as f:
                original = f.read()
            with open('patient_rating/views.py', 'w') as f:
                f.write(original)
            print('🔧 RESTORED FROM BACKUP')
