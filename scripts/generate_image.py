"""
이미지 생성 스크립트
썸네일 및 영상 배경으로 사용할 이미지 생성 (무료 Pillow 기반)
"""
import os
import sys
import json
import logging
import math
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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


def load_config() -> dict:
    """config.json 파일 로드"""
    config_path = project_root / "config" / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"설정 파일 파싱 오류: {e}")
        raise


def get_color_scheme_for_noise_type(noise_type: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """노이즈 타입에 따른 색상 스킴 반환 (시작 색상, 끝 색상)"""
    color_schemes = {
        "white_noise": ((20, 30, 60), (40, 60, 100)),  # 어두운 파란색 그라데이션
        "brown_noise": ((60, 40, 30), (100, 70, 50)),  # 따뜻한 갈색 그라데이션
        "pink_noise": ((80, 50, 80), (120, 80, 120)),  # 부드러운 핑크/퍼플 그라데이션
        "rain": ((30, 40, 60), (50, 70, 90)),  # 비 오는 밤 파란색
        "ocean": ((20, 40, 60), (40, 70, 100)),  # 바다 파란색
        "fireplace": ((80, 50, 30), (120, 70, 40)),  # 따뜻한 오렌지/빨강
    }
    return color_schemes.get(noise_type, ((30, 40, 60), (50, 70, 90)))


def create_gradient_image(
    width: int,
    height: int,
    start_color: Tuple[int, int, int],
    end_color: Tuple[int, int, int],
    direction: str = "vertical"
) -> Image.Image:
    """
    그라데이션 이미지 생성
    
    Args:
        width: 이미지 너비
        height: 이미지 높이
        start_color: 시작 색상 (R, G, B)
        end_color: 끝 색상 (R, G, B)
        direction: 그라데이션 방향 ("vertical", "horizontal", "diagonal", "radial")
    
    Returns:
        PIL Image 객체
    """
    # 이미지 생성
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    if direction == "vertical":
        # 수직 그라데이션
        for y in range(height):
            ratio = y / height
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            for x in range(width):
                pixels[x, y] = (r, g, b)
    
    elif direction == "horizontal":
        # 수평 그라데이션
        for x in range(width):
            ratio = x / width
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            for y in range(height):
                pixels[x, y] = (r, g, b)
    
    elif direction == "diagonal":
        # 대각선 그라데이션
        for y in range(height):
            for x in range(width):
                ratio = (x + y) / (width + height)
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                pixels[x, y] = (r, g, b)
    
    elif direction == "radial":
        # 방사형 그라데이션
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                ratio = min(dist / max_dist, 1.0)
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                pixels[x, y] = (r, g, b)
    
    return img


def add_texture(img: Image.Image, noise_type: str) -> Image.Image:
    """이미지에 텍스처 추가"""
    # 약간의 노이즈 추가로 자연스러운 느낌
    np_img = np.array(img)
    noise = np.random.randint(-10, 10, np_img.shape, dtype=np.int16)
    np_img = np.clip(np_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(np_img)
    
    # 부드러운 블러 적용
    if noise_type in ["rain", "ocean"]:
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    return img


def generate_background_image(noise_type: str) -> Path:
    """
    배경 이미지 생성 함수 (무료 Pillow 기반)
    
    Args:
        noise_type: 노이즈 타입
    
    Returns:
        생성된 이미지 파일 경로
    """
    try:
        logger.info(f"Pillow를 사용하여 배경 이미지 생성 중... (노이즈 타입: {noise_type})")
        
        # 타겟 해상도
        width, height = 1920, 1080
        
        # 노이즈 타입에 따른 색상 스킴 가져오기
        start_color, end_color = get_color_scheme_for_noise_type(noise_type)
        logger.info(f"색상 스킴: {start_color} -> {end_color}")
        
        # 그라데이션 방향 결정
        gradient_directions = {
            "white_noise": "vertical",
            "brown_noise": "diagonal",
            "pink_noise": "radial",
            "rain": "vertical",
            "ocean": "horizontal",
            "fireplace": "radial",
        }
        direction = gradient_directions.get(noise_type, "vertical")
        
        # 그라데이션 이미지 생성
        img = create_gradient_image(width, height, start_color, end_color, direction)
        
        # 텍스처 추가
        img = add_texture(img, noise_type)
        
        # 출력 디렉토리 확인
        output_dir = project_root / "images"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{noise_type}_bg.png"
        output_path = output_dir / filename
        
        # PNG로 저장
        img.save(str(output_path), "PNG", optimize=True)
        logger.info(f"이미지 파일 저장 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"이미지 생성 중 오류 발생: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        # 설정 로드
        config = load_config()
        
        # 노이즈 타입을 명령행 인자로 받거나 기본값 사용
        if len(sys.argv) > 1:
            noise_type = sys.argv[1]
        else:
            # 기본값으로 white_noise 사용
            noise_type = "white_noise"
            logger.warning("노이즈 타입이 지정되지 않아 기본값(white_noise)을 사용합니다.")
        
        # 이미지 생성
        output_path = generate_background_image(noise_type)
        logger.info(f"생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

