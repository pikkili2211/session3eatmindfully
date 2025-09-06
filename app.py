from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import json
import time

app = Flask(__name__)

# Global cache for meals data
meals_cache = {
    'data': None,
    'timestamp': None,
    'total_calories': None
}

# Read API key from key.properties file
def get_api_key():
    try:
        with open('key.properties', 'r') as f:
            for line in f:
                if line.startswith('key='):
                    return line.split('=')[1].strip()
    except FileNotFoundError:
        print("Error: key.properties file not found!")
        return None

# Configure Gemini API
api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Error: Could not load API key from key.properties")
model = genai.GenerativeModel('gemini-1.5-flash')

def calculate_bmr(age, gender, height, weight):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return bmr

def calculate_tdee(bmr, activity_level):
    """Calculate Total Daily Energy Expenditure"""
    activity_multipliers = {
        'no_activity': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725
    }
    return bmr * activity_multipliers.get(activity_level, 1.2)

def calculate_macros(calories):
    """Calculate macronutrient requirements"""
    protein_calories = calories * 0.25  # 25% protein
    carb_calories = calories * 0.45     # 45% carbs
    fat_calories = calories * 0.30      # 30% fat
    
    protein_grams = protein_calories / 4
    carb_grams = carb_calories / 4
    fat_grams = fat_calories / 9
    fiber_grams = calories / 1000 * 14  # 14g fiber per 1000 calories
    
    return {
        'protein': round(protein_grams, 1),
        'carbs': round(carb_grams, 1),
        'fat': round(fat_grams, 1),
        'fiber': round(fiber_grams, 1)
    }

