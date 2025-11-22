# API 통합 전략 문서

이 문서는 YouTube 롱폼 자동화 프로젝트에서 사용 가능한 모든 API를 정의하고, 각 API의 용도와 우선순위를 명시합니다.

---

## 🔑 사용 가능한 API 목록

### AI/LLM APIs

#### 1. OpenAI API
- **환경 변수**: `OPENAI_API_KEY`
- **용도**:
  - GPT-4o/GPT-4o-mini: 스크립트 생성, 메타데이터 생성, 문제 생성
  - DALL-E 3: 이미지 생성 (틀린그림찾기, 썸네일, 배경)
  - Whisper: 음성 인식 (향후 사용 가능)
- **비용**: 중간 (이미지 생성이 가장 비쌈)
- **우선순위**: **높음** (현재 주력 사용 중)

#### 2. Claude API (Anthropic)
- **환경 변수**: `ANTHROPIC_API_KEY` 또는 `CLAUDE_API_KEY`
- **용도**:
  - Claude 3.5 Sonnet: 긴 스크립트 생성, 복잡한 분석
  - Claude 3 Haiku: 빠른 메타데이터 생성, 간단한 작업
- **비용**: 낮음~중간 (GPT-4 대비 저렴)
- **우선순위**: **높음** (GPT와 병행 사용)
- **전략**:
  - 긴 콘텐츠(AI Explainer, 스토리): Claude 3.5 Sonnet
  - 짧은 메타데이터: Claude 3 Haiku
  - GPT API 할당량 초과 시 백업으로 사용

### 이미지 APIs

#### 3. DALL-E 3 (OpenAI)
- **환경 변수**: `OPENAI_API_KEY` (동일)
- **용도**: 고품질 커스텀 이미지 생성
- **비용**: 높음 ($0.04/image for 1024x1024)
- **우선순위**: **중간** (특별한 이미지가 필요할 때만)

#### 4. Unsplash API
- **환경 변수**: `UNSPLASH_ACCESS_KEY`
- **용도**: 무료 고품질 배경 이미지 다운로드
- **비용**: 무료 (50 requests/hour)
- **우선순위**: **높음** (배경 이미지 우선 사용)

#### 5. Pexels API
- **환경 변수**: `PEXELS_API_KEY`
- **용도**: 무료 고품질 배경 이미지/영상 다운로드
- **비용**: 무료 (200 requests/hour)
- **우선순위**: **높음** (Unsplash 대체/보완)

#### 6. Pixabay API
- **환경 변수**: `PIXABAY_API_KEY`
- **용도**: 무료 이미지/영상/음악 다운로드
- **비용**: 무료 (5,000 requests/day)
- **우선순위**: **중간** (음악 다운로드에 주로 사용)

### YouTube APIs

#### 7. YouTube Data API v3
- **환경 변수**: `YOUTUBE_API_KEY`
- **용도**: 영상 업로드, 채널 정보, 통계 조회
- **비용**: 무료 (10,000 quota/day)
- **우선순위**: **필수**

#### 8. YouTube Analytics API
- **환경 변수**: OAuth 토큰 사용
- **용도**: 상세 분석 데이터 (조회수, 수익, 시청 시간)
- **비용**: 무료
- **우선순위**: **높음** (수익 모니터링)

---

## 🎯 API 사용 전략

### 이미지 생성 우선순위

1. **배경 이미지 (BGM, 일반 콘텐츠)**:
   ```
   Unsplash → Pexels → Pixabay → DALL-E 3 (최후)
   ```
   - 무료 API를 우선 사용하여 비용 절감
   - 적합한 이미지가 없을 때만 DALL-E 3 사용

2. **커스텀 이미지 (틀린그림찾기, 특별한 테마)**:
   ```
   DALL-E 3 (우선) → Pexels/Unsplash (대체)
   ```
   - 정확한 요구사항이 있을 때는 DALL-E 3 직접 사용

### AI 텍스트 생성 우선순위

1. **긴 스크립트 (AI Explainer, 스토리)**:
   ```
   Claude 3.5 Sonnet (우선) → GPT-4o (대체)
   ```
   - Claude가 더 저렴하고 긴 컨텍스트 처리에 강함

2. **짧은 메타데이터 (제목, 설명, 태그)**:
   ```
   Claude 3 Haiku (우선) → GPT-4o-mini (대체)
   ```
   - 빠르고 저렴한 모델 우선 사용

3. **복잡한 분석 (문제 생성, 이미지 분석)**:
   ```
   GPT-4o (우선) → Claude 3.5 Sonnet (대체)
   ```
   - GPT-4o가 이미지 분석에 더 강함

