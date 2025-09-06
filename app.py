from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import json

app = Flask(__name__)

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
model = genai.GenerativeModel('gemini-2.0-flash-exp')

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

@app.route('/')
def index():
    return render_template('index.html')

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
        - Include both vegetarian and non-vegetarian options
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
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
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
    """Generate menus for all meal types at once"""
    try:
        data = request.json
        total_calories = data.get('total_calories', 2000)
        
        # Calculate calorie distribution
        calorie_targets = {
            'breakfast': int(total_calories * 0.25),
            'lunch': int(total_calories * 0.35),
            'snack': int(total_calories * 0.15),
            'dinner': int(total_calories * 0.25)
        }
        
        all_menus = {}
        
        for meal_type, calories in calorie_targets.items():
            try:
                # Generate menu for this meal type
                menu_data = {
                    'meal_type': meal_type,
                    'calories': calories,
                    'cuisine': 'Andhra'
                }
                
                # Call the existing generate_menu logic
                prompt = f"""
                You are an expert in Andhra Pradesh cuisine. Generate exactly 5 authentic Andhra {meal_type} dishes with calories around {calories}.

                Focus on traditional Andhra dishes with these characteristics:
                - Use authentic Andhra spices (red chilies, tamarind, curry leaves, mustard seeds)
                - Include both vegetarian and non-vegetarian options
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

                Do not include any text before or after the JSON array.
                """
                
                response = model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Parse JSON response
                menu_items = None
                try:
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                    start_idx = response_text.find('[')
                    end_idx = response_text.rfind(']') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = response_text[start_idx:end_idx]
                        menu_items = json.loads(json_str)
                        
                        if isinstance(menu_items, list) and len(menu_items) > 0:
                            for item in menu_items:
                                if not all(key in item for key in ['name', 'calories', 'protein', 'carbs', 'fiber']):
                                    raise ValueError("Invalid item structure")
                        else:
                            raise ValueError("Empty or invalid menu list")
                            
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"JSON parsing failed for {meal_type}: {e}")
                    menu_items = None
                
                # Use fallback if AI fails
                if not menu_items:
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
                
                all_menus[meal_type] = menu_items
                
            except Exception as e:
                print(f"Error generating menu for {meal_type}: {e}")
                # Use fallback for this meal type
                all_menus[meal_type] = [
                    {"name": f"Andhra {meal_type.title()} Option 1", "calories": calories//5, "protein": 10, "carbs": 20, "fiber": 3},
                    {"name": f"Andhra {meal_type.title()} Option 2", "calories": calories//5, "protein": 12, "carbs": 25, "fiber": 4},
                    {"name": f"Andhra {meal_type.title()} Option 3", "calories": calories//5, "protein": 8, "carbs": 30, "fiber": 5},
                    {"name": f"Andhra {meal_type.title()} Option 4", "calories": calories//5, "protein": 15, "carbs": 18, "fiber": 3},
                    {"name": f"Andhra {meal_type.title()} Option 5", "calories": calories//5, "protein": 11, "carbs": 22, "fiber": 4}
                ]
        
        return jsonify({
            'success': True,
            'menus': all_menus
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
        - Clear and concise (1-2 sentences max)

        Format your response as exactly 3 bullet points, each starting with "•"
        """
        
        print(f"Getting suggestions for: Cal={calorie_diff}, Pro={protein_diff}, Carb={carb_diff}, Fib={fiber_diff}")
        
        response = model.generate_content(prompt)
        suggestions = response.text.strip()
        
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
    app.run(debug=True, host='0.0.0.0', port=5001)
