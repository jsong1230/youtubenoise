"""
YouTube OAuth 토큰 갱신 스크립트
새로운 리프레시 토큰을 받기 위한 OAuth 플로우 실행
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# 프로젝트 루트
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# YouTube API 스코프
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    """OAuth 플로우를 실행하여 새로운 토큰 받기"""
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ YOUTUBE_CLIENT_ID와 YOUTUBE_CLIENT_SECRET이 .env 파일에 설정되어 있어야 합니다.")
        sys.exit(1)
    
    # OAuth 클라이언트 정보 구성
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    # 임시 파일에 클라이언트 정보 저장
    temp_config_file = project_root / "config" / "temp_client_secret.json"
    temp_config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_config_file, 'w') as f:
        json.dump(client_config, f)
    
    try:
        print("🌐 브라우저가 열립니다. Google 계정으로 로그인하고 권한을 승인해주세요...")
        
        flow = InstalledAppFlow.from_client_secrets_file(
            str(temp_config_file), SCOPES
        )
        creds = flow.run_local_server(port=0)
        
        # 새로운 리프레시 토큰 출력
        print("\n✅ 인증 성공!")
        print("\n=== 새로운 리프레시 토큰 ===")
        print(creds.refresh_token)
        print("\n이 토큰을 .env 파일의 YOUTUBE_REFRESH_TOKEN에 업데이트해주세요.")
        
        # 토큰 정보 저장 (선택사항)
        token_file = project_root / "config" / "token.json"
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
        print(f"\n토큰이 {token_file}에 저장되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)
    finally:
        # 임시 파일 삭제
        if temp_config_file.exists():
            temp_config_file.unlink()

if __name__ == "__main__":
    main()