### API 할당량 관리

- **일일 한도 추적**: `data/api_usage.json`에 기록
- **자동 전환**: 할당량 초과 시 대체 API로 자동 전환
- **비용 모니터링**: 월별 API 비용 추적

---

## 🛠️ 구현 계획

### 1. API Manager 클래스 생성
```python
# src/api/api_manager.py

class APIManager:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.usage_tracker = UsageTracker()
    
    def generate_text(self, prompt, length="short", priority="cost"):
        """
        텍스트 생성 (자동으로 최적 API 선택)
        
        Args:
            prompt: 프롬프트
            length: "short" | "medium" | "long"
            priority: "cost" | "quality" | "speed"
        """
        if length == "long" and priority == "cost":
            return self._claude_generate(prompt, model="claude-3-5-sonnet")
        elif length == "short" and priority == "speed":
            return self._claude_generate(prompt, model="claude-3-haiku")
        else:
            return self._gpt_generate(prompt, model="gpt-4o-mini")
    
    def generate_image(self, prompt, use_dalle=False):
        """
        이미지 생성 (무료 API 우선, 필요시 DALL-E)
        
        Args:
            prompt: 이미지 검색어 또는 생성 프롬프트
            use_dalle: True면 DALL-E 강제 사용
        """
        if use_dalle:
            return self._dalle_generate(prompt)
        
        # 무료 API 시도
        image = self._try_unsplash(prompt)
        if image:
            return image
        
        image = self._try_pexels(prompt)
        if image:
            return image
        
        # 최후의 수단: DALL-E
        return self._dalle_generate(prompt)
```

### 2. 사용량 추적 시스템
```python
# src/api/usage_tracker.py

class UsageTracker:
    def __init__(self):
        self.usage_file = Path("data/api_usage.json")
        self.load_usage()
    
    def track_request(self, api_name, cost=0):
        """API 요청 추적"""
        today = datetime.now().date().isoformat()
        if today not in self.usage:
            self.usage[today] = {}
        
        if api_name not in self.usage[today]:
            self.usage[today][api_name] = {"count": 0, "cost": 0}
        
        self.usage[today][api_name]["count"] += 1
        self.usage[today][api_name]["cost"] += cost
        self.save_usage()
    
    def get_daily_cost(self):
        """오늘의 총 비용"""
        today = datetime.now().date().isoformat()
        if today not in self.usage:
            return 0
        return sum(api["cost"] for api in self.usage[today].values())
```

### 3. 스크립트 업데이트

#### `scripts/generate_title_description.py` 업데이트
```python
from src.api.api_manager import APIManager

api_manager = APIManager()

def generate_metadata_for_bgm(preset_name, duration_minutes, language="ko"):
    prompt = f"Generate YouTube metadata for {preset_name} BGM ({duration_minutes} min)"
    
    # Claude Haiku로 빠르고 저렴하게 생성
    metadata = api_manager.generate_text(
        prompt, 
        length="short", 
        priority="cost"
    )
    return metadata
```

#### `scripts/generate_image.py` 업데이트
```python
from src.api.api_manager import APIManager

api_manager = APIManager()

def generate_background_image_for_bgm(preset_name):
    # 무료 API 우선 시도
    image = api_manager.generate_image(
        prompt=f"{preset_name} background calm aesthetic",
        use_dalle=False  # 무료 API 우선
    )
    return image

def generate_spot_difference_image(theme):
    # 틀린그림찾기는 정확성이 중요하므로 DALL-E 사용
    image = api_manager.generate_image(
        prompt=f"spot the difference game, {theme}, detailed illustration",
        use_dalle=True  # DALL-E 강제 사용
    )
    return image
```

---

## 📊 예상 비용 절감

### 현재 (GPT + DALL-E만 사용)
- 영상 1개당:
  - 메타데이터 생성 (GPT-4o-mini): $0.01
  - 이미지 생성 (DALL-E 3): $0.04
  - **총**: $0.05/영상

### 개선 후 (Claude + 무료 이미지 API 활용)
- 영상 1개당:
  - 메타데이터 생성 (Claude Haiku): $0.002
  - 이미지 다운로드 (Unsplash/Pexels): $0.00
  - **총**: $0.002/영상 (96% 절감!)

### 월간 비용 (일 1개 영상 기준)
- 현재: $1.50/월
- 개선 후: $0.06/월
- **절감액**: $1.44/월 (96%)

---

**마지막 업데이트**: 2025-11-22  
**다음 리뷰**: Phase 1 완료 후
