# YouTube Noise Generator

유튜브용 화이트노이즈/자연음 영상을 완전 자동으로 생성하고 업로드하여 수익을 낼 수 있는 Python 프로젝트입니다.

## 프로젝트 목적

이 프로젝트는 화이트노이즈, 브라운노이즈, 핑크노이즈, 빗소리, 파도 소리, 벽난로 소리 등의 환경음을 자동으로 생성하고, AI로 배경 이미지를 만들고, FFmpeg로 영상으로 합친 뒤, YouTube Data API를 통해 자동 업로드까지 하는 end-to-end 자동화 파이프라인입니다.

최종적으로는 cron 등으로 `scheduler.py`를 주기적으로 실행시키면 사람이 손대지 않아도 매일 새로운 화이트노이즈/자연음 영상이 유튜브에 업로드되어, 장기적으로 광고 수익을 만들 수 있는 구조를 목표로 합니다.

## 프로젝트 구조

```
youtube-noise/
  audio/              # 생성된 오디오 파일 저장
  images/             # 생성된 이미지 파일 저장
  videos/             # 생성된 영상 파일 저장
  scripts/            # 실행 스크립트들
    generate_audio.py              # 오디오 자동 생성
    generate_image.py              # AI 이미지 생성
    generate_title_description.py  # 제목/설명/태그 자동 생성
    make_video.py                  # 영상 생성
    upload_youtube.py              # 유튜브 업로드
    scheduler.py                   # 전체 파이프라인 스케줄러
  config/             # 설정 파일
    config.json                    # 기본 설정
    youtube_client_secret.json     # YouTube OAuth 클라이언트 시크릿 (직접 생성 필요)
    token.json                     # YouTube OAuth 토큰 (자동 생성)
  logs/               # 로그 파일
    app.log                       # 애플리케이션 로그
    history.json                  # 업로드 히스토리
  .env                # 환경변수 (직접 생성 필요)
  requirements.txt    # Python 패키지 의존성
  README.md          # 프로젝트 문서
```

## 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
cd /path/to/youtube-noise
```

### 2. Python 가상환경 생성 및 활성화 (권장)

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. FFmpeg 설치

FFmpeg는 영상 생성에 필요합니다.

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
[FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드하거나 Chocolatey로 설치:
```bash
choco install ffmpeg
```

## 환경변수 설정

### 1. .env 파일 생성

`.env.example` 파일을 참고하여 `.env` 파일을 생성하세요:

```bash
cp .env.example .env
```

### 2. OpenAI API 키 설정

`.env` 파일을 열고 OpenAI API 키를 입력하세요:

```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

OpenAI API 키는 [OpenAI Platform](https://platform.openai.com/api-keys)에서 발급받을 수 있습니다.

### 3. YouTube OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" > "사용자 인증 정보"로 이동
4. "사용자 인증 정보 만들기" > "OAuth 클라이언트 ID" 선택
5. 애플리케이션 유형: "데스크톱 앱" 선택
6. 이름 입력 후 생성
7. 다운로드한 JSON 파일을 `config/youtube_client_secret.json`에 저장
8. YouTube Data API v3를 사용 설정 (API 및 서비스 > 라이브러리에서 활성화)

## 설정 파일

`config/config.json` 파일에서 기본 설정을 변경할 수 있습니다:

```json
{
  "audio_length_sec": 14400,  // 오디오 길이 (초, 기본값: 4시간)
  "noise_types": ["white_noise", "brown_noise", "pink_noise", "rain", "ocean", "fireplace"],
  "language": "en",
  "openai_model": "gpt-4o-mini",  // 또는 "gpt-4o"
  "youtube": {
    "client_secret_file": "config/youtube_client_secret.json",
    "token_file": "config/token.json",
    "default_tags": ["white noise", "sleep", "relax", "study", "asmr"]
  }
}
```

## 실행 방법

### 개별 스크립트 실행

각 스크립트는 독립적으로 실행할 수 있습니다:

#### 1. 오디오 생성
```bash
python scripts/generate_audio.py
```

#### 2. 이미지 생성
```bash
python scripts/generate_image.py white_noise
```

#### 3. 메타데이터 생성
```bash
python scripts/generate_title_description.py white_noise 4
```

#### 4. 영상 생성
```bash
python scripts/make_video.py images/2025-11-15_white_noise_bg.png audio/2025-11-15_white_noise_4h.mp3
```

#### 5. 유튜브 업로드
```bash
python scripts/upload_youtube.py videos/video.mp4 "제목" "설명" '["tag1","tag2"]'
```

### 전체 파이프라인 실행 (권장)

`scheduler.py`를 실행하면 전체 파이프라인이 자동으로 실행됩니다:

```bash
python scripts/scheduler.py
```

이 스크립트는 다음을 자동으로 수행합니다:
1. 설정에서 노이즈 타입 랜덤 선택
2. 오디오 생성
3. 배경 이미지 생성
4. 제목/설명/태그 생성
5. 영상 생성
6. 유튜브 업로드
7. 결과를 로그에 기록

### 자동 스케줄링 (cron)

매일 자동으로 실행하려면 cron을 설정하세요:

```bash
# crontab 편집
crontab -e

# 매일 오전 2시에 실행
0 2 * * * cd /path/to/youtube-noise && /path/to/venv/bin/python scripts/scheduler.py >> logs/cron.log 2>&1
```

## 지원하는 노이즈 타입

- `white_noise`: 화이트 노이즈
- `brown_noise`: 브라운 노이즈
- `pink_noise`: 핑크 노이즈
- `rain`: 빗소리
- `ocean`: 파도 소리
- `fireplace`: 벽난로 소리

## 로그 및 히스토리

- `logs/app.log`: 모든 스크립트의 실행 로그
- `logs/history.json`: 업로드된 영상의 히스토리 (video ID, 생성 시간 등)

## 주의사항

1. **YouTube 정책 준수**: 자동 생성된 콘텐츠도 YouTube의 커뮤니티 가이드라인을 준수해야 합니다.
2. **API 비용**: OpenAI API 사용 시 비용이 발생할 수 있습니다. 사용량을 모니터링하세요.
3. **저작권**: 생성된 오디오와 이미지는 자동 생성된 것이지만, YouTube 정책을 확인하세요.
4. **OAuth 인증**: YouTube 업로드 시 처음 한 번은 브라우저에서 인증이 필요합니다.
5. **FFmpeg 필수**: 영상 생성에는 FFmpeg가 반드시 설치되어 있어야 합니다.

## 문제 해결

### FFmpeg를 찾을 수 없음
- FFmpeg가 설치되어 있는지 확인: `ffmpeg -version`
- PATH 환경변수에 FFmpeg가 포함되어 있는지 확인

### OpenAI API 오류
- `.env` 파일에 올바른 API 키가 설정되어 있는지 확인
- API 키의 사용량 한도를 확인

### YouTube 업로드 실패
- `config/youtube_client_secret.json` 파일이 올바른 위치에 있는지 확인
- YouTube Data API v3가 활성화되어 있는지 확인
- OAuth 인증이 완료되었는지 확인 (첫 실행 시 브라우저에서 인증 필요)

## 라이선스

이 프로젝트는 개인 사용 및 학습 목적으로 제공됩니다.

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

