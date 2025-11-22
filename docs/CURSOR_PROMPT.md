# Cursor AI 프롬프트 가이드

이 문서는 Cursor AI가 이 프로젝트를 이해하고 올바르게 구현할 수 있도록 작성된 가이드입니다.

## 프로젝트 개요

현재 프로젝트는 **다양한 주제의 YouTube 롱폼 영상**을 자동 생성하는 파이프라인입니다.

### 지원 모드

| 모드 | 설명 | 주요 스크립트 |
|------|------|--------------|
| `longform_bgm` | Public Domain 음악 또는 합성 음원을 조합한 2~6시간 BGM | `generate_bgm.py`, `generate_image.py`, `make_video.py` |
| `spot_difference` | GPT 이미지/분석을 활용한 시니어용 틀린그림찾기 (10~20 문제) | `generate_spot_difference*.py`, `make_spot_difference_video.py` |
| `brain_training` | GPT 문제 생성 기반 시니어 두뇌훈련 (7가지 모듈) | `generate_brain_training*.py`, `make_brain_training_video.py` |
| (Legacy) `noise` | 전통적인 노이즈/환경음 합성 | `generate_audio.py` |

## 프로젝트 구조

```
youtubenoise/
├── scripts/                    # 실행 스크립트들
│   ├── generate_audio.py       # 오디오 생성 (화이트노이즈, 브라운노이즈, 핑크노이즈, 빗소리, 파도, 벽난로 등)
│   ├── generate_bgm.py         # 롱폼 BGM 생성 (Public Domain 음악 조합 또는 알고리즘 생성)
│   ├── generate_image.py       # 배경 이미지 생성 (DALL·E, Public Domain 이미지, Pillow 그라데이션)
│   ├── generate_title_description.py  # YouTube 메타데이터 생성 (OpenAI API 사용)
│   ├── make_video.py           # FFmpeg로 영상 생성
│   ├── upload_youtube.py       # YouTube 업로드
│   ├── scheduler.py            # 전체 파이프라인 자동 실행
│   ├── public_domain_catalog.py  # Public Domain 음악 분류 및 카탈로그 관리
│   ├── generate_spot_difference.py  # 시니어용 틀린그림찾기 영상 생성 (메인 파이프라인)
│   ├── generate_spot_difference_image.py  # 틀린그림찾기용 이미지 생성/편집 (GPT 이미지 생성·분석 API)
│   ├── generate_spot_difference_metadata.py  # 틀린그림찾기 내레이션/자막/챕터 자동 생성
│   ├── make_spot_difference_video.py  # 비교 화면·카운트다운·정답 하이라이트 합성
│   ├── generate_brain_training.py  # 시니어 브레인트레이닝 콘텐츠 (메인 파이프라인)
│   ├── generate_brain_training_content.py  # 모듈별 문제 생성
│   ├── generate_brain_training_metadata.py  # 메타데이터 생성
│   ├── make_brain_training_video.py  # 영상 합성
│   └── log_prompt.py           # 프롬프트 로깅 유틸리티
├── config/                     # 설정 파일
│   ├── config.json             # 기본 설정
│   ├── bgm_presets.yaml        # BGM 프리셋 설정
│   ├── spot_difference_presets.yaml  # 틀린그림찾기 프리셋 설정
│   ├── brain_training_presets.yaml  # 브레인트레이닝 프리셋 설정
│   └── .env                    # 환경변수 (YouTube API, OpenAI API 키)
├── audio/
│   └── public_domain/          # 장르별 Public Domain 음악
├── images/                     # 생성된 배경/틀린그림찾기 이미지
├── videos/                     # 생성된 영상 파일
├── logs/                       # 로그 파일 및 히스토리
│   ├── app.log                 # 애플리케이션 로그
│   ├── prompts_YYYY-MM-DD.jsonl  # 프롬프트 로그 (날짜별)
│   └── history.json            # 작업 히스토리
└── docs/                       # 문서 모음
```

## 코드 스타일 및 규칙

### 경로 처리
- 모든 스크립트는 `project_root = Path(__file__).parent.parent` (또는 `.parent` for root scripts)를 기준으로 경로 처리
- `load_dotenv(project_root / ".env")`로 환경변수 로드
- `load_config()` 함수로 `config/config.json` 로드
- 절대 경로 사용 시 `Path(__file__).parent` 기준으로 상대 경로 계산

### 로깅
- `logging` 모듈 사용, `logs/app.log`에 저장
- 로거는 `logger = logging.getLogger(__name__)` 형식으로 생성
- INFO 레벨 이상의 로그는 파일과 콘솔 모두에 출력
- 한글로 로그 메시지 작성

