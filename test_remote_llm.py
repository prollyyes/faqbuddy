#!/usr/bin/env python3
"""
Test script to verify remote LLM connection works.
This script tests the remote LLM setup using the same curl command you provided.
"""

import os
import json
import requests
import subprocess
import sys

def test_remote_llm_connection():
    """Test the remote LLM connection using the provided curl command."""
    
    # Get environment variables
    remote_base = os.getenv("REMOTE_LLM_BASE")
    remote_model = os.getenv("REMOTE_LLM_MODEL", "mistral:7b-instruct")
    remote_key = os.getenv("REMOTE_LLM_API_KEY", "")
    
    if not remote_base:
        print("❌ REMOTE_LLM_BASE environment variable not set")
        print("Please set it to your cloudflare tunnel URL (e.g., https://abc123.trycloudflare.com)")
        return False
    
    print(f"🔗 Testing connection to: {remote_base}")
    print(f"🤖 Using model: {remote_model}")
    
    # Test using requests (Python equivalent of your curl command)
    url = f"{remote_base.rstrip('/')}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if remote_key:
        headers["Authorization"] = f"Bearer {remote_key}"
    
    payload = {
        "model": remote_model,
        "messages": [
            {"role": "system", "content": "Sei un assistente utile."},
            {"role": "user", "content": "Scrivi solo: ok"}
        ],
        "temperature": 0.1
    }
    
    try:
        print("📡 Sending test request...")
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        print(f"✅ Response received: '{content}'")
        
        if content.lower() == "ok":
            print("🎉 Remote LLM connection test PASSED!")
            return True
        else:
            print(f"⚠️  Unexpected response: '{content}' (expected 'ok')")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False
    except KeyError as e:
        print(f"❌ Invalid response format: {e}")
        print(f"Response: {data}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_curl_command():
    """Test using the exact curl command you provided."""
    
    remote_base = os.getenv("REMOTE_LLM_BASE")
    remote_model = os.getenv("REMOTE_LLM_MODEL", "mistral:7b-instruct")
    
    if not remote_base:
        print("❌ REMOTE_LLM_BASE environment variable not set")
        return False
    
    print("\n🔧 Testing with curl command...")
    
    curl_cmd = [
        "curl", "-sS", "-X", "POST", f"{remote_base}/v1/chat/completions",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": remote_model,
            "messages": [
                {"role": "system", "content": "Sei un assistente utile."},
                {"role": "user", "content": "Scrivi solo: ok"}
            ],
            "temperature": 0.1
        })
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                content = data["choices"][0]["message"]["content"].strip()
                print(f"✅ Curl response: '{content}'")
                
                if content.lower() == "ok":
                    print("🎉 Curl test PASSED!")
                    return True
                else:
                    print(f"⚠️  Unexpected curl response: '{content}'")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from curl: {result.stdout}")
                return False
        else:
            print(f"❌ Curl failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Curl command timed out")
        return False
    except Exception as e:
        print(f"❌ Curl error: {e}")
        return False

def test_faqbuddy_integration():
    """Test the actual FAQBuddy LLM integration."""
    
    print("\n🤖 Testing FAQBuddy LLM integration...")
    
    try:
        # Import the updated LLM modules
        sys.path.append('/home/edd/Documents/projects/faqbuddy/backend/src/utils')
        from llm_mistral import generate_answer as mistral_generate
        from llm_gemma import generate_answer as gemma_generate, classify_question
        
        # Test context and question
        context = "Il corso di Ingegneria Informatica ha 180 crediti totali. La durata è di 3 anni."
        question = "Quanti crediti ha il corso di Ingegneria Informatica?"
        
        print(f"📝 Testing question: {question}")
        print(f"📚 Context: {context}")
        
        # Test Mistral
        print("\n🔮 Testing Mistral...")
        mistral_response = mistral_generate(context, question)
        print(f"✅ Mistral response: {mistral_response[:100]}...")
        
        # Test Gemma classification
        print("\n🔍 Testing Gemma classification...")
        classification = classify_question(question)
        print(f"✅ Classification: {classification}")
        
        # Test Gemma generation
        print("\n💎 Testing Gemma generation...")
        gemma_response = gemma_generate(context, question)
        print(f"✅ Gemma response: {gemma_response[:100]}...")
        
        print("🎉 FAQBuddy integration test PASSED!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 FAQBuddy Remote LLM Test Suite")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    print(f"REMOTE_LLM_BASE: {os.getenv('REMOTE_LLM_BASE', 'NOT SET')}")
    print(f"REMOTE_LLM_MODEL: {os.getenv('REMOTE_LLM_MODEL', 'mistral:7b-instruct')}")
    print(f"REMOTE_LLM_API_KEY: {'SET' if os.getenv('REMOTE_LLM_API_KEY') else 'NOT SET'}")
    
    # Run tests
    tests = [
        ("Remote LLM Connection", test_remote_llm_connection),
        ("Curl Command", test_curl_command),
        ("FAQBuddy Integration", test_faqbuddy_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your remote LLM setup is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
