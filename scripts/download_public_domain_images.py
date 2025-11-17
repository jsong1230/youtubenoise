"""
Public Domain/무료 이미지 자동 다운로드 스크립트
Unsplash, Pexels, Pixabay 등에서 무료 이미지 다운로드
"""
import os
import sys
import logging
import requests
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
from PIL import Image
import io

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


def download_from_unsplash(query: str, output_dir: Optional[Path] = None, width: int = 1920, height: int = 1080) -> Optional[Path]:
    """
    Unsplash에서 무료 이미지 다운로드
    Unsplash는 모든 이미지가 무료로 사용 가능합니다.
    
    Args:
        query: 검색어
        output_dir: 저장 디렉토리
        width: 이미지 너비
        height: 이미지 높이
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "images" / "downloaded"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Unsplash API 키 확인
        unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not unsplash_key:
            logger.warning("Unsplash API 키가 없습니다. .env 파일에 UNSPLASH_ACCESS_KEY를 추가하세요.")
            logger.info("무료 API 키 발급: https://unsplash.com/developers")
            return None
        
        logger.info(f"Unsplash에서 '{query}' 이미지 검색 중...")
        
        # Unsplash API로 이미지 검색
        search_url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {unsplash_key}"
        }
        params = {
            "query": query,
            "per_page": 10,
            "orientation": "landscape",
            "content_filter": "high"
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            logger.warning(f"Unsplash에서 '{query}' 검색 결과가 없습니다.")
            return None
        
        # 첫 번째 결과 사용
        photo = results[0]
        photo_id = photo.get("id")
        download_url = photo.get("urls", {}).get("full") or photo.get("urls", {}).get("regular")
        
        if not download_url:
            logger.warning("Unsplash 이미지 URL을 찾을 수 없습니다.")
            return None
        
        # 이미지 다운로드
        logger.info(f"Unsplash 이미지 다운로드 중: {photo.get('description', 'No description')}")
        img_response = requests.get(download_url, timeout=30)
        img_response.raise_for_status()
        
        # 이미지 로드 및 리사이즈
        img = Image.open(io.BytesIO(img_response.content))
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # 파일 저장
        filename = f"unsplash_{query.replace(' ', '_')}_{photo_id}.jpg"
        output_path = output_dir / filename
        img.save(str(output_path), "JPEG", quality=95)
        
        logger.info(f"Unsplash 이미지 다운로드 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Unsplash 다운로드 실패: {e}")
        return None


def download_from_pexels(query: str, output_dir: Optional[Path] = None, width: int = 1920, height: int = 1080) -> Optional[Path]:
    """
    Pexels에서 무료 이미지 다운로드
    Pexels는 모든 이미지가 무료로 사용 가능합니다.
    
    Args:
        query: 검색어
        output_dir: 저장 디렉토리
        width: 이미지 너비
        height: 이미지 높이
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "images" / "downloaded"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pexels API 키 확인
        pexels_key = os.getenv("PEXELS_API_KEY")
        if not pexels_key:
            logger.warning("Pexels API 키가 없습니다. .env 파일에 PEXELS_API_KEY를 추가하세요.")
            logger.info("무료 API 키 발급: https://www.pexels.com/api/")
            return None
        
        logger.info(f"Pexels에서 '{query}' 이미지 검색 중...")
        
        # Pexels API로 이미지 검색
        search_url = "https://api.pexels.com/v1/search"
        headers = {
            "Authorization": pexels_key
        }
        params = {
            "query": query,
            "per_page": 10,
            "orientation": "landscape"
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        photos = data.get("photos", [])
        
        if not photos:
            logger.warning(f"Pexels에서 '{query}' 검색 결과가 없습니다.")
            return None
        
        # 첫 번째 결과 사용
        photo = photos[0]
        photo_id = photo.get("id")
        # 가장 큰 크기 선택
        src = photo.get("src", {})
        download_url = src.get("original") or src.get("large2x") or src.get("large")
        
        if not download_url:
            logger.warning("Pexels 이미지 URL을 찾을 수 없습니다.")
            return None
        
        # 이미지 다운로드
        logger.info(f"Pexels 이미지 다운로드 중: {photo.get('alt', 'No description')}")
        img_response = requests.get(download_url, timeout=30)
        img_response.raise_for_status()
        
        # 이미지 로드 및 리사이즈
        img = Image.open(io.BytesIO(img_response.content))
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # 파일 저장
        filename = f"pexels_{query.replace(' ', '_')}_{photo_id}.jpg"
        output_path = output_dir / filename
        img.save(str(output_path), "JPEG", quality=95)
        
        logger.info(f"Pexels 이미지 다운로드 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Pexels 다운로드 실패: {e}")
        return None


def download_from_pixabay(query: str, output_dir: Optional[Path] = None, width: int = 1920, height: int = 1080) -> Optional[Path]:
    """
    Pixabay에서 무료 이미지 다운로드
    Pixabay는 모든 이미지가 무료로 사용 가능합니다.
    
    Args:
        query: 검색어
        output_dir: 저장 디렉토리
        width: 이미지 너비
        height: 이미지 높이
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "images" / "downloaded"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pixabay API 키 확인
        pixabay_key = os.getenv("PIXABAY_API_KEY")
        if not pixabay_key:
            logger.warning("Pixabay API 키가 없습니다. .env 파일에 PIXABAY_API_KEY를 추가하세요.")
            logger.info("무료 API 키 발급: https://pixabay.com/api/docs/")
            return None
        
        logger.info(f"Pixabay에서 '{query}' 이미지 검색 중...")
        
        # Pixabay API로 이미지 검색
        search_url = "https://pixabay.com/api/"
        params = {
            "key": pixabay_key,
            "q": query,
            "image_type": "photo",
            "orientation": "horizontal",
            "category": "backgrounds",
            "min_width": width,
            "min_height": height,
            "per_page": 10,
            "safesearch": "true"
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", [])
        
        if not hits:
            logger.warning(f"Pixabay에서 '{query}' 검색 결과가 없습니다.")
            return None
        
        # 첫 번째 결과 사용
        photo = hits[0]
        photo_id = photo.get("id")
        download_url = photo.get("webformatURL") or photo.get("largeImageURL")
        
        if not download_url:
            logger.warning("Pixabay 이미지 URL을 찾을 수 없습니다.")
            return None
        
        # 이미지 다운로드
        logger.info(f"Pixabay 이미지 다운로드 중: {photo.get('tags', 'No description')}")
        img_response = requests.get(download_url, timeout=30)
        img_response.raise_for_status()
        
        # 이미지 로드 및 리사이즈
        img = Image.open(io.BytesIO(img_response.content))
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # 파일 저장
        filename = f"pixabay_{query.replace(' ', '_')}_{photo_id}.jpg"
        output_path = output_dir / filename
        img.save(str(output_path), "JPEG", quality=95)
        
        logger.info(f"Pixabay 이미지 다운로드 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Pixabay 다운로드 실패: {e}")
        return None


def get_background_image_for_preset(preset_name: str, width: int = 1920, height: int = 1080) -> Optional[Path]:
    """
    프리셋에 맞는 배경 이미지 다운로드
    
    Args:
        preset_name: BGM 프리셋 이름
        width: 이미지 너비
        height: 이미지 높이
    
    Returns:
        다운로드된 파일 경로
    """
    # 프리셋에 따른 검색어 매핑
    query_mapping = {
        "christmas_cafe_3h": "christmas cafe cozy warm",
        "christmas_cafe": "christmas cafe cozy warm",
        "christmas_classical_2h": "christmas winter snow",
        "christmas_classical": "christmas winter snow",
        "christmas_ambient_4h": "christmas night stars",
        "christmas_ambient": "christmas night stars",
        "cafe_jazz_2h": "cozy cafe warm",
        "cafe_jazz": "cozy cafe warm",
        "cafe_classical_3h": "cozy cafe study",
        "cafe_classical": "cozy cafe study",
        "classical_piano_2h": "classical music elegant",
        "classical_piano": "classical music elegant",
    }
    
    # 검색어 결정
    query = query_mapping.get(preset_name.lower(), preset_name.replace("_", " "))
    
    # 기존 다운로드된 이미지 확인
    output_dir = project_root / "images" / "downloaded"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 프리셋 이름으로 기존 이미지 찾기
    existing_files = list(output_dir.glob(f"*{preset_name}*"))
    if existing_files:
        logger.info(f"기존 다운로드된 이미지 발견: {existing_files[0]}")
        return existing_files[0]
    
    # 여러 소스에서 시도
    logger.info(f"'{query}' 이미지 다운로드 시도 중...")
    
    # 1. Unsplash 시도
    result = download_from_unsplash(query, output_dir, width, height)
    if result:
        return result
    
    # 2. Pexels 시도
    result = download_from_pexels(query, output_dir, width, height)
    if result:
        return result
    
    # 3. Pixabay 시도
    result = download_from_pixabay(query, output_dir, width, height)
    if result:
        return result
    
    logger.warning("모든 이미지 다운로드 소스 실패. 이미지 생성으로 대체됩니다.")
    return None


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Public Domain 이미지 다운로드")
    parser.add_argument("--query", type=str, default="christmas cafe", help="검색어")
    parser.add_argument("--preset", type=str, help="BGM 프리셋 이름")
    parser.add_argument("--source", type=str, choices=["unsplash", "pexels", "pixabay"], help="이미지 소스")
    
    args = parser.parse_args()
    
    if args.preset:
        result = get_background_image_for_preset(args.preset)
    elif args.source:
        query = args.query
        if args.source == "unsplash":
            result = download_from_unsplash(query)
        elif args.source == "pexels":
            result = download_from_pexels(query)
        elif args.source == "pixabay":
            result = download_from_pixabay(query)
        else:
            result = None
    else:
        # 모든 소스 시도
        result = download_from_unsplash(args.query)
        if not result:
            result = download_from_pexels(args.query)
        if not result:
            result = download_from_pixabay(args.query)
    
    if result:
        print(f"✅ 이미지 다운로드 완료: {result}")
    else:
        print("❌ 이미지 다운로드 실패")
        print("\nAPI 키 설정 안내:")
        print("1. Unsplash: https://unsplash.com/developers")
        print("   .env 파일에 추가: UNSPLASH_ACCESS_KEY=your_key")
        print("2. Pexels: https://www.pexels.com/api/")
        print("   .env 파일에 추가: PEXELS_API_KEY=your_key")
        print("3. Pixabay: https://pixabay.com/api/docs/")
        print("   .env 파일에 추가: PIXABAY_API_KEY=your_key")


if __name__ == "__main__":
    main()

