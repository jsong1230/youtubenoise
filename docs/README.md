# 문서 목록

## 주요 가이드

- **[MUSIC_GUIDE.md](MUSIC_GUIDE.md)**: Public Domain 음악 사용 가이드
- **[PUBLIC_DOMAIN_GENRES.md](PUBLIC_DOMAIN_GENRES.md)**: 장르별 Public Domain 음악 소스 가이드
- **[GENRE_DOWNLOAD_GUIDE.md](GENRE_DOWNLOAD_GUIDE.md)**: 장르별 음악 다운로드 사용 가이드
- **[IMAGE_DOWNLOAD.md](IMAGE_DOWNLOAD.md)**: 무료 이미지 다운로드 가이드
- **[STATISTICS.md](STATISTICS.md)**: YouTube 영상 통계 관리 가이드
- **[MUSIC_SOURCES.md](MUSIC_SOURCES.md)**: 음악 소스 상세 정보
- **[MULTIPLE_MUSIC_FILES.md](MULTIPLE_MUSIC_FILES.md)**: 여러 음악 파일 조합 가이드
- **[PIXABAY_DOWNLOAD.md](PIXABAY_DOWNLOAD.md)**: Pixabay 음악 다운로드 가이드

## 빠른 참조

### Public Domain 음악 다운로드

#### 장르별 자동 다운로드

```bash
# 재즈 음악 다운로드
python scripts/pixabay_genre_downloader.py --genre jazz

# 클래식 음악 다운로드 (최대 50개)
python scripts/pixabay_genre_downloader.py --genre classical --max-tracks 50

# 로파이 힙합 다운로드
python scripts/pixabay_genre_downloader.py --genre lofi
```

#### 기존 음악 파일 장르별 정리

```bash
# 시뮬레이션
python scripts/organize_music_by_genre.py --dry-run

# 실제 정리
python scripts/organize_music_by_genre.py
```

#### 수동 다운로드

1. **FreePD**: https://freepd.com/christmas.php
2. **Pixabay**: https://pixabay.com/music/search/christmas/
3. **Musopen**: https://musopen.org/music/?q=christmas&license=pd

자세한 내용은 [PUBLIC_DOMAIN_GENRES.md](PUBLIC_DOMAIN_GENRES.md) 참고

### 사용 방법

```bash
# 음악 다운로드 후 (장르별 폴더에 저장됨)
# 예: audio/public_domain/jazz/jazz_track.mp3

# BGM 생성 (자동으로 장르별 필터링)
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

### 무료 이미지 다운로드

API 키 설정 (`.env` 파일):
```bash
UNSPLASH_ACCESS_KEY=your_key  # https://unsplash.com/developers
PEXELS_API_KEY=your_key        # https://www.pexels.com/api/
PIXABAY_API_KEY=your_key       # https://pixabay.com/api/docs/
```

이미지 다운로드:
```bash
python scripts/download_public_domain_images.py --preset christmas_cafe_3h
```

