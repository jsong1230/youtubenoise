# Pixabay Selenium 다운로더 가이드

## 개요

`pixabay_christmas_downloader.py`는 Selenium을 사용하여 Pixabay에서 크리스마스 음악을 자동으로 다운로드하는 스크립트입니다.
Cloudflare 봇 차단을 우회하기 위해 실제 브라우저를 시뮬레이션합니다.

## 장점

- ✅ **Cloudflare 우회**: 실제 브라우저를 사용하여 봇 차단 우회
- ✅ **자동 다운로드**: 여러 페이지를 순회하며 자동으로 음악 다운로드
- ✅ **프로젝트 통합**: 다운로드한 파일이 자동으로 `audio/public_domain/`에 저장되어 BGM 생성에 사용됨

## 필수 요구사항

### 1. Chrome 브라우저 설치

macOS:
```bash
# Homebrew로 설치
brew install --cask google-chrome
```

Linux:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# 또는 Chromium
sudo apt-get install -y chromium-browser
```

### 2. Python 패키지 설치

```bash
pip install selenium webdriver-manager
```

또는 전체 requirements 설치:
```bash
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용

```bash
python scripts/pixabay_christmas_downloader.py
```

### 설정 변경

스크립트 상단의 설정값을 수정할 수 있습니다:

```python
MAX_PAGES = 3          # 최대 몇 페이지까지 순회할지
MAX_TRACKS = 50       # 최대 몇 곡까지 다운로드할지
WAIT_BETWEEN_DOWNLOADS = 2  # 곡 사이 딜레이(초)
```

## 동작 방식

1. **Chrome WebDriver 초기화**: Headless 모드로 Chrome 브라우저 실행
2. **페이지 순회**: Pixabay 크리스마스 음악 검색 결과 페이지를 순회
3. **트랙 링크 추출**: 각 페이지에서 개별 음악 트랙 링크 추출
4. **다운로드 버튼 클릭**: 각 트랙 페이지에서 Download 버튼 클릭
5. **MP3 URL 추출**: 팝업에서 실제 MP3 다운로드 URL 추출
6. **파일 다운로드**: `requests`로 MP3 파일 다운로드
7. **저장**: `audio/public_domain/` 폴더에 저장

## 저장 위치

다운로드된 파일은 다음 위치에 저장됩니다:

```
audio/public_domain/
  ├── Christmas_Holiday_Festive_Cheer_Snow.mp3
  ├── Jingle_Bells_Christmas_Music.mp3
  └── ...
```

## 문제 해결

### "WebDriver 설정 실패" 오류

**원인**: Chrome 브라우저가 설치되지 않았거나 ChromeDriver를 찾을 수 없음

**해결**:
1. Chrome 브라우저 설치 확인
2. `webdriver-manager`가 자동으로 ChromeDriver를 다운로드하지만, 수동 설치도 가능:
   ```bash
   pip install --upgrade webdriver-manager
   ```

### "페이지 로딩 타임아웃" 경고

**원인**: 네트워크가 느리거나 Pixabay 서버 응답 지연

**해결**:
- 인터넷 연결 확인
- 잠시 후 다시 시도
- `WAIT_BETWEEN_DOWNLOADS` 값을 늘려서 서버 부하 감소

### "Download 버튼을 찾지 못함" 경고

**원인**: Pixabay 웹사이트 구조 변경 또는 페이지 로딩 미완료

**해결**:
- 스크립트의 XPath 선택자를 업데이트 필요할 수 있음
- 페이지 로딩 대기 시간을 늘릴 수 있음

### Headless 모드 문제

Headless 모드에서 문제가 발생하면, 스크립트에서 headless 옵션을 주석 처리:

```python
# options.add_argument("--headless=new")  # 주석 처리
```

이렇게 하면 실제 브라우저 창이 열려서 디버깅이 쉬워집니다.

## 주의사항

1. **저작권**: Pixabay의 모든 음악은 무료로 사용 가능하지만, 각 음악의 라이센스를 확인하세요.
2. **서버 부하**: 너무 빠른 요청은 서버에 부담을 줄 수 있으므로 `WAIT_BETWEEN_DOWNLOADS`를 적절히 설정하세요.
3. **Chrome 업데이트**: Chrome 브라우저가 업데이트되면 ChromeDriver도 자동으로 업데이트됩니다.

## 기존 시스템과의 통합

다운로드된 파일은 자동으로 `audio/public_domain/` 폴더에 저장되므로,
BGM 생성 시 자동으로 사용됩니다:

```bash
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

## 대안

Selenium이 작동하지 않는 경우:

1. **수동 다운로드**: 브라우저에서 직접 다운로드 후 `audio/public_domain/`에 저장

