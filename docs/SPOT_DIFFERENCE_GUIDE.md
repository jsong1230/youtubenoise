# 시니어용 틀린그림찾기 롱폼 생성 가이드

## 개요

GPT API를 최대한 활용하여 시니어(60~80대) 친화적인 틀린그림찾기 롱폼 영상을 자동 생성합니다.

## 기능

- **GPT 이미지 생성**: DALL·E 3를 사용한 원본 이미지 생성
- **GPT 이미지 분석**: 차이점 자동 감지 및 좌표 추출
- **GPT 텍스트 생성**: 문제 안내, 정답 안내, 영상 메타데이터 자동 생성
- **자동 영상 합성**: 비교 화면, 카운트다운, 정답 화면을 자동으로 조합

## 사용법

### 기본 사용

```bash
# 쉬운 난이도 (3개 차이점, 15초 카운트다운, 15문제)
python main.py --mode spot_difference --preset senior_easy

# 보통 난이도 (5개 차이점, 10초 카운트다운, 20문제)
python main.py --mode spot_difference --preset senior_normal
```

### 스크립트 직접 실행

```bash
python scripts/generate_spot_difference.py senior_easy
```

## 프리셋 설정

`config/spot_difference_presets.yaml` 파일에서 프리셋을 수정하거나 추가할 수 있습니다.

### 주요 설정 항목

- `num_differences`: 차이점 개수 (3~5개)
- `countdown_seconds`: 카운트다운 시간 (10~15초)
- `num_problems`: 문제 개수 (10~20개)
- `themes`: 이미지 주제 리스트
- `color_scheme`: 색상 스킴 (배경, 텍스트, 하이라이트 등)
- `font_size`: 폰트 크기 (시니어 친화적 크기)

## 출력 파일

생성된 파일들은 `videos/spot_difference/` 폴더에 저장됩니다:

- `{date}_{preset}_ep01.mp4`: 최종 영상
- `{date}_{preset}_ep01_metadata.json`: 메타데이터 (제목, 설명, 챕터)
- `{date}_{preset}_ep01_title.txt`: 제목 텍스트
- `{date}_{preset}_ep01_description.txt`: 설명 텍스트

## 주의사항

- GPT API 사용량에 따라 비용이 발생할 수 있습니다
- 이미지 생성은 시간이 걸릴 수 있습니다 (문제당 약 1~2분)
- YouTube 업로드는 포함되지 않습니다 (로컬 파일만 생성)

