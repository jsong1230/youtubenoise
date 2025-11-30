# TODO 목록

> **참고**: 상세한 2025 전략 및 로드맵은 `TODO_2025_STRATEGY.md`를 참조하세요.

## 최근 완료된 작업

### 2025-11-30
- ✅ 켈틱 음악 장르 추가 및 Public Domain 지원
  - 켈틱 음악 폴더 생성 및 52개 음악 다운로드
  - `celtic_3h` 프리셋 추가
  - 카탈로그 키워드 추가 (celtic, fiddle, irish, scottish 등)
- ✅ Downloads 폴더에서 이미지 자동 사용 기능
  - 배경 이미지 및 썸네일 자동 생성
  - `create_thumbnail_from_downloads.py` 스크립트 추가
- ✅ BGM 생성 최적화
  - 기존 파일 재사용 로직 추가
  - 시간 소요 작업 전 사용자 확인 요청
  - 업로드만 요청 시 기존 파일 자동 재사용

### 2025-11-25
- ✅ AI Explainer 모드 전면 개선
  - TTS 내레이션 추가 (OpenAI TTS API)
  - 코드 스니펫 이미지 생성 (PIL)
  - 다이어그램 자동 생성 (DALL-E)
  - 애니메이션/전환 효과 (FFmpeg 페이드)
  - 자막 자동 생성 (SRT 형식)
  - B-roll 이미지 개선 (검색어 개선, DALL-E 옵션)
  - Claude API 실패 시 OpenAI fallback 개선
  - YAML 구조 수정 (standalone_topics 최상위 레벨로 이동)
  - 짧은 테스트 영상(5분) 생성 성공
- ⚠️ 성능 개선 필요: 영상 생성 시간 및 품질 최적화 필요

## 진행 중
- [x] 프롬프트 로깅 시스템 구현 (머신/IDE 정보 포함)
- [x] CURSOR_PROMPT.md 문서화 및 docs/ 이동

## 🚀 현재 진행 중 (Phase 1)

- [x] HISTORY.md 생성
- [x] data/channel_state.json 생성
- [x] data/api_usage.json 생성
- [x] scripts/sync_channel_state.py 생성
- [x] .gitignore 업데이트 (채널 상태 포함)
- [x] requirements.txt 업데이트 (Flask, anthropic 추가)
- [x] API Manager 구현 (src/api/)
- [x] Flask 웹 대시보드 구현 (src/web/)
- [x] 채널 상태 동기화 테스트

## 📅 다음 단계 (Phase 2-3)

- [x] 이중언어 메타데이터 시스템 구현
- [x] Claude API 통합
- [x] 무료 이미지 API 통합 (Unsplash, Pexels, Pixabay)
- [x] API 사용량 추적 시스템
- [x] AI Explainer 콘텐츠 필러 추가
- [x] 스케줄링 & 자동화 시스템 (요일별 필러 로테이션)

## 프로젝트 개선 사항

### 코드 품질 및 구조
- [x] 공통 유틸리티 함수 모듈화 (`scripts/utils.py` 생성)
- [x] 로깅 설정 중복 제거 (공통 로깅 모듈 생성)
- [x] 에러 처리 표준화 및 재시도 로직 추가
- [x] 나머지 스크립트들도 공통 유틸리티 사용하도록 업데이트 (14개 파일)
- [x] 타입 힌팅 전면 적용 (`scripts/utils.py`, 주요 스크립트들, mypy 설정)
- [x] 프로세스 중복 실행 방지 시스템 구현 (모든 모드에 적용)
- [ ] 단위 테스트 추가 (pytest)
- [ ] 코드 리팩토링 (중복 코드 제거)

