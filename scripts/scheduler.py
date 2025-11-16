"""
스케줄러 스크립트
전체 파이프라인을 자동으로 실행하여 영상을 생성하고 업로드
"""
import os
import sys
import json
import random
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

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


def load_config() -> dict:
    """config.json 파일 로드"""
    config_path = project_root / "config" / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"설정 파일 파싱 오류: {e}")
        raise


def run_script(script_name: str, args: list = None) -> tuple:
    """
    Python 스크립트 실행
    
    Args:
        script_name: 실행할 스크립트 이름 (예: "generate_audio.py")
        args: 추가 인자 리스트
    
    Returns:
        (성공 여부, 출력 메시지)
    """
    try:
        script_path = project_root / "scripts" / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"스크립트를 찾을 수 없습니다: {script_path}")
        
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        logger.info(f"스크립트 실행: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(project_root)
        )
        
        output = result.stdout + result.stderr
        logger.info(f"스크립트 실행 완료: {script_name}")
        if output:
            logger.debug(f"출력: {output}")
        
        return True, output
        
    except subprocess.CalledProcessError as e:
        error_msg = f"스크립트 실행 실패: {script_name}\n{e.stderr}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"스크립트 실행 중 오류: {e}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def import_and_call_function(module_name: str, function_name: str, *args, **kwargs):
    """모듈을 임포트하고 함수를 호출"""
    try:
        module = __import__(f"scripts.{module_name}", fromlist=[function_name])
        func = getattr(module, function_name)
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"함수 호출 실패 ({module_name}.{function_name}): {e}", exc_info=True)
        raise


def save_history(history_data: Dict):
    """히스토리 파일에 기록 저장"""
    history_file = project_root / "logs" / "history.json"
    
    # 기존 히스토리 로드
    history = []
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception as e:
            logger.warning(f"히스토리 파일 로드 실패: {e}")
    
    # 새 항목 추가
    history.append(history_data)
    
    # 저장
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info(f"히스토리 저장 완료: {history_file}")
    except Exception as e:
        logger.error(f"히스토리 저장 실패: {e}")


def main():
    """메인 실행 함수 - 전체 파이프라인 실행"""
    try:
        logger.info("=" * 60)
        logger.info("스케줄러 시작 - 영상 생성 및 업로드 파이프라인")
        logger.info("=" * 60)
        
        # 설정 로드
        config = load_config()
        audio_length_sec = config.get("audio_length_sec", 14400)
        noise_types = config.get("noise_types", ["white_noise"])
        
        # 노이즈 타입 선택 (랜덤 또는 순차)
        noise_type = random.choice(noise_types)
        duration_hours = audio_length_sec // 3600
        
        logger.info(f"선택된 노이즈 타입: {noise_type}")
        logger.info(f"영상 길이: {duration_hours}시간 ({audio_length_sec}초)")
        
        start_time = datetime.now()
        result = {
            "start_time": start_time.isoformat(),
            "noise_type": noise_type,
            "duration_hours": duration_hours,
            "status": "in_progress",
            "files": {},
            "video_id": None,
            "error": None
        }
        
        # 1. 오디오 생성
        logger.info("\n[1/6] 오디오 생성 중...")
        try:
            from scripts.generate_audio import generate_noise
            audio_path = generate_noise(noise_type, audio_length_sec)
            result["files"]["audio"] = str(audio_path)
            logger.info(f"오디오 생성 완료: {audio_path}")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"오디오 생성 실패: {e}"
            logger.error(result["error"], exc_info=True)
            save_history(result)
            raise
        
        # 2. 이미지 생성
        logger.info("\n[2/6] 배경 이미지 생성 중...")
        try:
            from scripts.generate_image import generate_background_image
            image_path = generate_background_image(noise_type)
            result["files"]["image"] = str(image_path)
            logger.info(f"이미지 생성 완료: {image_path}")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"이미지 생성 실패: {e}"
            logger.error(result["error"], exc_info=True)
            save_history(result)
            raise
        
        # 3. 메타데이터 생성
        logger.info("\n[3/6] 메타데이터 생성 중...")
        try:
            from scripts.generate_title_description import generate_metadata
            metadata = generate_metadata(noise_type, duration_hours)
            result["metadata"] = metadata
            logger.info(f"메타데이터 생성 완료")
            logger.info(f"제목: {metadata['title']}")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"메타데이터 생성 실패: {e}"
            logger.error(result["error"], exc_info=True)
            save_history(result)
            raise
        
        # 4. 영상 생성
        logger.info("\n[4/6] 영상 생성 중...")
        try:
            from scripts.make_video import make_video
            video_path = make_video(image_path, audio_path)
            result["files"]["video"] = str(video_path)
            logger.info(f"영상 생성 완료: {video_path}")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"영상 생성 실패: {e}"
            logger.error(result["error"], exc_info=True)
            save_history(result)
            raise
        
        # 5. 유튜브 업로드
        logger.info("\n[5/6] 유튜브 업로드 중...")
        try:
            from scripts.upload_youtube import upload_video
            video_id = upload_video(
                video_path=video_path,
                title=metadata["title"],
                description=metadata["description"],
                tags=metadata["tags"],
                thumbnail_path=image_path  # 썸네일로 이미지 사용
            )
            result["video_id"] = video_id
            result["files"]["thumbnail"] = str(image_path)
            logger.info(f"유튜브 업로드 완료! Video ID: {video_id}")
            logger.info(f"영상 URL: https://www.youtube.com/watch?v={video_id}")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"유튜브 업로드 실패: {e}"
            logger.error(result["error"], exc_info=True)
            save_history(result)
            raise
        
        # 6. 완료
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result["status"] = "completed"
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = duration
        
        logger.info("\n[6/6] 파이프라인 완료!")
        logger.info(f"총 소요 시간: {duration / 60:.2f}분")
        logger.info(f"Video ID: {result['video_id']}")
        logger.info("=" * 60)
        
        # 히스토리 저장
        save_history(result)
        
        return result
        
    except Exception as e:
        logger.error(f"파이프라인 실행 중 오류 발생: {e}", exc_info=True)
        if 'result' in locals():
            result["status"] = "failed"
            result["error"] = str(e)
            save_history(result)
        sys.exit(1)


if __name__ == "__main__":
    main()

