# Project Restructuring and Refactoring Walkthrough

## Overview
This walkthrough documents the refactoring of the `youtubenoise` project to improve directory structure and configuration management. The main goal was to centralize project paths and constants into a single `config.py` module and update all scripts to use it.

## Changes Made

### 1. Centralized Configuration (`config.py`)
- Created `config.py` in the project root.
- Defined constants for key directories and files:
  - `PROJECT_ROOT`: Root directory of the project.
  - `DATA_DIR`: Directory for configuration files and presets (`data/`).
  - `OUTPUT_DIR`: Directory for generated content (`output/`).
  - `LOG_FILE`: Path to the main log file (`output/logs/app.log`).
  - `CONFIG_JSON_FILE`: Path to `config.json` (`data/config.json`).
  - `BGM_PRESETS_FILE`: Path to `bgm_presets.yaml` (`data/bgm_presets.yaml`).

### 2. Directory Structure Updates
- **`data/`**: Created to store configuration files (`config.json`, `bgm_presets.yaml`, etc.).
- **`output/`**: Created to store generated files, organized by type:
  - `output/audio/`: Generated audio files.
  - `output/images/`: Generated images.
  - `output/videos/`: Generated videos.
  - `output/logs/`: Log files and history.
- **`src/`**: Created for source code (currently empty, potential future use).
- **`tests/`**: Created for tests.

### 3. Script Refactoring
Updated the following scripts to import and use constants from `config.py`:

- **Core Scripts:**
  - `main.py`: Main entry point.
  - `scripts/scheduler.py`: Orchestrates the pipeline.
  - `scripts/update_statistics.py`: Updates YouTube statistics.
  - `scripts/refresh_youtube_token.py`: Refreshes OAuth tokens.

- **Generation Scripts:**
  - `scripts/generate_bgm.py`: Generates BGM audio.
  - `scripts/generate_audio.py`: Generates noise audio.
  - `scripts/generate_image.py`: Generates background images.
  - `scripts/generate_title_description.py`: Generates metadata.
  - `scripts/make_video.py`: Combines audio and image into video.
  - `scripts/generate_spot_difference.py`: Generates spot-the-difference videos.
  - `scripts/generate_brain_training.py`: Generates brain training videos.

- **Utility Scripts:**
  - `scripts/upload_youtube.py`: Uploads videos to YouTube.
  - `scripts/download_public_domain_music.py`: Downloads public domain music.
  - `scripts/download_public_domain_images.py`: Downloads public domain images.
  - `scripts/download_music_simple.py`: Simple music downloader.
  - `scripts/add_video_to_history.py`: Manually adds videos to history.

### 4. File Movements
- Moved `config/config.json` to `data/config.json`.
- Moved `config/bgm_presets.yaml` to `data/bgm_presets.yaml`.
- Moved other YAML configuration files to `data/`.

## Verification Results

### Static Analysis
- Verified that all modified scripts import `config` and use the defined constants.
- Checked for any remaining hardcoded paths (e.g., `project_root / "config"`, `project_root / "logs"`).

### Directory Check
- Confirmed `data/` contains the necessary configuration files.
- Confirmed `scripts/` contains the updated scripts.

## Next Steps
- Run the full pipeline to ensure end-to-end functionality.
- Monitor `output/logs/app.log` for any path-related errors.
- Consider moving `audio/` (source files) to `data/audio` or `assets/audio` for better organization.
