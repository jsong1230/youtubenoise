"""
Sleep 관련 음악을 sleep 폴더로 정리하고, 50개 미만이면 다운로드하는 스크립트
"""
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging

# 프로젝트 루트 설정
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils import setup_logging
from scripts.public_domain_catalog import build_public_domain_catalog, analyze_track

PUBLIC_DOMAIN_DIR = project_root / "audio" / "public_domain"
SLEEP_DIR = PUBLIC_DOMAIN_DIR / "sleep"
CATALOG_PATH = PUBLIC_DOMAIN_DIR / "catalog.json"

# 로깅 설정
logger = setup_logging()

# Sleep 관련 키워드
SLEEP_KEYWORDS = [
    "sleep", "bedtime", "night", "peaceful", "calm", "relax", "relaxing",
    "meditation", "zen", "serene", "soft", "gentle", "deep sleep", "insomnia",
    "dream", "dreams", "lullaby", "lullabies", "rest", "restful", "tranquil",
    "soothing", "ambient", "quiet", "silent", "moonlight", "stars", "nighttime"
]

# Sleep 관련 카테고리
SLEEP_CATEGORIES = ["ambient", "piano", "calm", "meditation"]


def _tokenize(text: str) -> Set[str]:
    """파일명을 토큰화"""
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    return {token for token in tokens if token}


def is_sleep_related(filename: str, categories: List[str] = None, moods: List[str] = None) -> bool:
    """파일명이나 카테고리/무드에서 sleep 관련 여부 확인"""
    tokens = _tokenize(filename)
    
    # 키워드 매칭
    for keyword in SLEEP_KEYWORDS:
        if keyword in tokens:
            return True
    
    # 카테고리 매칭
    if categories:
        for cat in categories:
            if cat in SLEEP_CATEGORIES:
                return True
    
    # 무드 매칭 (calm은 sleep 관련)
    if moods:
        if "calm" in moods:
            return True
    
    return False


def find_sleep_music_files() -> List[Path]:
    """기존 public_domain 폴더에서 sleep 관련 음악 파일 찾기"""
    sleep_files = []
    
    # 모든 하위 폴더 포함하여 스캔
    for ext in ["*.mp3", "*.wav", "*.flac"]:
        for file_path in PUBLIC_DOMAIN_DIR.rglob(ext):
            # catalog.json은 제외
            if file_path.name == "catalog.json":
                continue
            
            # 이미 sleep 폴더에 있으면 스킵
            if file_path.parent == SLEEP_DIR:
                continue
            
            # 파일명으로 판단
            if is_sleep_related(file_path.name):
                sleep_files.append(file_path)
                continue
            
            # 카탈로그에서 메타데이터 확인
            try:
                metadata = analyze_track(file_path)
                if metadata:
                    if is_sleep_related(
                        metadata.filename,
                        metadata.categories,
                        metadata.moods
                    ):
                        sleep_files.append(file_path)
            except Exception as e:
                logger.debug(f"메타데이터 분석 실패 ({file_path.name}): {e}")
    
    return sleep_files


def move_to_sleep_folder(files: List[Path], dry_run: bool = False) -> int:
    """sleep 관련 파일들을 sleep 폴더로 이동"""
    if not files:
        logger.info("이동할 sleep 관련 파일이 없습니다.")
        return 0
    
    # sleep 폴더 생성
    if not dry_run:
        SLEEP_DIR.mkdir(parents=True, exist_ok=True)
    
    moved_count = 0
    skipped_count = 0
    
    for file_path in files:
        target_path = SLEEP_DIR / file_path.name
        
        # 이미 sleep 폴더에 같은 파일이 있으면 스킵
        if target_path.exists() and target_path != file_path:
            logger.warning(f"이미 존재하는 파일: {target_path.name} (스킵)")
            skipped_count += 1
            continue
        
        if not dry_run:
            try:
                shutil.move(str(file_path), str(target_path))
                logger.info(f"이동: {file_path.name} -> sleep/")
                moved_count += 1
            except Exception as e:
                logger.error(f"이동 실패: {file_path.name} - {e}")
        else:
            logger.info(f"[DRY RUN] 이동 예정: {file_path.name} -> sleep/")
            moved_count += 1
    
    logger.info(f"이동 완료: {moved_count}개 이동, {skipped_count}개 스킵")
    return moved_count


def count_sleep_music() -> int:
    """sleep 폴더의 음악 파일 개수 확인"""
    if not SLEEP_DIR.exists():
        return 0
    
    count = 0
    for ext in ["*.mp3", "*.wav", "*.flac"]:
        count += len(list(SLEEP_DIR.glob(ext)))
    
    return count


