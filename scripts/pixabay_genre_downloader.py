"""
Pixabay 장르별 음악 다운로더
다양한 장르의 음악을 Pixabay에서 다운로드하고 장르별 폴더로 자동 분류
"""
import os
import sys
import time
import urllib.parse
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging

# 로깅 설정
logger = setup_logging()

# ==========================
# 설정 값들
# ==========================
BASE_URL = "https://pixabay.com/music/search/"
DOWNLOAD_DIR = project_root / "audio" / "public_domain"
MAX_PAGES = None
MAX_TRACKS = None
WAIT_BETWEEN_DOWNLOADS = 3
MAX_RETRIES = 3

# 장르별 검색어 매핑
GENRE_SEARCH_TERMS = {
    "classical": ["classical", "symphony", "orchestral", "piano classical"],
    "jazz": ["jazz", "swing", "lounge", "bebop"],
    "rock": ["rock", "guitar", "electric rock"],
    "lofi": ["lofi", "chillhop", "chill", "study beats"],
    "ambient": ["ambient", "relax", "calm", "meditation"],
    "piano": ["piano", "piano solo", "piano instrumental"],
    "electronic": ["electronic", "edm", "synth", "electronic music"],
    "blues": ["blues", "blues guitar"],
    "folk": ["folk", "acoustic folk"],
    "world": ["world music", "ethnic", "traditional"],
    "celtic": ["celtic", "fiddle", "irish", "scottish", "celtic music", "irish music", "scottish music"],
    "christmas_carols": ["christmas carol", "carol", "christmas song", "holiday carol", "xmas carol"],
    "newyear": ["new year", "newyear", "new-year", "2026", "2025", "goodbye", "good bye", "adieu", "celebration", "countdown", "midnight", "year end", "year-end", "new years", "newyears", "new years eve", "newyears eve", "happy new year", "새해", "신년", "新年", "年明け", "元旦", "xīnnián", "yuándàn", "shinnen", "toshiake"],
}

# ==========================
# 유틸
# ==========================

