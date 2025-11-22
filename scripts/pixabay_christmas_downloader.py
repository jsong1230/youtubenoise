"""
Pixabay 크리스마스 음악 Selenium 다운로더
Cloudflare 봇 차단을 우회하기 위해 Selenium 사용
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
BASE_URL = "https://pixabay.com/music/search/christmas/"
DOWNLOAD_DIR = project_root / "audio" / "public_domain"  # 프로젝트 구조에 맞게 수정
MAX_PAGES = None                          # None이면 모든 페이지 순회, 숫자면 해당 페이지까지만
MAX_TRACKS = None                         # None이면 제한 없음, 숫자면 해당 개수까지만
WAIT_BETWEEN_DOWNLOADS = 3               # 곡 사이 딜레이(초) - 서버 부하 감소
MAX_RETRIES = 3                           # 다운로드 실패 시 재시도 횟수

# ==========================
# 유틸
# ==========================

def setup_driver(headless: bool = False):
    """Chrome WebDriver 설정 (headless 옵션 포함)"""
    options = webdriver.ChromeOptions()
    
    if headless:
        # headless 모드 (백그라운드 실행)
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 네트워크 로그 활성화 (MP3 URL 추적용)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # User-Agent 설정 (봇 차단 우회)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    logger.info("Chrome WebDriver 초기화 중...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_window_size(1920, 1080)
    driver.implicitly_wait(5)  # 암시적 대기 시간 설정
    
    # 봇 감지 우회 스크립트 실행
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


def ensure_download_dir():
    """다운로드 디렉토리 생성"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"다운로드 디렉토리: {DOWNLOAD_DIR}")


def sanitize_filename(name: str) -> str:
    # 윈도우, 맥, 리눅스 공통 문제되는 문자 제거
    bad_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for c in bad_chars:
        name = name.replace(c, "_")
    return name.strip()


# ==========================
# 크롤링 / 파싱 파트
# ==========================

