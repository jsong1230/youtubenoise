"""
유튜브 업로드 스크립트
YouTube Data API v3를 사용하여 영상 업로드
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from PIL import Image
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from config import LOG_FILE, CONFIG_JSON_FILE, DATA_DIR, PROJECT_ROOT
from scripts.utils import setup_logging, load_json_file

# 로깅 설정
logger = setup_logging()

# YouTube API 스코프
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def load_config() -> Dict[str, Any]:
    """config.json 파일 로드"""
    return load_json_file(CONFIG_JSON_FILE)


def get_authenticated_service():
    """인증된 YouTube API 서비스 객체 반환"""
    # 환경변수에서 인증 정보 확인 (우선순위 1)
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if client_id and client_secret and refresh_token:
        # 환경변수 방식 사용
        logger.info("환경변수에서 YouTube 인증 정보 로드")
        creds = Credentials(
            token=None,  # 처음에는 None, refresh로 획득
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
    
    # 파일 기반 인증 (기존 방식, 우선순위 2)
    logger.info("파일 기반 YouTube 인증 사용")
    config = load_config()
    client_secret_file = config.get("youtube", {}).get("client_secret_file", str(DATA_DIR / "youtube_client_secret.json"))
    token_file = config.get("youtube", {}).get("token_file", str(PROJECT_ROOT / "token.json"))
    
    # 경로를 절대 경로로 변환
    if not Path(client_secret_file).is_absolute():
        client_secret_file = PROJECT_ROOT / client_secret_file
    if not Path(token_file).is_absolute():
        token_file = PROJECT_ROOT / token_file
    
    creds = None
    
    # 기존 토큰 파일 확인
    if Path(token_file).exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception as e:
            logger.warning(f"토큰 파일 로드 실패: {e}")
    
    # 토큰이 없거나 유효하지 않으면 새로 인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"토큰 갱신 실패: {e}")
                creds = None
        
        if not creds:
            if not Path(client_secret_file).exists():
                raise FileNotFoundError(
                    f"클라이언트 시크릿 파일을 찾을 수 없습니다: {client_secret_file}\n"
                    "환경변수(YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN)를 설정하거나\n"
                    "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 "
                    "다운로드한 JSON 파일을 이 경로에 저장해주세요."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret_file), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # 토큰 저장
        token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        logger.info(f"토큰 저장 완료: {token_file}")
    
    return build('youtube', 'v3', credentials=creds)


def compress_thumbnail(thumbnail_path: Path, max_size_mb: float = 2.0) -> Path:
    """
    썸네일 이미지를 2MB 이하로 압축
    
    Args:
        thumbnail_path: 원본 썸네일 이미지 경로
        max_size_mb: 최대 파일 크기 (MB, 기본값: 2.0)
    
    Returns:
        압축된 이미지 파일 경로 (원본이 2MB 이하면 원본 경로 반환)
    """
    max_size_bytes = int(max_size_mb * 1024 * 1024)  # MB를 바이트로 변환
    
    # 파일 크기 확인
    file_size = thumbnail_path.stat().st_size
    if file_size <= max_size_bytes:
        logger.info(f"썸네일 크기 ({file_size / 1024 / 1024:.2f}MB)가 {max_size_mb}MB 이하입니다. 압축 불필요.")
        return thumbnail_path
    
    logger.info(f"썸네일 압축 시작... (원본 크기: {file_size / 1024 / 1024:.2f}MB)")
    
    try:
        # 이미지 열기
        img = Image.open(thumbnail_path)
        
        # RGB로 변환 (JPEG는 RGB만 지원)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # YouTube 썸네일 권장 크기: 1280x720 (16:9)
        # 하지만 원본 비율을 유지하면서 크기 조정
        original_width, original_height = img.size
        max_dimension = 1280  # YouTube 최대 권장 크기
        
        # 비율 유지하면서 크기 조정
        if original_width > max_dimension or original_height > max_dimension:
            ratio = min(max_dimension / original_width, max_dimension / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"이미지 크기 조정: {original_width}x{original_height} -> {new_width}x{new_height}")
        
        # 임시 파일 생성
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_path = Path(temp_file.name)
        temp_file.close()
        
        # JPEG 품질로 압축 (100에서 시작해서 점진적으로 낮춤)
        quality = 95
        min_quality = 50
        
        while quality >= min_quality:
            img.save(str(temp_path), 'JPEG', quality=quality, optimize=True)
            compressed_size = temp_path.stat().st_size
            
            if compressed_size <= max_size_bytes:
                logger.info(f"썸네일 압축 완료: {compressed_size / 1024 / 1024:.2f}MB (품질: {quality})")
                return temp_path
            
            # 품질을 5씩 낮춤
            quality -= 5
        
        # 최소 품질로도 2MB를 초과하면 크기를 더 줄임
        if compressed_size > max_size_bytes:
            logger.warning(f"최소 품질로도 2MB 초과 ({compressed_size / 1024 / 1024:.2f}MB). 크기를 더 줄입니다.")
            scale_factor = 0.9
            while compressed_size > max_size_bytes and scale_factor > 0.5:
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized_img.save(str(temp_path), 'JPEG', quality=min_quality, optimize=True)
                compressed_size = temp_path.stat().st_size
                scale_factor -= 0.1
            
            logger.info(f"썸네일 압축 완료 (크기 조정 후): {compressed_size / 1024 / 1024:.2f}MB")
        
        return temp_path
        
    except Exception as e:
        logger.error(f"썸네일 압축 중 오류 발생: {e}", exc_info=True)
        # 압축 실패 시 원본 반환
        return thumbnail_path


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: List[str],
    thumbnail_path: Optional[Path] = None
) -> str:
    """
    유튜브에 영상 업로드
    
    Args:
        video_path: 업로드할 영상 파일 경로
        title: 영상 제목
        description: 영상 설명
        tags: 태그 리스트
        thumbnail_path: 썸네일 이미지 경로 (선택사항)
    
    Returns:
        업로드된 영상의 video ID
    """
    try:
        # 파일 존재 확인
        if not video_path.exists():
            raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_path}")
        
        # 상대 경로를 절대 경로로 변환
        if not video_path.is_absolute():
            video_path = PROJECT_ROOT / video_path
        
        logger.info(f"유튜브 업로드 시작...")
        logger.info(f"영상 파일: {video_path}")
        logger.info(f"제목: {title}")
        
        # YouTube API 서비스 객체 생성
        youtube = get_authenticated_service()
        
        # 영상 메타데이터
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '10'  # Music 카테고리
            },
            'status': {
                'privacyStatus': 'private',  # 기본값: 비공개
                'selfDeclaredMadeForKids': False
            }
        }
        
        # 미디어 파일 업로드 객체 생성
        media = MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        # 업로드 요청
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        # 업로드 실행 (재개 가능한 업로드)
        logger.info("영상 업로드 중... (이 작업은 시간이 걸릴 수 있습니다)")
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        video_id = response['id']
                        logger.info(f"업로드 완료! Video ID: {video_id}")
                        logger.info(f"영상 URL: https://www.youtube.com/watch?v={video_id}")
                    else:
                        raise Exception(f"업로드 응답에 video ID가 없습니다: {response}")
                else:
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"업로드 진행률: {progress}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"재시도 가능한 오류: {e}"
                    logger.warning(error)
                    retry += 1
                    if retry > 3:
                        raise
                else:
                    raise
        
        # 썸네일 업로드 (선택사항)
        if thumbnail_path and Path(thumbnail_path).exists():
            try:
                # 썸네일 경로를 절대 경로로 변환
                if not Path(thumbnail_path).is_absolute():
                    thumbnail_path = PROJECT_ROOT / thumbnail_path
                
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
                    
            except Exception as e:
                logger.warning(f"썸네일 업로드 실패 (영상은 업로드됨): {e}")
                # 임시 파일 정리
                if 'compressed_thumbnail' in locals() and is_temp_file and compressed_thumbnail.exists():
                    try:
                        compressed_thumbnail.unlink()
                    except:
                        pass
        
        # 로그 기록
        logger.info(f"업로드 성공 - Video ID: {video_id}, 제목: {title}")
        
        return video_id
        
    except HttpError as e:
        logger.error(f"YouTube API 오류: {e}")
        logger.error(f"오류 내용: {e.content}")
        raise
    except Exception as e:
        logger.error(f"업로드 중 오류 발생: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        # 명령행 인자 확인
        if len(sys.argv) < 5:
            print("사용법: python upload_youtube.py <video_path> <title> <description> <tags_json> [thumbnail_path]")
            print("예시: python upload_youtube.py videos/video.mp4 'My Video' 'Description' '[\"tag1\",\"tag2\"]'")
            sys.exit(1)
        
        video_path = Path(sys.argv[1])
        title = sys.argv[2]
        description = sys.argv[3]
        tags = json.loads(sys.argv[4]) if isinstance(sys.argv[4], str) else sys.argv[4]
        thumbnail_path = Path(sys.argv[5]) if len(sys.argv) > 5 else None
        
        # 업로드
        video_id = upload_video(video_path, title, description, tags, thumbnail_path)
        print(f"\n업로드 완료!")
        print(f"Video ID: {video_id}")
        print(f"URL: https://www.youtube.com/watch?v={video_id}")
        
        return video_id
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

