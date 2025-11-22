"""
Flask 웹 대시보드 앱
"""
import sys
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Flask 앱 생성 및 설정
    
    Returns:
        Flask 앱 인스턴스
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    
    # CORS 설정
    CORS(app)
    
    # 설정
    app.config["JSON_AS_ASCII"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
    
    # 라우트 등록
    from .routes import dashboard, api
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(api.bp)
    
    logger.info("Flask 앱 초기화 완료")
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