def get_track_links_on_page(driver, page_num: int):
    """
    검색결과 페이지에서 개별 음악 상세 페이지 URL 리스트 추출
    """
    url = BASE_URL
    if page_num > 1:
        url = f"{BASE_URL}?pagi={page_num}"  # Pixabay는 pagi 파라미터 사용

    logger.info(f"페이지 로딩 중: {url}")
    driver.get(url)
    
    # 페이지가 완전히 로드될 때까지 대기
    time.sleep(5)  # Cloudflare 및 동적 콘텐츠 로딩 대기
    
    # 스크롤하여 모든 콘텐츠 로드 (React 앱이므로)
    try:
        # 페이지 하단까지 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        # 다시 상단으로
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    except Exception as e:
        logger.debug(f"스크롤 중 오류: {e}")

    # 실제 HTML 구조에 맞는 선택자 사용
    # HTML에서 확인: <a href="/music/christmas-christmas-holidays-270797/" class="title--7N7Nr">
    selectors = [
        "a.title--7N7Nr",  # 실제 클래스명
        "a[href^='/music/']",  # 상대 경로로 시작하는 링크
        ".audioRow--nAm4Z a[href*='/music/']",  # audioRow 내의 링크
        "a[href*='/music/']",  # 더 포괄적인 선택자
    ]
    
    links = set()
    
    for selector in selectors:
        try:
            # 요소가 나타날 때까지 대기
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            anchors = driver.find_elements(By.CSS_SELECTOR, selector)
            logger.debug(f"선택자 '{selector}'로 {len(anchors)}개 요소 발견")
            
            for a in anchors:
                try:
                    href = a.get_attribute("href")
                    if not href:
                        continue
                    
                    # 상대 경로를 절대 경로로 변환
                    if href.startswith("/"):
                        href = "https://pixabay.com" + href
                    
                    # 개별 트랙 URL 패턴 필터링
                    # 예: https://pixabay.com/music/christmas-christmas-holidays-270797/
                    if "/music/" in href and "pixabay.com" in href:
                        # 숫자 ID가 있는 URL만 선택 (슬러그-숫자ID 패턴)
                        parts = href.split("/")
                        if len(parts) >= 5:  # 최소 5개 부분 필요
                            last_part = parts[-1].split("?")[0].split("#")[0]
                            # 숫자가 포함된 경우 (ID)
                            if any(char.isdigit() for char in last_part):
                                clean = href.split("?")[0].split("#")[0]
                                if clean.endswith("/"):
                                    clean = clean.rstrip("/")
                                links.add(clean)
                except Exception as e:
                    logger.debug(f"링크 추출 중 오류: {e}")
                    continue
            
            if links:
                logger.info(f"선택자 '{selector}'로 {len(links)}개 링크 발견!")
                break  # 링크를 찾았으면 다른 선택자 시도 중단
                
        except TimeoutException:
            logger.debug(f"선택자 '{selector}'로 요소를 찾지 못함")
            continue
        except Exception as e:
            logger.debug(f"선택자 '{selector}' 처리 중 오류: {e}")
            continue
    
    # 추가로 페이지 소스에서 직접 URL 추출 시도
    if not links:
        logger.info("페이지 소스에서 직접 URL 추출 시도 중...")
        try:
            page_source = driver.page_source
            import re
            # 실제 HTML 구조에 맞는 패턴
            # href="/music/christmas-christmas-holidays-270797/"
            url_patterns = [
                r'href=["\'](/music/[^"\']*-\d+[^"\']*)["\']',  # 상대 경로 패턴
                r'href=["\'](https://pixabay\.com/music/[^"\']*-\d+[^"\']*)["\']',  # 절대 경로 패턴
                r'class="title--7N7Nr"[^>]*href=["\']([^"\']*)["\']',  # title 클래스와 함께
            ]
            for pattern in url_patterns:
                found_urls = re.findall(pattern, page_source, re.IGNORECASE)
                for url_match in found_urls:
                    if isinstance(url_match, tuple):
                        url_match = url_match[0] if url_match[0] else url_match[1]
                    
                    # 상대 경로를 절대 경로로 변환
                    if url_match.startswith("/"):
                        url_match = "https://pixabay.com" + url_match
                    
                    if "/music/" in url_match and any(char.isdigit() for char in url_match):
                        clean = url_match.split("?")[0].split("#")[0]
                        if clean.endswith("/"):
                            clean = clean.rstrip("/")
                        if "pixabay.com" in clean:
                            links.add(clean)
            
            if links:
                logger.info(f"페이지 소스에서 {len(links)}개 링크 발견!")
        except Exception as e:
            logger.debug(f"페이지 소스 파싱 중 오류: {e}")

    links = sorted(links)
    logger.info(f"페이지 {page_num}에서 트랙 {len(links)}개 발견")
    if links:
        logger.debug(f"첫 번째 링크 예시: {list(links)[:3]}")
    return links


