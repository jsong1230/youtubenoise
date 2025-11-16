# Public Domain 음악 사용 가이드

## 개요

롱폼 BGM 모드에서는 Public Domain 또는 CC0 라이선스 음악을 사용할 수 있습니다. 
`audio/public_domain/` 폴더에 음악 파일을 저장하면 자동으로 사용됩니다.

## 추천 음악 소스

### 1. FreePD (완전 Public Domain)

- **URL**: https://freepd.com/
- **특징**: 모든 음악이 완전 Public Domain
- **크리스마스 음악**: https://freepd.com/christmas.php
- **다운로드 방법**: 브라우저에서 직접 다운로드

### 2. Pixabay Music (상업용 완전 무료)

- **URL**: https://pixabay.com/music/
- **특징**: 상업용으로도 완전 무료 사용 가능
- **크리스마스 음악**: https://pixabay.com/music/search/christmas/
- **API 키**: 선택사항 (https://pixabay.com/api/docs/)
  - `.env` 파일에 `PIXABAY_API_KEY=your_key` 추가

### 3. Musopen (Public Domain 녹음만)

- **URL**: https://musopen.org/
- **특징**: Public Domain 녹음만 선택 가능
- **크리스마스 음악**: https://musopen.org/music/?q=christmas&license=pd
- **다운로드 방법**: 브라우저에서 "Public Domain" 필터 선택

## 사용 방법

### 방법 1: 수동 다운로드 (권장)

```bash
# 1. 브라우저에서 다음 중 하나 방문:
#    - https://freepd.com/christmas.php
#    - https://pixabay.com/music/search/christmas/
#    - https://musopen.org/music/?q=christmas&license=pd

# 2. 원하는 크리스마스 음악 다운로드

# 3. 다운로드한 파일을 다음 위치로 이동:
mv ~/Downloads/*.mp3 audio/public_domain/christmas_cafe.mp3

# 4. BGM 생성 (자동으로 Public Domain 음악 사용됨!)
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

### 방법 2: 여러 파일 조합

여러 MP3 파일을 `audio/public_domain/` 폴더에 저장하면 자동으로 조합됩니다:

```bash
# 여러 파일을 폴더에 저장
cp ~/Downloads/*.mp3 audio/public_domain/

# BGM 생성 시 자동으로 모든 파일이 조합됨
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

### 방법 3: 단일 파일 사용

`config/bgm_presets.yaml`에서 설정:

```yaml
christmas_cafe_3h:
  combine_mode: "single"  # 여러 파일 중 하나만 랜덤 선택
```

## 자동 다운로드

자동 다운로드 기능도 제공되지만, 웹 스크래핑 제한으로 실패할 수 있습니다:

```bash
# 자동 다운로드 시도 (실패 시 알고리즘 생성으로 대체)
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

## 주의사항

⚠️ **저작권 확인 필수**
- 다운로드한 음악이 반드시 Public Domain 또는 CC0인지 확인
- 작곡 저작권뿐만 아니라 **녹음 저작권**도 확인
- YouTube 업로드 시 설명란에 라이선스 명시 권장

## 파일 위치

```
audio/public_domain/
  ├── christmas_cafe.mp3      # 크리스마스 카페 BGM
  ├── christmas_classical.mp3  # 크리스마스 클래식 BGM
  └── ...
```

파일이 있으면 자동으로 사용되고, 없으면 알고리즘 생성으로 대체됩니다.

