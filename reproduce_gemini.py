import os
import sys
from dotenv import load_dotenv
import logging

# Add app to path
sys.path.append(os.getcwd())

from app.curriculum_agent import generate_curriculum, AVAILABLE_MODELS

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_gemini():
    print("Testing Default Model (Gemini 3 Flash Preview)...")
    
    teacher_input = {
        "grade": 5,
        "subject": "Science",
        "topic": "Photosynthesis",
        "session_length_minutes": 15,
        "learning_goal_type": "practice",
        "group_format": "small_group"
    }
    
    try:
        # Use default model (should be Gemini 3 Flash Preview)
        result = generate_curriculum(teacher_input)
        print("Success!")
        print(f"Teacher Guide title: {result.get('teacher_guide', {}).get('metadata', {}).get('title')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini()
