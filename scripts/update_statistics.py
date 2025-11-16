"""
YouTube 영상 통계 업데이트 스크립트
업로드된 모든 영상의 조회수, 좋아요, 댓글 수 등을 업데이트
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

# 로깅 설정
log_file = project_root / "logs" / "app.log"
log_file.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# YouTube API 스코프
# 참고: 통계 읽기를 위해서는 youtube.readonly 스코프가 필요합니다.
# YouTube Analytics API를 사용하려면 yt-analytics.readonly 스코프가 필요합니다.
# 현재 refresh token이 youtube.upload만 포함하는 경우, 통계 업데이트가 실패할 수 있습니다.
# 해결: Google Cloud Console에서 스코프를 추가하고 refresh token을 재발급하세요.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
ANALYTICS_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]


def get_authenticated_service():
    """인증된 YouTube API 서비스 객체 반환"""
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if not (client_id and client_secret and refresh_token):
        raise ValueError("YouTube 인증 정보가 .env 파일에 설정되지 않았습니다.")
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    
    try:
        creds.refresh(Request())
        logger.info("YouTube API 인증 완료")
    except Exception as e:
        logger.error(f"토큰 갱신 실패: {e}")
        raise
    
    return build('youtube', 'v3', credentials=creds)


def get_public_api_service():
    """Public API 키를 사용한 YouTube API 서비스 객체 반환 (통계 읽기용)"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        logger.warning("YOUTUBE_API_KEY가 설정되지 않았습니다. Public API를 사용할 수 없습니다.")
        return None
    
    try:
        service = build('youtube', 'v3', developerKey=api_key)
        logger.info("Public API 서비스 생성 완료")
        return service
    except Exception as e:
        logger.error(f"Public API 서비스 생성 실패: {e}")
        return None


def get_analytics_service():
    """YouTube Analytics API 서비스 객체 반환"""
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if not (client_id and client_secret and refresh_token):
        logger.warning("YouTube 인증 정보가 없습니다. Analytics API를 사용할 수 없습니다.")
        return None
    
    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=ANALYTICS_SCOPES
        )
        
        creds.refresh(Request())
        logger.info("YouTube Analytics API 인증 완료")
        
        # YouTube Analytics API v2 사용
        service = build('youtubeAnalytics', 'v2', credentials=creds)
        return service
    except Exception as e:
        logger.warning(f"YouTube Analytics API 인증 실패: {e}")
        logger.warning("Analytics API를 사용하려면 yt-analytics.readonly 스코프가 필요합니다.")
        return None


