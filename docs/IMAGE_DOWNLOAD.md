# 무료 이미지 다운로드 가이드

## 개요

배경 이미지를 생성하기 전에 먼저 무료 이미지를 다운로드 시도합니다.
다운로드가 실패하면 자동으로 이미지를 생성합니다.

## 지원하는 이미지 소스

### 1. Unsplash (권장)
- **URL**: https://unsplash.com/
- **특징**: 모든 이미지가 무료로 사용 가능
- **API 키 발급**: https://unsplash.com/developers
- **무료**: 일일 50회 요청 제한

### 2. Pexels
- **URL**: https://www.pexels.com/
- **특징**: 모든 이미지가 무료로 사용 가능
- **API 키 발급**: https://www.pexels.com/api/
- **무료**: 월 200회 요청 제한

### 3. Pixabay
- **URL**: https://pixabay.com/
- **특징**: 모든 이미지가 무료로 사용 가능
- **API 키 발급**: https://pixabay.com/api/docs/
- **무료**: 시간당 5,000회 요청 제한

## API 키 설정

`.env` 파일에 다음 중 하나 이상을 추가하세요:

```bash
# Unsplash (권장)
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# Pexels
PEXELS_API_KEY=your_pexels_api_key

# Pixabay (음악 다운로드에도 사용 가능)
PIXABAY_API_KEY=your_pixabay_api_key
```

## 사용 방법

### 자동 사용 (권장)

BGM 생성 시 자동으로 이미지 다운로드를 시도합니다:

```bash
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

### 수동 다운로드

특정 프리셋의 이미지를 다운로드:

```bash
python scripts/download_public_domain_images.py --preset christmas_cafe_3h
```

특정 검색어로 이미지 다운로드:

```bash
python scripts/download_public_domain_images.py --query "christmas cafe cozy" --source unsplash
```

## 프리셋별 검색어

다음 프리셋들은 자동으로 적절한 검색어를 사용합니다:

- `christmas_cafe_3h`: "christmas cafe cozy warm"
- `christmas_classical_2h`: "christmas winter snow"
- `christmas_ambient_4h`: "christmas night stars"
- `cafe_jazz_2h`: "cozy cafe warm"
- `cafe_classical_3h`: "cozy cafe study"
- `classical_piano_2h`: "classical music elegant"

## 다운로드 순서

1. **Unsplash** 시도 (가장 높은 품질)
2. **Pexels** 시도 (Unsplash 실패 시)
3. **Pixabay** 시도 (Pexels 실패 시)
4. **이미지 생성** (모든 다운로드 실패 시)

## 저장 위치

다운로드된 이미지는 다음 위치에 저장됩니다:

```
images/downloaded/
  ├── unsplash_christmas_cafe_123456.jpg
  ├── pexels_cozy_cafe_789012.jpg
  └── pixabay_winter_snow_345678.jpg
```

## 주의사항

1. **API 키 필요**: 다운로드를 사용하려면 최소 하나의 API 키가 필요합니다.
2. **인터넷 연결**: 다운로드는 인터넷 연결이 필요합니다.
3. **저작권**: 모든 이미지는 무료로 사용 가능하지만, 각 서비스의 이용약관을 확인하세요.
4. **대체**: API 키가 없거나 다운로드가 실패하면 자동으로 이미지를 생성합니다.

## 문제 해결

### "API 키가 없습니다" 경고
- `.env` 파일에 API 키를 추가하세요.
- API 키 발급 방법은 각 서비스의 문서를 참조하세요.

### 다운로드 실패
- 인터넷 연결을 확인하세요.
- API 키가 올바른지 확인하세요.
- API 요청 제한을 확인하세요 (일일/월간 제한).
- 실패 시 자동으로 이미지 생성으로 대체됩니다.

### 이미지 품질
- 다운로드된 이미지는 1920x1080 해상도로 자동 리사이즈됩니다.
- JPEG 품질 95%로 저장됩니다.

