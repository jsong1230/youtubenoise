# Public Domain/무료 음악 소스 가이드

## 지원하는 세 가지 소스

### 1. FreePD (완전 Public Domain)
- **URL**: https://freepd.com/
- **특징**: 모든 음악이 완전 Public Domain
- **크리스마스 음악**: https://freepd.com/christmas.php
- **다운로드 방법**:
  1. 브라우저에서 방문
  2. 원하는 크리스마스 음악 클릭
  3. 다운로드
  4. `audio/public_domain/christmas_cafe.mp3`로 저장

### 2. Pixabay Music (상업용 완전 무료)
- **URL**: https://pixabay.com/music/
- **특징**: 상업용으로도 완전 무료 사용 가능
- **크리스마스 음악**: https://pixabay.com/music/search/christmas/
- **다운로드 방법**:
  1. 브라우저에서 방문
  2. 원하는 크리스마스 음악 선택
  3. "Download" 클릭
  4. `audio/public_domain/christmas_cafe.mp3`로 저장
### 3. Musopen (Public Domain 녹음만)
- **URL**: https://musopen.org/
- **특징**: Public Domain 녹음만 선택 가능
- **크리스마스 음악**: https://musopen.org/music/?q=christmas&license=pd
- **다운로드 방법**:
  1. 브라우저에서 방문
  2. "Public Domain" 필터 선택
  3. 원하는 크리스마스 음악 다운로드
  4. `audio/public_domain/christmas_cafe.mp3`로 저장

## 자동 다운로드 시도 순서

BGM 생성 시 다음 순서로 자동 다운로드를 시도합니다:

1. **FreePD** (완전 PD) - 우선순위 1
2. **Pixabay Music** (상업용 무료) - 우선순위 2
3. **Musopen** (PD 녹음) - 우선순위 3

모든 자동 다운로드가 실패하면 알고리즘 생성으로 대체됩니다.

## 수동 다운로드 (권장)

자동 다운로드는 웹 스크래핑 제한으로 실패할 수 있습니다. 
**가장 확실한 방법은 브라우저에서 직접 다운로드하는 것입니다:**

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

## 파일 위치

다운로드한 음악 파일은 다음 위치에 저장하세요:

```
audio/public_domain/
  └── christmas_cafe.mp3  # 크리스마스 카페 BGM
```

파일이 있으면 자동으로 사용되고, 없으면 알고리즘 생성으로 대체됩니다.

