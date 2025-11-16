"""
이미지 생성 스크립트
썸네일 및 영상 배경으로 사용할 이미지 생성 (무료 Pillow 기반)
"""
import os
import sys
import json
import logging
import math
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# 프로젝트 루트 설정
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


def get_color_scheme_for_noise_type(noise_type: str) -> Tuple[Tuple[int, int, int], Tuple[int, int,  int]]:
    """노이즈 타입에 따른 색상 스킴 반환 (시작 색상, 끝 색상)"""
    color_schemes = {
        "white_noise": ((20, 30, 60), (40, 60, 100)),  # 어두운 파란색 그라데이션
        "brown_noise": ((60, 40, 30), (100, 70, 50)),  # 따뜻한 갈색 그라데이션
        "pink_noise": ((80, 50, 80), (120, 80, 120)),  # 부드러운 핑크/퍼플 그라데이션
        "rain": ((30, 40, 60), (50, 70, 90)),  # 비 오는 밤 파란색
        "ocean": ((20, 40, 60), (40, 70, 100)),  # 바다 파란색
        "fireplace": ((80, 50, 30), (120, 70, 40)),  # 따뜻한 오렌지/빨강
        "lofi": ((40, 30, 50), (80, 60, 90)),  # 로파이 느낌의 따뜻한 퍼플/핑크
        "asmr": ((50, 40, 60), (90, 80, 100)),  # 부드러운 라벤더/퍼플
    }
    return color_schemes.get(noise_type, ((30, 40, 60), (50, 70, 90)))


def get_color_scheme_for_bgm_preset(preset_name: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], str]:
    """BGM 프리셋에 따른 색상 스킴 반환"""
    import yaml
    presets_path = project_root / "config" / "bgm_presets.yaml"
    try:
        with open(presets_path, 'r', encoding='utf-8') as f:
            presets_data = yaml.safe_load(f)
            presets = presets_data.get("presets", {})
            if preset_name in presets:
                preset = presets[preset_name]
                color_scheme = preset.get("color_scheme", {})
                start = tuple(color_scheme.get("start", [50, 50, 50]))
                end = tuple(color_scheme.get("end", [100, 100, 100]))
                direction = color_scheme.get("gradient_direction", "vertical")
                return start, end, direction
    except Exception as e:
        logger.warning(f"BGM 프리셋 색상 로드 실패: {e}")
    
    # 기본값
    return ((50, 50, 50), (100, 100, 100), "vertical")


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


def add_christmas_elements(img: Image.Image) -> Image.Image:
    """크리스마스 요소 추가 (눈, 별, 트리 실루엣 등)"""
    width, height = img.size
    draw = ImageDraw.Draw(img)
    
    # 눈 추가 (작은 흰색 점들)
    for _ in range(200):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(2, 5)
        draw.ellipse([x-size, y-size, x+size, y+size], fill=(255, 255, 255, 180))
    
    # 별 추가 (상단)
    star_color = (255, 255, 200, 200)
    for _ in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height // 3)
        size = random.randint(3, 8)
        # 간단한 별 모양
        points = [
            (x, y - size),
            (x - size//3, y - size//3),
            (x - size, y),
            (x - size//3, y + size//3),
            (x, y + size),
            (x + size//3, y + size//3),
            (x + size, y),
            (x + size//3, y - size//3),
        ]
        draw.polygon(points, fill=star_color)
    
    # 크리스마스 트리 실루엣 (하단 중앙)
    tree_x = width // 2
    tree_y = height - 100
    tree_color = (30, 80, 30, 200)  # 어두운 초록
    
    # 트리 삼각형들
    for i in range(3):
        level_y = tree_y - i * 80
        level_width = 200 - i * 40
        points = [
            (tree_x, level_y - 60),
            (tree_x - level_width//2, level_y),
            (tree_x + level_width//2, level_y),
        ]
        draw.polygon(points, fill=tree_color)
    
    # 트리 줄기
    trunk_width = 30
    trunk_height = 60
    draw.rectangle(
        [tree_x - trunk_width//2, tree_y, tree_x + trunk_width//2, tree_y + trunk_height],
        fill=(80, 40, 20, 200)
    )
    
    # 트리 장식 (작은 원들)
    decoration_colors = [(255, 0, 0, 200), (255, 255, 0, 200), (0, 0, 255, 200), (255, 165, 0, 200)]
    for i in range(3):
        level_y = tree_y - i * 80
        for j in range(3):
            dec_x = tree_x - 60 + j * 60
            dec_y = level_y - 30 + random.randint(-10, 10)
            color = random.choice(decoration_colors)
            draw.ellipse([dec_x-5, dec_y-5, dec_x+5, dec_y+5], fill=color)
    
    return img


def generate_background_image_for_bgm(preset_name: str) -> Path:
    """
    BGM용 배경 이미지 생성 함수
    
    Args:
        preset_name: BGM 프리셋 이름
    
    Returns:
        생성된 이미지 파일 경로
    """
    try:
        logger.info(f"BGM용 배경 이미지 생성 중... (프리셋: {preset_name})")
        
        # 타겟 해상도
        width, height = 1920, 1080
        
        # 프리셋에서 색상 스킴 가져오기
        start_color, end_color, direction = get_color_scheme_for_bgm_preset(preset_name)
        logger.info(f"색상 스킴: {start_color} -> {end_color}, 방향: {direction}")
        
        # 그라데이션 이미지 생성
        img = create_gradient_image(width, height, start_color, end_color, direction)
        
        # 크리스마스 프리셋인 경우 크리스마스 요소 추가
        if "christmas" in preset_name.lower():
            logger.info("크리스마스 요소 추가 중...")
            # RGBA 모드로 변환 (투명도 지원)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img = add_christmas_elements(img)
            # 다시 RGB로 변환 (PNG 저장용)
            if img.mode == "RGBA":
                # 알파 채널을 배경과 합성
                background = Image.new("RGB", img.size, (0, 0, 0))
                background.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                img = background
        
        # 텍스처 추가
        img = add_texture(img, "bgm")
        
        # 출력 디렉토리 확인
        output_dir = project_root / "images"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{preset_name}_bg.png"
        output_path = output_dir / filename
        
        # PNG로 저장
        img.save(str(output_path), "PNG", optimize=True)
        logger.info(f"이미지 파일 저장 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"이미지 생성 중 오류 발생: {e}", exc_info=True)
        raise


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
            "lofi": "radial",
            "asmr": "diagonal",
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

