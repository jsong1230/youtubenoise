"""
틀린그림찾기용 이미지 생성 및 편집 스크립트
GPT API를 활용하여 원본 이미지 생성 및 차이점 추가
"""
import os
import sys
import json
import logging
import base64
import io
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

# 로깅 설정
log_file = project_root / "logs" / "app.log"
log_file.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

_openai_client: Optional[OpenAI] = None


def get_openai_client() -> Optional[OpenAI]:
    """OpenAI 클라이언트를 생성/캐싱"""
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return None
    
    _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def generate_base_image(theme: str, style: str) -> Optional[Path]:
    """
    GPT API로 원본 이미지 생성
    
    Args:
        theme: 이미지 주제 (예: "집안 풍경", "음식")
        style: 이미지 스타일 설명
    
    Returns:
        생성된 이미지 파일 경로
    """
    try:
        client = get_openai_client()
        if not client:
            return None
        
        prompt = (
            f"{theme}을 주제로 한 {style}. "
            f"시니어가 쉽게 구분할 수 있는 선명한 색감과 명확한 구도. "
            f"고해상도 일러스트 스타일. "
            f"틀린그림찾기 게임에 적합한 복잡도. "
            f"저작권 문제 없는 오리지널 이미지."
        )
        
        logger.info(f"원본 이미지 생성 중... (주제: {theme})")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # 이미지 다운로드
        import requests
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        
        # 이미지 저장
        output_dir = project_root / "images" / "spot_difference"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_base_{theme.replace(' ', '_')}.png"
        output_path = output_dir / filename
        
        with open(output_path, 'wb') as f:
            f.write(img_response.content)
        
        # 16:9 비율로 리사이즈 (중앙 크롭)
        img = Image.open(output_path)
        img = resize_and_crop_to_aspect(img, 16/9, (1920, 1080))
        img.save(output_path, "PNG", optimize=True)
        
        logger.info(f"원본 이미지 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"원본 이미지 생성 실패: {e}", exc_info=True)
        return None


def resize_and_crop_to_aspect(img: Image.Image, target_aspect: float, target_size: Tuple[int, int]) -> Image.Image:
    """이미지를 목표 비율로 중앙 크롭 후 리사이즈"""
    img_aspect = img.width / img.height
    
    if img_aspect > target_aspect:
        # 이미지가 더 넓음 - 높이 기준으로 크롭
        new_height = img.height
        new_width = int(new_height * target_aspect)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, new_height))
    else:
        # 이미지가 더 높음 - 너비 기준으로 크롭
        new_width = img.width
        new_height = int(new_width / target_aspect)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, new_width, top + new_height))
    
    # 목표 크기로 리사이즈
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    return img


def generate_differences_metadata(base_image_path: Path, num_differences: int, theme: str) -> Optional[Dict]:
    """
    GPT API로 차이점 목록 생성
    
    Args:
        base_image_path: 원본 이미지 경로
        num_differences: 차이점 개수
        theme: 이미지 주제
    
    Returns:
        차이점 정보 딕셔너리
    """
    try:
        client = get_openai_client()
        if not client:
            return None
        
        # 이미지를 base64로 인코딩
        with open(base_image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = (
            f"이 이미지를 분석하여 시니어가 쉽게 찾을 수 있는 {num_differences}개의 차이점을 제안해주세요. "
            f"각 차이점은 다음 중 하나의 타입이어야 합니다: "
            f"1. color_change (색상 변경) "
            f"2. object_added (물건 추가) "
            f"3. object_removed (물건 삭제) "
            f"4. position_change (위치 변경) "
            f"5. size_change (크기 변경) "
            f"6. pattern_change (패턴 변경). "
            f"JSON 형식으로 응답해주세요. "
            f"각 차이점에는 type, description, x, y 좌표(대략적인 위치), radius(표시할 원의 반지름)를 포함해주세요."
        )
        
        logger.info(f"차이점 메타데이터 생성 중... ({num_differences}개)")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"차이점 메타데이터 생성 완료: {len(result.get('differences', []))}개")
        
        return result
        
    except Exception as e:
        logger.error(f"차이점 메타데이터 생성 실패: {e}", exc_info=True)
        return None


