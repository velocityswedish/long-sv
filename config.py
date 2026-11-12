"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY SWEDISH"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "SWEDISH"
HANDLE = "@velocityswedish"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'sv',
 'name': 'Swedish',
 'native_name': 'Svenska',
 'history_key': 'swedish',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'sv-SE-SofieNeural',
 'native_fallback_voice': 'sv-SE-MattiasNeural',
 'native_engine': 'edge',
 'native_lang_code': 'sv',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'SVENSKA',
 'translit_label': 'SAY IT LIKE',
 'flag': 'se',
 'greeting': 'Hej!',
 'encouragement': 'Fantastiskt!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖåäö'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Motivation',
 'Love': 'Kärlek',
 'Success': 'Framgång',
 'Wisdom': 'Visdom',
 'Happiness': 'Lycka',
 'Self Improvement': 'Självförbättring',
 'Gratitude': 'Tacksamhet',
 'Friendship': 'Vänskap',
 'Hope': 'Hopp',
 'Creativity': 'Kreativitet',
 'Inner Peace': 'Inre Fred',
 'Confidence': 'Självsäkerhet',
 'Perseverance': 'Uthållighet',
 'Inspiration': 'Inspiration',
 'Positive Life': 'Positivt Liv',
 'Courage': 'Mod',
 'Kindness': 'Vänlighet',
 'Patience': 'Tålamod',
 'Forgiveness': 'Förlåtelse',
 'Strength': 'Styrka',
 'Joy': 'Glädje',
 'Balance': 'Balans',
 'Growth': 'Tillväxt',
 'Purpose': 'Syfte',
 'Mindfulness': 'Mindfulness',
 'Travel & Airport': 'Resor & Flygplats',
 'Ordering Food & Dining': 'Beställa mat & Äta ute',
 'Shopping & Prices': 'Shopping & Priser',
 'Asking for Directions': 'Fråga om vägen',
 'Hotel & Accommodation': 'Hotell & Boende',
 'Daily Routine': 'Vardagliga rutiner',
 'Meeting People & Greetings': 'Träffa folk & Hälsningar',
 'Emergency & Health': 'Nödsituationer & Hälsa',
 'Public Transportation': 'Kollektivtrafik',
 'Work & Office': 'Arbete & Kontor',
 'Weather & Small Talk': 'Väder & Småprat',
 'Coffee Shop & Bakery': 'Kafé & Bageri',
 'Family & Home': 'Familj & Hem',
 'Hobbies & Free Time': 'Hobbys & Fritid',
 'Dating & Romance': 'Dejting & Romantik',
 'Phone Calls & Messages': 'Telefonsamtal & Meddelanden',
 'Banking & Money': 'Bank & Pengar',
 'Doctor & Pharmacy': 'Läkare & Apotek',
 'Sports & Fitness': 'Sport & Träning',
 'Celebrations & Parties': 'Firanden & Fester',
 'Feelings & Emotions': 'Känslor & Tillstånd',
 'Agreeing & Disagreeing': 'Hålla med & Inte hålla med',
 'Making Plans': 'Att göra planer',
 'Common Native Slang': 'Vanligt vardagsspråk',
 'Cultural Traditions': 'Kulturella traditioner'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnswedish',
 '#swedishlessons',
 '#swedishforbeginners',
 '#languagelearning',
 '#swedishvocabulary',
 '#velocityswedish',
 '#dailyswedish',
 '#swedish',
 '#learnlanguages',
 '#speakswedish']
# ==== HASHTAGS END ====