def generate_all_meals_data(total_calories=2000):
    """Generate comprehensive meals data using Gemini API and cache it"""
    global meals_cache
    
    # Check if we have cached data for the same calorie target
    if (meals_cache['data'] is not None and 
        meals_cache['total_calories'] == total_calories and 
        meals_cache['timestamp'] is not None):
        
        # Check if cache is less than 1 hour old
        if time.time() - meals_cache['timestamp'] < 3600:
            print(f"Using cached meals data for {total_calories} calories")
            return meals_cache['data']
    
    print(f"Generating new meals data for {total_calories} calories using Gemini API...")
    
    # Calculate calorie distribution
    calorie_targets = {
        'breakfast': int(total_calories * 0.25),
        'lunch': int(total_calories * 0.35),
        'snack': int(total_calories * 0.15),
        'dinner': int(total_calories * 0.25)
    }
    
    all_menus = {}
    
    # Generate comprehensive prompt for all meals at once
    prompt = f"""
    You are an expert in Andhra Pradesh cuisine. Generate a comprehensive menu for all meal types with the following calorie targets:

    Meal Calorie Targets:
    - Breakfast: {calorie_targets['breakfast']} calories
    - Lunch: {calorie_targets['lunch']} calories  
    - Snack: {calorie_targets['snack']} calories
    - Dinner: {calorie_targets['dinner']} calories

    Focus on traditional Andhra dishes with these characteristics:
    - Use authentic Andhra spices (red chilies, tamarind, curry leaves, mustard seeds)
    - Include only vegetarian options
    - Traditional cooking methods and ingredients
    - Regional specialties from different parts of Andhra Pradesh

    Return ONLY a valid JSON object with this exact format:
    {{
        "breakfast": [
            {{"name": "Dish Name", "calories": 250, "protein": 15, "carbs": 30, "fiber": 5}},
            {{"name": "Another Dish", "calories": 280, "protein": 20, "carbs": 25, "fiber": 4}},
            {{"name": "Third Dish", "calories": 220, "protein": 12, "carbs": 35, "fiber": 6}},
            {{"name": "Fourth Dish", "calories": 300, "protein": 18, "carbs": 40, "fiber": 3}},
            {{"name": "Fifth Dish", "calories": 260, "protein": 14, "carbs": 32, "fiber": 5}}
        ],
        "lunch": [
            {{"name": "Dish Name", "calories": 350, "protein": 20, "carbs": 45, "fiber": 6}},
            {{"name": "Another Dish", "calories": 380, "protein": 25, "carbs": 40, "fiber": 5}},
            {{"name": "Third Dish", "calories": 320, "protein": 18, "carbs": 50, "fiber": 7}},
            {{"name": "Fourth Dish", "calories": 400, "protein": 22, "carbs": 55, "fiber": 4}},
            {{"name": "Fifth Dish", "calories": 360, "protein": 20, "carbs": 48, "fiber": 6}}
        ],
        "snack": [
            {{"name": "Dish Name", "calories": 150, "protein": 8, "carbs": 20, "fiber": 3}},
            {{"name": "Another Dish", "calories": 180, "protein": 10, "carbs": 25, "fiber": 4}},
            {{"name": "Third Dish", "calories": 120, "protein": 6, "carbs": 18, "fiber": 2}},
            {{"name": "Fourth Dish", "calories": 160, "protein": 9, "carbs": 22, "fiber": 3}},
            {{"name": "Fifth Dish", "calories": 140, "protein": 7, "carbs": 20, "fiber": 3}}
        ],
        "dinner": [
            {{"name": "Dish Name", "calories": 250, "protein": 12, "carbs": 35, "fiber": 4}},
            {{"name": "Another Dish", "calories": 280, "protein": 15, "carbs": 40, "fiber": 5}},
            {{"name": "Third Dish", "calories": 220, "protein": 10, "carbs": 32, "fiber": 3}},
            {{"name": "Fourth Dish", "calories": 300, "protein": 18, "carbs": 45, "fiber": 6}},
            {{"name": "Fifth Dish", "calories": 260, "protein": 14, "carbs": 38, "fiber": 4}}
        ]
    }}

    Do not include any text before or after the JSON object. Make sure all dish names are authentic Andhra cuisine.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        print(f"Gemini response length: {len(response_text)}")
        
        # Parse JSON response
        try:
            # Clean the response text
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Find JSON object boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                all_menus = json.loads(json_str)
                
                # Validate the response structure
                required_meals = ['breakfast', 'lunch', 'snack', 'dinner']
                if all(meal in all_menus for meal in required_meals):
                    for meal_type in required_meals:
                        if not isinstance(all_menus[meal_type], list) or len(all_menus[meal_type]) == 0:
                            raise ValueError(f"Invalid {meal_type} structure")
                        for item in all_menus[meal_type]:
                            if not all(key in item for key in ['name', 'calories', 'protein', 'carbs', 'fiber']):
                                raise ValueError(f"Invalid item structure in {meal_type}")
                else:
                    raise ValueError("Missing required meal types")
                    
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parsing failed: {e}")
            all_menus = None
        
        # Use fallback if AI response fails
        if not all_menus:
            print("Using fallback meals data...")
            all_menus = get_fallback_meals_data(calorie_targets)
        
        # Cache the data
        meals_cache['data'] = all_menus
        meals_cache['timestamp'] = time.time()
        meals_cache['total_calories'] = total_calories
        
        print(f"Successfully generated and cached meals data for {total_calories} calories")
        return all_menus
        
    except Exception as e:
        print(f"Error generating meals data: {e}")
        # Return fallback data
        fallback_data = get_fallback_meals_data(calorie_targets)
        meals_cache['data'] = fallback_data
        meals_cache['timestamp'] = time.time()
        meals_cache['total_calories'] = total_calories
        return fallback_data

def get_fallback_meals_data(calorie_targets):
    """Get fallback meals data when AI fails"""
    return {
        'breakfast': [
            {"name": "Andhra Upma with Coconut", "calories": calorie_targets['breakfast']//5, "protein": 8, "carbs": 45, "fiber": 4},
            {"name": "Pesarattu with Allam Chutney", "calories": calorie_targets['breakfast']//5, "protein": 12, "carbs": 35, "fiber": 6},
            {"name": "Idli with Gongura Chutney", "calories": calorie_targets['breakfast']//5, "protein": 6, "carbs": 35, "fiber": 5},
            {"name": "Masala Dosa with Coconut Chutney", "calories": calorie_targets['breakfast']//5, "protein": 5, "carbs": 40, "fiber": 3},
            {"name": "Ven Pongal with Ghee", "calories": calorie_targets['breakfast']//5, "protein": 10, "carbs": 50, "fiber": 4}
        ],
        'lunch': [
            {"name": "Andhra Chicken Curry with Rice", "calories": calorie_targets['lunch']//5, "protein": 30, "carbs": 55, "fiber": 6},
            {"name": "Gongura Dal with Rice", "calories": calorie_targets['lunch']//5, "protein": 15, "carbs": 65, "fiber": 8},
            {"name": "Andhra Vegetable Biryani", "calories": calorie_targets['lunch']//5, "protein": 12, "carbs": 70, "fiber": 5},
            {"name": "Chepala Pulusu (Fish Curry)", "calories": calorie_targets['lunch']//5, "protein": 25, "carbs": 50, "fiber": 4},
            {"name": "Royyala Iguru (Prawn Curry)", "calories": calorie_targets['lunch']//5, "protein": 18, "carbs": 60, "fiber": 10}
        ],
        'snack': [
            {"name": "Mirchi Bajji with Tea", "calories": calorie_targets['snack']//5, "protein": 6, "carbs": 25, "fiber": 3},
            {"name": "Ulli Vada with Chutney", "calories": calorie_targets['snack']//5, "protein": 5, "carbs": 20, "fiber": 2},
            {"name": "Banana Chips with Red Chili", "calories": calorie_targets['snack']//5, "protein": 2, "carbs": 28, "fiber": 3},
            {"name": "Roasted Peanuts with Curry Leaves", "calories": calorie_targets['snack']//5, "protein": 8, "carbs": 8, "fiber": 4},
            {"name": "Fresh Mango with Red Chili Powder", "calories": calorie_targets['snack']//5, "protein": 2, "carbs": 25, "fiber": 4}
        ],
        'dinner': [
            {"name": "Andhra Rasam with Rice", "calories": calorie_targets['dinner']//5, "protein": 4, "carbs": 40, "fiber": 3},
            {"name": "Gongura Sambar with Rice", "calories": calorie_targets['dinner']//5, "protein": 8, "carbs": 45, "fiber": 6},
            {"name": "Curd Rice with Andhra Pickle", "calories": calorie_targets['dinner']//5, "protein": 6, "carbs": 35, "fiber": 2},
            {"name": "Chapati with Dalcha", "calories": calorie_targets['dinner']//5, "protein": 12, "carbs": 40, "fiber": 5},
            {"name": "Andhra Vegetable Curry with Rice", "calories": calorie_targets['dinner']//5, "protein": 8, "carbs": 55, "fiber": 7}
        ]
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_meals_data', methods=['POST'])
def save_meals_data():
    """Save current meals data to JSON file"""
    try:
        global meals_cache
        
        if meals_cache['data'] is not None:
            # Save to JSON file
            with open('meals_data.json', 'w') as f:
                json.dump({
                    'data': meals_cache['data'],
                    'timestamp': meals_cache['timestamp'],
                    'total_calories': meals_cache['total_calories']
                }, f, indent=2)
            
            print(f"Meals data saved to meals_data.json")
            return jsonify({
                'success': True,
                'message': 'Meals data saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No meals data to save'
            })
            
    except Exception as e:
        print(f"Error saving meals data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/load_meals_data', methods=['GET'])
def load_meals_data():
    """Load meals data from JSON file"""
    try:
        global meals_cache
        
        if os.path.exists('meals_data.json'):
            with open('meals_data.json', 'r') as f:
                saved_data = json.load(f)
            
            # Check if saved data is less than 24 hours old
            if time.time() - saved_data['timestamp'] < 86400:  # 24 hours
                meals_cache = saved_data
                print(f"Loaded meals data from file for {saved_data['total_calories']} calories")
                return jsonify({
                    'success': True,
                    'message': 'Meals data loaded from file',
                    'data': saved_data['data']
                })
            else:
                print("Saved meals data is too old, will generate new data")
                return jsonify({
                    'success': False,
                    'message': 'Saved data is too old'
                })
        else:
            return jsonify({
                'success': False,
                'message': 'No saved meals data found'
            })
            
    except Exception as e:
        print(f"Error loading meals data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/calculate_calories', methods=['POST'])
def calculate_calories():
    try:
        data = request.json
        age = int(data['age'])
        gender = data['gender']
        height = float(data['height'])
        weight = float(data['weight'])
        activity_level = data['activity_level']
        
        # Calculate BMR and TDEE
        bmr = calculate_bmr(age, gender, height, weight)
        tdee = calculate_tdee(bmr, activity_level)
        macros = calculate_macros(tdee)
        
        return jsonify({
            'success': True,
            'bmr': round(bmr, 1),
            'tdee': round(tdee, 1),
            'macros': macros
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_menu', methods=['POST'])
def generate_menu():
    try:
        data = request.json
        meal_type = data['meal_type']
        calories = data.get('calories', 300)
        cuisine_preference = data.get('cuisine', 'Andhra')
        
        # Enhanced prompt specifically for Andhra cuisine
        prompt = f"""
        You are an expert in Andhra Pradesh cuisine. Generate exactly 5 authentic Andhra {meal_type} dishes with calories around {calories}.

        Focus on traditional Andhra dishes with these characteristics:
        - Use authentic Andhra spices (red chilies, tamarind, curry leaves, mustard seeds)
        - Include only vegetarian options
        - Traditional cooking methods and ingredients
        - Regional specialties from different parts of Andhra Pradesh

        Return ONLY a valid JSON array with this exact format:
        [
            {{"name": "Authentic Andhra Dish Name", "calories": 250, "protein": 15, "carbs": 30, "fiber": 5}},
            {{"name": "Another Andhra Dish", "calories": 280, "protein": 20, "carbs": 25, "fiber": 4}},
            {{"name": "Third Andhra Dish", "calories": 220, "protein": 12, "carbs": 35, "fiber": 6}},
            {{"name": "Fourth Andhra Dish", "calories": 300, "protein": 18, "carbs": 40, "fiber": 3}},
            {{"name": "Fifth Andhra Dish", "calories": 260, "protein": 14, "carbs": 32, "fiber": 5}}
        ]

        Do not include any text before or after the JSON array. Make sure all dish names are authentic Andhra cuisine.
        """
        
        print(f"Generating Andhra {meal_type} menu with {calories} calories...")
        
        # Generate content with Gemini AI
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
        except Exception as api_error:
            print(f"Gemini API error for menu generation: {api_error}")
            response_text = ""
        
        print(f"Gemini response: {response_text[:200]}...")
        
        # Parse JSON response
        menu_items = None
        try:
            # Clean the response text
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Find JSON array boundaries
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                menu_items = json.loads(json_str)
                
                # Validate the response structure
                if isinstance(menu_items, list) and len(menu_items) > 0:
                    for item in menu_items:
                        if not all(key in item for key in ['name', 'calories', 'protein', 'carbs', 'fiber']):
                            raise ValueError("Invalid item structure")
                else:
                    raise ValueError("Empty or invalid menu list")
                    
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parsing failed: {e}")
            menu_items = None
        
        # Enhanced fallback menu with more authentic Andhra dishes
        if not menu_items:
            print("Using enhanced Andhra fallback menu...")
            fallback_menus = {
                'breakfast': [
                    {"name": "Andhra Upma with Coconut", "calories": 250, "protein": 8, "carbs": 45, "fiber": 4},
                    {"name": "Pesarattu with Allam Chutney", "calories": 280, "protein": 12, "carbs": 35, "fiber": 6},
                    {"name": "Idli with Gongura Chutney", "calories": 200, "protein": 6, "carbs": 35, "fiber": 5},
                    {"name": "Masala Dosa with Coconut Chutney", "calories": 220, "protein": 5, "carbs": 40, "fiber": 3},
                    {"name": "Ven Pongal with Ghee", "calories": 300, "protein": 10, "carbs": 50, "fiber": 4}
                ],
                'lunch': [
                    {"name": "Andhra Chicken Curry with Rice", "calories": 450, "protein": 30, "carbs": 55, "fiber": 6},
                    {"name": "Gongura Dal with Rice", "calories": 380, "protein": 15, "carbs": 65, "fiber": 8},
                    {"name": "Andhra Vegetable Biryani", "calories": 420, "protein": 12, "carbs": 70, "fiber": 5},
                    {"name": "Chepala Pulusu (Fish Curry)", "calories": 400, "protein": 25, "carbs": 50, "fiber": 4},
                    {"name": "Royyala Iguru (Prawn Curry)", "calories": 350, "protein": 18, "carbs": 60, "fiber": 10}
                ],
                'snack': [
                    {"name": "Mirchi Bajji with Tea", "calories": 180, "protein": 6, "carbs": 25, "fiber": 3},
                    {"name": "Ulli Vada with Chutney", "calories": 150, "protein": 5, "carbs": 20, "fiber": 2},
                    {"name": "Banana Chips with Red Chili", "calories": 120, "protein": 2, "carbs": 28, "fiber": 3},
                    {"name": "Roasted Peanuts with Curry Leaves", "calories": 160, "protein": 8, "carbs": 8, "fiber": 4},
                    {"name": "Fresh Mango with Red Chili Powder", "calories": 100, "protein": 2, "carbs": 25, "fiber": 4}
                ],
                'dinner': [
                    {"name": "Andhra Rasam with Rice", "calories": 200, "protein": 4, "carbs": 40, "fiber": 3},
                    {"name": "Gongura Sambar with Rice", "calories": 250, "protein": 8, "carbs": 45, "fiber": 6},
                    {"name": "Curd Rice with Andhra Pickle", "calories": 220, "protein": 6, "carbs": 35, "fiber": 2},
                    {"name": "Chapati with Dalcha", "calories": 280, "protein": 12, "carbs": 40, "fiber": 5},
                    {"name": "Andhra Vegetable Curry with Rice", "calories": 300, "protein": 8, "carbs": 55, "fiber": 7}
                ]
            }
            menu_items = fallback_menus.get(meal_type, fallback_menus['lunch'])
        
        return jsonify({
            'success': True,
            'menu_items': menu_items,
            'source': 'ai' if menu_items and 'fallback' not in str(menu_items) else 'fallback'
        })
        
    except Exception as e:
        print(f"Error in generate_menu: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_all_menus', methods=['POST'])
def generate_all_menus():
    """Generate menus for all meal types using cached data"""
    try:
        data = request.json
        total_calories = data.get('total_calories', 2000)
        
        # Use the cached meals data function
        all_menus = generate_all_meals_data(total_calories)
        
        return jsonify({
            'success': True,
            'menus': all_menus,
            'cached': meals_cache['data'] is not None and meals_cache['total_calories'] == total_calories
        })
        
    except Exception as e:
        print(f"Error in generate_all_menus: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_suggestions', methods=['POST'])
def get_suggestions():
    try:
        data = request.json
        calorie_diff = data['calorie_diff']
        protein_diff = data['protein_diff']
        carb_diff = data['carb_diff']
        fiber_diff = data['fiber_diff']
        
        # Enhanced prompt for better suggestions
        prompt = f"""
        You are a nutrition expert specializing in Andhra cuisine. Based on the nutrition analysis below, provide exactly 3 personalized recommendations.

        Current Nutrition Status:
        - Calorie difference: {calorie_diff} calories (positive = surplus, negative = deficit)
        - Protein difference: {protein_diff} grams (positive = surplus, negative = deficit)
        - Carbohydrate difference: {carb_diff} grams (positive = surplus, negative = deficit)
        - Fiber difference: {fiber_diff} grams (positive = surplus, negative = deficit)

        Provide exactly 3 specific, actionable suggestions focusing on:
        1. Specific Andhra cuisine dishes that can help balance nutrition
        2. Practical portion adjustments or meal modifications
        3. Healthy snack or meal additions from Andhra cuisine

        Each suggestion should be:
        - Specific to Andhra cuisine
        - Actionable and practical
        - Focused on the most important nutrition gap
        - Clear and concise (3-4 sentences max)

        Format your response as exactly 3 bullet points, each starting with "•"
        """
        
        print(f"Getting suggestions for: Cal={calorie_diff}, Pro={protein_diff}, Carb={carb_diff}, Fib={fiber_diff}")
        
        try:
            response = model.generate_content(prompt)
            suggestions = response.text.strip()
        except Exception as api_error:
            print(f"Gemini API error: {api_error}")
            # Return fallback suggestions if API fails
            suggestions = generate_fallback_suggestions(calorie_diff, protein_diff, carb_diff, fiber_diff)
        
        # Fallback suggestions if AI fails
        if not suggestions or len(suggestions) < 50:
            suggestions = generate_fallback_suggestions(calorie_diff, protein_diff, carb_diff, fiber_diff)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        print(f"Error in get_suggestions: {e}")
        # Return fallback suggestions
        suggestions = generate_fallback_suggestions(
            data.get('calorie_diff', 0),
            data.get('protein_diff', 0),
            data.get('carb_diff', 0),
            data.get('fiber_diff', 0)
        )
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

def generate_fallback_suggestions(calorie_diff, protein_diff, carb_diff, fiber_diff):
    """Generate fallback suggestions when AI is unavailable"""
    suggestions = []
    
    # Prioritize the most significant nutrition gap
    if abs(calorie_diff) > abs(protein_diff) and abs(calorie_diff) > abs(fiber_diff):
        if calorie_diff < -200:
            suggestions.append("• Add Andhra snacks like roasted peanuts or banana chips to increase calories")
            suggestions.append("• Include an extra serving of rice with your meals")
        elif calorie_diff > 200:
            suggestions.append("• Reduce portion sizes, especially rice and oil in curries")
            suggestions.append("• Choose lighter Andhra options like rasam rice instead of heavy curries")
    elif abs(protein_diff) > abs(fiber_diff):
        if protein_diff < -10:
            suggestions.append("• Include more dal, chicken curry, or fish curry in your meals")
            suggestions.append("• Add protein-rich Andhra snacks like roasted chana or boiled eggs")
        elif protein_diff > 10:
            suggestions.append("• Balance with more vegetables and reduce meat portions")
    else:
        if fiber_diff < -5:
            suggestions.append("• Include more vegetables in your Andhra meals")
            suggestions.append("• Add fruits like banana or apple as snacks")
    
    # Fill remaining slots with general healthy advice
    if len(suggestions) < 3:
        suggestions.append("• Maintain balanced portions of rice, dal, and vegetables")
    if len(suggestions) < 3:
        suggestions.append("• Stay hydrated with water and buttermilk")
    if len(suggestions) < 3:
        suggestions.append("• Consider traditional Andhra snacks like pesarattu or upma")
    
    return "\n".join(suggestions[:3])  # Return exactly 3 suggestions

if __name__ == '__main__':
    # Try to load cached meals data on startup
    try:
        if os.path.exists('meals_data.json'):
            with open('meals_data.json', 'r') as f:
                saved_data = json.load(f)
            
            # Check if saved data is less than 24 hours old
            if time.time() - saved_data['timestamp'] < 86400:  # 24 hours
                meals_cache = saved_data
                print(f"✅ Loaded cached meals data for {saved_data['total_calories']} calories")
            else:
                print("⏰ Cached meals data is too old, will generate new data when needed")
        else:
            print("📝 No cached meals data found, will generate new data when needed")
    except Exception as e:
        print(f"⚠️ Error loading cached meals data: {e}")
    
    print("🚀 Starting Eat Mindfully server...")
    app.run(debug=True, host='0.0.0.0', port=5001)