def create_modified_image(base_image_path: Path, differences: List[Dict]) -> Optional[Path]:
    """
    원본 이미지에 차이점을 적용하여 수정본 이미지 생성
    
    Args:
        base_image_path: 원본 이미지 경로
        differences: 차이점 정보 리스트
    
    Returns:
        수정본 이미지 파일 경로
    """
    try:
        img = Image.open(base_image_path).copy()
        draw = ImageDraw.Draw(img)
        
        for diff in differences:
            diff_type = diff.get('type')
            x = diff.get('x', 0)
            y = diff.get('y', 0)
            
            if diff_type == 'color_change':
                # 색상 변경 (간단한 예시: 해당 영역의 색상 변경)
                radius = diff.get('radius', 30)
                # 원 영역의 색상을 변경 (예: 빨간색으로)
                bbox = (x - radius, y - radius, x + radius, y + radius)
                # 간단한 색상 오버레이
                overlay = Image.new('RGBA', img.size, (255, 0, 0, 100))
                mask = Image.new('L', img.size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse(bbox, fill=255)
                img = Image.composite(overlay, img, mask).convert('RGB')
                
            elif diff_type == 'object_added':
                # 물건 추가 (간단한 원으로 표시)
                radius = diff.get('radius', 25)
                draw.ellipse(
                    [x - radius, y - radius, x + radius, y + radius],
                    fill=(255, 200, 0),
                    outline=(255, 100, 0),
                    width=3
                )
                
            elif diff_type == 'object_removed':
                # 물건 삭제 (X 표시)
                size = diff.get('radius', 20)
                draw.line([x - size, y - size, x + size, y + size], fill=(200, 200, 200), width=5)
                draw.line([x - size, y + size, x + size, y - size], fill=(200, 200, 200), width=5)
                
            elif diff_type == 'position_change':
                # 위치 변경 (화살표 표시)
                radius = diff.get('radius', 20)
                offset = 15
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(100, 150, 255), outline=(50, 100, 200), width=2)
                draw.line([x, y, x + offset, y], fill=(50, 100, 200), width=3)
                draw.polygon([(x + offset, y), (x + offset - 5, y - 5), (x + offset - 5, y + 5)], fill=(50, 100, 200))
                
            # 더 정교한 편집은 GPT 이미지 편집 API를 사용할 수 있지만,
            # 여기서는 간단한 예시로 구현
        
        # 수정본 이미지 저장
        output_dir = project_root / "images" / "spot_difference"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        base_name = base_image_path.stem.replace('_base', '_modified')
        output_path = output_dir / f"{date_str}_{base_name}.png"
        
        img.save(output_path, "PNG", optimize=True)
        logger.info(f"수정본 이미지 생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"수정본 이미지 생성 실패: {e}", exc_info=True)
        return None


def generate_spot_difference_images(theme: str, num_differences: int, style: str) -> Optional[Dict]:
    """
    틀린그림찾기용 이미지 쌍 생성
    
    Args:
        theme: 이미지 주제
        num_differences: 차이점 개수
        style: 이미지 스타일
    
    Returns:
        {
            "base_image": Path,
            "modified_image": Path,
            "differences": List[Dict]
        }
    """
    try:
        # 1. 원본 이미지 생성
        base_image = generate_base_image(theme, style)
        if not base_image:
            return None
        
        # 2. 차이점 메타데이터 생성
        differences_metadata = generate_differences_metadata(base_image, num_differences, theme)
        if not differences_metadata:
            return None
        
        differences = differences_metadata.get('differences', [])
        if len(differences) < num_differences:
            logger.warning(f"요청한 차이점 개수({num_differences})보다 적게 생성됨({len(differences)})")
        
        # 3. 수정본 이미지 생성
        modified_image = create_modified_image(base_image, differences[:num_differences])
        if not modified_image:
            return None
        
        return {
            "base_image": base_image,
            "modified_image": modified_image,
            "differences": differences[:num_differences]
        }
        
    except Exception as e:
        logger.error(f"틀린그림찾기 이미지 생성 실패: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    # 테스트
    result = generate_spot_difference_images(
        theme="집안 풍경",
        num_differences=3,
        style="warm, clear, high contrast, senior-friendly illustration"
    )
    if result:
        print(f"원본: {result['base_image']}")
        print(f"수정본: {result['modified_image']}")
        print(f"차이점: {len(result['differences'])}개")

