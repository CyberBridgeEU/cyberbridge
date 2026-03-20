"""
Example Authentication Usage

This script demonstrates how to authenticate with the Dark Web Scanner API
using both JWT tokens and API keys.

SECURITY FEATURES:
1. JWT tokens expire after 15 minutes (configurable)
2. API keys can be generated with custom expiration
3. All endpoints require authentication
"""

import requests
import json

# Base URL of your API
BASE_URL = "http://localhost:8001"


def example_jwt_authentication():
    """Example: Login with JWT and make authenticated requests"""
    
    print("=" * 60)
    print("EXAMPLE 1: JWT Authentication")
    print("=" * 60)
    
    # Step 1: Login to get JWT tokens
    login_data = {
        "email": "admin@example.com",
        "password": "YourSecurePassword123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        expires_in = tokens["expires_in"]  # seconds
        
        print(f"✅ Login successful!")
        print(f"   Access token expires in: {expires_in // 60} minutes")
        print(f"   Token: {access_token[:50]}...")
        
        # Step 2: Use the access token to make authenticated requests
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Example: Start a scan
        scan_data = {
            "keyword": "example search"
        }
        
        scan_response = requests.post(
            f"{BASE_URL}/scan",
            params=scan_data,
            headers=headers
        )
        
        if scan_response.status_code == 200:
            print(f"✅ Scan started: {scan_response.json()}")
        else:
            print(f"❌ Scan failed: {scan_response.text}")
        
        # Step 3: When token expires (after 15 minutes), refresh it
        print("\n--- Token Refresh (use when access token expires) ---")
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        refresh_response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json=refresh_data
        )
        
        if refresh_response.status_code == 200:
            new_tokens = refresh_response.json()
            new_access_token = new_tokens["access_token"]
            print(f"✅ Token refreshed!")
            print(f"   New token: {new_access_token[:50]}...")
        
    else:
        print(f"❌ Login failed: {response.text}")


def example_api_key_authentication():
    """Example: Use API Key for authentication"""
    
    print("\n" + "=" * 60)
    print("EXAMPLE 2: API Key Authentication")
    print("=" * 60)
    
    # Step 1: First login with JWT to generate an API key
    login_data = {
        "email": "admin@example.com",
        "password": "YourSecurePassword123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens["access_token"]
        
        # Step 2: Generate API key using JWT
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        api_key_data = {
            "name": "Production API Key",
            "description": "For automated scans",
            "expires_days": 90  # Expires in 90 days (or None for never)
        }
        
        api_key_response = requests.post(
            f"{BASE_URL}/api-keys/",
            json=api_key_data,
            headers=headers
        )
        
        if api_key_response.status_code == 201:
            api_key_info = api_key_response.json()
            api_key = api_key_info["key"]  # SAVE THIS! Only shown once
            
            print(f"✅ API Key generated!")
            print(f"   Key: {api_key}")
            print(f"   ⚠️  SAVE THIS KEY! It won't be shown again.")
            
            # Step 3: Use API key for authentication (no need to refresh!)
            print("\n--- Using API Key for requests ---")
            
            api_headers = {
                "X-API-Key": api_key
            }
            
            scan_data = {
                "keyword": "api key test"
            }
            
            scan_response = requests.post(
                f"{BASE_URL}/scan",
                params=scan_data,
                headers=api_headers
            )
            
            if scan_response.status_code == 200:
                print(f"✅ Scan started with API key: {scan_response.json()}")
            else:
                print(f"❌ Scan failed: {scan_response.text}")
            
            # API keys don't expire until the set date (90 days in this example)
            print(f"\n✅ This API key will work for {api_key_data['expires_days']} days")
            print(f"   No need to refresh - perfect for automation!")
        
        else:
            print(f"❌ API key generation failed: {api_key_response.text}")
    
    else:
        print(f"❌ Login failed: {response.text}")


def get_auth_info():
    """Get authentication configuration from the API"""
    
    print("\n" + "=" * 60)
    print("API Authentication Configuration")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/auth/info")
    
    if response.status_code == 200:
        info = response.json()
        print(json.dumps(info, indent=2))
    else:
        print(f"❌ Failed to get auth info: {response.text}")


if __name__ == "__main__":
    print("\n🔐 Dark Web Scanner - Authentication Examples\n")
    
    # Show API configuration
    get_auth_info()
    
    # Example 1: JWT Authentication (expires after 15 minutes)
    # Uncomment to test:
    # example_jwt_authentication()
    
    # Example 2: API Key Authentication (long-lived)
    # Uncomment to test:
    # example_api_key_authentication()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print("1. JWT Tokens: Use for web applications and short sessions")
    print("   - Expires after 15 minutes")
    print("   - Can be refreshed for 7 days")
    print("   - Header: Authorization: Bearer <token>")
    print()
    print("2. API Keys: Use for automation and long-running scripts")
    print("   - Custom expiration (or never expires)")
    print("   - No need to refresh")
    print("   - Header: X-API-Key: <key>")
    print("=" * 60)