def download_sleep_music(target_count: int = 50) -> int:
    """sleep 관련 음악 다운로드 (Pixabay API 사용)"""
    import os
    import requests
    from dotenv import load_dotenv
    
    load_dotenv(project_root / ".env")
    pixabay_api_key = os.getenv("PIXABAY_API_KEY")
    
    current_count = count_sleep_music()
    needed = max(0, target_count - current_count)
    
    if needed == 0:
        logger.info(f"이미 {current_count}개의 sleep 음악이 있습니다. 다운로드 불필요.")
        return 0
    
    logger.info(f"sleep 음악 {needed}개 다운로드 시작...")
    
    # sleep 폴더 생성
    SLEEP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Pixabay Music API로 sleep 관련 음악 검색
    search_queries = ["sleep", "meditation", "ambient", "calm", "peaceful", "relaxing", "zen", "lullaby"]
    
    downloaded = 0
    
    if pixabay_api_key:
        # Pixabay API 사용
        for query in search_queries:
            if downloaded >= needed:
                break
            
            try:
                # Pixabay Music API
                search_url = "https://pixabay.com/api/audio/"
                params = {
                    "key": pixabay_api_key,
                    "q": query,
                    "audio_type": "music",
                    "category": "music",
                    "per_page": min(20, needed - downloaded),
                    "safesearch": "true"
                }
                
                response = requests.get(search_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                hits = data.get("hits", [])
                
                if hits:
                    logger.info(f"'{query}' 검색어로 {len(hits)}개 발견")
                    
                    for audio in hits:
                        if downloaded >= needed:
                            break
                        
                        try:
                            download_url = audio.get("url")
                            if not download_url:
                                continue
                            
                            # 파일명 생성
                            audio_id = audio.get("id", "unknown")
                            filename = f"pixabay_{audio_id}_{query}.mp3"
                            output_path = SLEEP_DIR / filename
                            
                            # 이미 존재하면 스킵
                            if output_path.exists():
                                continue
                            
                            # 다운로드
                            logger.info(f"다운로드 중: {audio.get('tags', 'Unknown')}")
                            audio_response = requests.get(download_url, timeout=30, stream=True)
                            audio_response.raise_for_status()
                            
                            with open(output_path, "wb") as f:
                                for chunk in audio_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            downloaded += 1
                            logger.info(f"다운로드 완료: {filename}")
                            
                        except Exception as e:
                            logger.warning(f"개별 파일 다운로드 실패: {e}")
                            continue
                else:
                    logger.debug(f"'{query}' 검색 결과 없음")
                    
            except Exception as e:
                logger.warning(f"'{query}' 검색 실패: {e}")
                continue
    else:
        logger.warning("PIXABAY_API_KEY가 설정되지 않았습니다.")
        logger.info("수동 다운로드 안내:")
        logger.info("1) https://pixabay.com/music/search/sleep/ 방문")
        logger.info("2) 원하는 sleep 관련 음악 다운로드")
        logger.info(f"3) 다운로드한 파일을 {SLEEP_DIR}에 저장")
        logger.info(f"4) 목표: {needed}개 추가 필요")
    
    if downloaded > 0:
        logger.info(f"다운로드 완료: {downloaded}개 추가")
    else:
        logger.warning("다운로드된 파일이 없습니다.")
    
    return downloaded


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sleep 관련 음악을 sleep 폴더로 정리하고 다운로드")
    parser.add_argument("--dry-run", action="store_true", help="실제 이동하지 않고 시뮬레이션만 수행")
    parser.add_argument("--no-download", action="store_true", help="다운로드하지 않음")
    parser.add_argument("--target-count", type=int, default=50, help="목표 파일 개수 (기본값: 50)")
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("=== DRY RUN 모드 (실제 이동하지 않음) ===")
    
    # 1. 기존 sleep 관련 음악 찾기
    logger.info("기존 sleep 관련 음악 파일 검색 중...")
    sleep_files = find_sleep_music_files()
    logger.info(f"sleep 관련 파일 {len(sleep_files)}개 발견")
    
    # 2. sleep 폴더로 이동
    if sleep_files:
        logger.info(f"\n{sleep_files[0].parent} 등에서 sleep 폴더로 이동 중...")
        moved = move_to_sleep_folder(sleep_files, dry_run=args.dry_run)
    else:
        moved = 0
    
    # 3. 현재 개수 확인
    current_count = count_sleep_music()
    logger.info(f"\n현재 sleep 폴더의 음악 파일: {current_count}개")
    
    # 4. 50개 미만이면 다운로드
    if not args.no_download and current_count < args.target_count:
        needed = args.target_count - current_count
        logger.info(f"\n{needed}개 부족합니다. 다운로드 시작...")
        if not args.dry_run:
            downloaded = download_sleep_music(args.target_count)
            if downloaded > 0:
                current_count = count_sleep_music()
                logger.info(f"다운로드 후 총 {current_count}개")
        else:
            logger.info(f"[DRY RUN] {needed}개 다운로드 예정")
    elif current_count >= args.target_count:
        logger.info(f"이미 목표 개수({args.target_count}개) 이상입니다.")
    
    logger.info("\n작업 완료!")
    logger.info("카탈로그를 새로고침하려면:")
    logger.info("python scripts/public_domain_catalog.py --refresh --summary")


if __name__ == "__main__":
    main()

