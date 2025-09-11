print('🔧 ADDING MISSING SLIDER UPDATE JAVASCRIPT...')
print('='*70)

# Read the current template
with open('templates/patient_rating/unified_dashboard.html', 'r') as f:
    content = f.read()

# Create backup
with open('templates/patient_rating/unified_dashboard.html.pre_js_fix', 'w') as f:
    f.write(content)

print('✅ Created backup: unified_dashboard.html.pre_js_fix')

# Find the script section
import re
script_match = re.search(r'(<script>)(.*?)(</script>)', content, re.DOTALL)

if script_match:
    script_start = script_match.group(1)
    existing_js = script_match.group(2)
    script_end = script_match.group(3)
    
    # Add the missing slider update JavaScript
    slider_update_js = '''
    // Slider update functions for Update Weights button
    function updateHiddenInput(sliderId, hiddenId) {
        const slider = document.getElementById(sliderId);
        const hidden = document.getElementById(hiddenId);
        if (slider && hidden) {
            hidden.value = slider.value;
        }
    }
    
    // Initialize slider event listeners when page loads
    document.addEventListener('DOMContentLoaded', function() {
        // Simple weight sliders (Boolean triggers)
        const appointmentsSlider = document.getElementById('appointments-booked-weight');
        if (appointmentsSlider) {
            appointmentsSlider.addEventListener('input', function() {
                updateHiddenInput('appointments-booked-weight', 'appointments-booked-weight-hidden');
            });
        }
        
        const openDnaSlider = document.getElementById('open-dna-invoice-weight');
        if (openDnaSlider) {
            openDnaSlider.addEventListener('input', function() {
                updateHiddenInput('open-dna-invoice-weight', 'open-dna-invoice-weight-hidden');
            });
        }
        
        // Complex weight sliders (with points)
        const unpaidInvoicesSlider = document.getElementById('unpaid-invoices-weight');
        if (unpaidInvoicesSlider) {
            unpaidInvoicesSlider.addEventListener('input', function() {
                updateHiddenInput('unpaid-invoices-weight', 'unpaid-invoices-weight-hidden');
            });
        }
        
        // Add listeners for all other weight sliders
        const sliderMappings = [
            ['age-demographics-weight', 'age-demographics-weight-hidden'],
            ['yearly-spend-weight', 'yearly-spend-weight-hidden'],
            ['consecutive-attendance-weight', 'consecutive-attendance-weight-hidden'],
            ['cancellations-weight', 'cancellations-weight-hidden'],
            ['dna-weight', 'dna-weight-hidden']
        ];
        
        sliderMappings.forEach(function([sliderId, hiddenId]) {
            const slider = document.getElementById(sliderId);
            if (slider) {
                slider.addEventListener('input', function() {
                    updateHiddenInput(sliderId, hiddenId);
                });
            }
        });
        
        console.log('✅ All slider update listeners initialized');
    });
'''
    
    # Insert the new JavaScript before the existing JS
    new_js_content = slider_update_js + existing_js
    
    # Replace the script section
    new_content = content.replace(
        script_start + existing_js + script_end,
        script_start + new_js_content + script_end
    )
    
    # Write the updated file
    with open('templates/patient_rating/unified_dashboard.html', 'w') as f:
        f.write(new_content)
    
    print('✅ ADDED MISSING SLIDER UPDATE JAVASCRIPT')
    print('✅ All 8 weight sliders now have event listeners')
    
    print('\n📋 ADDED FUNCTIONALITY:')
    print('   ✅ appointments_booked_weight slider updates')
    print('   ✅ unpaid_invoices_weight slider updates') 
    print('   ✅ open_dna_invoice_weight slider updates')
    print('   ✅ All other weight sliders update')
    print('   ✅ Hidden form fields update when sliders move')
    
    print('\n🔄 RESTART DJANGO AND TEST:')
    print('   python manage.py runserver')
    
    print('\n📋 EXPECTED RESULTS:')
    print('   ✅ Move Unpaid Invoices slider → hidden field updates')
    print('   ✅ Move Open DNA Invoice slider → hidden field updates')
    print('   ✅ Click Update Weights button → saves current slider positions')
    print('   ✅ Refresh page → sliders stay at saved positions')
    
else:
    print('❌ Could not find script section')
