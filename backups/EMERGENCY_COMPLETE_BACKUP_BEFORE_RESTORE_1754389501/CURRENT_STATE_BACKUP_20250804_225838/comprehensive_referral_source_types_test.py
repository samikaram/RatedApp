#!/usr/bin/env python3
"""
REFERRER SCORE TEST - COMPREHENSIVE REFERRAL SOURCE TYPES ANALYSIS
Testing GET /referral_source_types endpoint for complete referral system structure
Following official Cliniko List Referral Source Types documentation
Examining all referral source types and their referrers fields
"""

import requests
import json
import base64
from datetime import datetime
import pytz
import time

# ✅ CORRECT API KEY - July 3, 2025
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Known IDs
BRONWYN_PATIENT_ID = "1707655488738428562"
SAMI_PATIENT_ID = "1104221"

def get_auth_header(api_key):
    """Create proper Cliniko API authentication header"""
    credentials = f"{api_key}:"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"

def get_all_referral_source_types():
    """Get ALL referral source types using the List endpoint"""
    print("🔍 STEP 1: GET ALL REFERRAL SOURCE TYPES")
    print("="*70)
    print(f"✅ Endpoint: GET /referral_source_types")
    print(f"✅ Following: Official Cliniko List Referral Source Types documentation")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    try:
        # Get all referral source types
        response = requests.get(
            f"{BASE_URL}/referral_source_types",
            headers=headers
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Successfully retrieved referral source types")
            print(f"\n📋 COMPLETE API RESPONSE:")
            print(json.dumps(data, indent=2))
            
            # Extract referral source types
            referral_types = data.get('referral_source_types', [])
            
            print(f"\n📊 FOUND {len(referral_types)} REFERRAL SOURCE TYPES:")
            
            types_with_referrers = []
            
            for i, ref_type in enumerate(referral_types):
                print(f"\n📋 TYPE {i+1}:")
                print(f"   ID: {ref_type.get('id')}")
                print(f"   Name: {ref_type.get('name')}")
                print(f"   Referrer Type: {ref_type.get('referrer_type')}")
                print(f"   Created: {ref_type.get('created_at')}")
                print(f"   Updated: {ref_type.get('updated_at')}")
                print(f"   Archived: {ref_type.get('archived_at')}")
                
                # Check for referrers field
                referrers = ref_type.get('referrers')
                if referrers:
                    print(f"   🎯 REFERRERS FIELD FOUND!")
                    print(f"      Type: {type(referrers)}")
                    print(f"      Content: {referrers}")
                    
                    if isinstance(referrers, dict):
                        referrers_links = referrers.get('links', {})
                        if referrers_links:
                            print(f"      Links: {referrers_links}")
                            types_with_referrers.append({
                                'id': ref_type.get('id'),
                                'name': ref_type.get('name'),
                                'referrer_type': ref_type.get('referrer_type'),
                                'referrers_links': referrers_links
                            })
                else:
                    print(f"   ⚠️ No referrers field")
                
                # Check for subcategories
                subcategories = ref_type.get('subcategories')
                if subcategories:
                    print(f"   📋 Subcategories: {subcategories}")
                    
                # Check for links
                links = ref_type.get('links', {})
                if links:
                    print(f"   🔗 Links: {links}")
                    
            return referral_types, types_with_referrers
            
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return [], []
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return [], []

def test_referral_source_types_filtering():
    """Test filtering capabilities on referral source types endpoint"""
    print(f"\n🔍 STEP 2: TEST REFERRAL SOURCE TYPES FILTERING")
    print("="*70)
    print(f"✅ Testing documented filters: archived_at, created_at, id, updated_at")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    # Test different filters from documentation
    test_filters = [
        ('archived_at', '!?'),  # Not archived
        ('id', '37606'),        # Patient referral source type
        ('created_at', '>2014-01-01T00:00:00Z'),  # After 2014
    ]
    
    successful_filters = []
    
    for filter_name, filter_value in test_filters:
        try:
            print(f"\n📡 Testing filter: {filter_name}:{filter_value}")
            
            filter_params = {
                'q[]': f'{filter_name}:{filter_value}'
            }
            
            response = requests.get(
                f"{BASE_URL}/referral_source_types",
                headers=headers,
                params=filter_params
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                types = data.get('referral_source_types', [])
                print(f"✅ SUCCESS: Found {len(types)} types with {filter_name}:{filter_value}")
                
                if types:
                    successful_filters.append((filter_name, filter_value, len(types)))
                    
                    # Show results
                    for ref_type in types:
                        print(f"   📋 {ref_type.get('name')} (ID: {ref_type.get('id')})")
                        
            elif response.status_code == 400:
                error_msg = response.json().get('message', response.text)
                print(f"❌ ERROR 400: {error_msg}")
            else:
                print(f"❌ ERROR {response.status_code}: {response.text}")
                
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            
    return successful_filters

def test_all_referrers_endpoints(types_with_referrers):
    """Test all referrers endpoints found in referral source types"""
    print(f"\n🔍 STEP 3: TEST ALL REFERRERS ENDPOINTS")
    print("="*70)
    print(f"✅ Testing {len(types_with_referrers)} referral source types with referrers links")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    referrer_data = []
    
    for ref_type in types_with_referrers:
        try:
            print(f"\n📋 TESTING: {ref_type['name']} (ID: {ref_type['id']})")
            print(f"   Referrer Type: {ref_type['referrer_type']}")
            
            referrers_links = ref_type['referrers_links']
            referrers_url = referrers_links.get('self')
            
            if referrers_url:
                print(f"   🔗 Referrers URL: {referrers_url}")
                
                # Test the referrers endpoint
                response = requests.get(referrers_url, headers=headers)
                print(f"   📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ SUCCESS: Retrieved referrers data")
                    
                    # Analyze the structure
                    print(f"   📋 Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Look for referrers list
                    referrers_list = []
                    if isinstance(data, dict):
                        # Check common keys for referrers data
                        for key in ['patients', 'contacts', 'practitioners', 'referrers', 'data']:
                            if key in data and isinstance(data[key], list):
                                referrers_list = data[key]
                                print(f"   🎯 FOUND REFERRERS LIST: {len(referrers_list)} items in '{key}' field")
                                break
                    
                    if referrers_list:
                        # Search for Bronwyn and Sami in referrers
                        bronwyn_found = False
                        sami_found = False
                        
                        for referrer in referrers_list[:10]:  # Check first 10
                            if isinstance(referrer, dict):
                                referrer_id = str(referrer.get('id', ''))
                                name = f"{referrer.get('first_name', '')} {referrer.get('last_name', '')}"
                                
                                if referrer_id == BRONWYN_PATIENT_ID:
                                    bronwyn_found = True
                                    print(f"   🎯 BRONWYN FOUND: {name}")
                                    
                                if referrer_id == SAMI_PATIENT_ID:
                                    sami_found = True
                                    print(f"   🎯 SAMI FOUND: {name}")
                                    
                        referrer_data.append({
                            'type_name': ref_type['name'],
                            'type_id': ref_type['id'],
                            'referrer_type': ref_type['referrer_type'],
                            'referrers_count': len(referrers_list),
                            'bronwyn_found': bronwyn_found,
                            'sami_found': sami_found,
                            'endpoint_url': referrers_url
                        })
                        
                    else:
                        print(f"   ⚠️ No referrers list found in response")
                        
                elif response.status_code == 404:
                    print(f"   ❌ ERROR 404: Referrers endpoint not found")
                else:
                    print(f"   ❌ ERROR {response.status_code}: {response.text}")
                    
            else:
                print(f"   ⚠️ No referrers URL found")
                
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            
    return referrer_data

def main():
    """Main comprehensive test function"""
    print("🚀 STARTING COMPREHENSIVE REFERRAL SOURCE TYPES ANALYSIS")
    print("📋 Following official Cliniko List Referral Source Types documentation")
    print(f"📅 Test Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🎯 REFERRER SCORE TEST - COMPLETE SYSTEM ANALYSIS")
    print("="*80)
    print("✅ APPROACH: Analyze ALL referral source types and their referrers endpoints")
    print("✅ STEP 1: Get all referral source types using List endpoint")
    print("✅ STEP 2: Test filtering capabilities on referral source types")
    print("✅ STEP 3: Test all referrers endpoints found in different types")
    print("✅ GOAL: Find efficient way to calculate referrer scores for any patient")
    print("="*80)
    
    # Step 1: Get all referral source types
    all_types, types_with_referrers = get_all_referral_source_types()
    
    # Step 2: Test filtering capabilities
    successful_filters = test_referral_source_types_filtering()
    
    # Step 3: Test all referrers endpoints
    referrer_data = test_all_referrers_endpoints(types_with_referrers)
    
    # Final results
    print(f"\n🎯 FINAL COMPREHENSIVE RESULTS:")
    print("="*80)
    
    print(f"📊 REFERRAL SOURCE TYPES FOUND: {len(all_types)}")
    print(f"📊 TYPES WITH REFERRERS FIELD: {len(types_with_referrers)}")
    print(f"📊 SUCCESSFUL FILTERS: {len(successful_filters)}")
    print(f"📊 REFERRER ENDPOINTS TESTED: {len(referrer_data)}")
    
    # Show referrer data results
    bronwyn_referrer_score = 0
    sami_referrer_score = 0
    working_endpoints = []
    
    for data in referrer_data:
        print(f"\n📋 {data['type_name']} ({data['referrer_type']}):")
        print(f"   Referrers Count: {data['referrers_count']}")
        print(f"   Bronwyn Found: {data['bronwyn_found']}")
        print(f"   Sami Found: {data['sami_found']}")
        print(f"   Endpoint: {data['endpoint_url']}")
        
        if data['referrers_count'] > 0:
            working_endpoints.append(data)
            
    if working_endpoints:
        print(f"\n✅ WORKING REFERRER ENDPOINTS: {len(working_endpoints)}")
        print(f"🎉 SUCCESS: Found functional referrer data structure!")
        
        # Calculate referrer scores if patients found
        for data in referrer_data:
            if data['bronwyn_found']:
                bronwyn_referrer_score += 1
            if data['sami_found']:
                sami_referrer_score += 1
                
        print(f"\n🎯 REFERRER SCORES:")
        print(f"   Bronwyn: {bronwyn_referrer_score}")
        print(f"   Sami: {sami_referrer_score}")
        
    else:
        print(f"\n⚠️ NO WORKING REFERRER ENDPOINTS FOUND")
        print(f"🔍 May need alternative approach")
    
    # Save comprehensive results
    results = {
        'extraction_date': datetime.now(AEST).isoformat(),
        'all_referral_source_types': all_types,
        'types_with_referrers': types_with_referrers,
        'successful_filters': successful_filters,
        'referrer_data': referrer_data,
        'working_endpoints': working_endpoints,
        'bronwyn_referrer_score': bronwyn_referrer_score,
        'sami_referrer_score': sami_referrer_score,
        'method': 'Comprehensive referral source types analysis'
    }
    
    filename = f"comprehensive_referral_source_types_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"🎉 COMPREHENSIVE REFERRAL SOURCE TYPES ANALYSIS COMPLETE!")
    
    # Summary recommendations
    print(f"\n📋 SUMMARY & RECOMMENDATIONS:")
    print("="*80)
    
    if working_endpoints:
        print(f"✅ BREAKTHROUGH: Found {len(working_endpoints)} working referrer endpoints!")
        print(f"✅ This means referrer scores CAN be calculated efficiently!")
        print(f"✅ Next step: Implement referrer score calculation using working endpoints")
        
        for endpoint in working_endpoints:
            print(f"   📋 Use: {endpoint['type_name']} endpoint for {endpoint['referrer_type']} referrals")
            
    else:
        print(f"⚠️ NO WORKING REFERRER ENDPOINTS FOUND")
        print(f"💡 RECOMMENDATION: Remove referrer score from 11-category system")
        print(f"💡 ALTERNATIVE: Implement brute-force patient search (slow but functional)")
        
    print(f"\n🎯 NEXT ACTIONS:")
    if working_endpoints:
        print(f"1. ✅ Implement referrer score calculation using discovered endpoints")
        print(f"2. ✅ Test referrer score calculation for multiple patients")
        print(f"3. ✅ Integrate into main patient behavior extraction system")
        print(f"4. ✅ Finalize 11-category patient rating system")
    else:
        print(f"1. 🔄 Consider removing referrer score (recommended)")
        print(f"2. 🔄 OR implement brute-force approach (slow)")
        print(f"3. ✅ Finalize 10-category patient rating system")
        print(f"4. ✅ Focus on other behavior categories that work efficiently")

if __name__ == "__main__":
    main()