def get_reporting_service():
    """YouTube Reporting API 서비스 객체 반환"""
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if not (client_id and client_secret and refresh_token):
        logger.warning("YouTube 인증 정보가 없습니다. Reporting API를 사용할 수 없습니다.")
        return None
    
    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=ANALYTICS_SCOPES  # Reporting API도 동일한 스코프 사용
        )
        
        creds.refresh(Request())
        logger.info("YouTube Reporting API 인증 완료")
        
        # YouTube Reporting API v1 사용
        service = build('youtubereporting', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.warning(f"YouTube Reporting API 인증 실패: {e}")
        logger.warning("Reporting API를 사용하려면 yt-analytics.readonly 스코프가 필요합니다.")
        return None


def get_channel_id_from_youtube(youtube) -> Optional[str]:
    """인증된 YouTube API에서 채널 ID 가져오기"""
    try:
        channels_response = youtube.channels().list(
            part='id',
            mine=True
        ).execute()
        
        if channels_response.get('items'):
            return channels_response['items'][0]['id']
        return None
    except Exception as e:
        logger.error(f"채널 ID 가져오기 실패: {e}")
        return None


def get_video_analytics(analytics_service, channel_id: str, video_id: str, start_date: str, end_date: str) -> Optional[Dict]:
    """YouTube Analytics API를 사용하여 영상 통계 가져오기"""
    try:
        # Analytics API는 채널 전체 통계만 제공하므로, 개별 영상 통계는 Data API 사용
        # Analytics API는 주로 채널 레벨 통계에 유용합니다
        logger.debug(f"Analytics API는 채널 레벨 통계에 사용됩니다. 개별 영상은 Data API를 사용합니다.")
        return None
    except Exception as e:
        logger.error(f"Analytics API 통계 가져오기 실패: {e}")
        return None


def get_channel_analytics(analytics_service, channel_id: str, start_date: str, end_date: str) -> Optional[Dict]:
    """YouTube Analytics API를 사용하여 채널 통계 가져오기"""
    try:
        if not analytics_service or not channel_id:
            return None
        
        # 채널 통계 조회 (조회수, 시청 시간 등)
        response = analytics_service.reports().query(
            ids=f'channel=={channel_id}',
            startDate=start_date,
            endDate=end_date,
            metrics='views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments,shares',
            dimensions='day'
        ).execute()
        
        if response.get('rows'):
            # 데이터 집계
            total_views = sum(row[0] for row in response['rows'])
            total_minutes = sum(row[1] for row in response['rows'])
            total_subscribers = sum(row[3] for row in response['rows'])
            total_likes = sum(row[4] for row in response['rows'])
            total_comments = sum(row[5] for row in response['rows'])
            total_shares = sum(row[6] for row in response['rows'])
            
            return {
                'views': total_views,
                'estimated_minutes_watched': total_minutes,
                'subscribers_gained': total_subscribers,
                'likes': total_likes,
                'comments': total_comments,
                'shares': total_shares,
                'period': f'{start_date} to {end_date}'
            }
        
        return None
    except Exception as e:
        logger.error(f"채널 Analytics 통계 가져오기 실패: {e}")
        return None


def list_reporting_jobs(reporting_service, channel_id: str) -> List[Dict]:
    """YouTube Reporting API 리포트 작업 목록 가져오기"""
    try:
        if not reporting_service or not channel_id:
            return []
        
        # 리포트 작업 목록 조회
        response = reporting_service.jobs().list(
            onBehalfOfContentOwner=channel_id
        ).execute()
        
        jobs = response.get('jobs', [])
        logger.info(f"리포트 작업 {len(jobs)}개 발견")
        return jobs
    except Exception as e:
        logger.error(f"리포트 작업 목록 가져오기 실패: {e}")
        return []


def get_channel_reporting_stats(reporting_service, channel_id: str) -> Optional[Dict]:
    """YouTube Reporting API를 사용하여 채널 리포트 통계 가져오기"""
    try:
        if not reporting_service or not channel_id:
            return None
        
        # 리포트 작업 목록 확인
        jobs = list_reporting_jobs(reporting_service, channel_id)
        
        if not jobs:
            logger.info("리포트 작업이 없습니다. Reporting API는 리포트 작업을 먼저 생성해야 합니다.")
            return None
        
        # 가장 최근 작업의 리포트 다운로드 (간단한 예시)
        # 실제로는 리포트 타입에 따라 다르게 처리해야 함
        logger.info("Reporting API 리포트 데이터 처리는 복잡하므로 Analytics API를 권장합니다.")
        return None
    except Exception as e:
        logger.error(f"Reporting API 통계 가져오기 실패: {e}")
        return None


def get_channel_videos(youtube, max_results: int = 50) -> List[Dict]:
    """YouTube 채널의 최근 업로드 영상 목록 가져오기"""
    try:
        # 채널 ID 가져오기 (인증된 사용자의 채널)
        channels_response = youtube.channels().list(
            part='contentDetails',
            mine=True
        ).execute()
        
        if not channels_response.get('items'):
            logger.warning("채널을 찾을 수 없습니다.")
            return []
        
        channel_id = channels_response['items'][0]['id']
        uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # 업로드 플레이리스트에서 영상 가져오기
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            playlist_items_response = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page_token
            ).execute()
            
            for item in playlist_items_response.get('items', []):
                video_id = item['contentDetails']['videoId']
                snippet = item['snippet']
                
                videos.append({
                    'video_id': video_id,
                    'title': snippet.get('title', ''),
                    'published_at': snippet.get('publishedAt', ''),
                    'description': snippet.get('description', '')
                })
            
            next_page_token = playlist_items_response.get('nextPageToken')
            if not next_page_token:
                break
        
        logger.info(f"채널에서 {len(videos)}개의 영상 발견")
        return videos
        
    except Exception as e:
        logger.error(f"채널 영상 목록 가져오기 실패: {e}")
        return []


