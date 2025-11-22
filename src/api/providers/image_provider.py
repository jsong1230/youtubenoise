"""
무료 이미지 API 통합 Provider
Unsplash, Pexels, Pixabay 지원
"""
import os
import sys
import logging
import requests
from pathlib import Path
from typing import Optional, Dict
from PIL import Image
import io

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import IMAGES_DIR
from scripts.utils import retry_with_backoff

logger = logging.getLogger(__name__)


class ImageProvider:
    """무료 이미지 API 통합 Provider"""
    
    def __init__(self):
        """Image Provider 초기화"""
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        
        logger.info("Image Provider 초기화 완료")
        logger.info(f"  Unsplash: {'사용 가능' if self.unsplash_key else '사용 불가'}")
        logger.info(f"  Pexels: {'사용 가능' if self.pexels_key else '사용 불가'}")
        logger.info(f"  Pixabay: {'사용 가능' if self.pixabay_key else '사용 불가'}")
    
    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(requests.RequestException, requests.Timeout, requests.ConnectionError),
        logger=None
    )
    def download_from_unsplash(
        self,
        query: str,
        width: int = 1920,
        height: int = 1080,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Unsplash에서 이미지 다운로드
        
        Args:
            query: 검색어
            width: 이미지 너비
            height: 이미지 높이
            output_path: 저장 경로 (None이면 자동 생성)
        
        Returns:
            저장된 이미지 파일 경로
        """
        if not self.unsplash_key:
            logger.warning("Unsplash API 키가 설정되지 않았습니다.")
            return None
        
        logger.info(f"Unsplash에서 이미지 검색 중... (검색어: {query})")
        
        # 검색 API
        search_url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not data.get("results"):
            logger.warning(f"Unsplash에서 '{query}' 검색 결과 없음")
            return None
        
        # 이미지 URL 가져오기
        image_url = data["results"][0]["urls"]["raw"]
        image_url += f"&w={width}&h={height}&fit=crop"
        
        # 이미지 다운로드
        img_response = requests.get(image_url, timeout=10)
        img_response.raise_for_status()
        
        # PIL Image로 변환 및 저장
        img = Image.open(io.BytesIO(img_response.content))
        img = img.convert("RGB")
        
        if output_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output_path = IMAGES_DIR / "downloaded" / f"unsplash_{query}_{timestamp}.jpg"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "JPEG", quality=90)
        
        logger.info(f"Unsplash 이미지 다운로드 완료: {output_path}")
        return output_path
    
    def download_from_pexels(
        self,
        query: str,
        width: int = 1920,
        height: int = 1080,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Pexels에서 이미지 다운로드
        
        Args:
            query: 검색어
            width: 이미지 너비
            height: 이미지 높이
            output_path: 저장 경로 (None이면 자동 생성)
        
        Returns:
            저장된 이미지 파일 경로
        """
        if not self.pexels_key:
            logger.warning("Pexels API 키가 설정되지 않았습니다.")
            return None
        
        try:
            logger.info(f"Pexels에서 이미지 검색 중... (검색어: {query})")
            
            # 검색 API
            search_url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape"
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if not data.get("photos"):
                logger.warning(f"Pexels에서 '{query}' 검색 결과 없음")
                return None
            
            # 이미지 URL 가져오기 (원본 크기)
            image_url = data["photos"][0]["src"]["original"]
            
            # 이미지 다운로드
            img_response = requests.get(image_url, timeout=10)
            img_response.raise_for_status()
            
            # PIL Image로 변환 및 리사이즈
            img = Image.open(io.BytesIO(img_response.content))
            img = img.convert("RGB")
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            if output_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                output_path = IMAGES_DIR / "downloaded" / f"pexels_{query}_{timestamp}.jpg"
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "JPEG", quality=90)
            
            logger.info(f"Pexels 이미지 다운로드 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Pexels 이미지 다운로드 실패: {e}", exc_info=True)
            return None
    
    def download_from_pixabay(
        self,
        query: str,
        width: int = 1920,
        height: int = 1080,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Pixabay에서 이미지 다운로드
        
        Args:
            query: 검색어
            width: 이미지 너비
            height: 이미지 높이
            output_path: 저장 경로 (None이면 자동 생성)
        
        Returns:
            저장된 이미지 파일 경로
        """
        if not self.pixabay_key:
            logger.warning("Pixabay API 키가 설정되지 않았습니다.")
            return None
        
        try:
            logger.info(f"Pixabay에서 이미지 검색 중... (검색어: {query})")
            
            # 검색 API
            search_url = "https://pixabay.com/api/"
            params = {
                "key": self.pixabay_key,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 1
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if not data.get("hits"):
                logger.warning(f"Pixabay에서 '{query}' 검색 결과 없음")
                return None
            
            # 이미지 URL 가져오기 (큰 이미지)
            image_url = data["hits"][0].get("largeImageURL") or data["hits"][0]["webformatURL"]
            
            # 이미지 다운로드
            img_response = requests.get(image_url, timeout=10)
            img_response.raise_for_status()
            
            # PIL Image로 변환 및 리사이즈
            img = Image.open(io.BytesIO(img_response.content))
            img = img.convert("RGB")
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            if output_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                output_path = IMAGES_DIR / "downloaded" / f"pixabay_{query}_{timestamp}.jpg"
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "JPEG", quality=90)
            
            logger.info(f"Pixabay 이미지 다운로드 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Pixabay 이미지 다운로드 실패: {e}", exc_info=True)
            return None
    
    def download_image(
        self,
        query: str,
        width: int = 1920,
        height: int = 1080,
        priority: list = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        무료 이미지 API를 순차적으로 시도하여 이미지 다운로드
        
        Args:
            query: 검색어
            width: 이미지 너비
            height: 이미지 높이
            priority: 우선순위 리스트 (["unsplash", "pexels", "pixabay"])
            output_path: 저장 경로
        
        Returns:
            저장된 이미지 파일 경로 (모두 실패 시 None)
        """
        if priority is None:
            priority = ["unsplash", "pexels", "pixabay"]
        
        for provider in priority:
            if provider == "unsplash":
                result = self.download_from_unsplash(query, width, height, output_path)
                if result:
                    return result
            elif provider == "pexels":
                result = self.download_from_pexels(query, width, height, output_path)
                if result:
                    return result
            elif provider == "pixabay":
                result = self.download_from_pixabay(query, width, height, output_path)
                if result:
                    return result
        
        logger.warning(f"모든 무료 이미지 API에서 '{query}' 검색 실패")
        return None

