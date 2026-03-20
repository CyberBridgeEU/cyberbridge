#!/usr/bin/env python3
"""
Quick Authentication Test Script

Tests both JWT and API Key authentication methods.
Run this after starting the backend server.

Usage:
    python test_authentication.py
"""

import requests
import sys
import json

BASE_URL = "http://localhost:8001"

# Test credentials (use your actual admin credentials)
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "Admin123!"  # Change this to your actual password


def test_auth_info():
    """Test 1: Get authentication info (public endpoint)"""
    print("\n" + "="*70)
    print("TEST 1: Getting Authentication Configuration")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/auth/info")
        if response.status_code == 200:
            print("✅ Auth info endpoint working")
            info = response.json()
            print(f"\nJWT Expiration: {info['authentication_methods']['jwt_bearer']['token_expiration_minutes']} minutes")
            print(f"Refresh Token Valid: {info['authentication_methods']['jwt_bearer']['refresh_token_expiration_days']} days")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_jwt_login():
    """Test 2: Login with JWT"""
    print("\n" + "="*70)
    print("TEST 2: JWT Authentication")
    print("="*70)
    
    try:
        # Login
        print(f"Attempting login with {TEST_EMAIL}...")
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens['access_token']
            print(f"✅ Login successful!")
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Expires in: {tokens['expires_in']} seconds ({tokens['expires_in']//60} minutes)")
            
            # Test authenticated endpoint with JWT
            print("\nTesting authenticated endpoint with JWT...")
            headers = {"Authorization": f"Bearer {access_token}"}
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"✅ Authenticated successfully as: {user_info['email']}")
                print(f"   Role: {user_info['role']}")
                return access_token
            else:
                print(f"❌ Authentication failed: {me_response.status_code}")
                return None
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            print("\n⚠️  Update TEST_EMAIL and TEST_PASSWORD in this script!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_api_key_creation(jwt_token):
    """Test 3: Create and use API Key"""
    print("\n" + "="*70)
    print("TEST 3: API Key Authentication")
    print("="*70)
    
    if not jwt_token:
        print("❌ Skipping (no JWT token)")
        return None
    
    try:
        # Create API key
        print("Creating API key...")
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.post(
            f"{BASE_URL}/api-keys/",
            json={
                "name": "Test API Key",
                "description": "Testing API key authentication",
                "expires_days": None  # Never expires
            },
            headers=headers
        )
        
        if response.status_code == 201:
            key_data = response.json()
            api_key = key_data['key']
            print(f"✅ API Key created!")
            print(f"   Key: {api_key}")
            print(f"   Name: {key_data['name']}")
            print(f"   ⚠️  This key would only be shown once in production!")
            
            # Test authenticated endpoint with API Key
            print("\nTesting authenticated endpoint with API Key...")
            api_headers = {"X-API-Key": api_key}
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=api_headers)
            
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"✅ Authenticated with API Key as: {user_info['email']}")
                print(f"   Role: {user_info['role']}")
                return api_key
            else:
                print(f"❌ API Key authentication failed: {me_response.status_code}")
                return None
        else:
            print(f"❌ API Key creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_both_auth_methods(jwt_token, api_key):
    """Test 4: Verify both methods work on scan endpoint"""
    print("\n" + "="*70)
    print("TEST 4: Testing Both Auth Methods on Scan Endpoint")
    print("="*70)
    
    if not jwt_token or not api_key:
        print("❌ Skipping (missing credentials)")
        return
    
    try:
        # Test with JWT
        print("\n1. Testing scan with JWT token...")
        jwt_headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(f"{BASE_URL}/scans", headers=jwt_headers)
        
        if response.status_code == 200:
            print(f"✅ JWT authentication works on /scans")
        else:
            print(f"❌ JWT failed: {response.status_code}")
        
        # Test with API Key
        print("\n2. Testing scan with API Key...")
        api_headers = {"X-API-Key": api_key}
        response = requests.get(f"{BASE_URL}/scans", headers=api_headers)
        
        if response.status_code == 200:
            print(f"✅ API Key authentication works on /scans")
        else:
            print(f"❌ API Key failed: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def cleanup_test_api_key(jwt_token, api_key):
    """Cleanup: Delete test API key"""
    print("\n" + "="*70)
    print("CLEANUP: Removing Test API Key")
    print("="*70)
    
    if not jwt_token:
        return
    
    try:
        # List API keys to find the test key
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(f"{BASE_URL}/api-keys/", headers=headers)
        
        if response.status_code == 200:
            keys = response.json()
            for key in keys:
                if key['name'] == "Test API Key":
                    delete_response = requests.delete(
                        f"{BASE_URL}/api-keys/{key['id']}",
                        headers=headers
                    )
                    if delete_response.status_code == 204:
                        print(f"✅ Test API key deleted")
                    else:
                        print(f"⚠️  Could not delete test key: {delete_response.status_code}")
                    break
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")


def main():
    print("\n" + "🔐"*35)
    print("      DARK WEB SCANNER - AUTHENTICATION TESTS")
    print("🔐"*35)
    
    # Test 1: Auth info
    if not test_auth_info():
        print("\n⚠️  Server might not be running. Start it with: cd backend && python main.py")
        sys.exit(1)
    
    # Test 2: JWT Login
    jwt_token = test_jwt_login()
    
    # Test 3: API Key
    api_key = test_api_key_creation(jwt_token)
    
    # Test 4: Both methods
    test_both_auth_methods(jwt_token, api_key)
    
    # Cleanup
    cleanup_test_api_key(jwt_token, api_key)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY - Global Middleware Authentication")
    print("="*70)
    print("\n🔐 Architecture:")
    print("   - Global middleware runs on ALL routes automatically")
    print("   - Checks: JWT first → API Key → Reject 401")
    print("   - Sets principal.type for tracking (user vs service)")
    print("\n✅ Security Features:")
    print("   1. JWT tokens expire after 15 minutes (refreshable)")
    print("   2. Refresh tokens valid for 7 days")
    print("   3. API keys support custom expiration")
    print("   4. All endpoints protected by global middleware")
    print("   5. Principal type tracking (user vs service)")
    print("\n📊 Principal Types:")
    print("   - JWT → principal.type = 'user' (human users, web UI)")
    print("   - API Key → principal.type = 'service' (automation, scripts)")
    print("\n📚 Usage:")
    print("   - Web UI: JWT (automatic refresh)")
    print("   - Scripts: API Keys (generate from Profile page)")
    print("   - Both methods accepted on all protected endpoints")
    print("\n🔍 Check Logs:")
    print("   Backend logs show principal.type for audit tracking:")
    print("   ✅ JWT Auth: user@example.com (type=user) → POST /scan")
    print("   ✅ API Key Auth: automation@example.com (type=service) → POST /scan")
    print("\n📖 Documentation:")
    print("   - See AUTHENTICATION_ARCHITECTURE.md for details")
    print("   - See JWT_CONFIGURATION.txt for configuration")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
