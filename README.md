# 🍽️ Eat Mindfully - AI-Powered Nutrition Tracker

A comprehensive nutrition tracking application that uses Google Gemini AI to provide personalized meal recommendations with a focus on Andhra cuisine.

## ✨ Features

### 📊 Calorie Calculation
- **User Input**: Age, Gender, Height (cm), Weight (kg), Activity Level
- **Activity Options**:
  - No Activity
  - Light: Exercise 1-3 times/week
  - Moderate: Exercise 4-5 times/week
  - Active: Daily exercise or intense exercise 3-4 times/week
- **Calculations**: BMR (Basal Metabolic Rate) and TDEE (Total Daily Energy Expenditure)

### 🍴 Meal Planning & Tracking
- **4 Meal Types**: Breakfast, Lunch, Snack, Dinner (displayed horizontally)
- **AI-Generated Menus**: Andhra-style cuisine suggestions using Gemini API
- **Multi-select Dropdown**: Choose from AI-generated options with checkboxes
- **Custom Input**: Add manual items if not available in dropdown
- **Real-time Tracking**: Live calculation of consumed vs required calories
- **Macronutrient Tracking**: Protein, Carbohydrates, and Fiber tracking
- **AI Suggestions**: Personalized recommendations based on nutrition differences

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Flask 2.3.3
- **AI Model**: Google Gemini-2.0-Flash-Exp
- **Styling**: Custom CSS with modern gradient design
- **Environment**: Python 3.7+

## 📋 Prerequisites

- Python 3.7 or higher
- Google Gemini API key
- pip (Python package installer)

## 🚀 Installation Steps

### 1. Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd session3eatmindfully

# Or download and extract the project files
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up API Key
1. Edit the `key.properties` file and add your Gemini API key:
   ```
   key=your_actual_gemini_api_key_here
   ```
   
   The file should contain a single line with your API key in the format shown above.

### 5. Get Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Paste it in your `key.properties` file

### 6. Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

## 🎯 How to Use

### Step 1: Calculate Your Calorie Needs
1. Fill in your personal information (age, gender, height, weight)
2. Select your activity level
3. Click "Calculate Calories"
4. View your BMR, TDEE, and macronutrient requirements

### Step 2: Plan Your Meals
1. Click "Generate AI Menus" to get Andhra cuisine suggestions
2. Select items from the dropdown menus for each meal type
3. Add custom items if needed using the text input
4. Track your nutrition in real-time

### Step 3: Monitor Your Progress
- View real-time nutrition tracking with progress bars
- Get AI-powered suggestions based on your intake
- Adjust your meals based on recommendations

## 🔧 API Endpoints

- `GET /` - Main application page
- `POST /calculate_calories` - Calculate BMR, TDEE, and macronutrients
- `POST /generate_menu` - Generate AI-powered menu suggestions
- `POST /get_suggestions` - Get personalized nutrition recommendations

## 📁 Project Structure

```
session3eatmindfully/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── env_example.txt       # Environment variables template
├── README.md             # This file
└── templates/
    └── index.html        # Main HTML template
```

## 🎨 Features Overview

### Modern UI Design
- Gradient backgrounds and modern styling
- Responsive design for mobile and desktop
- Interactive progress bars and animations
- Clean, intuitive user interface

### AI Integration
- Optimized Gemini API calls
- Fallback menu options if API fails
- Contextual prompts for better results
- Error handling and user feedback

### Real-time Tracking
- Live nutrition calculations
- Visual progress indicators
- Instant feedback on meal selections
- Comprehensive macronutrient breakdown

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure your Gemini API key is correctly set in the `key.properties` file
   - Verify the API key is active and has proper permissions

2. **Port Already in Use**
   - Change the port in `app.py` from 5000 to another port (e.g., 5001)
   - Or kill the process using port 5000

3. **Module Not Found**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check if virtual environment is activated

4. **Menu Generation Fails**
   - The app includes fallback menu options
   - Check your internet connection
   - Verify API key permissions

## 🔒 Security Notes

- Never commit your `key.properties` file to version control
- Keep your API keys secure and private
- The application runs locally and doesn't store personal data

## 📈 Future Enhancements

- User authentication and data persistence
- Meal history and analytics
- Integration with fitness trackers
- More cuisine options
- Recipe suggestions with cooking instructions
- Social sharing features

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Eating Mindfully! 🍽️✨**
