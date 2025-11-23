"""
두뇌훈련 영상용 썸네일 생성 (DALL-E 사용)
"""
import os
import sys
import base64
import io
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime

from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging
from config import OUTPUT_DIR

# 로깅 설정
logger = setup_logging()


def generate_thumbnail_with_dalle(
    title: str,
    language: str = "ko",
    output_path: Optional[Path] = None,
    width: int = 1280,
    height: int = 720
) -> Optional[Path]:
    """
    DALL-E를 사용하여 두뇌훈련 영상 썸네일 생성
    
    Args:
        title: 영상 제목
        language: 언어 ("ko" 또는 "en")
        output_path: 출력 경로 (None이면 자동 생성)
        width: 썸네일 너비 (기본값: 1280)
        height: 썸네일 높이 (기본값: 720)
    
    Returns:
        생성된 썸네일 파일 경로
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY가 설정되지 않아 썸네일 생성을 건너뜁니다.")
            return None
        
        client = OpenAI(api_key=api_key)
        
        # 언어에 따라 프롬프트 생성
        if language == "en":
            prompt = f"""Create a YouTube thumbnail image for a senior brain training video.
Title: {title}

Style requirements:
- Warm, friendly, and inviting colors (soft pastels, warm tones)
- Large, clear text that's easy to read
- Senior-friendly design with high contrast
- Include visual elements representing brain training: puzzle pieces, numbers, patterns, clocks, colorful shapes
- Clean, simple layout suitable for YouTube thumbnail
- Professional but approachable
- Bright and cheerful atmosphere
- No text overlay (image only, text will be added separately if needed)

Image should convey: mental exercise, memory training, cognitive health, fun and engaging activities for seniors."""
        else:
            prompt = f"""시니어용 두뇌훈련 YouTube 썸네일 이미지를 만들어주세요.
제목: {title}

스타일 요구사항:
- 따뜻하고 친근한 색상 (부드러운 파스텔 톤, 따뜻한 색조)
- 읽기 쉬운 크고 명확한 텍스트
- 높은 대비의 시니어 친화적 디자인
- 두뇌훈련을 나타내는 시각적 요소 포함: 퍼즐 조각, 숫자, 패턴, 시계, 다양한 색상의 도형
- YouTube 썸네일에 적합한 깔끔하고 단순한 레이아웃
- 전문적이지만 친근한 느낌
- 밝고 쾌활한 분위기
- 텍스트 오버레이 없음 (이미지만, 필요시 별도로 텍스트 추가 가능)

이미지는 다음을 전달해야 합니다: 정신 운동, 기억력 훈련, 인지 건강, 시니어를 위한 재미있고 매력적인 활동"""
        
        logger.info(f"DALL-E로 썸네일 생성 중... (언어: {language})")
        
        # DALL-E 3 사용 (고품질)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",  # DALL-E 3는 1024x1024만 지원
            quality="hd",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # 이미지 다운로드
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        
        # 이미지 열기 및 리사이즈
        img = Image.open(io.BytesIO(img_response.content))
        img = img.convert("RGB")
        
        # YouTube 썸네일 비율 (16:9)로 리사이즈 및 크롭
        img = resize_and_crop_to_thumbnail(img, width, height)
        
        # 출력 경로 설정
        if output_path is None:
            output_dir = OUTPUT_DIR / "videos" / "brain_training"
            output_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_path = output_dir / f"{date_str}_thumbnail_{language}.jpg"
        
        # JPEG로 저장 (YouTube 권장)
        img.save(str(output_path), "JPEG", quality=95, optimize=True)
        logger.info(f"썸네일 생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}", exc_info=True)
        return None


def resize_and_crop_to_thumbnail(
    img: Image.Image,
    target_width: int,
    target_height: int
) -> Image.Image:
    """
    이미지를 썸네일 크기로 리사이즈 및 크롭 (16:9 비율 유지)
    
    Args:
        img: 원본 이미지
        target_width: 목표 너비
        target_height: 목표 높이
    
    Returns:
        리사이즈된 이미지
    """
    target_aspect = target_width / target_height
    img_aspect = img.width / img.height
    
    if img_aspect > target_aspect:
        # 이미지가 더 넓음 - 높이에 맞춰서 크롭
        new_height = img.height
        new_width = int(new_height * target_aspect)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, new_height))
    else:
        # 이미지가 더 높음 - 너비에 맞춰서 크롭
        new_width = img.width
        new_height = int(new_width / target_aspect)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, new_width, top + new_height))
    
    # 최종 리사이즈
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    return img


if __name__ == "__main__":
    """테스트용"""
    if len(sys.argv) < 3:
        print("사용법: python generate_brain_training_thumbnail.py <title> <language> [output_path]")
        print("예시: python generate_brain_training_thumbnail.py '치매 예방 두뇌훈련' ko")
        sys.exit(1)
    
    title = sys.argv[1]
    language = sys.argv[2]
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    
    result = generate_thumbnail_with_dalle(title, language, output_path)
    if result:
        print(f"썸네일 생성 완료: {result}")
    else:
        print("썸네일 생성 실패")
        sys.exit(1)

