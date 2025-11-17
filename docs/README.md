# 문서 목록

## 주요 가이드

- **[MUSIC_GUIDE.md](MUSIC_GUIDE.md)**: Public Domain 음악 사용 가이드
- **[IMAGE_DOWNLOAD.md](IMAGE_DOWNLOAD.md)**: 무료 이미지 다운로드 가이드
- **[STATISTICS.md](STATISTICS.md)**: YouTube 영상 통계 관리 가이드
- **[MUSIC_SOURCES.md](MUSIC_SOURCES.md)**: 음악 소스 상세 정보
- **[MULTIPLE_MUSIC_FILES.md](MULTIPLE_MUSIC_FILES.md)**: 여러 음악 파일 조합 가이드
- **[PIXABAY_DOWNLOAD.md](PIXABAY_DOWNLOAD.md)**: Pixabay 음악 다운로드 가이드

## 빠른 참조

### Public Domain 음악 다운로드

1. **FreePD**: https://freepd.com/christmas.php
2. **Pixabay**: https://pixabay.com/music/search/christmas/
3. **Musopen**: https://musopen.org/music/?q=christmas&license=pd

### 사용 방법

```bash
# 음악 다운로드 후
mv ~/Downloads/*.mp3 audio/public_domain/christmas_cafe.mp3

# BGM 생성 (이미지도 자동으로 다운로드 시도)
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

