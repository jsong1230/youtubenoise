# Pixabay Music 다운로드 가이드

## 문제: Pixabay 봇 차단

Pixabay는 Cloudflare를 사용하여 자동화된 요청(봇)을 차단합니다. 
따라서 웹 스크래핑으로는 자동 다운로드가 어렵습니다.

## 해결 방법

### 방법 1: Pixabay API 사용 (권장)

1. **API 키 발급**
   - https://pixabay.com/api/docs/ 방문
   - 무료 계정 생성 후 API 키 발급

2. **API 키 설정**
   ```bash
   # .env 파일에 추가
   echo "PIXABAY_API_KEY=your_api_key_here" >> .env
   ```

3. **자동 다운로드**
   - API 키가 설정되면 자동으로 Pixabay에서 음악을 다운로드합니다.

### 방법 2: 수동 다운로드 (가장 확실)

1. **브라우저에서 방문**
   ```
   https://pixabay.com/music/search/christmas/
   ```

2. **원하는 크리스마스 음악 선택**
   - 상업용으로도 완전 무료 사용 가능

3. **다운로드**
   - "Download" 버튼 클릭

4. **파일 이동**
   ```bash
   mv ~/Downloads/*.mp3 audio/public_domain/christmas_cafe.mp3
   ```

5. **BGM 생성**
   ```bash
   python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
   ```

## 현재 상태

- ✅ **FreePD**: 자동 다운로드 시도 (웹 스크래핑 제한)
- ⚠️ **Pixabay**: Cloudflare 봇 차단 (API 키 필요 또는 수동 다운로드)
- ✅ **Musopen**: 자동 다운로드 시도 (웹 스크래핑 제한)

## 권장 사항

**가장 확실한 방법은 브라우저에서 직접 다운로드하는 것입니다.**

자동 다운로드는 웹 스크래핑 제한과 봇 차단으로 인해 실패할 수 있습니다.
수동 다운로드 후 `audio/public_domain/christmas_cafe.mp3`에 저장하면
자동으로 사용됩니다.

