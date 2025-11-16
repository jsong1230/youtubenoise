#!/bin/bash
# Public Domain 크리스마스 음악 자동 다운로드 스크립트

AUDIO_DIR="audio/public_domain"
mkdir -p "$AUDIO_DIR"

echo "=========================================="
echo "Public Domain 크리스마스 음악 다운로드"
echo "=========================================="
echo ""

# FreePD에서 크리스마스 음악 다운로드
echo "FreePD에서 크리스마스 음악 다운로드 중..."

# FreePD는 직접 다운로드가 어려우므로, curl을 사용하여 잘 알려진 Public Domain 음악 다운로드
# 실제로는 사용자가 직접 다운로드해야 함

# 대안: Kevin MacLeod의 Public Domain 크리스마스 음악 (Incompetech)
# 또는 다른 Public Domain 소스

echo ""
echo "다음 명령어로 수동 다운로드하세요:"
echo ""
echo "1. FreePD (https://freepd.com/):"
echo "   - 크리스마스 카테고리 방문"
echo "   - 원하는 음악 다운로드"
echo "   - 다음 위치에 저장: $AUDIO_DIR/christmas_cafe.mp3"
echo ""
echo "2. 또는 직접 URL에서 다운로드:"
echo "   python scripts/download_public_domain_music.py <URL> christmas_cafe.mp3"
echo ""

# 예시: 잘 알려진 Public Domain 크리스마스 음악 URL (실제 URL로 교체 필요)
# curl -L -o "$AUDIO_DIR/christmas_cafe.mp3" "https://example.com/public-domain-christmas.mp3"

echo "Public Domain 음악 디렉토리: $AUDIO_DIR"
ls -lh "$AUDIO_DIR" 2>/dev/null || echo "디렉토리가 비어있습니다."

