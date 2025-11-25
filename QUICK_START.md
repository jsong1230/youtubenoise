# 빠른 시작 가이드 (Quick Start Guide)

**다른 머신이나 IDE에서 작업을 시작할 때 이 문서를 먼저 읽으세요.**

---

## 📍 현재 프로젝트 상태

- **프로젝트명**: YouTube Longform Generator
- **최종 업데이트**: 2025-11-22
- **현재 단계**: 코드 품질 개선 완료 → 다음 단계: 타입 힌팅 적용

---

## 🚀 5분 안에 시작하기

### 1. 저장소 클론/업데이트
```bash
git pull  # 또는 git clone
cd youtubenoise
```

### 2. 필수 문서 확인
```bash
# 작업 히스토리 확인 (가장 중요!)
cat HISTORY.md

# TODO 확인
cat TODO.md
```

### 3. 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 확인/생성
cp .env.example .env  # 필요시
# .env 파일에 필수 API 키 설정
```

### 4. 프로젝트 상태 확인
```bash
# 공통 유틸리티 테스트
python -c "from scripts.utils import setup_logging; print('✅ Utils OK')"

# 주요 스크립트 import 테스트
python -c "import scripts.generate_bgm; import scripts.upload_youtube; print('✅ Scripts OK')"
```

---

## 📚 필수 문서 읽기 순서

1. **`HISTORY.md`** ⭐ (가장 중요)
   - 최근 작업 내역
   - 현재 상태
   - 프로젝트 전체 히스토리
   - 주요 결정사항

2. **`TODO.md`**
   - 진행 중인 작업
   - 다음 우선순위

3. **`README.md`**
   - 프로젝트 개요
   - 사용법

4. **`docs/CURSOR_PROMPT.md`**
   - Cursor AI 가이드
   - 프로젝트 구조

---

## 🔑 필수 API 키

`.env` 파일에 다음 키들이 설정되어 있어야 합니다:

```bash
# 필수
OPENAI_API_KEY=sk-...
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...

# 선택 (기능 사용 시 필요)
ANTHROPIC_API_KEY=sk-ant-...  # Claude API (AI Explainer)
UNSPLASH_ACCESS_KEY=...        # 무료 이미지 API
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
```

---

## 🎯 주요 명령어

### 콘텐츠 생성
```bash
# BGM 생성
python main.py --mode longform_bgm --preset cafe_jazz_3h

# 틀린그림찾기 생성
python main.py --mode spot_difference --preset senior_easy

# AI Explainer 생성
python main.py --mode ai_explainer --topic "ChatGPT로 코딩하기"

# 자동 스케줄 실행
python main.py --mode auto
```

### 모니터링
```bash
# 웹 대시보드 실행
python run_dashboard.py
# 브라우저에서 http://localhost:5001 접속

# 채널 상태 동기화
python scripts/sync_channel_state.py
```

---

## 🛠️ 개발 환경 설정

### Python 버전
- Python 3.8 이상 권장

### 주요 의존성
- `openai`: OpenAI API
- `anthropic`: Claude API
- `flask`: 웹 대시보드
- `pydub`: 오디오 처리
- `Pillow`: 이미지 처리
- `ffmpeg`: 영상 생성 (시스템 설치 필요)

### FFmpeg 설치 확인
```bash
ffmpeg -version  # 설치 확인
# 설치되지 않았다면:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

---

## 📁 프로젝트 구조 핵심

```
youtubenoise/
├── scripts/           # 실행 스크립트
│   └── utils.py      # ⭐ 공통 유틸리티 (최신)
├── src/
│   ├── api/          # API 통합
│   └── web/          # 웹 대시보드
├── config/           # 설정 파일
├── data/             # 데이터 (Git 추적)
├── docs/             # 문서
├── HISTORY.md        # ⭐ 작업 히스토리 및 프로젝트 히스토리
└── TODO.md           # TODO 목록
```

---

## ⚠️ 주의사항

### Git 관리
- `data/channel_state.json`, `data/api_usage.json`은 Git으로 추적됨
- 민감한 정보가 포함되지 않도록 주의

### 로깅
- 모든 스크립트는 `scripts/utils.py`의 `setup_logging()` 사용
- 로그 파일: `logs/app.log`

### API 비용
- Claude API 사용 시 비용 96% 절감 (GPT 대비)
- 무료 이미지 API 우선 사용 (Unsplash, Pexels, Pixabay)
- API 사용량은 `data/api_usage.json`에 추적됨

---

## 🆘 문제 해결

### Import 에러
```bash
# 프로젝트 루트에서 실행 확인
cd /path/to/youtubenoise
python -c "from scripts.utils import setup_logging; print('OK')"
```

### 로깅 문제
- `logs/app.log` 파일 권한 확인
- `scripts/utils.py`의 `setup_logging()` 함수 확인

### API 호출 실패
- `.env` 파일의 API 키 확인
- `logs/app.log`에서 에러 메시지 확인
- 재시도 로직이 자동으로 작동함 (최대 3회)

---

## 📞 다음 단계

작업을 시작하기 전에:
1. `HISTORY.md` 읽기
2. `TODO.md`에서 다음 우선순위 확인
3. 현재 브랜치 확인: `git branch`
4. 최신 상태로 업데이트: `git pull`

---

**마지막 업데이트**: 2025-11-22  
**작성 목적**: 다른 머신/IDE에서 빠르게 작업 시작하기

