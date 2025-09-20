"""
Setup script to securely store Facebook app token
"""

import os
from config.secrets import SecretManager

def setup_facebook_token():
    """Setup Facebook app token in the secret management system"""
    
    # Your Facebook app token
    app_token = "5857679854344905|ll5MIrsnV0lBA4SxwsI83Ujc4YQ"
    
    # Use file-based secret storage for persistence
    secret_manager = SecretManager(backend="file")
    
    # Store the token securely
    success = secret_manager.set_secret("FACEBOOK_APP_TOKEN", app_token)
    
    if success:
        print("✅ Facebook app token stored successfully in encrypted file")
        
        # Verify it was stored
        retrieved_token = secret_manager.get_secret("FACEBOOK_APP_TOKEN")
        if retrieved_token == app_token:
            print("✅ Token verification successful")
        else:
            print("❌ Token verification failed")
    else:
        print("❌ Failed to store Facebook app token")
    
    # Also set API version
    api_version_success = secret_manager.set_secret("FACEBOOK_API_VERSION", "v18.0")
    if api_version_success:
        print("✅ Facebook API version stored successfully in encrypted file")
    else:
        print("❌ Failed to store Facebook API version")
    
    # Set environment variable to use file backend
    os.environ["SECRETS_BACKEND"] = "file"
    print("✅ Secret backend configured to use encrypted file storage")

if __name__ == "__main__":
    setup_facebook_token()
