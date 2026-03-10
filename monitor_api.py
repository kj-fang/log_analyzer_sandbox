import requests
import json
from configs.key import expertgpt_token

expert_api_key = expertgpt_token

def test_quota_endpoint(api_key):
    """Test the /v1/quota endpoint with an existing API key"""
    
    
    if not api_key:
        print("❌ No personal API key found in database")
        print("Please generate one from your profile page first")
        return False
    
    print(f"API Key: {api_key[:15]}...")
    print()
    
    url = "https://expertgpt.intel.com/v1/quota"
    
    # Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Testing /v1/quota endpoint...")
    print(f"URL: {url}")
    print()
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)

        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            quota_data = response.json()
            print("✅ SUCCESS! Quota endpoint is working perfectly!")
            print()
            print("📊 QUOTA SUMMARY:")
            print("=" * 50)
            
            summary = quota_data.get('quota_summary', {})
            print(f"📧 User: {quota_data.get('user', 'N/A')}")
            print(f"📈 Daily Usage: {summary.get('daily_usage', 0)} calls")
            print(f"🎯 Daily Limit: {summary.get('daily_limit', 0)} calls")
            print(f"⚡ Daily Remaining: {summary.get('daily_remaining', 0)} calls")
            print(f"🔄 Reset Time: {summary.get('reset_time', 'N/A')}")
            print()
            
            print("🤖 MODEL QUOTAS:")
            print("=" * 50)
            model_quotas = quota_data.get('model_quotas', {})
            
            for model, quota_info in model_quotas.items():
                quota_type = quota_info.get('quota_type', 'unknown')
                used = quota_info.get('used', 0)
                limit = quota_info.get('limit', 0)
                remaining = quota_info.get('remaining', 0)
                expires = quota_info.get('expires_at')
                
                # Status indicators
                if remaining > limit * 0.7:
                    status_icon = "🟢"  # Green - plenty remaining
                elif remaining > limit * 0.3:
                    status_icon = "🟡"  # Yellow - moderate usage
                elif remaining > 0:
                    status_icon = "🟠"  # Orange - high usage
                else:
                    status_icon = "🔴"  # Red - at limit
                
                custom_icon = " 🔥" if quota_type == 'custom' else ""
                
                print(f"{status_icon} {model}{custom_icon}")
                print(f"   📊 Used: {used}/{limit} calls ({quota_type})")
                print(f"   ⚡ Remaining: {remaining} calls")
                if expires:
                    print(f"   ⏰ Expires: {expires}")
                print()
            
            print(f"🎁 Custom Quotas Active: {quota_data.get('custom_quotas_count', 0)}")
            print(f"🕐 Last Updated: {quota_data.get('last_updated', 'N/A')}")
            
            # Show example curl command
            print("\n" + "=" * 60)
            print("🐚 EXAMPLE CURL COMMAND:")
            print("=" * 60)
            print(f"""curl -X GET \\
  "https://expertgpt.intel.com/v1/quota" \\
  -H "Authorization: Bearer {api_key}" \\
  -H "Content-Type: application/json\"""")
            
            return True
            
        else:
            print("❌ ERROR! Quota endpoint failed.")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR!")
        print("Check if you can access: https://expertgpt.intel.com")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 TESTING /v1/quota ENDPOINT")
    print("=" * 60)
    
    success = test_quota_endpoint(expert_api_key)
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        print("The /v1/quota endpoint is working correctly.")
        print("\n📋 WHAT THIS ENDPOINT PROVIDES:")
        print("• Daily usage and remaining calls")
        print("• Per-model quota information")
        print("• Custom quota details (if any)")
        print("• Quota reset times")
        print("• API-compatible format")
    else:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED!")
        print("Check the error messages above.")