### 에러 처리
- 모든 주요 함수는 try-except 블록으로 에러 처리
- 예외 발생 시 로깅 후 적절한 fallback 처리
- 사용자에게 명확한 에러 메시지 제공

### 함수 설계
- 함수는 독립적으로 실행 가능하도록 설계
- 함수는 재사용 가능하도록 모듈화
- 함수명은 한글 docstring 포함

### 설정 관리
- 설정은 `config.json` 또는 YAML 파일 사용
- 환경변수는 `.env` 파일 사용
- API 키는 절대 코드에 하드코딩하지 않음

### 이미지 처리
- DALL·E 생성 이미지는 1024x1024에서 1920x1080으로 리사이즈
- 썸네일은 2MB 이하로 압축 (JPEG, quality=90)
- 이미지 저장 시 날짜 프리픽스 사용 (예: `2025-11-17_*.png`)
- **중요**: 썸네일/배경 이미지는 16:9 비율(1920x1080)로 중앙 크롭 후 리사이즈 (좌우 늘어남 방지)

### 음악 처리
- Public Domain 음악은 `audio/public_domain/`에 저장
- `public_domain_catalog.py`로 자동 분류 및 카탈로그 생성
- BGM 생성 시 프리셋의 `public_domain_categories` 설정에 따라 필터링

### 비디오 처리
- FFmpeg를 사용하여 영상 생성
- 영상 파일명 형식: `{date}_{preset}_{duration}min.mp4`
- 롱폼 BGM은 2~6시간 길이 지원

## 구현 시 참고사항

1. **기존 코드 패턴을 따라 구현**: 새로운 기능 추가 시 기존 스크립트의 패턴을 참고
2. **`project_root` 기준으로 경로 처리**: 모든 파일 경로는 `project_root`를 기준으로 계산
3. **로깅 및 에러 처리 포함**: 모든 주요 함수에 로깅과 에러 처리 포함
4. **함수는 재사용 가능하도록 모듈화**: 독립적으로 실행 가능하고 재사용 가능한 함수 설계
5. **설정은 `config.json` 또는 YAML 파일 사용**: 하드코딩 지양
6. **환경변수는 `.env` 파일 사용**: API 키 등 민감한 정보는 환경변수로 관리
7. **문서 구조**: `docs/README.md`의 Active/Legacy 섹션 참고하여 문서 분류

## 프롬프트 로깅

프로젝트에는 프롬프트 로깅 시스템이 포함되어 있습니다. 사용자가 Cursor에서 입력한 프롬프트는 자동으로 `logs/prompts_YYYY-MM-DD.jsonl`에 기록됩니다.

### 로그 형식
```json
{
  "timestamp": "2025-11-21T10:30:00.123456",
  "machine": {
    "hostname": "machine-name",
    "platform": "Darwin-25.1.0",
    "system": "Darwin",
    "release": "25.1.0",
    "python_version": "3.11.0"
  },
  "ide": {
    "ide": "Cursor",
    "cursor_version": "0.40.0"
  },
  "prompt": "사용자가 입력한 프롬프트",
  "context": "추가 컨텍스트 (선택사항)",
  "metadata": {}
}
```

### 사용법
```bash
# 프롬프트 로깅
python -m scripts.log_prompt --prompt "프롬프트 내용"

# 로그 읽기
python -m scripts.log_prompt --read

# 특정 날짜 로그 읽기
python -m scripts.log_prompt --read --date 2025-11-21
```

## 주요 기능

### 롱폼 BGM 모드
- Public Domain 음악 자동 선택 및 조합
- DALL·E를 통한 배경 이미지 생성 (fallback: Public Domain 이미지 → Pillow 그라데이션)
- OpenAI GPT를 통한 제목/설명/태그 자동 생성
- YouTube 자동 업로드

### 틀린그림찾기 모드
- GPT API를 활용한 이미지 생성 및 편집
- 차이점 자동 분석 및 좌표 추출
- 비교 화면, 카운트다운, 정답 화면 자동 생성
- 시니어 친화적 디자인 (큰 글자, 따뜻한 색상)

### 브레인트레이닝 모드
- 7가지 모듈: 숫자 기억, 사라진 물건 찾기, 패턴 순서, 단어 연상, 시계 읽기, 한글 퍼즐, 종합 훈련
- GPT API를 활용한 문제 자동 생성
- 시니어 친화적 디자인 (큰 글자, 높은 대비, 느린 템포)

## 응답 언어

- 모든 응답은 한글로 작성
- 코드 주석도 한글로 작성
- 로그 메시지도 한글로 작성

