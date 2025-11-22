"""
채널 상태 동기화 스크립트
YouTube API로 채널 통계를 가져와 channel_state.json 업데이트
"""
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_DIR, LOG_FILE, OUTPUT_DIR, PROJECT_ROOT

# 환경 변수 로드
load_dotenv()

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


def get_youtube_client():
    """YouTube API 클라이언트 생성"""
    # OAuth 토큰 사용
    token_file = PROJECT_ROOT / "token.json"
    
    if not token_file.exists():
        logger.error(f"토큰 파일을 찾을 수 없습니다: {token_file}")
        logger.error("먼저 scripts/refresh_youtube_token.py를 실행하여 토큰을 발급받으세요.")
        sys.exit(1)
    
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    credentials = Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.getenv('YOUTUBE_CLIENT_ID'),
        client_secret=os.getenv('YOUTUBE_CLIENT_SECRET')
    )
    
    return build('youtube', 'v3', credentials=credentials)


def sync_channel_state():
    """채널 상태 동기화"""
    try:
        logger.info("=" * 60)
        logger.info("채널 상태 동기화 시작")
        logger.info("=" * 60)
        
        # YouTube API 클라이언트
        youtube = get_youtube_client()
        
        # 채널 통계 가져오기
        logger.info("YouTube API로 채널 통계 가져오는 중...")
        request = youtube.channels().list(
            part='statistics,snippet',
            mine=True
        )
        response = request.execute()
        
        if not response.get('items'):
            logger.error("채널 정보를 찾을 수 없습니다.")
            sys.exit(1)
        
        channel = response['items'][0]
        stats = channel['statistics']
        snippet = channel['snippet']
        
        logger.info(f"채널 발견: {snippet['title']}")
        
        # channel_state.json 로드
        state_file = DATA_DIR / "channel_state.json"
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # 기본 통계 업데이트
        state['channel_id'] = channel['id']
        state['channel_name'] = snippet['title']
        state['total_videos'] = int(stats.get('videoCount', 0))
        state['total_views'] = int(stats.get('viewCount', 0))
        state['total_subscribers'] = int(stats.get('subscriberCount', 0))
        state['last_sync'] = datetime.now().isoformat()
        
        logger.info(f"  총 영상: {state['total_videos']}개")
        logger.info(f"  총 조회수: {state['total_views']:,}회")
        logger.info(f"  구독자: {state['total_subscribers']:,}명")
        
        # 영상 목록 가져오기 (최근 50개)
        logger.info("\n최근 영상 목록 가져오는 중...")
        videos_request = youtube.search().list(
            part='snippet',
            forMine=True,
            type='video',
            maxResults=50,
            order='date'
        )
        videos_response = videos_request.execute()
        
        # 콘텐츠 필러별 분류 (제목 기반)
        pillar_keywords = {
            'brain_training': ['두뇌', 'brain', 'training', '기억', 'memory'],
            'spot_difference': ['틀린그림', 'spot', 'difference', '찾기'],
            'bgm_focus': ['집중', 'focus', 'study', 'work', '공부', '업무'],
            'bgm_sleep': ['수면', 'sleep', 'calm', '잠', '힐링', 'relax'],
            'ai_explainer': ['ai', 'gpt', 'claude', '자동화', 'automation']
        }
        
        # 필러별 카운트 초기화
        for pillar in state['content_pillars']:
            state['content_pillars'][pillar]['count'] = 0
        
        # 영상 분류
        for video in videos_response.get('items', []):
            title = video['snippet']['title'].lower()
            
            # 제목에서 필러 감지
            for pillar, keywords in pillar_keywords.items():
                if any(keyword in title for keyword in keywords):
                    state['content_pillars'][pillar]['count'] += 1
                    
                    # 최근 업로드 시간 업데이트
                    published_at = video['snippet']['publishedAt']
                    if (state['content_pillars'][pillar]['last_upload'] is None or
                        published_at > state['content_pillars'][pillar]['last_upload']):
                        state['content_pillars'][pillar]['last_upload'] = published_at
                    break
        
        # 필러별 통계 로깅
        logger.info("\n콘텐츠 필러별 통계:")
        for pillar, data in state['content_pillars'].items():
            logger.info(f"  {pillar}: {data['count']}개 영상")
        
        # 저장
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ 채널 상태 동기화 완료: {state_file}")
        logger.info("=" * 60)
        
        return state
        
    except Exception as e:
        logger.error(f"채널 상태 동기화 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    sync_channel_state()
