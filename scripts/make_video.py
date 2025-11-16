"""
영상 생성 스크립트
오디오 파일 + 배경 이미지 파일 → mp4 영상 파일 생성
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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


def check_ffmpeg() -> bool:
    """FFmpeg 설치 여부 확인"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def make_video(background_image: Path, audio_file: Path, output_path: Optional[Path] = None) -> Path:
    """
    영상 생성 함수
    
    Args:
        background_image: 배경 이미지 파일 경로
        audio_file: 오디오 파일 경로
        output_path: 출력 파일 경로 (None이면 자동 생성)
    
    Returns:
        생성된 영상 파일 경로
    """
    try:
        # FFmpeg 확인
        if not check_ffmpeg():
            raise RuntimeError("FFmpeg가 설치되지 않았습니다. FFmpeg를 설치해주세요.")
        
        # 파일 존재 확인
        if not background_image.exists():
            raise FileNotFoundError(f"배경 이미지 파일을 찾을 수 없습니다: {background_image}")
        if not audio_file.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_file}")
        
        # 출력 경로 자동 생성
        if output_path is None:
            output_dir = project_root / "videos"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            # 오디오 파일명에서 정보 추출
            audio_name = audio_file.stem
            filename = f"{date_str}_{audio_name}.mp4"
            output_path = output_dir / filename
        
        # 출력 디렉토리 확인
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"영상 생성 시작...")
        logger.info(f"배경 이미지: {background_image}")
        logger.info(f"오디오 파일: {audio_file}")
        logger.info(f"출력 파일: {output_path}")
        
        # FFmpeg 명령어 구성
        # -y: 기존 파일 덮어쓰기
        # -loop 1: 이미지를 반복 재생
        # -i: 입력 파일
        # -c:v libx264: 비디오 코덱
        # -tune stillimage: 정적 이미지 최적화
        # -c:a aac: 오디오 코덱
        # -b:a 192k: 오디오 비트레이트
        # -pix_fmt yuv420p: 픽셀 포맷 (호환성)
        # -shortest: 오디오 길이에 맞춤
        # -vf scale=1920:1080: 해상도 설정
        cmd = [
            "ffmpeg",
            "-y",  # 기존 파일 덮어쓰기
            "-loop", "1",  # 이미지 반복
            "-i", str(background_image),  # 배경 이미지
            "-i", str(audio_file),  # 오디오 파일
            "-c:v", "libx264",  # 비디오 코덱
            "-tune", "stillimage",  # 정적 이미지 최적화
            "-c:a", "aac",  # 오디오 코덱
            "-b:a", "192k",  # 오디오 비트레이트
            "-pix_fmt", "yuv420p",  # 픽셀 포맷
            "-vf", "scale=1920:1080",  # 해상도 설정
            "-shortest",  # 오디오 길이에 맞춤
            "-r", "30",  # 프레임레이트
            str(output_path)  # 출력 파일
        ]
        
        # FFmpeg 실행
        logger.info(f"FFmpeg 명령어 실행: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"영상 생성 완료: {output_path} ({file_size_mb:.2f} MB)")
            return output_path
        else:
            raise RuntimeError("영상 파일이 생성되지 않았습니다.")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg 실행 오류: {e}")
        logger.error(f"표준 출력: {e.stdout}")
        logger.error(f"표준 오류: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"영상 생성 중 오류 발생: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        # 명령행 인자 확인
        if len(sys.argv) < 3:
            print("사용법: python make_video.py <background_image> <audio_file> [output_path]")
            print("예시: python make_video.py images/2025-11-15_white_noise_bg.png audio/2025-11-15_white_noise_4h.mp3")
            sys.exit(1)
        
        background_image = Path(sys.argv[1])
        audio_file = Path(sys.argv[2])
        output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        
        # 상대 경로를 절대 경로로 변환
        if not background_image.is_absolute():
            background_image = project_root / background_image
        if not audio_file.is_absolute():
            audio_file = project_root / audio_file
        
        # 영상 생성
        output_path = make_video(background_image, audio_file, output_path)
        logger.info(f"생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

