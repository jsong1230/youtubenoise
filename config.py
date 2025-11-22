import os
from pathlib import Path
from dotenv import load_dotenv

# Project Root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Load Environment Variables
load_dotenv(PROJECT_ROOT / ".env")

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"

# Subdirectories
VIDEOS_DIR = OUTPUT_DIR / "videos"
IMAGES_DIR = OUTPUT_DIR / "images"
LOGS_DIR = OUTPUT_DIR / "logs"

# Ensure directories exist
for directory in [DATA_DIR, OUTPUT_DIR, VIDEOS_DIR, IMAGES_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# File Paths
LOG_FILE = LOGS_DIR / "app.log"
TOKEN_FILE = PROJECT_ROOT / "token.json"
BGM_PRESETS_FILE = DATA_DIR / "bgm_presets.yaml"
AMBIENCE_PRESETS_FILE = DATA_DIR / "ambience_presets.yaml"
BRAIN_TRAINING_PRESETS_FILE = DATA_DIR / "brain_training_presets.yaml"
SPOT_DIFFERENCE_PRESETS_FILE = DATA_DIR / "spot_difference_presets.yaml"
POMODORO_UI_TEXT_FILE = DATA_DIR / "pomodoro_ui_text.yaml"
SLEEP_STORY_PROMPTS_FILE = DATA_DIR / "sleep_story_prompts.yaml"
CONFIG_JSON_FILE = DATA_DIR / "config.json"

# Export paths for use in other modules
__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "OUTPUT_DIR",
    "SRC_DIR",
    "TESTS_DIR",
    "VIDEOS_DIR",
    "IMAGES_DIR",
    "LOGS_DIR",
    "LOG_FILE",
    "TOKEN_FILE",
    "BGM_PRESETS_FILE",
    "AMBIENCE_PRESETS_FILE",
    "BRAIN_TRAINING_PRESETS_FILE",
    "SPOT_DIFFERENCE_PRESETS_FILE",
    "POMODORO_UI_TEXT_FILE",
    "SLEEP_STORY_PROMPTS_FILE",
    "CONFIG_JSON_FILE",
]