def get_mp3_url_from_track_page(driver, track_url: str) -> tuple[str, str] | tuple[None, None]:
    """
    트랙 상세 페이지에서 Download 버튼을 클릭하고, 실제 MP3 URL을 추출
    (Selenium으로 버튼 클릭 → 팝업 내 .mp3 링크 찾기)
    """
    logger.info(f"트랙 열기: {track_url}")
    driver.get(track_url)

    # 페이지 로딩 완료 대기 (제목 영역이 뜰 때까지)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except TimeoutException:
        logger.warning("페이지 로딩 타임아웃")
        return None, None

    # 트랙 제목도 파일명으로 쓰기 위해 가져오기 (없으면 대체)
    try:
        title_el = driver.find_element(By.TAG_NAME, "h1")
        title = title_el.text.strip()
    except Exception:
        title = track_url.rstrip("/").split("/")[-1]

    title = sanitize_filename(title)

    # Download 버튼 클릭 (button 또는 a 태그 안에 "Download" 텍스트 포함)
    try:
        # 요소를 찾고 클릭 가능할 때까지 대기
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Download')] | //a[contains(., 'Download')]"
            ))
        )
        
        # StaleElementReferenceException 방지: 클릭 직전에 다시 찾기
        download_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Download')] | //a[contains(., 'Download')]"
        )
        
        logger.info("Download 버튼 클릭")
        # 현재 창 핸들 저장
        original_window = driver.current_window_handle
        all_windows_before = driver.window_handles
        
        # JavaScript로 클릭하여 더 안정적으로 처리
        driver.execute_script("arguments[0].click();", download_btn)
        time.sleep(3)  # 팝업 로딩 대기 (시간 증가)
        
        # 새 창/탭이 열렸는지 확인
        all_windows_after = driver.window_handles
        if len(all_windows_after) > len(all_windows_before):
            # 새 창이 열렸다면 전환
            new_window = [w for w in all_windows_after if w not in all_windows_before][0]
            driver.switch_to.window(new_window)
            time.sleep(1)
            current_url = driver.current_url
            if '.mp3' in current_url.lower():
                mp3_url = current_url
                logger.info(f"MP3 URL 발견 (새 창): {mp3_url[:50]}...")
                driver.close()
                driver.switch_to.window(original_window)
                return title, mp3_url
            driver.close()
            driver.switch_to.window(original_window)
        
        # 방법 5: 네트워크 로그에서 MP3 다운로드 요청 찾기
        try:
            logs = driver.get_log('performance')
            for log in logs[-50:]:  # 최근 50개 로그만 확인
                message = log.get('message', '')
                if '.mp3' in message.lower():
                    import json
                    try:
                        log_data = json.loads(message)
                        if 'message' in log_data:
                            method = log_data['message'].get('method', '')
                            params = log_data['message'].get('params', {})
                            if method == 'Network.responseReceived':
                                response = params.get('response', {})
                                url = response.get('url', '')
                                if '.mp3' in url.lower() and 'pixabay' in url.lower():
                                    mp3_url = url
                                    logger.info(f"MP3 URL 발견 (방법 5 - 네트워크 로그): {mp3_url[:50]}...")
                                    return title, mp3_url
                            elif method == 'Network.requestWillBeSent':
                                request = params.get('request', {})
                                url = request.get('url', '')
                                if '.mp3' in url.lower() and 'pixabay' in url.lower():
                                    mp3_url = url
                                    logger.info(f"MP3 URL 발견 (방법 5 - 네트워크 요청): {mp3_url[:50]}...")
                                    return title, mp3_url
                    except:
                        pass
        except Exception as e:
            logger.debug(f"방법 5 (네트워크 로그) 실패: {e}")
    except TimeoutException:
        logger.warning("Download 버튼을 찾지 못함")
        return None, None
    except Exception as e:
        logger.error(f"Download 버튼 클릭 중 오류: {e}")
        return None, None

    # 팝업 또는 다운로드 영역 내에서 .mp3 링크 찾기
    # 여러 방법 시도
    mp3_url = None
    
    # 방법 1: 직접 .mp3 링크 찾기
    try:
        mp3_link_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.mp3')]"))
        )
        mp3_url = mp3_link_el.get_attribute("href")
        logger.info(f"MP3 URL 발견 (방법 1): {mp3_url[:50]}...")
        return title, mp3_url
    except TimeoutException:
        logger.debug("방법 1: .mp3 링크를 찾지 못함")
    
    # 방법 2: 페이지 소스에서 직접 MP3 URL 추출
    try:
        page_source = driver.page_source
        import re
        # 다양한 패턴으로 MP3 URL 찾기
        mp3_patterns = [
            r'https?://[^"\s]+\.mp3[^"\s]*',
            r'href=["\']([^"\']*\.mp3[^"\']*)["\']',
            r'url\(["\']?([^"\')\s]+\.mp3[^"\')\s]*)["\']?\)',
            r'["\']([^"\']*cdn\.pixabay\.com[^"\']*\.mp3[^"\']*)["\']',
        ]
        for pattern in mp3_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                if '.mp3' in match.lower() and 'pixabay' in match.lower():
                    mp3_url = match.strip('"\'')
                    logger.info(f"MP3 URL 발견 (방법 2): {mp3_url[:50]}...")
                    return title, mp3_url
    except Exception as e:
        logger.debug(f"방법 2 실패: {e}")
    
    # 방법 3: 다운로드 버튼의 data 속성 확인
    try:
        download_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Download')] | //a[contains(., 'Download')]"
        )
        # data-url, data-href, data-download 등의 속성 확인
        for attr in ['data-url', 'data-href', 'data-download', 'data-src', 'href']:
            url = download_btn.get_attribute(attr)
            if url and '.mp3' in url.lower():
                mp3_url = url
                logger.info(f"MP3 URL 발견 (방법 3): {mp3_url[:50]}...")
                return title, mp3_url
    except Exception as e:
        logger.debug(f"방법 3 실패: {e}")
    
    # 방법 4: 트랙 ID에서 직접 URL 구성 시도
    try:
        # URL에서 트랙 ID 추출: https://pixabay.com/music/...-123456/
        track_id = track_url.rstrip("/").split("-")[-1]
        if track_id.isdigit():
            # Pixabay CDN 패턴 시도
            possible_urls = [
                f"https://cdn.pixabay.com/audio/2024/11/30/20-43-14-990.mp3",  # 예시 패턴
                f"https://cdn.pixabay.com/audio/{track_id}.mp3",
            ]
            # 실제로는 이 방법이 작동하지 않을 수 있으므로 로그만 남김
            logger.debug(f"트랙 ID 추출: {track_id}")
    except Exception as e:
        logger.debug(f"방법 4 실패: {e}")
    
    logger.warning(".mp3 링크를 찾지 못함 - 모든 방법 실패")
    logger.debug("페이지 URL을 확인하거나 수동으로 다운로드 링크를 찾아주세요.")
    return None, None