def sync_from_youtube() -> List[Dict]:
    """YouTube 채널에서 영상 목록을 가져와서 히스토리에 동기화"""
    try:
        logger.info("YouTube 채널에서 영상 목록 동기화 중...")
        
        # YouTube API 서비스 생성
        try:
            youtube = get_authenticated_service()
        except Exception as e:
            logger.error(f"YouTube API 인증 실패: {e}")
            return []
        
        # 채널에서 영상 목록 가져오기
        channel_videos = get_channel_videos(youtube, max_results=50)
        if not channel_videos:
            logger.warning("채널에서 영상을 찾을 수 없습니다.")
            return []
        
        # 기존 히스토리 로드
        history = load_history()
        existing_video_ids = {entry.get('video_id') for entry in history if entry.get('video_id')}
        
        # 새로운 영상 추가
        new_count = 0
        for video in channel_videos:
            video_id = video['video_id']
            if video_id not in existing_video_ids:
                # 통계 가져오기
                stats = get_video_statistics(youtube, video_id)
                
                history_entry = {
                    'start_time': video.get('published_at', datetime.now().isoformat()),
                    'video_id': video_id,
                    'status': 'completed',
                    'metadata': {
                        'title': video.get('title', ''),
                        'description': video.get('description', '')
                    },
                    'statistics': stats if stats else {},
                    'synced_from_youtube': True,
                    'synced_at': datetime.now().isoformat()
                }
                history.append(history_entry)
                new_count += 1
                logger.info(f"새 영상 추가: {video_id} - {video.get('title', '')[:50]}")
        
        if new_count > 0:
            save_history(history)
            logger.info(f"히스토리에 {new_count}개의 새 영상 추가됨")
        else:
            logger.info("추가할 새 영상이 없습니다.")
        
        return history
        
    except Exception as e:
        logger.error(f"YouTube 동기화 실패: {e}", exc_info=True)
        return []


def load_history() -> List[Dict]:
    """히스토리 파일 로드"""
    history_file = project_root / "logs" / "history.json"
    if not history_file.exists():
        logger.warning(f"히스토리 파일이 없습니다: {history_file}")
        return []
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return history if isinstance(history, list) else []
    except Exception as e:
        logger.error(f"히스토리 파일 로드 실패: {e}")
        return []


def save_history(history: List[Dict]):
    """히스토리 파일 저장"""
    history_file = project_root / "logs" / "history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info(f"히스토리 저장 완료: {history_file}")
    except Exception as e:
        logger.error(f"히스토리 저장 실패: {e}")
        raise


