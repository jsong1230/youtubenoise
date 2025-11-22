"""
대시보드 라우트
"""
import sys
import json
from pathlib import Path
from flask import Blueprint, render_template

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_DIR

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    """홈 대시보드"""
    # 채널 상태 로드
    channel_state_file = DATA_DIR / "channel_state.json"
    channel_state = {}
    if channel_state_file.exists():
        try:
            with open(channel_state_file, 'r', encoding='utf-8') as f:
                channel_state = json.load(f)
        except Exception:
            pass
    
    # API 사용량 로드
    api_usage_file = DATA_DIR / "api_usage.json"
    api_usage = {}
    if api_usage_file.exists():
        try:
            with open(api_usage_file, 'r', encoding='utf-8') as f:
                api_usage = json.load(f)
        except Exception:
            pass
    
    return render_template(
        "dashboard.html",
        channel_state=channel_state,
        api_usage=api_usage
    )


@bp.route("/videos")
def videos():
    """영상 목록 페이지"""
    # 채널 상태 로드
    channel_state_file = DATA_DIR / "channel_state.json"
    channel_state = {}
    if channel_state_file.exists():
        try:
            with open(channel_state_file, 'r', encoding='utf-8') as f:
                channel_state = json.load(f)
        except Exception:
            pass
    
    return render_template("videos.html", channel_state=channel_state)

