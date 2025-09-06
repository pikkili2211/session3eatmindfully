#!/usr/bin/env python3
"""
Test script to verify API key loading and Gemini connection
"""

def get_api_key():
    try:
        with open('key.properties', 'r') as f:
            for line in f:
                if line.startswith('key='):
                    return line.split('=')[1].strip()
    except FileNotFoundError:
        print("Error: key.properties file not found!")
        return None

def test_gemini_connection():
    try:
        import google.generativeai as genai
        
        api_key = get_api_key()
        if not api_key:
            print("❌ No API key found")
            return False
        
        print(f"✅ API key loaded: {api_key[:10]}...")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Test with a simple prompt
        response = model.generate_content("Say 'Hello, Eat Mindfully!' in one word.")
        print(f"✅ Gemini response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gemini: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing Eat Mindfully API Configuration")
    print("=" * 40)
    
    if test_gemini_connection():
        print("\n🎉 All tests passed! The app is ready to run.")
    else:
        print("\n❌ Tests failed. Please check your configuration.")
