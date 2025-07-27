#!/usr/bin/env python3
"""
Simple test script to verify the API endpoints work correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_basic_connectivity():
    """Test basic connectivity"""
    try:
        response = requests.get(f"{BASE_URL}/test")
        print(f"Test endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Test endpoint failed: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze endpoint with a sample request"""
    try:
        data = {
            "symbol": "AAPL",
            "days_back": 7,
            "technical_interval": "1D",
            "technical_limit": 100
        }
        
        response = requests.post(
            f"{BASE_URL}/analyze",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=60
        )
        
        print(f"Analyze endpoint: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Analysis successful!")
            print(f"Technical Analysis: {result.get('technicalAnalysis', {})}")
            print(f"Semantic Analysis: {result.get('semanticAnalysis', {})}")
            print(f"AI Insight: {result.get('aiInsight', 'N/A')}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Analyze endpoint failed: {e}")
        return False

def main():
    print("Testing API endpoints...")
    print("=" * 50)
    
    # Test basic connectivity
    if not test_basic_connectivity():
        print("❌ Basic connectivity test failed")
        return
    print("✅ Basic connectivity test passed")
    print()
    
    # Test health endpoint
    if not test_health():
        print("❌ Health check failed")
        return
    print("✅ Health check passed")
    print()
    
    # Test analyze endpoint
    print("Testing analyze endpoint (this may take a while)...")
    if not test_analyze_endpoint():
        print("❌ Analyze endpoint test failed")
        return
    print("✅ Analyze endpoint test passed")
    
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    main() 