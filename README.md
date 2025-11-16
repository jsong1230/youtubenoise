# YouTube Noise Generator

유튜브용 화이트노이즈/자연음/롱폼 BGM 영상을 완전 자동으로 생성하고 업로드하여 수익을 낼 수 있는 Python 프로젝트입니다.

## 프로젝트 목적

이 프로젝트는 화이트노이즈, 브라운노이즈, 핑크노이즈, 빗소리, 파도 소리, 벽난로 소리, 로파이 힙합 비트, ASMR 소리 등의 환경음/음악을 자동으로 생성하고, AI로 배경 이미지를 만들고, FFmpeg로 영상으로 합친 뒤, YouTube Data API를 통해 자동 업로드까지 하는 end-to-end 자동화 파이프라인입니다.

**새로운 기능**: 롱폼 BGM 모드로 2~6시간 길이의 카페/클래식/크리스마스 BGM 영상을 자동 생성할 수 있습니다.

최종적으로는 cron 등으로 스크립트를 주기적으로 실행시키면 사람이 손대지 않아도 매일 새로운 화이트노이즈/자연음/롱폼 BGM 영상이 유튜브에 업로드되어, 장기적으로 광고 수익을 만들 수 있는 구조를 목표로 합니다.

## 프로젝트 구조

```
youtubenoise/
  audio/                    # 생성된 오디오 파일 저장
    public_domain/          # Public Domain 음악 파일
  images/                   # 생성된 이미지 파일 저장
  videos/                   # 생성된 영상 파일 저장
  scripts/                  # 실행 스크립트들
    generate_audio.py       # 오디오 자동 생성
    generate_bgm.py         # 롱폼 BGM 생성
    generate_image.py       # 이미지 생성
    generate_title_description.py  # 제목/설명/태그 자동 생성
    make_video.py           # 영상 생성
    upload_youtube.py       # 유튜브 업로드
    update_statistics.py    # 영상 통계 업데이트
    scheduler.py            # 전체 파이프라인 스케줄러
  config/                   # 설정 파일
    config.json             # 기본 설정
    bgm_presets.yaml        # BGM 프리셋 설정
    ambience_presets.yaml   # 앰비언스 프리셋
  logs/                     # 로그 파일
    app.log                 # 애플리케이션 로그
    history.json            # 업로드 히스토리
  .env                      # 환경변수 (직접 생성 필요)
  requirements.txt          # Python 패키지 의존성
  main.py                   # 메인 CLI 인터페이스
  README.md                 # 프로젝트 문서
```

## 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
cd /path/to/youtubenoise
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

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# OpenAI API 키 (메타데이터 생성용)
OPENAI_API_KEY=sk-your-openai-api-key-here

# YouTube OAuth 인증 정보
YOUTUBE_CLIENT_ID=your-client-id
YOUTUBE_CLIENT_SECRET=your-client-secret
YOUTUBE_REFRESH_TOKEN=your-refresh-token

# 선택사항: Pixabay API 키 (Public Domain 음악 다운로드용)
PIXABAY_API_KEY=your-pixabay-api-key
```

### 2. OpenAI API 키 설정

OpenAI API 키는 [OpenAI Platform](https://platform.openai.com/api-keys)에서 발급받을 수 있습니다.

**참고**: 
- 오디오 생성: pydub와 numpy로 직접 생성 (무료)
- 이미지 생성: Pillow로 직접 생성 (무료)
- 메타데이터 생성: OpenAI API 사용 (유료, 하지만 gpt-4o-mini는 매우 저렴함)

### 3. YouTube OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" > "사용자 인증 정보"로 이동
4. "사용자 인증 정보 만들기" > "OAuth 클라이언트 ID" 선택
5. 애플리케이션 유형: "데스크톱 앱" 선택
6. 이름 입력 후 생성
7. 클라이언트 ID와 시크릿을 `.env` 파일에 추가
8. YouTube Data API v3를 사용 설정 (API 및 서비스 > 라이브러리에서 활성화)

## 실행 방법

### 롱폼 BGM 모드 (권장)

롱폼 BGM 모드는 2~6시간 길이의 카페/클래식/크리스마스 BGM 영상을 자동 생성합니다.

#### 기본 사용법

```bash
# 프리셋 목록 보기
python main.py --list-presets

# 크리스마스 카페 BGM 생성 (3시간, 업로드 없음)
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180

# 크리스마스 카페 BGM 생성 및 YouTube 업로드
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180 --upload
```

#### Public Domain 음악 사용

`audio/public_domain/` 폴더에 MP3 파일을 저장하면 자동으로 사용됩니다:

```bash
# 1. Public Domain 음악 다운로드 (브라우저에서)
# - https://freepd.com/christmas.php
# - https://pixabay.com/music/search/christmas/
# - https://musopen.org/music/?q=christmas&license=pd