def get_video_statistics(youtube, video_id: str) -> Optional[Dict]:
    """YouTube 영상 통계 가져오기"""
    try:
        request = youtube.videos().list(
            part='statistics,snippet,contentDetails',
            id=video_id
        )
        response = request.execute()
        
        if not response.get('items'):
            logger.warning(f"영상을 찾을 수 없습니다: {video_id}")
            return None
        
        item = response['items'][0]
        stats = item.get('statistics', {})
        snippet = item.get('snippet', {})
        content_details = item.get('contentDetails', {})
        
        return {
            'view_count': int(stats.get('viewCount', 0)),
            'like_count': int(stats.get('likeCount', 0)),
            'comment_count': int(stats.get('commentCount', 0)),
            'title': snippet.get('title', ''),
            'published_at': snippet.get('publishedAt', ''),
            'duration': content_details.get('duration', ''),
            'updated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"영상 통계 가져오기 실패 ({video_id}): {e}")
        return None


def get_video_statistics_public(video_id: str) -> Optional[Dict]:
    """Public API를 사용하여 YouTube 영상 통계 가져오기 (인증 없이)"""
    try:
        # Public API 서비스 생성
        youtube = get_public_api_service()
        if not youtube:
            return None
        
        request = youtube.videos().list(
            part='statistics,snippet,contentDetails',
            id=video_id
        )
        response = request.execute()
        
        if not response.get('items'):
            logger.warning(f"영상을 찾을 수 없습니다: {video_id}")
            return None
        
        item = response['items'][0]
        stats = item.get('statistics', {})
        snippet = item.get('snippet', {})
        content_details = item.get('contentDetails', {})
        
        return {
            'view_count': int(stats.get('viewCount', 0)),
            'like_count': int(stats.get('likeCount', 0)),
            'comment_count': int(stats.get('commentCount', 0)),
            'title': snippet.get('title', ''),
            'published_at': snippet.get('publishedAt', ''),
            'duration': content_details.get('duration', ''),
            'updated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Public API로 영상 통계 가져오기 실패 ({video_id}): {e}")
        return None


def update_all_statistics() -> Dict:
    """모든 영상의 통계 업데이트"""
    try:
        logger.info("=" * 60)
        logger.info("YouTube 영상 통계 업데이트 시작")
        logger.info("=" * 60)
        
        # 히스토리 로드
        history = load_history()
        if not history:
            logger.warning("업데이트할 영상이 없습니다.")
            return {"updated": 0, "failed": 0, "total": 0}
        
        # YouTube API 서비스 생성
        try:
            youtube = get_authenticated_service()
        except Exception as e:
            logger.error(f"YouTube API 인증 실패: {e}")
            logger.warning("통계 업데이트를 위해 YouTube API 스코프가 필요합니다.")
            logger.warning("자세한 내용은 docs/STATISTICS.md를 참고하세요.")
            return {"updated": 0, "failed": len([e for e in history if e.get('video_id')]), "total": len([e for e in history if e.get('video_id')])}
        
        # 통계 업데이트
        updated_count = 0
        failed_count = 0
        
        # Public API 시도 (스코프 문제 해결)
        public_youtube = get_public_api_service()
        
        # Analytics API 시도 (더 상세한 통계)
        analytics_service = get_analytics_service()
        reporting_service = get_reporting_service()
        channel_id = None
        if analytics_service or reporting_service:
            try:
                # 인증된 YouTube API에서 채널 ID 가져오기
                auth_youtube = get_authenticated_service()
                channel_id = get_channel_id_from_youtube(auth_youtube)
                if channel_id:
                    if analytics_service:
                        logger.info(f"Analytics API 사용 가능: 채널 ID {channel_id}")
                    if reporting_service:
                        logger.info(f"Reporting API 사용 가능: 채널 ID {channel_id}")
            except Exception as e:
                logger.debug(f"채널 ID 가져오기 실패: {e}")
        
        for entry in history:
            video_id = entry.get('video_id')
            if not video_id:
                continue
            
            logger.info(f"통계 업데이트 중: {video_id}")
            
            # 먼저 Public API 시도 (인증 없이 가능)
            stats = None
            if public_youtube:
                stats = get_video_statistics_public(video_id)
            
            # Public API 실패 시 인증된 API 시도
            if not stats:
                try:
                    stats = get_video_statistics(youtube, video_id)
                except Exception as e:
                    logger.debug(f"인증된 API 실패 ({video_id}): {e}")
            
            if stats:
                # 통계 형식 변환 (공통 형식으로)
                statistics = {
                    'viewCount': stats.get('view_count', 0),
                    'likeCount': stats.get('like_count', 0),
                    'commentCount': stats.get('comment_count', 0),
                    'favoriteCount': 0
                }
                
                # 기존 통계와 비교
                old_stats = entry.get('statistics', {})
                entry['statistics'] = statistics
                entry['last_updated'] = datetime.now().isoformat()
                
                # 제목 업데이트
                if stats.get('title'):
                    entry['metadata'] = entry.get('metadata', {})
                    entry['metadata']['title'] = stats['title']
                
                # 변경사항 로그
                if old_stats:
                    view_diff = statistics['viewCount'] - old_stats.get('viewCount', 0)
                    like_diff = statistics['likeCount'] - old_stats.get('likeCount', 0)
                    if view_diff > 0 or like_diff > 0:
                        logger.info(f"  조회수: {old_stats.get('viewCount', 0)} → {statistics['viewCount']} (+{view_diff})")
                        logger.info(f"  좋아요: {old_stats.get('likeCount', 0)} → {statistics['likeCount']} (+{like_diff})")
                else:
                    logger.info(f"  조회수: {statistics['viewCount']}, 좋아요: {statistics['likeCount']}")
                
                updated_count += 1
            else:
                failed_count += 1
        
        # 히스토리 저장
        save_history(history)
        
        result = {
            "updated": updated_count,
            "failed": failed_count,
            "total": len([e for e in history if e.get('video_id')])
        }
        
        logger.info("=" * 60)
        logger.info(f"통계 업데이트 완료: {updated_count}개 성공, {failed_count}개 실패 (전체 {result['total']}개)")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"통계 업데이트 중 오류 발생: {e}", exc_info=True)
        raise


def generate_report() -> str:
    """영상 통계 리포트 생성"""
    try:
        history = load_history()
        if not history:
            return "업로드된 영상이 없습니다."
        
        # 통계 집계
        total_videos = len([e for e in history if e.get('video_id')])
        total_views = 0
        total_likes = 0
        total_comments = 0
        
        videos_with_stats = []
        for entry in history:
            video_id = entry.get('video_id')
            if not video_id:
                continue
            
            stats = entry.get('statistics', {})
            if stats:
                views = stats.get('viewCount', stats.get('view_count', 0))
                likes = stats.get('likeCount', stats.get('like_count', 0))
                comments = stats.get('commentCount', stats.get('comment_count', 0))
                
                total_views += views
                total_likes += likes
                total_comments += comments
                
                videos_with_stats.append({
                    'video_id': video_id,
                    'title': stats.get('title', entry.get('metadata', {}).get('title', 'Unknown')),
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'published_at': stats.get('published_at', entry.get('start_time', '')),
                    'last_updated': entry.get('last_updated', '')
                })
        
        # 리포트 생성
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("YouTube 영상 통계 리포트")
        report_lines.append("=" * 80)
        report_lines.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        report_lines.append("전체 통계:")
        report_lines.append(f"  총 영상 수: {total_videos}개")
        report_lines.append(f"  총 조회수: {total_views:,}회")
        report_lines.append(f"  총 좋아요: {total_likes:,}개")
        report_lines.append(f"  총 댓글: {total_comments:,}개")
        if total_videos > 0:
            report_lines.append(f"  평균 조회수: {total_views // total_videos:,}회/영상")
            report_lines.append(f"  평균 좋아요: {total_likes // total_videos:,}개/영상")
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("영상별 상세 통계:")
        report_lines.append("-" * 80)
        
        # 조회수 순으로 정렬
        videos_with_stats.sort(key=lambda x: x['views'], reverse=True)
        
        for i, video in enumerate(videos_with_stats, 1):
            report_lines.append(f"\n{i}. {video['title']}")
            report_lines.append(f"   Video ID: {video['video_id']}")
            report_lines.append(f"   URL: https://www.youtube.com/watch?v={video['video_id']}")
            report_lines.append(f"   조회수: {video['views']:,}회")
            report_lines.append(f"   좋아요: {video['likes']:,}개")
            report_lines.append(f"   댓글: {video['comments']:,}개")
            if video['published_at']:
                report_lines.append(f"   업로드: {video['published_at']}")
            if video['last_updated']:
                report_lines.append(f"   마지막 업데이트: {video['last_updated']}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"리포트 생성 중 오류 발생: {e}", exc_info=True)
        return f"리포트 생성 실패: {e}"


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube 영상 통계 업데이트 및 리포트")
    parser.add_argument(
        "--update",
        action="store_true",
        help="모든 영상의 통계 업데이트"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="YouTube 채널에서 영상 목록 동기화"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="통계 리포트 출력"
    )
    
    args = parser.parse_args()
    
    if args.sync:
        sync_from_youtube()
    elif args.update:
        update_all_statistics()
    elif args.report:
        report = generate_report()
        print(report)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

