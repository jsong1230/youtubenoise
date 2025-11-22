"""
공통 유틸리티 함수 모듈
프로젝트 전반에서 사용되는 공통 함수들
"""
import os
import sys
import subprocess
import logging
import time
import functools
from pathlib import Path
from typing import Optional, Callable, TypeVar, Any, Dict, Tuple, Union
from dotenv import load_dotenv

T = TypeVar('T')

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE, PROJECT_ROOT

# .env 파일 로드
load_dotenv(project_root / ".env")


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    공통 로깅 설정
    
    Args:
        log_file: 로그 파일 경로 (None이면 기본 LOG_FILE 사용)
        level: 로깅 레벨
    
    Returns:
        설정된 로거
    """
    if log_file is None:
        log_file = LOG_FILE
    
    # 로그 디렉토리 생성
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 로깅 설정 (이미 설정되어 있으면 건너뛰기)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True
        )
    
    return logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """
    FFmpeg 설치 여부 확인
    
    Returns:
        FFmpeg 설치 여부
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_project_root() -> Path:
    """
    프로젝트 루트 경로 반환
    
    Returns:
        프로젝트 루트 Path 객체
    """
    return project_root


def ensure_output_dir(dir_path: Path) -> Path:
    """
    출력 디렉토리 생성 (없으면 생성)
    
    Args:
        dir_path: 디렉토리 경로
    
    Returns:
        생성된 디렉토리 경로
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def load_yaml_file(file_path: Path) -> dict:
    """
    YAML 파일 로드
    
    Args:
        file_path: YAML 파일 경로
    
    Returns:
        파싱된 딕셔너리
    """
    import yaml
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger = logging.getLogger(__name__)
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"YAML 파일 로드 오류: {e}")
        raise


def save_json_file(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """
    JSON 파일 저장
    
    Args:
        data: 저장할 데이터
        file_path: 저장 경로
        indent: 들여쓰기 (기본값: 2)
    """
    import json
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    JSON 파일 로드
    
    Args:
        file_path: JSON 파일 경로
    
    Returns:
        파싱된 딕셔너리
    """
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger = logging.getLogger(__name__)
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"JSON 파일 로드 오류: {e}")
        raise


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    재시도 데코레이터 (지수 백오프)
    
    Args:
        max_retries: 최대 재시도 횟수
        initial_delay: 초기 대기 시간 (초)
        backoff_factor: 백오프 배수
        exceptions: 재시도할 예외 타입
        logger: 로거 (None이면 기본 로거 사용)
    
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def api_call():
            ...
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} 실패 (시도 {attempt + 1}/{max_retries + 1}): {e}. "
                            f"{delay:.1f}초 후 재시도..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"{func.__name__} 최종 실패 ({max_retries + 1}회 시도): {e}"
                        )
            
            # 모든 재시도 실패 시 예외 발생
            raise last_exception
        
        return wrapper
    return decorator


def handle_api_error(
    error: Exception,
    operation: str,
    logger: Optional[logging.Logger] = None,
    retryable_status_codes: Tuple[int, ...] = (500, 502, 503, 504, 429)
) -> bool:
    """
    API 에러 처리 및 재시도 가능 여부 판단
    
    Args:
        error: 발생한 예외
        operation: 수행 중이던 작업 설명
        logger: 로거 (None이면 기본 로거 사용)
        retryable_status_codes: 재시도 가능한 HTTP 상태 코드
    
    Returns:
        재시도 가능 여부
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # HTTP 에러인 경우
    if hasattr(error, 'resp') and hasattr(error.resp, 'status'):
        status = error.resp.status
        if status in retryable_status_codes:
            logger.warning(f"{operation} 실패 (HTTP {status}): 재시도 가능")
            return True
        else:
            logger.error(f"{operation} 실패 (HTTP {status}): 재시도 불가")
            return False
    
    # 네트워크 에러인 경우
    error_str = str(error).lower()
    network_errors = ('timeout', 'connection', 'network', 'dns', 'refused')
    if any(err in error_str for err in network_errors):
        logger.warning(f"{operation} 실패 (네트워크 에러): 재시도 가능")
        return True
    
    # 기타 에러
    logger.error(f"{operation} 실패: {error}")
    return False


def safe_execute(
    func: Callable[..., T],
    *args,
    default: Optional[T] = None,
    logger: Optional[logging.Logger] = None,
    error_message: Optional[str] = None,
    **kwargs
) -> Optional[T]:
    """
    안전한 함수 실행 (예외 발생 시 기본값 반환)
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        default: 예외 발생 시 반환할 기본값
        logger: 로거 (None이면 기본 로거 사용)
        error_message: 에러 메시지 (None이면 기본 메시지 사용)
        **kwargs: 함수 키워드 인자
    
    Returns:
        함수 실행 결과 또는 기본값
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        msg = error_message or f"{func.__name__} 실행 중 오류 발생"
        logger.error(f"{msg}: {e}", exc_info=True)
        return default