# 2. 다운로드한 파일을 다음 위치로 이동
mv ~/Downloads/*.mp3 audio/public_domain/christmas_cafe.mp3

# 3. BGM 생성 (자동으로 Public Domain 음악 사용됨!)
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

여러 파일이 있으면 자동으로 조합됩니다.

#### 영상 통계 관리

```bash
# 모든 영상의 통계 업데이트 (조회수, 좋아요, 댓글 수)
python main.py --update-stats

# 영상 통계 리포트 출력
python main.py --report
```

### 기존 노이즈 모드

기존의 화이트노이즈/자연음 생성 모드도 사용할 수 있습니다:

```bash
# 전체 파이프라인 실행
python scripts/scheduler.py

# 개별 스크립트 실행
python scripts/generate_audio.py white_noise
python scripts/generate_image.py white_noise
python scripts/make_video.py images/bg.png audio/noise.mp3
```

## 지원하는 콘텐츠 타입

### 롱폼 BGM 프리셋

- `christmas_cafe_3h`: 크리스마스 카페 BGM (3시간)
- `cafe_jazz_3h`: 카페 재즈 BGM (3시간)
- `cafe_classical_3h`: 카페 클래식 BGM (3시간)
- `classical_piano_3h`: 클래식 피아노 BGM (3시간)

### 노이즈 타입

- `white_noise`: 화이트 노이즈
- `brown_noise`: 브라운 노이즈
- `pink_noise`: 핑크 노이즈
- `rain`: 빗소리
- `ocean`: 파도 소리
- `fireplace`: 벽난로 소리
- `lofi`: 로파이 힙합 비트 (공부/집중용)
- `asmr`: ASMR 소리 (속삭임, 타이핑, 물소리 등)

## Public Domain 음악 사용 가이드

### 추천 소스

1. **FreePD** (https://freepd.com/)
   - 완전 Public Domain
   - 크리스마스 카테고리 제공

2. **Pixabay Music** (https://pixabay.com/music/)
   - 상업용 완전 무료
   - API 키로 자동 다운로드 가능

3. **Musopen** (https://musopen.org/)
   - Public Domain 녹음만 선택 가능
   - 클래식 음악 전문

### 사용 방법

1. 브라우저에서 Public Domain 음악 다운로드
2. `audio/public_domain/` 폴더에 저장
3. BGM 생성 시 자동으로 사용됨

자세한 내용은 `MUSIC_SOURCES.md`를 참고하세요.

## 설정 파일

### config/config.json

```json
{
  "audio_length_sec": 14400,
  "noise_types": ["white_noise", "brown_noise", "pink_noise", "rain", "ocean", "fireplace", "lofi", "asmr"],
  "language": "en",
  "openai_model": "gpt-4o-mini",
  "youtube": {
    "client_secret_file": "config/youtube_client_secret.json",
    "token_file": "config/token.json",
    "default_tags": ["white noise", "sleep", "relax", "study", "asmr"]
  }
}
```

### config/bgm_presets.yaml

BGM 프리셋 설정 파일입니다. 프리셋별로 음악 스타일, 악기, 색상 스킴 등을 설정할 수 있습니다.

## 로그 및 히스토리

- `logs/app.log`: 모든 스크립트의 실행 로그
- `logs/history.json`: 업로드된 영상의 히스토리 (video ID, 생성 시간, 통계 등)

## 자동 스케줄링 (cron)

매일 자동으로 실행하려면 cron을 설정하세요:

```bash
# crontab 편집
crontab -e

# 매일 오전 2시에 실행
0 2 * * * cd /path/to/youtubenoise && /path/to/venv/bin/python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180 --upload >> logs/cron.log 2>&1
```

## 주의사항

1. **YouTube 정책 준수**: 자동 생성된 콘텐츠도 YouTube의 커뮤니티 가이드라인을 준수해야 합니다.
2. **저작권**: Public Domain 또는 CC0 라이선스 음악만 사용하세요. 알고리즘 생성 음악도 사용 가능하지만, 실제 Public Domain 음악 사용을 권장합니다.
3. **API 비용**: OpenAI API 사용 시 비용이 발생할 수 있습니다. gpt-4o-mini는 매우 저렴하지만 사용량을 모니터링하세요.
4. **OAuth 인증**: YouTube 업로드 시 처음 한 번은 브라우저에서 인증이 필요합니다.
5. **FFmpeg 필수**: 영상 생성에는 FFmpeg가 반드시 설치되어 있어야 합니다.

## 문제 해결

### FFmpeg를 찾을 수 없음
- FFmpeg가 설치되어 있는지 확인: `ffmpeg -version`
- PATH 환경변수에 FFmpeg가 포함되어 있는지 확인

### OpenAI API 오류
- `.env` 파일에 올바른 API 키가 설정되어 있는지 확인
- API 키의 사용량 한도를 확인
- gpt-4o-mini 모델 사용을 권장 (비용 효율적)

### YouTube 업로드 실패
- `.env` 파일에 YouTube OAuth 정보가 올바르게 설정되어 있는지 확인
- YouTube Data API v3가 활성화되어 있는지 확인
- OAuth 인증이 완료되었는지 확인

### Public Domain 음악이 사용되지 않음
- `audio/public_domain/` 폴더에 MP3 또는 WAV 파일이 있는지 확인
- 파일 권한 확인
- 로그 파일에서 오류 메시지 확인

## 라이선스

이 프로젝트는 개인 사용 및 학습 목적으로 제공됩니다.

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.
