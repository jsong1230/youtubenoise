"""
다른 폴더에서 newyear 관련 음악 파일을 찾아서 newyear 폴더로 이동
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging

logger = setup_logging()

# newyear 관련 키워드
NEWYEAR_KEYWORDS = [
    "new year", "newyear", "new-year", "newyears", "newyears",
    "2026", "2025",
    "goodbye", "good bye", "good-bye", "adieu",
    "celebration",
    "countdown",
    "midnight",
    "year end", "year-end", "yearend",
    "new years eve", "newyears eve",
    "happy new year",
    "새해", "신년",  # 한국어
    "新年", "年明け", "元旦",  # 일본어
    "xīnnián", "yuándàn",  # 중국어 (병음)
]

PUBLIC_DOMAIN_DIR = project_root / "audio" / "public_domain"
NEWYEAR_DIR = PUBLIC_DOMAIN_DIR / "newyear"


def is_newyear_related(filename: str) -> bool:
    """파일명이 newyear 관련인지 확인"""
    filename_lower = filename.lower()
    for keyword in NEWYEAR_KEYWORDS:
        if keyword in filename_lower:
            return True
    return False


def organize_newyear_music():
    """다른 폴더에서 newyear 관련 음악을 찾아서 newyear 폴더로 이동"""
    NEWYEAR_DIR.mkdir(parents=True, exist_ok=True)
    
    # 이미 newyear 폴더에 있는 파일 목록
    existing_files = {f.name for f in NEWYEAR_DIR.glob("*.mp3") if f.is_file()}
    existing_files.update({f.name for f in NEWYEAR_DIR.glob("*.wav") if f.is_file()})
    existing_files.update({f.name for f in NEWYEAR_DIR.glob("*.flac") if f.is_file()})
    
    moved_count = 0
    skipped_count = 0
    
    # 모든 하위 폴더에서 음악 파일 검색 (newyear 폴더 제외)
    for extension in ("*.mp3", "*.wav", "*.flac"):
        for file_path in PUBLIC_DOMAIN_DIR.rglob(extension):
            # newyear 폴더는 제외
            if "newyear" in str(file_path.parent):
                continue
            
            # 파일명이 newyear 관련인지 확인
            if is_newyear_related(file_path.name):
                # 이미 newyear 폴더에 같은 이름의 파일이 있으면 스킵
                if file_path.name in existing_files:
                    logger.info(f"이미 존재: {file_path.name} (스킵)")
                    skipped_count += 1
                    continue
                
                # newyear 폴더로 이동
                dest_path = NEWYEAR_DIR / file_path.name
                try:
                    file_path.rename(dest_path)
                    logger.info(f"이동: {file_path.relative_to(project_root)} -> {dest_path.relative_to(project_root)}")
                    moved_count += 1
                except Exception as e:
                    logger.error(f"이동 실패: {file_path.name} - {e}")
    
    logger.info(f"\n=== 정리 완료 ===")
    logger.info(f"이동된 파일: {moved_count}개")
    logger.info(f"스킵된 파일: {skipped_count}개")
    logger.info(f"newyear 폴더 총 파일 수: {len(list(NEWYEAR_DIR.glob('*.mp3'))) + len(list(NEWYEAR_DIR.glob('*.wav'))) + len(list(NEWYEAR_DIR.glob('*.flac')))}개")


if __name__ == "__main__":
    organize_newyear_music()