def download_mp3(mp3_url: str, title: str, retry_count: int = 0):
    """
    requests 로 실제 mp3 파일 다운로드 (재시도 로직 포함)
    """
    if not mp3_url:
        return None

    # URL에서 파일명 추출 + 타이틀 붙여줌
    parsed_name = urllib.parse.unquote(mp3_url.split("/")[-1].split("?")[0])
    ext = ".mp3"
    if "." in parsed_name:
        ext = "." + parsed_name.split(".")[-1]

    filename = sanitize_filename(f"{title}{ext}")
    save_path = DOWNLOAD_DIR / filename

    if save_path.exists():
        logger.debug(f"이미 존재: {save_path.name}")
        return save_path

    if retry_count > 0:
        logger.info(f"다운로드 재시도 ({retry_count}/{MAX_RETRIES}): {save_path.name}")
    else:
        logger.info(f"다운로드 시작: {save_path.name}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": BASE_URL,
    }
    try:
        with requests.get(mp3_url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            file_size_mb = save_path.stat().st_size / (1024 * 1024)
            logger.info(f"다운로드 완료: {save_path.name} ({file_size_mb:.2f} MB)")
            return save_path
    except Exception as e:
        logger.error(f"다운로드 실패: {e}")
        if save_path.exists():
            save_path.unlink()
        
        # 재시도 로직
        if retry_count < MAX_RETRIES:
            time.sleep(2)  # 재시도 전 대기
            return download_mp3(mp3_url, title, retry_count + 1)
        
        return None


# ==========================
# 메인 루프
# ==========================

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pixabay 크리스마스 음악 Selenium 다운로더")
    parser.add_argument("--headless", action="store_true", help="Headless 모드 활성화 (브라우저 숨김)")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 (더 자세한 로그)")
    parser.add_argument("--max-pages", type=int, default=None, help="최대 페이지 수 (기본값: 모든 페이지)")
    parser.add_argument("--max-tracks", type=int, default=None, help="최대 다운로드 트랙 수 (기본값: 제한 없음)")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 전역 변수 업데이트
    global MAX_PAGES, MAX_TRACKS
    if args.max_pages is not None:
        MAX_PAGES = args.max_pages
    if args.max_tracks is not None:
        MAX_TRACKS = args.max_tracks
    
    logger.info("=" * 60)
    logger.info("Pixabay 크리스마스 음악 Selenium 다운로더 시작")
    logger.info("=" * 60)
    
    ensure_download_dir()
    
    try:
        driver = setup_driver(headless=args.headless)
    except Exception as e:
        logger.error(f"WebDriver 설정 실패: {e}")
        logger.error("Chrome 브라우저가 설치되어 있는지 확인하세요.")
        return
    
    try:
        total_downloaded = 0
        total_skipped = 0
        total_failed = 0
        page = 1
        processed_urls = set()  # 중복 URL 방지
        
        # 기존에 다운로드된 파일 목록 확인
        existing_files = {f.name for f in DOWNLOAD_DIR.glob("*.mp3")}
        logger.info(f"기존 파일 {len(existing_files)}개 발견 (건너뛰기)")

        while True:
            # MAX_PAGES 제한 확인
            if MAX_PAGES is not None and page > MAX_PAGES:
                logger.info(f"최대 페이지 수({MAX_PAGES})에 도달했습니다.")
                break
            
            # MAX_TRACKS 제한 확인
            if MAX_TRACKS is not None and total_downloaded >= MAX_TRACKS:
                logger.info(f"최대 다운로드 수({MAX_TRACKS})에 도달했습니다.")
                break

            logger.info(f"\n{'='*60}")
            logger.info(f"페이지 {page} 처리 중...")
            logger.info(f"현재 진행 상황: 다운로드 {total_downloaded}개, 건너뜀 {total_skipped}개, 실패 {total_failed}개")
            logger.info(f"{'='*60}")

            track_links = get_track_links_on_page(driver, page)
            
            if not track_links:
                logger.warning(f"페이지 {page}에서 트랙을 찾지 못했습니다. 모든 페이지를 순회했습니다.")
                break

            logger.info(f"페이지 {page}에서 {len(track_links)}개 트랙 발견")

            for idx, track_url in enumerate(track_links, 1):
                # MAX_TRACKS 제한 확인
                if MAX_TRACKS is not None and total_downloaded >= MAX_TRACKS:
                    logger.info(f"최대 다운로드 수({MAX_TRACKS})에 도달했습니다.")
                    break
                
                # 중복 URL 체크
                if track_url in processed_urls:
                    logger.debug(f"중복 URL 건너뛰기: {track_url}")
                    total_skipped += 1
                    continue
                
                processed_urls.add(track_url)
                
                logger.info(f"\n[{page}-{idx}/{len(track_links)}] 트랙 처리 중: {track_url}")

                try:
                    title, mp3_url = get_mp3_url_from_track_page(driver, track_url)
                    if not mp3_url:
                        logger.warning(f"MP3 URL을 찾지 못했습니다: {track_url}")
                        total_failed += 1
                        continue

                    # 파일명으로 이미 다운로드되었는지 확인
                    parsed_name = urllib.parse.unquote(mp3_url.split("/")[-1].split("?")[0])
                    ext = ".mp3"
                    if "." in parsed_name:
                        ext = "." + parsed_name.split(".")[-1]
                    filename = sanitize_filename(f"{title}{ext}")
                    
                    if filename in existing_files:
                        logger.info(f"이미 다운로드된 파일: {filename}")
                        total_skipped += 1
                        continue

                    result = download_mp3(mp3_url, title)
                    if result:
                        total_downloaded += 1
                        existing_files.add(filename)  # 새로 다운로드된 파일 추가
                        logger.info(f"✓ 성공 ({total_downloaded}번째)")
                    else:
                        total_failed += 1
                        logger.warning(f"✗ 실패")
                        
                except Exception as e:
                    logger.error(f"트랙 처리 중 오류: {e}", exc_info=True)
                    total_failed += 1

                time.sleep(WAIT_BETWEEN_DOWNLOADS)

            # 다음 페이지로
            page += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"다운로드 완료!")
        logger.info(f"  - 다운로드: {total_downloaded}개")
        logger.info(f"  - 건너뜀: {total_skipped}개")
        logger.info(f"  - 실패: {total_failed}개")
        logger.info(f"  - 총 처리: {total_downloaded + total_skipped + total_failed}개")
        logger.info(f"저장 위치: {DOWNLOAD_DIR}")
        logger.info(f"{'='*60}")

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
