"""
다이어그램 이미지 생성 스크립트
DALL-E를 사용하여 개념 다이어그램 자동 생성
"""
import sys
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from io import BytesIO

from dotenv import load_dotenv
import openai
import requests
from PIL import Image

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import OUTPUT_DIR
from scripts.utils import setup_logging

# .env 파일 로드
load_dotenv(project_root / ".env")

# 로깅 설정
logger = setup_logging()

# OpenAI API 키 설정
import os
openai.api_key = os.getenv("OPENAI_API_KEY")


def create_diagram_image(
    concept: str,
    diagram_type: str = "flowchart",
    output_path: Optional[Path] = None,
    width: int = 1920,
    height: int = 1080,
    language: str = "ko"
) -> Path:
    """
    DALL-E를 사용하여 개념 다이어그램 이미지 생성
    
    Args:
        concept: 설명할 개념
        diagram_type: 다이어그램 타입 (flowchart, architecture, process, comparison 등)
        output_path: 출력 경로
        width: 이미지 너비
        height: 이미지 높이
        language: 언어 (ko, en)
    
    Returns:
        생성된 이미지 파일 경로
    """
    try:
        import os
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        # 다이어그램 타입별 프롬프트 생성
        diagram_prompts = {
            "flowchart": "flowchart diagram showing the process",
            "architecture": "system architecture diagram",
            "process": "process flow diagram",
            "comparison": "comparison diagram",
            "timeline": "timeline diagram",
            "hierarchy": "hierarchical diagram",
            "network": "network diagram"
        }
        
        diagram_desc = diagram_prompts.get(diagram_type, "diagram")
        
        if language == "ko":
            prompt = f"""Create a professional {diagram_desc} in Korean explaining: {concept}

Requirements:
- Clean, modern design with high contrast
- Korean text labels
- Professional color scheme (blue, green, or neutral tones)
- Clear visual hierarchy
- Suitable for educational YouTube video
- 16:9 aspect ratio (1920x1080)
- No decorative elements, focus on clarity"""
        else:
            prompt = f"""Create a professional {diagram_desc} in English explaining: {concept}

Requirements:
- Clean, modern design with high contrast
- English text labels
- Professional color scheme (blue, green, or neutral tones)
- Clear visual hierarchy
- Suitable for educational YouTube video
- 16:9 aspect ratio (1920x1080)
- No decorative elements, focus on clarity"""
        
        logger.info(f"DALL-E로 다이어그램 생성 중... (개념: {concept})")
        
        # DALL-E 3 호출
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        logger.info(f"이미지 URL: {image_url}")
        
        # 이미지 다운로드
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        
        img = Image.open(BytesIO(img_response.content))
        img = img.convert("RGB")
        
        # 1920x1080으로 리사이즈
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # 출력 경로 설정
        if output_path is None:
            output_dir = OUTPUT_DIR / "images" / "diagrams"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"diagram_{timestamp}.png"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path), "PNG", optimize=True)
        
        logger.info(f"다이어그램 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"다이어그램 생성 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="다이어그램 이미지 생성")
    parser.add_argument("--concept", type=str, required=True, help="설명할 개념")
    parser.add_argument("--type", type=str, default="flowchart",
                       choices=["flowchart", "architecture", "process", "comparison", "timeline", "hierarchy", "network"],
                       help="다이어그램 타입")
    parser.add_argument("--output", type=str, help="출력 이미지 경로")
    parser.add_argument("--language", type=str, default="ko", choices=["ko", "en"], help="언어")
    
    args = parser.parse_args()
    
    output_path = Path(args.output) if args.output else None
    create_diagram_image(
        concept=args.concept,
        diagram_type=args.type,
        output_path=output_path,
        language=args.language
    )
    print(f"다이어그램 생성 완료: {output_path}")

