#!/usr/bin/env python3
"""
간단한 Public Domain 음악 다운로드 스크립트
실제 다운로드 가능한 링크를 사용
"""
import sys
import requests
from pathlib import Path

def download_music(url: str, output_path: Path):
    """음악 다운로드"""
    print(f"다운로드 중: {url}")
    print(f"저장 위치: {output_path}")
    
    try:
        response = requests.get(url, stream=True, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) == 0:
                            print(f"진행률: {progress:.1f}%")
        
        size_mb = downloaded / 1024 / 1024
        print(f"✅ 다운로드 완료: {output_path} ({size_mb:.2f} MB)")
        return True
        
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        if output_path.exists():
            output_path.unlink()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python download_music_simple.py <URL> [출력파일명]")
        print("\n예시:")
        print("python download_music_simple.py https://example.com/music.mp3 christmas_cafe.mp3")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else "downloaded_music.mp3"
    output_path = Path("audio/public_domain") / filename
    
    download_music(url, output_path)

