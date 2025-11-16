# YouTube 영상 통계 관리 가이드

## 개요

업로드된 영상의 조회수, 좋아요, 댓글 수 등을 자동으로 업데이트하고 리포트를 생성할 수 있습니다.

## 사용 방법

### YouTube 채널 동기화

```bash
python main.py --sync-youtube
```

YouTube 채널에서 최근 업로드된 영상 목록을 가져와서 히스토리에 자동으로 추가합니다.

**참고**: YouTube API 스코프가 `youtube.readonly`를 포함해야 합니다. 스코프가 없으면 수동 추가를 사용하세요.

### Video ID 수동 추가

YouTube 채널에서 Video ID를 확인한 후 수동으로 추가할 수 있습니다:

```bash
python scripts/add_video_to_history.py <video_id> [제목] [업로드시간]
```

예시:
```bash
python scripts/add_video_to_history.py abc123xyz 'Christmas Cafe BGM - 5분' '2025-11-16T23:55:00'
```

### 통계 업데이트

```bash
python main.py --update-stats
```

모든 업로드된 영상의 통계를 YouTube API에서 가져와서 `logs/history.json`에 저장합니다.

### 리포트 출력

```bash
python main.py --report
```

현재 저장된 통계를 기반으로 리포트를 출력합니다.

## API 키 설정

통계 업데이트를 위해서는 **YouTube Data API v3 Public API 키**가 필요합니다.

### API 키 발급 방법

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택
3. "API 및 서비스" > "사용자 인증 정보" 이동
4. "API 키 만들기" 클릭
5. 생성된 API 키 복사
6. `.env` 파일에 추가:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```

**참고**: Public API 키는 공개 영상의 통계를 읽을 수 있으며, OAuth 스코프가 필요 없습니다.

### YouTube Analytics API (선택사항)

더 상세한 통계를 원한다면 YouTube Analytics API를 활성화할 수 있습니다:

1. Google Cloud Console에서 "YouTube Analytics API" 활성화
2. OAuth 동의 화면에서 다음 스코프 추가:
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
3. Refresh Token 재발급

**중요**: 
- 스코프는 "승인된 리디렉션 URI"가 아닌 "OAuth 동의 화면" 또는 "승인된 스코프" 섹션에서 설정해야 합니다
- 리디렉션 URI는 `http://localhost:8080/` 같은 실제 URL이어야 합니다

**참고**: Analytics API는 채널 소유자만 자신의 채널 통계를 볼 수 있습니다.

### YouTube Reporting API (선택사항)

가장 상세한 리포트 데이터를 원한다면 YouTube Reporting API를 활성화할 수 있습니다:

1. Google Cloud Console에서 "YouTube Reporting API" 활성화
2. OAuth 클라이언트 ID에 다음 스코프 추가:
   - `https://www.googleapis.com/auth/yt-analytics.readonly` (Analytics API와 동일)
3. Refresh Token 재발급

**참고**: 
- Reporting API는 Analytics API와 동일한 스코프를 사용합니다
- Reporting API는 리포트 작업(jobs)을 생성하고 다운로드하는 방식으로 작동합니다
- 채널 소유자만 자신의 채널 리포트를 볼 수 있습니다
- 일반적인 통계 조회에는 Analytics API가 더 간단합니다

### 스코프 방식 (선택사항)

OAuth를 사용하여 통계를 읽으려면 `youtube.readonly` 스코프가 필요합니다:

1. Google Cloud Console에서 OAuth 클라이언트 ID 편집
2. 스코프에 다음 추가:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube.readonly`
3. Refresh Token 재발급

**권장**: Public API 키 방식을 사용하는 것이 더 간단합니다.

## 리포트 예시

```
================================================================================
YouTube 영상 통계 리포트
================================================================================
생성 시간: 2025-11-17 00:34:51

전체 통계:
  총 영상 수: 5개
  총 조회수: 1,234,567회
  총 좋아요: 12,345개
  총 댓글: 123개
  평균 조회수: 246,913회/영상
  평균 좋아요: 2,469개/영상

--------------------------------------------------------------------------------
영상별 상세 통계:
--------------------------------------------------------------------------------

1. Christmas Cafe BGM - 3시간 Long Form BGM
   Video ID: 8Q99UdhWqCA
   URL: https://www.youtube.com/watch?v=8Q99UdhWqCA
   조회수: 500,000회
   좋아요: 5,000개
   댓글: 50개
   ...
```

## 자동화

cron으로 주기적으로 통계를 업데이트할 수 있습니다:

```bash
# 매일 오전 3시에 통계 업데이트
0 3 * * * cd /path/to/youtubenoise && /path/to/venv/bin/python main.py --update-stats >> logs/stats.log 2>&1
```

