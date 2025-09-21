#!/usr/bin/env python3
"""
Facebook API Token Setup Script for Tunisia Intelligence

This script helps you set up the Facebook API token required for
Facebook page monitoring and data extraction.

Usage:
    python setup_facebook_api_token.py
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_banner():
    """Print setup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    Facebook API Token Setup                                  ║
║                    Tunisia Intelligence System                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_existing_token():
    """Check if Facebook token is already configured."""
    token = os.getenv('FACEBOOK_APP_TOKEN')
    if token and token != 'your_facebook_app_token_here':
        print(f"✅ Facebook token is already configured: {token[:20]}...")
        return True
    else:
        print("❌ Facebook token is not configured")
        return False

def get_env_file_path():
    """Get the path to the .env file."""
    env_file = Path('.env')
    if not env_file.exists():
        # Create .env from template
        template_file = Path('.env.unified_control_example')
        if template_file.exists():
            print("📋 Creating .env file from template...")
            with open(template_file, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created from template")
        else:
            print("❌ No .env template found")
            return None
    return env_file

def update_env_file(token):
    """Update the .env file with the Facebook token."""
    env_file = get_env_file_path()
    if not env_file:
        return False
    
    try:
        # Read current content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add the Facebook token
        token_updated = False
        for i, line in enumerate(lines):
            if line.startswith('FACEBOOK_APP_TOKEN='):
                lines[i] = f'FACEBOOK_APP_TOKEN={token}\n'
                token_updated = True
                break
        
        if not token_updated:
            lines.append(f'FACEBOOK_APP_TOKEN={token}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print("✅ Facebook token updated in .env file")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def create_facebook_app_instructions():
    """Display instructions for creating a Facebook app."""
    instructions = """
🔧 HOW TO GET A FACEBOOK API TOKEN:

1. **Go to Facebook Developers Console:**
   https://developers.facebook.com/

2. **Create a New App:**
   - Click "Create App"
   - Choose "Business" as app type
   - Fill in app details (name, email, etc.)

3. **Add Facebook Login Product:**
   - In your app dashboard, click "Add Product"
   - Find "Facebook Login" and click "Set Up"

4. **Get Your App Token:**
   - Go to Tools > Graph API Explorer
   - Select your app from the dropdown
   - Click "Generate Access Token"
   - Choose "Get App Token"
   - Copy the generated token

5. **Set Permissions (if needed):**
   - pages_read_engagement
   - pages_show_list
   - public_profile

6. **For Production (Optional):**
   - Submit your app for review if you need advanced permissions
   - For basic page monitoring, app token should be sufficient

📋 ALTERNATIVE - Use Page Access Token:
   - Go to your Facebook page
   - Settings > Page Access Tokens
   - Generate a token for your page
   - This works for single page monitoring

⚠️ IMPORTANT NOTES:
   - Keep your token secure and never share it publicly
   - Tokens may expire, so you might need to regenerate them
   - Test your token with Facebook's Graph API Explorer first
"""
    print(instructions)

def test_facebook_token(token):
    """Test if the Facebook token works."""
    try:
        import requests
        
        # Test the token with a simple API call
        url = "https://graph.facebook.com/me"
        params = {
            'access_token': token,
            'fields': 'id,name'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token is valid! App/Page: {data.get('name', 'Unknown')}")
            return True
        else:
            error_data = response.json()
            print(f"❌ Token test failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            return False
            
    except ImportError:
        print("⚠️ Cannot test token - requests library not available")
        print("   Install with: pip install requests")
        return None
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def main():
    """Main setup function."""
    print_banner()
    
    print("🔍 Checking current Facebook API token configuration...")
    
    if check_existing_token():
        choice = input("\nDo you want to update the existing token? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            print("✅ Keeping existing token configuration")
            return
    
    print("\n" + "="*70)
    create_facebook_app_instructions()
    print("="*70)
    
    # Get token from user
    print("\n🔑 Enter your Facebook API token:")
    print("   (Paste your token here - it will be saved securely)")
    
    token = input("Facebook Token: ").strip()
    
    if not token:
        print("❌ No token provided. Setup cancelled.")
        return
    
    if token == 'your_facebook_app_token_here':
        print("❌ Please provide a real Facebook token, not the placeholder.")
        return
    
    # Test the token
    print("\n🧪 Testing Facebook token...")
    test_result = test_facebook_token(token)
    
    if test_result is False:
        choice = input("\nToken test failed. Do you still want to save it? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            print("❌ Setup cancelled.")
            return
    
    # Update .env file
    print("\n💾 Saving token to .env file...")
    if update_env_file(token):
        print("\n🎉 Facebook API token setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Restart your dashboard: python launch_dashboard.py")
        print("   2. Test the Facebook pipeline from the dashboard")
        print("   3. Monitor Facebook pages for Tunisian government content")
        
        print(f"\n🔒 Your token is saved securely in the .env file")
        print(f"   Token preview: {token[:20]}...")
        
    else:
        print("❌ Failed to save token. Please check file permissions.")

if __name__ == "__main__":
    main()
