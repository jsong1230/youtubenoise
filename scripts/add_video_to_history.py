"""
히스토리에 Video ID 수동 추가 스크립트
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 프로젝트 루트 설정
# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import OUTPUT_DIR, PROJECT_ROOT

def load_history() -> List[Dict]:
    """히스토리 파일 로드"""
    history_file = OUTPUT_DIR / "logs" / "history.json"
    if not history_file.exists():
        return []
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return history if isinstance(history, list) else []
    except Exception as e:
        print(f"히스토리 파일 로드 실패: {e}")
        return []


def save_history(history: List[Dict]):
    """히스토리 파일 저장"""
    history_file = OUTPUT_DIR / "logs" / "history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"히스토리 저장 완료: {history_file}")
    except Exception as e:
        print(f"히스토리 저장 실패: {e}")
        raise


def add_video(video_id: str, title: str = "", published_at: str = ""):
    """히스토리에 Video ID 추가"""
    history = load_history()
    
    # 중복 확인
    existing_ids = {entry.get('video_id') for entry in history if entry.get('video_id')}
    if video_id in existing_ids:
        print(f"Video ID {video_id}는 이미 히스토리에 있습니다.")
        return
    
    # 새 항목 추가
    entry = {
        'video_id': video_id,
        'status': 'completed',
        'metadata': {
            'title': title or f'Video {video_id}'
        },
        'start_time': published_at or datetime.now().isoformat(),
        'added_manually': True
    }
    
    history.append(entry)
    save_history(history)
    print(f"Video ID {video_id} 추가 완료!")
    print(f"영상 URL: https://www.youtube.com/watch?v={video_id}")


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python add_video_to_history.py <video_id> [title] [published_at]")
        print("\n예시:")
        print("  python add_video_to_history.py abc123xyz")
        print("  python add_video_to_history.py abc123xyz 'My Video Title' '2025-11-16T10:00:00'")
        sys.exit(1)
    
    video_id = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else ""
    published_at = sys.argv[3] if len(sys.argv) > 3 else ""
    
    add_video(video_id, title, published_at)


if __name__ == "__main__":
    main()