### 기능 개선
- [x] **두뇌훈련 영상 생성 로직 수정 (긴급)** ✅ 2025-11-23 완료
  - [x] 틀린그림 찾기: 같은 그림에서 물건을 제거한 새 이미지 생성 (DALL-E 사용)
  - [x] 다국어 옵션: 한글 전용 또는 영어 전용으로 선택 가능하도록 수정
  - [x] 문제 반복 문제 수정 (시계, 패턴 문제 다양성 확보)
  - [x] 한글/영어 다국어 지원 구현
  - [x] `missing_object` 모듈: 두 이미지를 좌우로 배치한 비교 이미지 생성 ✅
  - [x] `pattern_sequence` 모듈: 패턴 표시 로직 추가 ✅
  - [x] `word_association` 모듈: 단어 연상 문제 표시 로직 추가 ✅
  - [x] `clock_reading` 모듈: 시계 이미지 생성 로직 추가 ✅
  - [x] `korean_word_puzzle` 모듈: 한글 퍼즐 표시 로직 추가 ✅
  - [x] 모든 모듈에서 문제가 제대로 표시되는지 테스트 ✅ (한글 테스트 영상 생성 완료)
  - [x] 틀린그림 찾기 기능 비활성화 (구현이 어려워 사용하지 않음) ✅ 2025-11-23
  - [x] 두뇌훈련 모듈 확장 (5개 추가) ✅ 2025-11-23
    - [x] color_memory (색상 기억) - 1순위
    - [x] simple_calculation (간단한 계산) - 1순위
    - [x] direction_memory (방향 기억) - 1순위
    - [x] category_classification (카테고리 분류) - 2순위
    - [x] shape_matching (도형 매칭) - 2순위
  - [x] spot_difference 모드 제거 (구현이 어려워 제거) ✅ 2025-11-24
- [ ] BGM: 다양한 장르 프리셋 추가 (jazz, piano, world 등)
- [ ] BGM: 앞으로 mode와 preset을 다양하게 추가하는 목표
- [ ] 영상 메타데이터 최적화 (SEO 개선)
- [ ] 기존 크리스마스 음악 파일 장르별 폴더 정리 실행
- [ ] 다양한 장르 음악 다운로드 테스트
- [ ] 새로운 롱폼 콘텐츠 모드 추가 (예: 명상, 학습, 수면 스토리 등)
- [ ] 🔥 AI 음성합성 기반 "할아버지 목소리 옛날이야기" 콘텐츠
  - [ ] 할아버지 목소리 TTS 음성합성 구현
  - [ ] 지혜로운 옛날이야기 스토리 생성 (GPT API)
  - [ ] ASMR 분위기 배경음악 및 효과음 추가
  - [ ] YouTube 롱폼 영상 자동 생성 및 업로드

### 시스템 개선
- [ ] SORA를 통한 배경 이미지 생성 (테스트 필요)
- [ ] 음악 다운로드 자동화 개선
- [ ] 영상 품질 최적화 (해상도, 비트레이트)
- [ ] 자동 업로드 스케줄링 개선
- [ ] YouTube API 쿼터 관리 및 재시도 로직
- [ ] 썸네일 생성 자동화 (여러 버전 생성 후 최적 선택)
- [ ] 영상 생성 진행률 표시 (프로그레스 바)
- [ ] 배치 처리 최적화 (병렬 처리)

### 인프라 및 운영
- [ ] 환경별 설정 분리 (dev/prod)
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인 구축
- [ ] 모니터링 및 알림 시스템 추가
- [ ] 백업 및 복구 전략 수립
- [ ] 로그 분석 및 대시보드 구축

### 문서화
- [ ] API 문서화 (각 스크립트의 함수별 docstring 보완)
- [ ] 사용자 가이드 보완
- [ ] 개발자 온보딩 문서 작성
- [ ] 트러블슈팅 가이드 추가

## 📚 참고 문서

- `TODO_2025_STRATEGY.md`: 전체 로드맵 및 Phase 1-7 계획
- `docs/API_INTEGRATION_STRATEGY.md`: API 통합 전략 및 비용 절감 계획
- `HISTORY.md`: 프로젝트 히스토리 및 API 설정 가이드
- `implementation_plan.md`: 상세 구현 계획

## ✅ 최근 완료된 작업 (2025-11)

### 두뇌훈련 시계 및 색상 개선 (2025-11-25)
- [x] 시계 읽기 문제: 시계가 항상 12시가 위에 오도록 각도 계산 수정
- [x] 색상 기억 문제: 색상 구분을 명확하게 하기 위해 더 밝고 선명한 색상 사용
- [x] 색상 박스 테두리를 더 두껍게 하여 구분 명확히

