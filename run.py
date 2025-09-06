#!/usr/bin/env python3
"""
Eat Mindfully - AI-Powered Nutrition Tracker
Run script for easy application startup
"""

import os
import sys
from app import app

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if key.properties file exists
    if not os.path.exists('key.properties'):
        print("❌ key.properties file not found!")
        print("📝 Please create a key.properties file with your API key")
        print("💡 Format: key=your_api_key_here")
        return False
    
    # Check if API key is set in key.properties
    try:
        with open('key.properties', 'r') as f:
            api_key = None
            for line in f:
                if line.startswith('key='):
                    api_key = line.split('=')[1].strip()
                    break
        
        if not api_key or api_key == 'your_api_key_here':
            print("❌ API key not set in key.properties file!")
            print("🔑 Please add your Google Gemini API key to the key.properties file")
            return False
        
        print("✅ API key found in key.properties!")
        
    except Exception as e:
        print(f"❌ Error reading key.properties: {e}")
        return False
    
    print("✅ All requirements met!")
    return True

def main():
    """Main function to run the application"""
    print("🍽️ Eat Mindfully - AI-Powered Nutrition Tracker")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)
    
    print("\n🚀 Starting the application...")
    print("📱 Open your browser and go to: http://localhost:5001")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Application stopped. Thank you for using Eat Mindfully!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
