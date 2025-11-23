# TODO 목록

> **참고**: 상세한 2025 전략 및 로드맵은 `TODO_2025_STRATEGY.md`를 참조하세요.

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
  - [ ] 틀린그림찾기: 다양한 테마 및 난이도 프리셋 추가 (비활성화됨)
  - [ ] 틀린그림찾기: TTS 내레이션 기능 추가 (선택사항) (비활성화됨)
- [ ] BGM: 다양한 장르 프리셋 추가 (jazz, piano, world 등)
- [ ] BGM: 앞으로 mode와 preset을 다양하게 추가하는 목표
- [ ] 영상 메타데이터 최적화 (SEO 개선)
- [ ] 기존 크리스마스 음악 파일 장르별 폴더 정리 실행
- [ ] 다양한 장르 음악 다운로드 테스트
- [ ] 새로운 롱폼 콘텐츠 모드 추가 (예: 명상, 학습, 수면 스토리 등)

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
- [ ] 이미지 다운로드 타임아웃 에러 해결 (재시도 로직 추가)
- [ ] 영어 테스트 영상 생성
- [ ] 영상 품질 검증 및 개선
- [ ] 15분 영상 테스트 생성 (10개 모듈 활용)

### 기능 추가
- [ ] 3순위 모듈 추가 (word_order, date_memory, find_difference_text 등)
- [ ] 모듈별 난이도 조절 기능
- [ ] 문제 생성 다양성 개선 (더 많은 변형)

---
**마지막 업데이트**: 2025-11-23 (두뇌훈련 모듈 5개 추가 완료)