def setup_driver(headless: bool = False):
    """Chrome WebDriver 설정"""
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    logger.info("Chrome WebDriver 초기화 중...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_window_size(1920, 1080)
    driver.implicitly_wait(5)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        '''
    })
    
    logger.info("WebDriver 준비 완료")
    return driver


def sanitize_filename(filename: str) -> str:
    """파일명에서 특수문자 제거"""
    # Windows/Mac에서 문제가 되는 문자 제거
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # 연속된 공백/언더스코어 정리
    filename = ' '.join(filename.split())
    return filename[:200]  # 파일명 길이 제한


def find_mp3_url(driver, track_url: str) -> str:
    """트랙 페이지에서 MP3 다운로드 URL 찾기"""
    strategies = [
        # 전략 1: 직접 다운로드 링크 찾기
        lambda: _find_direct_download_link(driver),
        # 전략 2: 페이지 소스에서 정규식으로 찾기
        lambda: _find_in_page_source(driver),
        # 전략 3: data 속성에서 찾기
        lambda: _find_in_data_attributes(driver),
        # 전략 4: 네트워크 로그에서 찾기
        lambda: _find_in_network_logs(driver),
    ]
    
    for i, strategy in enumerate(strategies, 1):
        try:
            url = strategy()
            if url:
                logger.info(f"MP3 URL 발견 (전략 {i}): {url[:80]}...")
                return url
        except Exception as e:
            logger.debug(f"전략 {i} 실패: {e}")
    
    return ""


def _find_direct_download_link(driver) -> str:
    """직접 다운로드 링크 찾기"""
    try:
        download_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, '.mp3')]")
        for btn in download_buttons:
            href = btn.get_attribute('href')
            if href and '.mp3' in href:
                return href
    except:
        pass
    return ""


def _find_in_page_source(driver) -> str:
    """페이지 소스에서 MP3 URL 찾기"""
    page_source = driver.page_source
    import re
    patterns = [
        r'https?://[^"\s]+\.mp3',
        r'"(https?://[^"]+download[^"]+\.mp3[^"]*)"',
        r'url\(["\']?(https?://[^"\']+\.mp3[^"\']*?)["\']?\)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, page_source)
        for match in matches:
            if 'pixabay' in match.lower() and '.mp3' in match.lower():
                return match
    return ""


def _find_in_data_attributes(driver) -> str:
    """data 속성에서 MP3 URL 찾기"""
    try:
        elements = driver.find_elements(By.XPATH, "//*[@data-url or @data-src or @data-mp3]")
        for elem in elements:
            for attr in ['data-url', 'data-src', 'data-mp3']:
                url = elem.get_attribute(attr)
                if url and '.mp3' in url:
                    return url
    except:
        pass
    return ""


def _find_in_network_logs(driver) -> str:
    """네트워크 로그에서 MP3 URL 찾기"""
    try:
        logs = driver.get_log('performance')
        for log in logs:
            message = log.get('message', '')
            if '.mp3' in message and 'download' in message.lower():
                import json
                try:
                    log_data = json.loads(message)
                    if 'message' in log_data:
                        params = log_data['message'].get('params', {})
                        request = params.get('request', {})
                        url = request.get('url', '')
                        if '.mp3' in url:
                            return url
                except:
                    pass
    except:
        pass
    return ""


def download_mp3(url: str, output_path: Path, retries: int = MAX_RETRIES) -> bool:
    """MP3 파일 다운로드"""
    for attempt in range(retries):
        try:
            logger.info(f"다운로드 시도 {attempt + 1}/{retries}: {output_path.name}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            if downloaded > 0:
                logger.info(f"다운로드 완료: {output_path.name} ({downloaded / 1024 / 1024:.2f} MB)")
                return True
        except Exception as e:
            logger.warning(f"다운로드 실패 (시도 {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
    
    if output_path.exists():
        output_path.unlink()
    return False


def download_genre_music(genre: str, search_term: str, max_tracks: int = None, max_pages: int = None, headless: bool = False):
    """특정 장르의 음악 다운로드"""
    if genre not in GENRE_SEARCH_TERMS:
        logger.error(f"지원하지 않는 장르: {genre}")
        logger.info(f"지원하는 장르: {', '.join(GENRE_SEARCH_TERMS.keys())}")
        return
    
    # 장르별 폴더 생성
    genre_dir = DOWNLOAD_DIR / genre
    genre_dir.mkdir(parents=True, exist_ok=True)
    
    # 이미 다운로드된 파일 목록
    existing_files = {f.name for f in genre_dir.glob("*.mp3")}
    
    # 검색 URL
    search_url = BASE_URL + urllib.parse.quote(search_term) + "/"
    logger.info(f"장르: {genre}, 검색어: {search_term}")
    logger.info(f"검색 URL: {search_url}")
    
    driver = setup_driver(headless=headless)
    downloaded_count = 0
    page = 1
    
    try:
        while True:
            if max_pages and page > max_pages:
                break
            
            url = f"{search_url}?pagi={page}"
            logger.info(f"\n=== 페이지 {page} ===")
            driver.get(url)
            time.sleep(3)
            
            # 트랙 링크 찾기
            try:
                track_links = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/music/']"))
                )
            except TimeoutException:
                logger.warning(f"페이지 {page}에서 트랙을 찾을 수 없습니다.")
                break
            
            # 고유한 트랙 URL만 추출
            unique_tracks = set()
            for link in track_links:
                href = link.get_attribute('href')
                if href and '/music/' in href and 'search' not in href:
                    unique_tracks.add(href)
            
            logger.info(f"페이지 {page}에서 {len(unique_tracks)}개의 트랙 발견")
            
            if not unique_tracks:
                logger.info("더 이상 트랙이 없습니다.")
                break
            
            for track_url in unique_tracks:
                if max_tracks and downloaded_count >= max_tracks:
                    logger.info(f"최대 다운로드 개수({max_tracks})에 도달했습니다.")
                    break
                
                try:
                    driver.get(track_url)
                    time.sleep(2)
                    
                    # 트랙 제목 가져오기
                    try:
                        title_elem = driver.find_element(By.TAG_NAME, "h1")
                        title = title_elem.text.strip()
                    except:
                        title = f"track_{downloaded_count + 1}"
                    
                    # 파일명 생성
                    filename = sanitize_filename(f"{title}.mp3")
                    output_path = genre_dir / filename
                    
                    # 이미 다운로드된 파일이면 스킵
                    if filename in existing_files or output_path.exists():
                        logger.info(f"이미 존재: {filename} (스킵)")
                        continue
                    
                    # 다운로드 버튼 클릭 시도
                    try:
                        download_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download') or contains(@class, 'download')]"))
                        )
                        driver.execute_script("arguments[0].click();", download_btn)
                        time.sleep(3)
                    except:
                        pass
                    
                    # MP3 URL 찾기
                    mp3_url = find_mp3_url(driver, track_url)
                    
                    if not mp3_url:
                        logger.warning(f"MP3 URL을 찾을 수 없습니다: {title}")
                        continue
                    
                    # 다운로드
                    if download_mp3(mp3_url, output_path):
                        downloaded_count += 1
                        existing_files.add(filename)
                        logger.info(f"진행: {downloaded_count}개 다운로드 완료")
                    
                    time.sleep(WAIT_BETWEEN_DOWNLOADS)
                    
                except Exception as e:
                    logger.error(f"트랙 처리 실패: {e}")
                    continue
            
            if max_tracks and downloaded_count >= max_tracks:
                break
            
            page += 1
            time.sleep(2)
    
    finally:
        driver.quit()
        logger.info(f"\n=== 다운로드 완료 ===")
        logger.info(f"총 {downloaded_count}개 다운로드됨")
        logger.info(f"저장 위치: {genre_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pixabay에서 장르별 음악 다운로드")
    parser.add_argument("--genre", type=str, required=True, 
                       choices=list(GENRE_SEARCH_TERMS.keys()),
                       help="다운로드할 장르")
    parser.add_argument("--search", type=str, help="커스텀 검색어 (기본값: 장르별 검색어 사용)")
    parser.add_argument("--max-tracks", type=int, help="최대 다운로드 개수")
    parser.add_argument("--max-pages", type=int, help="최대 페이지 수")
    parser.add_argument("--headless", action="store_true", help="헤드리스 모드 (브라우저 숨김)")
    
    args = parser.parse_args()
    
    search_term = args.search or GENRE_SEARCH_TERMS[args.genre][0]
    
    download_genre_music(
        genre=args.genre,
        search_term=search_term,
        max_tracks=args.max_tracks or MAX_TRACKS,
        max_pages=args.max_pages or MAX_PAGES,
        headless=args.headless
    )

