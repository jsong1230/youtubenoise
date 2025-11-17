"""
Public Domain 음악 자동 다운로드 스크립트
FreePD, Pixabay Music, Musopen 등에서 무료 음악 다운로드
"""
import os
import sys
import logging
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

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


def download_from_freepd(query: str = "christmas", output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    FreePD에서 Public Domain 음악 다운로드
    FreePD는 완전 Public Domain 음악을 제공합니다.
    
    Args:
        query: 검색어 (기본값: "christmas")
        output_dir: 저장 디렉토리
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "audio" / "public_domain"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FreePD에서 '{query}' Public Domain 음악 다운로드 시도 중...")
        
        # FreePD 메인 페이지에서 크리스마스 음악 찾기
        freepd_urls = [
            "https://freepd.com/",
            "https://freepd.com/christmas.php",
        ]
        
        import re
        for base_url in freepd_urls:
            try:
                response = requests.get(base_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    html = response.text
                    
                    # FreePD의 다운로드 링크 패턴 찾기
                    # FreePD는 보통 /up/ 폴더에 파일을 저장하거나 직접 링크 제공
                    patterns = [
                        r'href=["\']([^"\']*\.mp3)["\']',
                        r'href=["\']([^"\']*christmas[^"\']*\.mp3)["\']',
                        r'href=["\']([^"\']*holiday[^"\']*\.mp3)["\']',
                        r'<a[^>]*href=["\']([^"\']*\.mp3)["\'][^>]*>',
                    ]
                    
                    all_links = []
                    for pattern in patterns:
                        links = re.findall(pattern, html, re.IGNORECASE)
                        all_links.extend(links)
                    
                    # 중복 제거 및 크리스마스 관련 링크 우선
                    unique_links = []
                    christmas_links = []
                    for link in all_links:
                        if link not in unique_links:
                            unique_links.append(link)
                            if 'christmas' in link.lower() or 'holiday' in link.lower():
                                christmas_links.append(link)
                    
                    # 크리스마스 링크 우선 시도
                    test_links = christmas_links[:3] if christmas_links else unique_links[:5]
                    
                    for link in test_links:
                        try:
                            download_url = link
                            if not download_url.startswith('http'):
                                if download_url.startswith('/'):
                                    download_url = "https://freepd.com" + download_url
                                else:
                                    download_url = "https://freepd.com/" + download_url
                            
                            # HEAD 요청으로 파일 존재 확인
                            head_response = requests.head(download_url, timeout=5, allow_redirects=True)
                            if head_response.status_code == 200:
                                content_type = head_response.headers.get('content-type', '')
                                if 'audio' in content_type or 'mp3' in content_type or 'octet-stream' in content_type:
                                    filename = "freepd_christmas.mp3"
                                    logger.info(f"FreePD 다운로드 링크 발견: {download_url[:80]}...")
                                    result = download_christmas_music_from_url(download_url, filename, output_dir)
                                    if result:
                                        return result
                        except Exception as e:
                            logger.debug(f"링크 다운로드 실패: {e}")
                            continue
                    
            except Exception as e:
                logger.debug(f"FreePD 페이지 접근 실패 ({base_url}): {e}")
                continue
        
        # 실패 시 수동 다운로드 안내
        logger.warning("FreePD 자동 다운로드 실패. 수동 다운로드 안내:")
        logger.info(f"1. https://freepd.com/ 방문")
        logger.info(f"2. 크리스마스 음악 다운로드")
        logger.info(f"3. {output_dir / 'christmas_cafe.mp3'}에 저장")
        
        return None
        
    except Exception as e:
        logger.error(f"FreePD 다운로드 실패: {e}")
        return None


def download_christmas_music_from_url(url: str, filename: str, output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    URL에서 Public Domain 크리스마스 음악 다운로드
    
    Args:
        url: 다운로드 URL
        filename: 저장할 파일명
        output_dir: 저장 디렉토리
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "audio" / "public_domain"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        
        # 이미 다운로드되어 있으면 스킵
        if output_path.exists():
            logger.info(f"파일이 이미 존재합니다: {output_path}")
            return output_path
        
        logger.info(f"음악 다운로드 중: {url}")
        logger.info(f"저장 위치: {output_path}")
        
        # 다운로드
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # 파일 저장
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) == 0:  # 1MB마다
                            logger.info(f"다운로드 진행률: {progress:.1f}%")
        
        logger.info(f"다운로드 완료: {output_path} ({downloaded / 1024 / 1024:.2f} MB)")
        return output_path
        
    except Exception as e:
        logger.error(f"다운로드 실패: {e}")
        if output_path.exists():
            output_path.unlink()  # 실패한 파일 삭제
        return None


def download_from_freesound(query: str = "christmas", output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Freesound에서 CC0 크리스마스 음악 다운로드 (웹 스크래핑)
    API 키 없이 웹사이트에서 직접 다운로드 링크 찾기
    
    Args:
        query: 검색어 (기본값: "christmas")
        output_dir: 저장 디렉토리
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "audio" / "public_domain"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Freesound 웹사이트에서 '{query}' CC0 음악 검색 중...")
        logger.warning("Freesound는 API 키가 필요합니다. 웹 스크래핑은 제한적입니다.")
        logger.info("대신 브라우저에서 직접 다운로드하세요:")
        logger.info("https://freesound.org/search/?q=christmas&f=license_filter%3A%22cc0%22")
        logger.info(f"다운로드한 파일을 {output_dir}/christmas_cafe.mp3 로 저장하세요.")
        
        return None
        
    except Exception as e:
        logger.error(f"Freesound 다운로드 실패: {e}")
        return None


def download_from_pixabay(query: str = "christmas", output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Pixabay Music에서 상업용 완전 무료 음악 다운로드
    
    Args:
        query: 검색어 (기본값: "christmas")
        output_dir: 저장 디렉토리
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "audio" / "public_domain"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pixabay API 키 확인 (선택사항, 없어도 웹 스크래핑 가능)
        pixabay_api_key = os.getenv("PIXABAY_API_KEY", "")
        
        logger.info(f"Pixabay Music에서 '{query}' 무료 음악 검색 중...")
        
        # Pixabay Music 검색 (API 또는 웹)
        if pixabay_api_key:
            # API 사용
            search_url = "https://pixabay.com/api/audio/"
            params = {
                "key": pixabay_api_key,
                "q": query,
                "audio_type": "music",
                "category": "music",
                "per_page": 5,
                "safesearch": "true"
            }
            
            try:
                response = requests.get(search_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                hits = data.get("hits", [])
                
                if hits:
                    # 첫 번째 결과 다운로드
                    audio = hits[0]
                    download_url = audio.get("url")
                    if download_url:
                        filename = f"pixabay_{audio.get('id', 'music')}_{query}.mp3"
                        logger.info(f"Pixabay 음악 발견: {audio.get('tags', 'Unknown')}")
                        result = download_christmas_music_from_url(download_url, filename, output_dir)
                        if result:
                            return result
            except Exception as e:
                logger.debug(f"Pixabay API 실패: {e}")
        
        # API 없이 웹 스크래핑 시도 (더 정교한 헤더 사용)
        pixabay_search_url = f"https://pixabay.com/music/search/{query}/"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(pixabay_search_url, timeout=15, headers=headers, allow_redirects=True)
            
            if response.status_code == 200:
                import re
                html = response.text
                
                # Pixabay의 오디오 다운로드 링크 찾기 (더 포괄적인 패턴)
                patterns = [
                    # JSON 데이터에서 URL 찾기
                    r'"url":"([^"]*\.mp3)"',
                    r'"download":"([^"]*)"',
                    r'href=["\']([^"\']*audio/download/[^"\']*)["\']',
                    r'href=["\']([^"\']*music/download/[^"\']*)["\']',
                    r'data-url=["\']([^"\']*\.mp3)["\']',
                    r'data-download=["\']([^"\']*)["\']',
                    r'<a[^>]*download[^>]*href=["\']([^"\']*\.mp3)["\']',
                    # Pixabay CDN 링크
                    r'https://cdn\.pixabay\.com/[^"\']*\.mp3',
                ]
                
                all_links = []
                for pattern in patterns:
                    links = re.findall(pattern, html, re.IGNORECASE)
                    all_links.extend(links)
                
                # 중복 제거
                unique_links = list(set(all_links))
                
                if unique_links:
                    logger.info(f"Pixabay에서 {len(unique_links)}개의 링크 발견")
                    # 각 링크 시도
                    for link in unique_links[:5]:  # 최대 5개 시도
                        try:
                            download_url = link
                            if not download_url.startswith('http'):
                                download_url = "https://pixabay.com" + (download_url if download_url.startswith('/') else '/' + download_url)
                            
                            # HEAD 요청으로 확인
                            head_response = requests.head(download_url, timeout=5, headers=headers, allow_redirects=True)
                            if head_response.status_code == 200:
                                content_type = head_response.headers.get('content-type', '')
                                if 'audio' in content_type or 'mp3' in content_type or 'octet-stream' in content_type:
                                    filename = f"pixabay_{query}.mp3"
                                    logger.info(f"Pixabay 다운로드 링크 확인: {download_url[:80]}...")
                                    result = download_christmas_music_from_url(download_url, filename, output_dir)
                                    if result:
                                        return result
                        except Exception as e:
                            logger.debug(f"Pixabay 링크 다운로드 실패: {e}")
                            continue
            elif response.status_code == 403:
                logger.warning("Pixabay가 봇을 차단했습니다. API 키를 사용하거나 수동 다운로드를 권장합니다.")
        except Exception as e:
            logger.debug(f"Pixabay 웹 스크래핑 실패: {e}")
        
        logger.warning("Pixabay 자동 다운로드 실패.")
        logger.info("Pixabay는 Cloudflare로 봇을 차단합니다.")
        logger.info("해결 방법:")
        logger.info("1. Pixabay API 키 사용 (권장):")
        logger.info("   - https://pixabay.com/api/docs/ 에서 API 키 발급")
        logger.info("   - .env 파일에 PIXABAY_API_KEY=your_key 추가")
        logger.info("2. 수동 다운로드:")
        logger.info(f"   - https://pixabay.com/music/search/{query}/ 방문")
        logger.info(f"   - 원하는 음악 다운로드")
        logger.info(f"   - {output_dir / 'christmas_cafe.mp3'}에 저장")
        
        return None
        
    except Exception as e:
        logger.error(f"Pixabay 다운로드 실패: {e}")
        return None


def download_from_musopen(query: str = "christmas", output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Musopen에서 Public Domain 녹음 다운로드
    PD 녹음만 선택하여 다운로드
    
    Args:
        query: 검색어 (기본값: "christmas")
        output_dir: 저장 디렉토리
    
    Returns:
        다운로드된 파일 경로
    """
    try:
        if output_dir is None:
            output_dir = project_root / "audio" / "public_domain"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Musopen에서 '{query}' Public Domain 녹음 검색 중...")
        
        # Musopen 검색 (PD 녹음만)
        musopen_search_url = f"https://musopen.org/music/?q={query}&license=pd"
        
        try:
            response = requests.get(musopen_search_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                import re
                # Musopen의 다운로드 링크 찾기
                # Musopen은 보통 /music/download/ 또는 직접 다운로드 링크 제공
                patterns = [
                    r'href=["\']([^"\']*download[^"\']*\.mp3)["\']',
                    r'href=["\']([^"\']*\.mp3)["\']',
                    r'<a[^>]*download[^>]*href=["\']([^"\']*)["\']',
                ]
                
                for pattern in patterns:
                    links = re.findall(pattern, response.text, re.IGNORECASE)
                    if links:
                        # 첫 번째 다운로드 링크 시도
                        for link in links[:3]:
                            try:
                                download_url = link
                                if not download_url.startswith('http'):
                                    download_url = "https://musopen.org" + (download_url if download_url.startswith('/') else '/' + download_url)
                                
                                # HEAD 요청으로 확인
                                head_response = requests.head(download_url, timeout=5, allow_redirects=True)
                                if head_response.status_code == 200:
                                    filename = f"musopen_{query}.mp3"
                                    logger.info(f"Musopen 다운로드 링크 발견: {download_url[:80]}...")
                                    result = download_christmas_music_from_url(download_url, filename, output_dir)
                                    if result:
                                        return result
                            except Exception as e:
                                logger.debug(f"Musopen 링크 다운로드 실패: {e}")
                                continue
        except Exception as e:
            logger.debug(f"Musopen 웹 스크래핑 실패: {e}")
        
        logger.warning("Musopen 자동 다운로드 실패. 수동 다운로드 안내:")
        logger.info(f"1. https://musopen.org/music/?q={query}&license=pd 방문")
        logger.info(f"2. Public Domain 녹음 선택 후 다운로드")
        logger.info(f"3. {output_dir / 'christmas_cafe.mp3'}에 저장")
        
        return None
        
    except Exception as e:
        logger.error(f"Musopen 다운로드 실패: {e}")
        return None


def download_from_incompetech() -> Optional[Path]:
    """
    Incompetech (Kevin MacLeod)에서 Public Domain 크리스마스 음악 다운로드
    Kevin MacLeod의 음악은 모두 Public Domain입니다.
    """
    output_dir = project_root / "audio" / "public_domain"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Incompetech의 Public Domain 크리스마스 음악 직접 다운로드 링크
    incompetech_urls = {
        "christmas_song": "https://incompetech.com/music/royalty-free/music/Christmas_Song.mp3",
        "snow_theme": "https://incompetech.com/music/royalty-free/music/Snow_Theme.mp3",
    }
    
    for name, url in incompetech_urls.items():
        try:
            filename = f"{name}.mp3"
            output_path = output_dir / filename
            
            if output_path.exists():
                logger.info(f"이미 다운로드됨: {output_path}")
                return output_path
            
            logger.info(f"Incompetech에서 다운로드 중: {name}")
            result = download_christmas_music_from_url(url, filename, output_dir)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Incompetech 다운로드 실패 ({name}): {e}")
            continue
    
    return None


def get_public_domain_christmas_music() -> Optional[Path]:
    """
    Public Domain 크리스마스 음악 다운로드
    여러 소스를 시도
    
    Returns:
        다운로드된 파일 경로
    """
    output_dir = project_root / "audio" / "public_domain"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 이미 다운로드된 파일 확인
    existing_files = list(output_dir.glob("*.mp3")) + list(output_dir.glob("*.wav"))
    if existing_files:
        logger.info(f"기존 Public Domain 음악 파일 발견: {existing_files[0]}")
        return existing_files[0]
    
    # 방법 1: FreePD에서 Public Domain 음악 다운로드 시도 (완전 PD)
    logger.info("FreePD에서 Public Domain 크리스마스 음악 다운로드 시도 중...")
    result = download_from_freepd("christmas", output_dir)
    if result:
        return result
    
    # 방법 2: Pixabay Music에서 상업용 완전 무료 음악 다운로드 시도
    logger.info("Pixabay Music에서 상업용 완전 무료 크리스마스 음악 다운로드 시도 중...")
    result = download_from_pixabay("christmas", output_dir)
    if result:
        return result
    
    # 방법 2-1: Pixabay Selenium 다운로더 시도 (Cloudflare 우회)
    try:
        logger.info("Pixabay Selenium 다운로더로 크리스마스 음악 다운로드 시도 중...")
        from scripts.pixabay_christmas_downloader import main as pixabay_selenium_main
        # Selenium 다운로더는 여러 파일을 다운로드하므로, 기존 파일 확인만 수행
        existing_files = list(output_dir.glob("*.mp3")) + list(output_dir.glob("*.wav"))
        if existing_files:
            logger.info(f"기존 Public Domain 음악 파일 발견: {existing_files[0]}")
            return existing_files[0]
        # Selenium 다운로더는 별도로 실행하도록 안내
        logger.info("Selenium 다운로더는 별도로 실행하세요: python scripts/pixabay_christmas_downloader.py")
    except ImportError:
        logger.debug("Selenium이 설치되지 않았습니다. pip install selenium webdriver-manager")
    except Exception as e:
        logger.debug(f"Selenium 다운로더 확인 실패: {e}")
    
    # 방법 3: Musopen에서 Public Domain 녹음 다운로드 시도 (PD 녹음만)
    logger.info("Musopen에서 Public Domain 크리스마스 녹음 다운로드 시도 중...")
    result = download_from_musopen("christmas", output_dir)
    if result:
        return result
    
    # 방법 3: 사용자에게 수동 다운로드 안내
    logger.info("=" * 60)
    logger.info("Public Domain 크리스마스 음악 다운로드 안내")
    logger.info("=" * 60)
    logger.info("")
    logger.info("자동 다운로드 실패. 다음 명령어로 수동 다운로드하세요:")
    logger.info("")
    logger.info("# 방법 1: FreePD에서 직접 다운로드")
    logger.info("curl -L -o " + str(output_dir / "christmas_cafe.mp3") + " 'https://freepd.com/christmas/Christmas_Song.mp3'")
    logger.info("")
    logger.info("# 방법 2: 브라우저에서 다운로드")
    logger.info("1. https://freepd.com/christmas.php 방문")
    logger.info("2. 원하는 음악 클릭 후 다운로드")
    logger.info(f"3. {output_dir / 'christmas_cafe.mp3'}에 저장")
    logger.info("")
    logger.info("=" * 60)
    
    return None


def main():
    """메인 함수"""
    try:
        if len(sys.argv) > 1:
            url = sys.argv[1]
            filename = sys.argv[2] if len(sys.argv) > 2 else "downloaded_music.mp3"
            result = download_christmas_music_from_url(url, filename)
            if result:
                print(f"\n다운로드 완료: {result}")
                return result
        else:
            # 자동 다운로드 시도
            result = get_public_domain_christmas_music()
            if result:
                print(f"\n음악 파일: {result}")
                return result
            else:
                print("\n자동 다운로드 불가. 위 안내를 따라 수동으로 다운로드하세요.")
                print(f"다운로드한 파일을 다음 위치에 저장하세요:")
                print(f"{project_root / 'audio' / 'public_domain' / 'christmas_cafe.mp3'}")
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

