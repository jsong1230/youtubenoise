# Cursor 프롬프트

이 레포 구조에 맞춰서 구현해줘.

현재 프로젝트는 YouTube 노이즈/환경음 영상 자동 생성 파이프라인입니다.

## 프로젝트 구조
- `scripts/`: 실행 스크립트들
  - `generate_audio.py`: 오디오 생성 (화이트노이즈, 브라운노이즈, 핑크노이즈, 빗소리, 파도, 벽난로 등)
  - `generate_image.py`: 배경 이미지 생성 (Pillow 기반 그라데이션)
  - `generate_title_description.py`: YouTube 메타데이터 생성 (OpenAI API 사용)
  - `make_video.py`: FFmpeg로 영상 생성
  - `upload_youtube.py`: YouTube 업로드
  - `scheduler.py`: 전체 파이프라인 자동 실행
- `config/`: 설정 파일
  - `config.json`: 기본 설정
- `.env`: 환경변수 (YouTube API, OpenAI API 키)

## 코드 스타일
- 모든 스크립트는 `project_root`를 기준으로 경로 처리
- `load_dotenv(project_root / ".env")`로 환경변수 로드
- `load_config()` 함수로 `config/config.json` 로드
- 로깅은 `logging` 모듈 사용, `logs/app.log`에 저장
- 함수는 독립적으로 실행 가능하도록 설계
- 에러 처리 및 로깅 포함

## 구현 시 참고사항
1. 기존 코드 패턴을 따라 구현
2. `project_root` 기준으로 경로 처리
3. 로깅 및 에러 처리 포함
4. 함수는 재사용 가능하도록 모듈화
5. 설정은 `config.json` 또는 YAML 파일 사용
6. 환경변수는 `.env` 파일 사용

