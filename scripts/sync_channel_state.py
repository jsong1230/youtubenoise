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
from google.auth.transport.requests import Request
import os
from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_DIR, LOG_FILE, OUTPUT_DIR, PROJECT_ROOT
from scripts.utils import setup_logging

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = setup_logging()


def get_youtube_client():
    """YouTube API 클라이언트 생성"""
    # 환경변수에서 인증 정보 확인
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if not (client_id and client_secret and refresh_token):
        logger.error("YouTube 인증 정보가 .env 파일에 설정되지 않았습니다.")
        logger.error("YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN을 확인해주세요.")
        sys.exit(1)
    
    credentials = Credentials(
        token=None,  # 처음에는 None, refresh로 획득
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=[
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube.readonly',  # 채널 정보 읽기용
            'https://www.googleapis.com/auth/yt-analytics.readonly'
        ]
    )
    
    # 토큰 갱신
    try:
        credentials.refresh(Request())
        logger.info("YouTube API 인증 완료")
    except Exception as e:
        logger.error(f"토큰 갱신 실패: {e}")
        logger.error("YOUTUBE_REFRESH_TOKEN이 유효한지 확인해주세요.")
        sys.exit(1)
    
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
        
        # 영상 목록 가져오기 (모든 영상)
        logger.info("\n영상 목록 가져오는 중...")
        all_videos = []
        next_page_token = None
        
        # 페이지네이션으로 모든 영상 가져오기
        while True:
            videos_request = youtube.search().list(
                part='snippet',
                forMine=True,
                type='video',
                maxResults=50,
                order='date',
                pageToken=next_page_token
            )
            videos_response = videos_request.execute()
            
            all_videos.extend(videos_response.get('items', []))
            next_page_token = videos_response.get('nextPageToken')
            
            if not next_page_token:
                break
        
        logger.info(f"  총 {len(all_videos)}개 영상 가져옴")
        
        # 영상 상세 정보 가져오기 (조회수, 좋아요 등)
        if all_videos:
            video_ids = [video['id']['videoId'] for video in all_videos]
            
            # 50개씩 나눠서 가져오기 (API 제한)
            video_details = []
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                videos_detail_request = youtube.videos().list(
                    part='statistics,snippet,contentDetails',
                    id=','.join(batch_ids)
                )
                videos_detail_response = videos_detail_request.execute()
                video_details.extend(videos_detail_response.get('items', []))
            
            # 영상 목록 저장
            state['videos'] = []
            for video_detail in video_details:
                video_info = {
                    'video_id': video_detail['id'],
                    'title': video_detail['snippet']['title'],
                    'description': video_detail['snippet']['description'][:200] if video_detail['snippet'].get('description') else '',
                    'published_at': video_detail['snippet']['publishedAt'],
                    'thumbnail': video_detail['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'views': int(video_detail['statistics'].get('viewCount', 0)),
                    'likes': int(video_detail['statistics'].get('likeCount', 0)),
                    'comments': int(video_detail['statistics'].get('commentCount', 0)),
                    'duration': video_detail['contentDetails'].get('duration', '')
                }
                state['videos'].append(video_info)
        
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
            state['content_pillars'][pillar]['total_views'] = 0
        
        # 영상 분류 및 통계 계산
        for video_info in state.get('videos', []):
            title = video_info['title'].lower()
            
            # 제목에서 필러 감지
            for pillar, keywords in pillar_keywords.items():
                if any(keyword in title for keyword in keywords):
                    state['content_pillars'][pillar]['count'] += 1
                    state['content_pillars'][pillar]['total_views'] += video_info['views']
                    
                    # 최근 업로드 시간 업데이트
                    published_at = video_info['published_at']
                    if (state['content_pillars'][pillar]['last_upload'] is None or
                        published_at > state['content_pillars'][pillar]['last_upload']):
                        state['content_pillars'][pillar]['last_upload'] = published_at
                    break
        
        # 필러별 평균 조회수 계산
        for pillar, data in state['content_pillars'].items():
            if data['count'] > 0:
                data['avg_views'] = data['total_views'] // data['count']
            else:
                data['avg_views'] = 0
        
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
