"""
스케줄러 스크립트
요일별 필러 로테이션 및 자동 업로드
upload_schedule.yaml을 읽어서 자동 실행
"""
import os
import sys
import json
import yaml
import random
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# 프로젝트 루트를 sys.path에 추가
# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE, CONFIG_JSON_FILE, OUTPUT_DIR, PROJECT_ROOT
from scripts.utils import setup_logging, load_json_file, load_yaml_file

# 업로드 스케줄 파일 경로
UPLOAD_SCHEDULE_FILE = project_root / "data" / "upload_schedule.yaml"

# 로깅 설정
logger = setup_logging()


def load_config() -> dict:
    """config.json 파일 로드"""
    return load_json_file(CONFIG_JSON_FILE)


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
        script_path = PROJECT_ROOT / "scripts" / script_name
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
            cwd=str(PROJECT_ROOT)
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
    history_file = OUTPUT_DIR / "logs" / "history.json"
    
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


def load_upload_schedule() -> dict:
    """업로드 스케줄 파일 로드"""
    try:
        if not UPLOAD_SCHEDULE_FILE.exists():
            logger.warning(f"업로드 스케줄 파일을 찾을 수 없습니다: {UPLOAD_SCHEDULE_FILE}")
            return {}
        return load_yaml_file(UPLOAD_SCHEDULE_FILE)
    except Exception as e:
        logger.error(f"업로드 스케줄 파일 로드 오류: {e}")
        return {}


def get_today_schedule() -> Optional[Dict]:
    """
    오늘 요일에 해당하는 스케줄 가져오기
    
    Returns:
        오늘의 스케줄 딕셔너리 (없으면 None)
    """
    try:
        schedule_data = load_upload_schedule()
        schedule = schedule_data.get("schedule", {})
        
        # 요일 이름 매핑 (0=월요일, 6=일요일)
        weekday_names = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday"
        }
        
        today = datetime.now().weekday()
        day_name = weekday_names.get(today, "monday")
        
        today_schedule = schedule.get(day_name)
        if today_schedule:
            logger.info(f"오늘({day_name}) 스케줄: {today_schedule.get('mode')} - {today_schedule.get('preset')}")
            return today_schedule
        
        # 폴백 스케줄 사용
        fallback = schedule_data.get("fallback_schedule", [])
        if fallback:
            selected = random.choice(fallback)
            logger.info(f"스케줄이 없어 폴백 사용: {selected.get('mode')} - {selected.get('preset')}")
            return selected
        
        return None
        
    except Exception as e:
        logger.error(f"스케줄 가져오기 실패: {e}", exc_info=True)
        return None


def run_scheduled_content(schedule: Dict) -> Dict:
    """
    스케줄에 따라 콘텐츠 생성 및 업로드
    
    Args:
        schedule: 스케줄 딕셔너리
    
    Returns:
        실행 결과 딕셔너리
    """
    try:
        mode = schedule.get("mode")
        preset = schedule.get("preset")
        upload = schedule.get("upload", True)
        language = schedule.get("language", "en")
        
        start_time = datetime.now()
        result = {
            "start_time": start_time.isoformat(),
            "mode": mode,
            "preset": preset,
            "status": "in_progress",
            "files": {},
            "video_id": None,
            "error": None
        }
        
        logger.info("=" * 60)
        logger.info(f"스케줄 실행: {mode} - {preset}")
        logger.info("=" * 60)
        
        # 모드별 실행
        if mode == "longform_bgm":
            duration_minutes = schedule.get("duration_minutes", 180)
            from main import run_longform_bgm
            run_longform_bgm(preset, duration_minutes, upload)
            
        elif mode == "spot_difference":
            from scripts.generate_spot_difference import generate_spot_difference_video
            video_path = generate_spot_difference_video(preset)
            result["files"]["video"] = str(video_path)
            
            if upload:
                # 업로드 로직 (향후 구현)
                logger.info("틀린그림찾기 업로드는 향후 구현 예정")
            
        elif mode == "brain_training":
            from scripts.generate_brain_training import generate_brain_training_video
            video_path = generate_brain_training_video(preset)
            result["files"]["video"] = str(video_path)
            
            if upload:
                # 업로드 로직 (향후 구현)
                logger.info("두뇌훈련 업로드는 향후 구현 예정")
            
        elif mode == "ai_explainer":
            from scripts.generate_ai_explainers import generate_ai_explainer_script
            from scripts.make_ai_explainer_video import make_ai_explainer_video
            from pathlib import Path
            
            # 스크립트 생성
            script_data = generate_ai_explainer_script(preset)
            script_file_path = Path(script_data.get("script_file_path"))
            
            # 영상 제작
            video_path = make_ai_explainer_video(script_file_path)
            result["files"]["video"] = str(video_path)
            
            if upload:
                # 업로드 로직 (향후 구현)
                logger.info("AI Explainer 업로드는 향후 구현 예정")
        
        else:
            raise ValueError(f"지원하지 않는 모드: {mode}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result["status"] = "completed"
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = duration
        
        logger.info(f"\n스케줄 실행 완료! (소요 시간: {duration / 60:.2f}분)")
        logger.info("=" * 60)
        
        # 히스토리 저장
        save_history(result)
        
        return result
        
    except Exception as e:
        logger.error(f"스케줄 실행 중 오류 발생: {e}", exc_info=True)
        if 'result' in locals():
            result["status"] = "failed"
            result["error"] = str(e)
            save_history(result)
        raise


def main():
    """메인 실행 함수 - 오늘의 스케줄에 따라 자동 실행"""
    try:
        logger.info("=" * 60)
        logger.info("스케줄러 시작 - 요일별 필러 로테이션")
        logger.info("=" * 60)
        
        # 오늘의 스케줄 가져오기
        schedule = get_today_schedule()
        
        if not schedule:
            logger.warning("오늘의 스케줄이 없습니다. 종료합니다.")
            return
        
        # 스케줄 실행
        result = run_scheduled_content(schedule)
        
        return result
        
    except Exception as e:
        logger.error(f"스케줄러 실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

