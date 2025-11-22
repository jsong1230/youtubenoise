"""
API 라우트 (JSON 엔드포인트)
"""
import sys
import json
from pathlib import Path
from flask import Blueprint, jsonify

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_DIR

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/stats")
def stats():
    """채널 통계 JSON"""
    channel_state_file = DATA_DIR / "channel_state.json"
    if not channel_state_file.exists():
        return jsonify({"error": "채널 상태 파일을 찾을 수 없습니다."}), 404
    
    try:
        with open(channel_state_file, 'r', encoding='utf-8') as f:
            channel_state = json.load(f)
        return jsonify(channel_state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/videos")
def videos():
    """영상 목록 JSON"""
    channel_state_file = DATA_DIR / "channel_state.json"
    if not channel_state_file.exists():
        return jsonify({"error": "채널 상태 파일을 찾을 수 없습니다."}), 404
    
    try:
        with open(channel_state_file, 'r', encoding='utf-8') as f:
            channel_state = json.load(f)
        
        videos_list = channel_state.get('videos', [])
        return jsonify({
            "videos": videos_list,
            "total": len(videos_list)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/usage")
def usage():
    """API 사용량 JSON"""
    api_usage_file = DATA_DIR / "api_usage.json"
    if not api_usage_file.exists():
        return jsonify({
            "daily": {},
            "monthly": {},
            "total": {"cost": 0.0, "requests": 0}
        })
    
    try:
        with open(api_usage_file, 'r', encoding='utf-8') as f:
            api_usage = json.load(f)
        return jsonify(api_usage)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/revenue")
def revenue():
    """수익 데이터 JSON (향후 구현)"""
    return jsonify({"message": "수익 데이터 API는 향후 구현 예정입니다.", "revenue": {}})

