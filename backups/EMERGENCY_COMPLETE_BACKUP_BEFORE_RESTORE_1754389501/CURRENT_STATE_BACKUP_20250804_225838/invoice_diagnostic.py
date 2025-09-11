import requests
import json
from datetime import datetime
import pytz
import base64

# API Configuration
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Create headers
auth_string = f"{API_KEY}:"
encoded_auth = base64.b64encode(auth_string.encode()).decode()
headers = {
    'Authorization': f'Basic {encoded_auth}',
    'Accept': 'application/json',
    'User-Agent': 'Patient Behavior Rating System'
}

def main():
    print("🔍 INVOICE PAYMENT DIAGNOSTIC")
    print("="*50)
    
    # Get a few target invoices and examine their structure
    response = requests.get(f"{BASE_URL}/invoices", headers=headers, params={'per_page': 10})
    if response.status_code == 200:
        data = response.json()
        invoices = data.get('invoices', [])
        
        print(f"📋 Examining first 3 invoices:")
        for i, inv in enumerate(invoices[:3], 1):
            print(f"\n📄 INVOICE {i}:")
            print(f"   ID: {inv.get('id')}")
            print(f"   Total Amount: ${inv.get('total_amount', 0)}")
            print(f"   Outstanding Amount: ${inv.get('outstanding_amount', 'N/A')}")
            print(f"   Amount Paid: ${inv.get('amount_paid', 'N/A')}")
            print(f"   Status: {inv.get('status', 'N/A')}")
            print(f"   Payment Status: {inv.get('payment_status', 'N/A')}")
            print(f"   Created: {inv.get('created_at', 'N/A')}")
            
            # Show ALL available fields
            print(f"   📝 All fields: {list(inv.keys())}")
            
            # Calculate payment using different methods
            total = float(inv.get('total_amount', 0))
            outstanding = float(inv.get('outstanding_amount', total))
            paid = float(inv.get('amount_paid', 0))
            
            print(f"   🧮 Payment calculation:")
            print(f"      Method 1 (outstanding=0): ${total if outstanding <= 0.01 else 0:.2f}")
            print(f"      Method 2 (amount_paid): ${paid:.2f}")
            print(f"      Method 3 (total-outstanding): ${total - outstanding:.2f}")
    
    print(f"\n🎯 RECOMMENDATION:")
    print(f"Based on the field structure above, we can fix the payment logic!")

if __name__ == "__main__":
    main()

