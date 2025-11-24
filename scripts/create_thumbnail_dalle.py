"""
DALL-E를 사용하여 두뇌훈련 영상 썸네일 생성
"""
import os
import sys
import logging
from pathlib import Path
from io import BytesIO

from dotenv import load_dotenv
import openai
from PIL import Image

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging

# 로깅 설정
logger = setup_logging()

# OpenAI API 설정
openai.api_key = os.getenv("OPENAI_API_KEY")


def create_thumbnail_with_dalle(title: str, language: str = "ko", output_path: Path = None) -> Path:
    """
    DALL-E를 사용하여 썸네일 이미지 생성
    
    Args:
        title: 영상 제목
        language: 언어 ('ko' 또는 'en')
        output_path: 출력 경로
    
    Returns:
        생성된 썸네일 이미지 경로
    """
    try:
        if language == "ko":
            prompt = f"""Create a professional YouTube thumbnail image for a brain training video for seniors.

Title: {title}

Requirements:
- Bright, warm, and friendly color scheme (pastel colors, soft tones)
- Large, clear text showing the title in Korean
- Images representing brain training activities (puzzles, memory games, numbers, colors)
- Senior-friendly design with high contrast
- Professional and engaging appearance
- YouTube thumbnail style (1280x720 aspect ratio)
- No text overlay needed, just visual elements that represent brain training

Style: Modern, clean, friendly, suitable for seniors aged 60-80"""
        else:
            prompt = f"""Create a professional YouTube thumbnail image for a brain training video for seniors.

Title: {title}

Requirements:
- Bright, warm, and friendly color scheme (pastel colors, soft tones)
- Large, clear text showing the title in English
- Images representing brain training activities (puzzles, memory games, numbers, colors)
- Senior-friendly design with high contrast
- Professional and engaging appearance
- YouTube thumbnail style (1280x720 aspect ratio)
- No text overlay needed, just visual elements that represent brain training

Style: Modern, clean, friendly, suitable for seniors aged 60-80"""
        
        logger.info(f"DALL-E로 썸네일 생성 중... (언어: {language})")
        logger.info(f"프롬프트: {prompt[:100]}...")
        
        # DALL-E 3로 이미지 생성
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",  # DALL-E 3는 1024x1024만 지원
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        logger.info(f"이미지 URL: {image_url}")
        
        # 이미지 다운로드
        import requests
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        
        # 이미지 열기 및 리사이즈 (YouTube 권장 크기: 1280x720)
        img = Image.open(BytesIO(img_response.content))
        img = img.convert("RGB")
        
        # 1280x720으로 리사이즈 (16:9 비율)
        thumbnail = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # 저장
        if output_path is None:
            output_path = project_root / "output" / "thumbnails" / f"thumbnail_{language}.jpg"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        thumbnail.save(str(output_path), "JPEG", quality=95, optimize=True)
        
        logger.info(f"썸네일 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        # 한글 버전 썸네일 생성
        logger.info("한글 버전 썸네일 생성 중...")
        ko_title = "치매 예방을 위한 두뇌 훈련 - 쉽고 재미있는 34문제"
        ko_thumbnail = create_thumbnail_with_dalle(
            ko_title,
            language="ko",
            output_path=project_root / "output" / "thumbnails" / "2025-11-24_mixed_brain_training_senior_ep01_thumbnail.jpg"
        )
        logger.info(f"한글 썸네일: {ko_thumbnail}")
        
        # 영어 버전 썸네일 생성
        logger.info("영어 버전 썸네일 생성 중...")
        en_title = "Brain Training for Seniors: Fun Activities to Prevent Dementia"
        en_thumbnail = create_thumbnail_with_dalle(
            en_title,
            language="en",
            output_path=project_root / "output" / "thumbnails" / "2025-11-24_mixed_brain_training_senior_en_ep01_thumbnail.jpg"
        )
        logger.info(f"영어 썸네일: {en_thumbnail}")
        
        print(f"\n썸네일 생성 완료!")
        print(f"한글 썸네일: {ko_thumbnail}")
        print(f"영어 썸네일: {en_thumbnail}")
        
        return ko_thumbnail, en_thumbnail
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

