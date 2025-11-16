#!/bin/bash
# Public Domain 크리스마스 음악 자동 다운로드 스크립트

AUDIO_DIR="audio/public_domain"
mkdir -p "$AUDIO_DIR"

echo "=========================================="
echo "Public Domain 크리스마스 음악 다운로드"
echo "=========================================="
echo ""

# 방법 1: FreePD에서 직접 다운로드 시도
echo "FreePD에서 크리스마스 음악 다운로드 시도 중..."

# FreePD의 실제 크리스마스 음악 다운로드 (사이트 구조 확인 필요)
# curl -L -o "$AUDIO_DIR/christmas_cafe.mp3" "https://freepd.com/christmas/..."

# 방법 2: 잘 알려진 Public Domain 크리스마스 음악 다운로드
# OpenGameArt, Freesound 등에서 CC0 음악 다운로드

echo ""
echo "다음 사이트에서 Public Domain 크리스마스 음악을 다운로드하세요:"
echo ""
echo "1. FreePD: https://freepd.com/christmas.php"
echo "   - 브라우저에서 방문 후 원하는 음악 다운로드"
echo "   - 저장 위치: $AUDIO_DIR/christmas_cafe.mp3"
echo ""
echo "2. Freesound (CC0 필터): https://freesound.org/"
echo "   - 'christmas' 검색, 라이선스: CC0 선택"
echo ""
echo "3. Musopen: https://musopen.org/"
echo "   - 'Christmas' 검색, CC0 라이선스 선택"
echo ""

