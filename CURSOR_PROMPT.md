# Cursor 프롬프트

이 레포 구조에 맞춰서 구현해줘.

현재 프로젝트는 YouTube 노이즈/환경음/롱폼 BGM 영상 자동 생성 파이프라인입니다.
추가로 시니어용 틀린그림찾기 롱폼 영상 생성 기능도 포함합니다.

## 프로젝트 구조
- `scripts/`: 실행 스크립트들
  - `generate_audio.py`: 오디오 생성 (화이트노이즈, 브라운노이즈, 핑크노이즈, 빗소리, 파도, 벽난로 등)
  - `generate_bgm.py`: 롱폼 BGM 생성 (Public Domain 음악 조합 또는 알고리즘 생성)
  - `generate_image.py`: 배경 이미지 생성 (DALL·E, Public Domain 이미지, Pillow 그라데이션)
  - `generate_title_description.py`: YouTube 메타데이터 생성 (OpenAI API 사용)
  - `make_video.py`: FFmpeg로 영상 생성
  - `upload_youtube.py`: YouTube 업로드
  - `scheduler.py`: 전체 파이프라인 자동 실행
  - `public_domain_catalog.py`: Public Domain 음악 분류 및 카탈로그 관리
  - `generate_spot_difference.py`: 시니어용 틀린그림찾기 영상 생성 (메인 파이프라인)
  - `generate_spot_difference_image.py`: 틀린그림찾기용 이미지 생성 및 편집 (GPT API)
  - `generate_spot_difference_metadata.py`: 틀린그림찾기용 메타데이터 생성 (GPT API)
  - `make_spot_difference_video.py`: 틀린그림찾기 영상 합성
- `config/`: 설정 파일
  - `config.json`: 기본 설정
  - `bgm_presets.yaml`: BGM 프리셋 설정
  - `spot_difference_presets.yaml`: 틀린그림찾기 프리셋 설정
  - `.env`: 환경변수 (YouTube API, OpenAI API 키)

## 코드 스타일
- 모든 스크립트는 `project_root`를 기준으로 경로 처리
- `load_dotenv(project_root / ".env")`로 환경변수 로드
- `load_config()` 함수로 `config/config.json` 로드
- 로깅은 `logging` 모듈 사용, `logs/app.log`에 저장
- 함수는 독립적으로 실행 가능하도록 설계
- 에러 처리 및 로깅 포함
- 썸네일/배경 이미지는 16:9 비율(1920x1080)로 중앙 크롭 후 리사이즈

## 구현 시 참고사항
1. 기존 코드 패턴을 따라 구현
2. `project_root` 기준으로 경로 처리
3. 로깅 및 에러 처리 포함
4. 함수는 재사용 가능하도록 모듈화
5. 설정은 `config.json` 또는 YAML 파일 사용
6. 환경변수는 `.env` 파일 사용

