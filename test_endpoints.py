#!/usr/bin/env python3
"""
Test script to verify API endpoints work correctly
"""

import requests
import json

def test_calorie_calculation():
    """Test calorie calculation endpoint"""
    print("🧪 Testing calorie calculation...")
    
    data = {
        "age": 30,
        "gender": "female",
        "height": 165,
        "weight": 60,
        "activity_level": "moderate"
    }
    
    try:
        response = requests.post('http://localhost:5001/calculate_calories', json=data)
        result = response.json()
        
        if result.get('success'):
            print(f"✅ Calorie calculation successful!")
            print(f"   BMR: {result['bmr']} calories")
            print(f"   TDEE: {result['tdee']} calories")
            print(f"   Protein: {result['macros']['protein']}g")
            return result['tdee']
        else:
            print(f"❌ Calorie calculation failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing calorie calculation: {e}")
        return None

def test_menu_generation():
    """Test menu generation endpoint"""
    print("\n🧪 Testing menu generation...")
    
    data = {
        "meal_type": "breakfast",
        "calories": 300,
        "cuisine": "Andhra"
    }
    
    try:
        response = requests.post('http://localhost:5001/generate_menu', json=data)
        result = response.json()
        
        if result.get('success'):
            print(f"✅ Menu generation successful!")
            print(f"   Generated {len(result['menu_items'])} items")
            print(f"   Source: {result.get('source', 'unknown')}")
            for item in result['menu_items'][:2]:  # Show first 2 items
                print(f"   - {item['name']}: {item['calories']} cal")
            return True
        else:
            print(f"❌ Menu generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing menu generation: {e}")
        return False

def test_all_menus_generation():
    """Test all menus generation endpoint"""
    print("\n🧪 Testing all menus generation...")
    
    data = {
        "total_calories": 2000
    }
    
    try:
        response = requests.post('http://localhost:5001/generate_all_menus', json=data)
        result = response.json()
        
        if result.get('success'):
            print(f"✅ All menus generation successful!")
            for meal_type, items in result['menus'].items():
                print(f"   {meal_type.title()}: {len(items)} items")
            return True
        else:
            print(f"❌ All menus generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing all menus generation: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing Eat Mindfully API Endpoints")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get('http://localhost:5001/')
        if response.status_code == 200:
            print("✅ Server is running on port 5001")
        else:
            print("❌ Server not responding properly")
            exit(1)
    except:
        print("❌ Server not running. Please start the app first with: python3 run.py")
        exit(1)
    
    # Run tests
    tdee = test_calorie_calculation()
    test_menu_generation()
    test_all_menus_generation()
    
    print("\n🎉 API endpoint tests completed!")
    print("📱 You can now open http://localhost:5001 in your browser")
