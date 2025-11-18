# 장르별 음악 다운로드 가이드

## 개요

이 가이드는 다양한 장르의 Public Domain 음악을 다운로드하고 장르별로 분류하는 방법을 설명합니다.

## 빠른 시작

### 1. 기존 음악 파일 장르별 정리

기존에 `audio/public_domain/`에 평면적으로 저장된 음악 파일들을 장르별 폴더로 자동 정리:

```bash
# 시뮬레이션 (실제 이동하지 않음)
python scripts/organize_music_by_genre.py --dry-run

# 실제 정리
python scripts/organize_music_by_genre.py
```

### 2. Pixabay에서 장르별 음악 다운로드

```bash
# 재즈 음악 다운로드
python scripts/pixabay_genre_downloader.py --genre jazz

# 클래식 음악 다운로드 (최대 50개)
python scripts/pixabay_genre_downloader.py --genre classical --max-tracks 50

# 로파이 힙합 다운로드 (커스텀 검색어)
python scripts/pixabay_genre_downloader.py --genre lofi --search "lofi study"

# 헤드리스 모드 (브라우저 숨김)
python scripts/pixabay_genre_downloader.py --genre jazz --headless
```

## 지원하는 장르

- `classical`: 클래식 음악
- `jazz`: 재즈 음악
- `rock`: 록 음악
- `lofi`: 로파이 힙합
- `ambient`: 앰비언트 음악
- `piano`: 피아노 음악
- `electronic`: 일렉트로닉 음악
- `blues`: 블루스
- `folk`: 포크 음악
- `world`: 월드 뮤직

## 사용 예시

### 예시 1: 재즈 음악 대량 다운로드

```bash
# 재즈 음악을 최대 100개까지 다운로드
python scripts/pixabay_genre_downloader.py --genre jazz --max-tracks 100
```

다운로드된 파일은 `audio/public_domain/jazz/` 폴더에 저장됩니다.

### 예시 2: 클래식 음악 다운로드

```bash
# 클래식 음악 다운로드 (최대 3페이지)
python scripts/pixabay_genre_downloader.py --genre classical --max-pages 3
```

### 예시 3: 커스텀 검색어 사용

```bash
# "piano solo"로 검색하여 피아노 폴더에 저장
python scripts/pixabay_genre_downloader.py --genre piano --search "piano solo"
```

## 다운로드 후 작업

### 1. 카탈로그 새로고침

새로 다운로드한 음악을 카탈로그에 반영:

```bash
python scripts/public_domain_catalog.py --refresh --summary
```

### 2. 장르별 통계 확인

```bash
python scripts/public_domain_catalog.py --summary
```

출력 예시:
```
총 150개 트랙 분류됨
- jazz: 45곡
- classical: 30곡
- lofi: 25곡
- piano: 20곡
- ambient: 15곡
- christmas: 15곡
```

## BGM 생성 시 장르 필터링

`config/bgm_presets.yaml`에서 장르별 필터링 설정:

```yaml
jazz_cafe_3h:
  public_domain_categories:
    include: ["jazz", "lounge", "swing"]
    exclude: ["rock", "electronic"]

classical_study_3h:
  public_domain_categories:
    include: ["classical", "piano", "strings"]
    exclude: ["rock", "electronic"]
```

## 수동 다운로드 방법

자동 다운로드가 실패하거나 특정 곡을 선택하고 싶을 때:

1. **Pixabay Music** 방문: https://pixabay.com/music/
2. 원하는 장르 검색 (예: "jazz", "classical", "lofi")
3. 원하는 음악 다운로드
4. 적절한 폴더로 이동:

```bash
# 재즈 음악을 jazz 폴더로
mv ~/Downloads/jazz_track.mp3 audio/public_domain/jazz/

# 클래식 음악을 classical 폴더로
mv ~/Downloads/classical_track.mp3 audio/public_domain/classical/
```

## 다른 소스에서 다운로드

### FreePD (완전 Public Domain)

```bash
# 브라우저에서 다운로드 후
mv ~/Downloads/*.mp3 audio/public_domain/classical/
```

### Musopen (Public Domain 녹음)

```bash
# 브라우저에서 다운로드 후
mv ~/Downloads/*.mp3 audio/public_domain/classical/
```

자세한 소스 정보는 [PUBLIC_DOMAIN_GENRES.md](PUBLIC_DOMAIN_GENRES.md) 참고.

## 문제 해결

### 다운로드가 실패하는 경우

1. **네트워크 연결 확인**: 인터넷 연결 상태 확인
2. **헤드리스 모드 해제**: `--headless` 옵션 제거하여 브라우저 확인
3. **수동 다운로드**: 브라우저에서 직접 다운로드 후 폴더로 이동

### 장르 분류가 잘못된 경우

1. `organize_music_by_genre.py`의 `GENRE_FOLDERS` 딕셔너리 수정
2. 파일명에 장르 키워드 포함 (예: `jazz_track.mp3`)

### 카탈로그가 업데이트되지 않는 경우

```bash
# 강제 새로고침
python scripts/public_domain_catalog.py --refresh --summary
```

---

**마지막 업데이트**: 2025-11-17

