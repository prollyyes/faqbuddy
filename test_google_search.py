#!/usr/bin/env python3
"""
Quick Google Search API Test
============================

This script tests if your Google Custom Search API is working correctly.
"""

import os
import requests
from dotenv import load_dotenv

def test_google_search():
    """Test Google Custom Search API."""
    print("🔍 Testing Google Custom Search API")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Get API credentials
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    cx = os.getenv('GOOGLE_SEARCH_CX')
    
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"🔍 Search Engine ID: {'✅ Set' if cx else '❌ Missing'}")
    
    if not api_key or not cx:
        print("\n❌ Missing credentials!")
        print("Please set both GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX in your .env file")
        return False
    
    # Test query
    test_query = "Sapienza Università di Roma ingegneria informatica"
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cx,
            'q': test_query,
            'num': 3
        }
        
        print(f"\n🔍 Testing query: {test_query}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            print(f"✅ Success! Found {len(items)} results")
            
            for i, item in enumerate(items, 1):
                print(f"   {i}. {item.get('title', 'No title')}")
                print(f"      URL: {item.get('link', 'No URL')}")
                print(f"      Snippet: {item.get('snippet', 'No snippet')[:100]}...")
                print()
            
            return True
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_google_search()
    
    if success:
        print("🎉 Google Search API is working correctly!")
        print("You can now use web search enhancement in your RAG system.")
    else:
        print("⚠️ Please check your API configuration and try again.") 