### 썸네일 자동 생성 기능 추가 (2025-11-24)
- [x] DALL-E 3를 사용한 썸네일 생성 스크립트 추가 (`scripts/create_thumbnail_dalle.py`)
- [x] YouTube 썸네일 업로드 스크립트 추가 (`scripts/upload_thumbnail.py`)
- [x] 모든 모드(brain_training, longform_bgm, ai_explainer)에 자동 썸네일 생성 로직 추가
- [x] 썸네일 경로를 메타데이터에 자동 포함

### 두뇌훈련 영상 다국어 지원 개선 (2025-11-24)
- [x] 영어 버전에서 한글 텍스트 제거 및 폰트 깨짐 문제 해결
- [x] 모든 이미지 생성 함수에 languages 파라미터 추가
- [x] 영어 버전일 때 영어 폰트(Helvetica) 사용, 한글 폰트(AppleSDGothicNeo)는 한글 버전에서만 사용
- [x] korean_word_puzzle 모듈을 영어 버전에서 자동 제외
- [x] word_association, pattern_sequence, category_classification 모듈이 영어로 생성되도록 수정
- [x] 언어별 파일명 구분 (_ko_, _en_ 식별자 추가)
- [x] 메타데이터, 제목, 설명, 태그 파일도 언어별로 구분

### spot_difference 모드 제거 (2025-11-24)
- [x] main.py에서 spot_difference 모드 제거
- [x] README.md에서 spot_difference 관련 내용 제거

## ✅ 이전 완료된 작업 (2025-11)

- [x] 이중언어 메타데이터 시스템 구현 (한글/영어 자동 생성)
- [x] generate_image.py APIManager 통합 (DALL-E 우선, 무료 API 폴백)
- [x] AI Explainer 콘텐츠 필러 추가 (Claude 3.5 Sonnet 사용)
- [x] 스케줄링 & 자동화 시스템 (요일별 필러 로테이션)
- [x] main.py에 --mode auto 옵션 추가
- [x] 문서 업데이트 (README.md, TODO.md)
- [x] 코드 품질 개선: 공통 유틸리티 모듈화 (`scripts/utils.py`)
- [x] 로깅 설정 중복 제거 (모든 스크립트가 `setup_logging()` 사용)
- [x] 에러 처리 표준화 및 재시도 로직 추가 (`retry_with_backoff` 데코레이터)
- [x] API Provider에 재시도 로직 적용 (OpenAI, Claude, Image Provider)
- [x] 타입 힌팅 전면 적용 (`scripts/utils.py`, 주요 스크립트들)
- [x] mypy 정적 타입 체크 설정 (`mypy.ini`)

## 🎯 다음 작업 (우선순위)

### 두뇌훈련 영상 개선
- [x] 이미지 다운로드 타임아웃 에러 해결 (재시도 로직 추가) ✅ 2025-11-24
- [x] 영어 테스트 영상 생성 ✅ 2025-11-24
- [x] 15분 영상 테스트 생성 (10개 모듈 활용) ✅ 2025-11-24
- [x] 30-45분 두뇌훈련 영상 생성 (한글/영어 각각) ✅ 2025-11-24
  - [x] 프리셋 생성 (`brain_training_30min_korean`, `brain_training_30min_english`)
  - [x] 영상 생성 (45개 문제, 약 30-45분)
  - [x] 메타데이터 생성 (정확한 영상 길이 포함)
  - [x] 썸네일 생성 (DALL-E 사용)
  - [x] BGM 자동 포함 (public_domain 폴더에서 랜덤 선택, 루프 반복)
- [ ] 영상 품질 검증 및 개선

### 기능 추가
- [ ] 3순위 모듈 추가 (word_order, date_memory, find_difference_text 등)
- [ ] 모듈별 난이도 조절 기능
- [ ] 문제 생성 다양성 개선 (더 많은 변형)

---
**마지막 업데이트**: 2025-11-24 (30-45분 두뇌훈련 영상 생성 완료, BGM 루프 반복 기능 추가)
