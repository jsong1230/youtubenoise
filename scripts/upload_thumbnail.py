"""
YouTube 영상에 썸네일 업로드
"""
import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging
from scripts.upload_youtube import compress_thumbnail

# 로깅 설정
logger = setup_logging()

# YouTube API 스코프
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def get_authenticated_service():
    """인증된 YouTube API 서비스 객체 반환"""
    # 환경변수에서 인증 정보 확인
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if client_id and client_secret and refresh_token:
        logger.info("환경변수에서 YouTube 인증 정보 로드")
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        
        # 토큰 갱신
        try:
            creds.refresh(Request())
            logger.info("토큰 갱신 완료")
        except Exception as e:
            logger.error(f"토큰 갱신 실패: {e}")
            raise
        
        return build('youtube', 'v3', credentials=creds)
    else:
        raise ValueError("YouTube 인증 정보가 환경변수에 설정되지 않았습니다.")


def upload_thumbnail(video_id: str, thumbnail_path: Path):
    """
    YouTube 영상에 썸네일 업로드
    
    Args:
        video_id: YouTube 영상 ID
        thumbnail_path: 썸네일 이미지 경로
    """
    try:
        if not thumbnail_path.exists():
            raise FileNotFoundError(f"썸네일 파일을 찾을 수 없습니다: {thumbnail_path}")
        
        logger.info(f"썸네일 업로드 시작...")
        logger.info(f"Video ID: {video_id}")
        logger.info(f"썸네일 파일: {thumbnail_path}")
        
        # YouTube API 서비스 객체 생성
        youtube = get_authenticated_service()
        
        # 썸네일 압축 (2MB 이하로)
        compressed_thumbnail = compress_thumbnail(Path(thumbnail_path))
        is_temp_file = compressed_thumbnail != Path(thumbnail_path)
        
        logger.info("썸네일 업로드 중...")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(compressed_thumbnail))
        ).execute()
        logger.info("썸네일 업로드 완료")
        
        # 임시 파일이면 삭제
        if is_temp_file and compressed_thumbnail.exists():
            compressed_thumbnail.unlink()
            logger.debug("임시 압축 파일 삭제 완료")
        
        logger.info(f"썸네일 업로드 성공 - Video ID: {video_id}")
        
    except Exception as e:
        logger.error(f"썸네일 업로드 실패: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        if len(sys.argv) < 3:
            print("사용법: python upload_thumbnail.py <video_id> <thumbnail_path>")
            print("예시: python upload_thumbnail.py wTMPI2_EdwI thumbnails/thumbnail.jpg")
            sys.exit(1)
        
        video_id = sys.argv[1]
        thumbnail_path = Path(sys.argv[2])
        
        # 상대 경로를 절대 경로로 변환
        if not thumbnail_path.is_absolute():
            thumbnail_path = project_root / thumbnail_path
        
        upload_thumbnail(video_id, thumbnail_path)
        print(f"\n썸네일 업로드 완료!")
        print(f"Video ID: {video_id}")
        print(f"URL: https://www.youtube.com/watch?v={video_id}")
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

