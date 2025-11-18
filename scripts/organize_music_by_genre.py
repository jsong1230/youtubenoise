"""
Public Domain 음악을 장르별 폴더로 정리하는 스크립트

기존에 audio/public_domain/에 평면적으로 저장된 음악 파일들을
장르별 폴더로 자동 분류하여 이동합니다.
"""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
PUBLIC_DOMAIN_DIR = project_root / "audio" / "public_domain"
CATALOG_PATH = PUBLIC_DOMAIN_DIR / "catalog.json"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "logs" / "app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 장르별 폴더 매핑
GENRE_FOLDERS = {
    "classical": ["classical", "symphony", "orchestral", "bach", "mozart", "beethoven", "chopin", "debussy"],
    "jazz": ["jazz", "swing", "lounge", "bebop", "cool"],
    "rock": ["rock", "guitar", "electric"],
    "lofi": ["lofi", "chillhop", "chill", "study", "beats"],
    "ambient": ["ambient", "relax", "calm", "soft", "serene", "meditation"],
    "piano": ["piano", "keys", "grand", "solo"],
    "electronic": ["electronic", "edm", "synth", "future"],
    "blues": ["blues"],
    "folk": ["folk", "acoustic"],
    "world": ["world", "ethnic", "traditional"],
    "christmas": ["christmas", "xmas", "holiday", "winter", "snow", "santa", "carol", "noel"],
}

# 우선순위: 여러 키워드가 매칭되면 우선순위가 높은 폴더로 이동
GENRE_PRIORITY = [
    "christmas",  # 크리스마스는 우선
    "classical",
    "jazz",
    "rock",
    "lofi",
    "ambient",
    "piano",
    "electronic",
    "blues",
    "folk",
    "world",
]


def _tokenize(text: str) -> List[str]:
    """파일명을 토큰화"""
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    return [token for token in tokens if token]


def detect_genre(filename: str) -> Optional[str]:
    """파일명에서 장르 감지"""
    tokens = set(_tokenize(filename))
    
    # 각 장르별로 매칭 점수 계산
    genre_scores: Dict[str, int] = {}
    
    for genre, keywords in GENRE_FOLDERS.items():
        score = 0
        for keyword in keywords:
            if keyword in tokens:
                score += 1
        if score > 0:
            genre_scores[genre] = score
    
    if not genre_scores:
        return None
    
    # 우선순위에 따라 정렬
    sorted_genres = sorted(
        genre_scores.items(),
        key=lambda x: (GENRE_PRIORITY.index(x[0]) if x[0] in GENRE_PRIORITY else 999, -x[1])
    )
    
    return sorted_genres[0][0]


def organize_music_files(dry_run: bool = False) -> Dict[str, List[str]]:
    """
    음악 파일을 장르별 폴더로 정리
    
    Args:
        dry_run: True면 실제 이동하지 않고 시뮬레이션만 수행
    
    Returns:
        장르별로 이동된 파일 목록
    """
    if not PUBLIC_DOMAIN_DIR.exists():
        logger.error(f"Public Domain 디렉토리가 존재하지 않습니다: {PUBLIC_DOMAIN_DIR}")
        return {}
    
    # 장르별 폴더 생성
    for genre in GENRE_FOLDERS.keys():
        genre_dir = PUBLIC_DOMAIN_DIR / genre
        if not dry_run:
            genre_dir.mkdir(parents=True, exist_ok=True)
    
    # 기존 파일 스캔 (루트 디렉토리의 음악 파일만)
    music_files = []
    for ext in ["*.mp3", "*.wav", "*.flac"]:
        music_files.extend(PUBLIC_DOMAIN_DIR.glob(ext))
    
    # catalog.json은 제외
    music_files = [f for f in music_files if f.name != "catalog.json"]
    
    logger.info(f"총 {len(music_files)}개의 음악 파일 발견")
    
    organized: Dict[str, List[str]] = {}
    moved_count = 0
    skipped_count = 0
    
    for file_path in music_files:
        # 이미 하위 폴더에 있으면 스킵
        if file_path.parent != PUBLIC_DOMAIN_DIR:
            skipped_count += 1
            continue
        
        genre = detect_genre(file_path.name)
        
        if not genre:
            # 장르를 감지하지 못한 경우 "misc" 폴더로
            genre = "misc"
            misc_dir = PUBLIC_DOMAIN_DIR / genre
            if not dry_run:
                misc_dir.mkdir(parents=True, exist_ok=True)
        
        target_dir = PUBLIC_DOMAIN_DIR / genre
        target_path = target_dir / file_path.name
        
        # 이미 목적지에 같은 파일이 있으면 스킵
        if target_path.exists() and target_path != file_path:
            logger.warning(f"이미 존재하는 파일: {target_path.name} (스킵)")
            skipped_count += 1
            continue
        
        organized.setdefault(genre, []).append(file_path.name)
        
        if not dry_run:
            try:
                shutil.move(str(file_path), str(target_path))
                logger.info(f"이동: {file_path.name} -> {genre}/")
                moved_count += 1
            except Exception as e:
                logger.error(f"이동 실패: {file_path.name} - {e}")
        else:
            logger.info(f"[DRY RUN] 이동 예정: {file_path.name} -> {genre}/")
            moved_count += 1
    
    logger.info(f"정리 완료: {moved_count}개 이동, {skipped_count}개 스킵")
    
    # 요약 출력
    print("\n=== 장르별 정리 결과 ===")
    for genre, files in sorted(organized.items()):
        print(f"{genre}: {len(files)}개")
    
    return organized


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Public Domain 음악을 장르별 폴더로 정리")
    parser.add_argument("--dry-run", action="store_true", help="실제 이동하지 않고 시뮬레이션만 수행")
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("=== DRY RUN 모드 (실제 이동하지 않음) ===")
    
    organize_music_files(dry_run=args.dry_run)
    
    logger.info("\n정리 완료 후 카탈로그를 새로고침하려면:")
    logger.info("python scripts/public_domain_catalog.py --refresh --summary")

