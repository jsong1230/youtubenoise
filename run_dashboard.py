"""
Flask 웹 대시보드 실행 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.web.app import create_app

if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("Flask 웹 대시보드 시작")
    print("=" * 60)
    port = 5001
    print(f"URL: http://localhost:{port}")
    print(f"대시보드: http://localhost:{port}/")
    print(f"영상 목록: http://localhost:{port}/videos")
    print(f"API 통계: http://localhost:{port}/api/stats")
    print(f"API 사용량: http://localhost:{port}/api/usage")
    print("=" * 60)
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 60)
    
    port = 5001  # macOS AirPlay Receiver가 5000을 사용할 수 있으므로 5001 사용
    app.run(host="0.0.0.0", port=port, debug=True)

