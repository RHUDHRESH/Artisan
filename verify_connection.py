"""
Verification script to test Vercel-Render connectivity
Run this to verify your backend is accessible and CORS is configured correctly
"""
import requests
import json
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://artisan-rem1.onrender.com"  # Update if different
FRONTEND_ORIGIN = "https://your-app.vercel.app"  # Update with your Vercel domain


def test_root_endpoint() -> Dict[str, Any]:
    """Test the root endpoint"""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "data": response.json()
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_health_endpoint() -> Dict[str, Any]:
    """Test the health check endpoint"""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "data": response.json()
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_cors_headers() -> Dict[str, Any]:
    """Test CORS headers with OPTIONS request"""
    print("\n🔍 Testing CORS headers...")
    try:
        headers = {
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        response = requests.options(f"{BACKEND_URL}/api/chat", headers=headers, timeout=10)
        print(f"✅ Status: {response.status_code}")
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
        }
        
        print("📄 CORS Headers:")
        for key, value in cors_headers.items():
            print(f"   {key}: {value}")
        
        # Check if CORS is properly configured
        allow_origin = cors_headers.get("Access-Control-Allow-Origin")
        if allow_origin == "*" or allow_origin == FRONTEND_ORIGIN:
            print("✅ CORS appears to be configured correctly")
            success = True
        else:
            print(f"⚠️  WARNING: CORS might not allow {FRONTEND_ORIGIN}")
            print(f"   Current allow-origin: {allow_origin}")
            success = False
        
        return {
            "success": success,
            "status_code": response.status_code,
            "cors_headers": cors_headers
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def test_chat_endpoint() -> Dict[str, Any]:
    """Test the chat endpoint with a POST request"""
    print("\n🔍 Testing chat endpoint (POST /api/chat)...")
    try:
        headers = {
            "Content-Type": "application/json",
            "Origin": FRONTEND_ORIGIN
        }
        payload = {"message": "Hello! This is a test."}
        
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json()
            }
        else:
            print(f"⚠️  Response: {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("🚀 Vercel-Render Connection Verification")
    print("=" * 60)
    print(f"\n📍 Backend URL: {BACKEND_URL}")
    print(f"🌐 Frontend Origin: {FRONTEND_ORIGIN}")
    print(f"\n⚠️  Update FRONTEND_ORIGIN in this script to match your Vercel domain")
    
    results = {
        "root": test_root_endpoint(),
        "health": test_health_endpoint(),
        "cors": test_cors_headers(),
        "chat": test_chat_endpoint()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    all_success = True
    for test_name, result in results.items():
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
        if not result.get("success"):
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 All tests passed! Your backend is accessible.")
        print("\nNext steps:")
        print("1. Set NEXT_PUBLIC_API_URL in Vercel to:", BACKEND_URL)
        print("2. Redeploy your Vercel app")
        print("3. Test from your live Vercel deployment")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        print("\nCommon fixes:")
        print("1. Update CORS_ORIGINS in Render to include:", FRONTEND_ORIGIN)
        print("2. Redeploy Render service after env var changes")
        print("3. Wait for Render to fully start (free tier sleeps)")
    print("=" * 60)


if __name__ == "__main__":
    main()
