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
import base64
import io
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

_openai_client: Optional[OpenAI] = None


def get_openai_client() -> Optional[OpenAI]:
    """OpenAI 클라이언트를 생성/캐싱"""
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY가 설정되지 않아 DALL·E 생성을 건너뜁니다.")
        return None
    
    _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def load_bgm_preset(preset_name: str) -> Optional[dict]:
    """BGM 프리셋 정보 로드"""
    import yaml
    presets_path = project_root / "config" / "bgm_presets.yaml"
    try:
        with open(presets_path, 'r', encoding='utf-8') as f:
            presets_data = yaml.safe_load(f)
            return presets_data.get("presets", {}).get(preset_name)
    except Exception as e:
        logger.warning(f"BGM 프리셋 로드 실패: {e}")
        return None

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
    try:
        preset = load_bgm_preset(preset_name)
        if preset:
            color_scheme = preset.get("color_scheme", {})
            start = tuple(color_scheme.get("start", [50, 50, 50]))
            end = tuple(color_scheme.get("end", [100, 100, 100]))
            direction = color_scheme.get("gradient_direction", "vertical")
            return start, end, direction
    except Exception as e:
        logger.warning(f"BGM 프리셋 색상 로드 실패: {e}")
    
    # 기본값
    return ((50, 50, 50), (100, 100, 100), "vertical")


def resize_and_crop_to_aspect(
    img: Image.Image,
    target_width: int,
    target_height: int,
) -> Image.Image:
    """이미지를 비율 왜곡 없이 지정 비율/크기로 맞춤"""
    target_ratio = target_width / target_height
    src_ratio = img.width / img.height

    if src_ratio > target_ratio:
        # 가로가 더 길면 좌우를 잘라냄
        new_width = int(img.height * target_ratio)
        offset = (img.width - new_width) // 2
        img = img.crop((offset, 0, offset + new_width, img.height))
    elif src_ratio < target_ratio:
        # 세로가 더 길면 상하를 잘라냄
        new_height = int(img.width / target_ratio)
        offset = (img.height - new_height) // 2
        img = img.crop((0, offset, img.width, offset + new_height))

    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def create_gradient_image(
    width: int,
    height: int,
    start_color: Tuple[int, int, int],
    end_color: Tuple[int, int, int],
    direction: str = "vertical"
) -> Image.Image:
    """
    그라데이션 이미지 생성 (개선된 다중 색상 그라데이션)
    
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
    
    # 중간 색상 추가로 더 부드러운 그라데이션
    mid_color = (
        (start_color[0] + end_color[0]) // 2,
        (start_color[1] + end_color[1]) // 2,
        (start_color[2] + end_color[2]) // 2
    )
    
    if direction == "vertical":
        # 수직 그라데이션 (다중 색상)
        for y in range(height):
            ratio = y / height
            if ratio < 0.5:
                # 상단에서 중간까지
                sub_ratio = ratio * 2
                r = int(start_color[0] + (mid_color[0] - start_color[0]) * sub_ratio)
                g = int(start_color[1] + (mid_color[1] - start_color[1]) * sub_ratio)
                b = int(start_color[2] + (mid_color[2] - start_color[2]) * sub_ratio)
            else:
                # 중간에서 하단까지
                sub_ratio = (ratio - 0.5) * 2
                r = int(mid_color[0] + (end_color[0] - mid_color[0]) * sub_ratio)
                g = int(mid_color[1] + (end_color[1] - mid_color[1]) * sub_ratio)
                b = int(mid_color[2] + (end_color[2] - mid_color[2]) * sub_ratio)
            
            # 약간의 수평 변화 추가 (자연스러운 느낌)
            for x in range(width):
                h_variation = math.sin(x / 200) * 3  # 미세한 수평 변화
                pixels[x, y] = (
                    max(0, min(255, int(r + h_variation))),
                    max(0, min(255, int(g + h_variation))),
                    max(0, min(255, int(b + h_variation)))
                )
    
    elif direction == "horizontal":
        # 수평 그라데이션
        for x in range(width):
            ratio = x / width
            if ratio < 0.5:
                sub_ratio = ratio * 2
                r = int(start_color[0] + (mid_color[0] - start_color[0]) * sub_ratio)
                g = int(start_color[1] + (mid_color[1] - start_color[1]) * sub_ratio)
                b = int(start_color[2] + (mid_color[2] - start_color[2]) * sub_ratio)
            else:
                sub_ratio = (ratio - 0.5) * 2
                r = int(mid_color[0] + (end_color[0] - mid_color[0]) * sub_ratio)
                g = int(mid_color[1] + (end_color[1] - mid_color[1]) * sub_ratio)
                b = int(mid_color[2] + (end_color[2] - mid_color[2]) * sub_ratio)
            for y in range(height):
                pixels[x, y] = (r, g, b)
    
    elif direction == "diagonal":
        # 대각선 그라데이션
        for y in range(height):
            for x in range(width):
                ratio = (x + y) / (width + height)
                if ratio < 0.5:
                    sub_ratio = ratio * 2
                    r = int(start_color[0] + (mid_color[0] - start_color[0]) * sub_ratio)
                    g = int(start_color[1] + (mid_color[1] - start_color[1]) * sub_ratio)
                    b = int(start_color[2] + (mid_color[2] - start_color[2]) * sub_ratio)
                else:
                    sub_ratio = (ratio - 0.5) * 2
                    r = int(mid_color[0] + (end_color[0] - mid_color[0]) * sub_ratio)
                    g = int(mid_color[1] + (end_color[1] - mid_color[1]) * sub_ratio)
                    b = int(mid_color[2] + (end_color[2] - mid_color[2]) * sub_ratio)
                pixels[x, y] = (r, g, b)
    
    elif direction == "radial":
        # 방사형 그라데이션 (중앙에서 밖으로)
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                ratio = min(dist / max_dist, 1.0)
                # 중앙이 밝고, 가장자리가 어두운 효과
                if ratio < 0.5:
                    sub_ratio = ratio * 2
                    r = int(start_color[0] + (mid_color[0] - start_color[0]) * sub_ratio)
                    g = int(start_color[1] + (mid_color[1] - start_color[1]) * sub_ratio)
                    b = int(start_color[2] + (mid_color[2] - start_color[2]) * sub_ratio)
                else:
                    sub_ratio = (ratio - 0.5) * 2
                    r = int(mid_color[0] + (end_color[0] - mid_color[0]) * sub_ratio)
                    g = int(mid_color[1] + (end_color[1] - mid_color[1]) * sub_ratio)
                    b = int(mid_color[2] + (end_color[2] - mid_color[2]) * sub_ratio)
                pixels[x, y] = (r, g, b)
    
    return img


def add_texture(img: Image.Image, noise_type: str) -> Image.Image:
    """이미지에 텍스처 추가 (개선된 자연스러운 텍스처)"""
    # 더 자연스러운 노이즈 추가 (가우시안 노이즈)
    np_img = np.array(img, dtype=np.float32)
    
    # 가우시안 노이즈 생성 (더 자연스러움)
    noise = np.random.normal(0, 5, np_img.shape).astype(np.float32)
    np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(np_img)
    
    # 부드러운 블러 적용 (깊이감 추가)
    if noise_type in ["rain", "ocean", "bgm"]:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # 미세한 필름 그레인 효과
    np_img = np.array(img, dtype=np.float32)
    grain = np.random.normal(0, 2, np_img.shape).astype(np.float32)
    np_img = np.clip(np_img + grain, 0, 255).astype(np.uint8)
    img = Image.fromarray(np_img)
    
    return img


def add_christmas_elements(img: Image.Image) -> Image.Image:
    """크리스마스 요소 추가 (개선된 현실적인 크리스마스 장면)"""
    width, height = img.size
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # 1. 창문 실루엣과 불빛 효과 (좌우에)
    window_width = 300
    window_height = 400
    window_y = height - window_height - 50
    
    # 왼쪽 창문
    left_window_x = 100
    window_frame_color = (40, 30, 20, 255)  # 어두운 갈색
    window_light_color = (255, 200, 150, 120)  # 따뜻한 불빛
    
    # 창문 불빛 (중앙에서 퍼지는 효과)
    for i in range(5):
        light_size = window_width // 2 - i * 20
        light_alpha = 80 - i * 15
        draw.ellipse(
            [left_window_x + window_width//2 - light_size//2, 
             window_y + window_height//2 - light_size//2,
             left_window_x + window_width//2 + light_size//2,
             window_y + window_height//2 + light_size//2],
            fill=(255, 200, 150, light_alpha)
        )
    
    # 창문 프레임
    frame_thickness = 15
    draw.rectangle(
        [left_window_x, window_y, left_window_x + window_width, window_y + window_height],
        outline=window_frame_color, width=frame_thickness
    )
    # 창문 십자형 프레임
    draw.line([left_window_x + window_width//2, window_y, 
               left_window_x + window_width//2, window_y + window_height], 
              fill=window_frame_color, width=frame_thickness)
    draw.line([left_window_x, window_y + window_height//2,
               left_window_x + window_width, window_y + window_height//2],
              fill=window_frame_color, width=frame_thickness)
    
    # 오른쪽 창문
    right_window_x = width - 100 - window_width
    for i in range(5):
        light_size = window_width // 2 - i * 20
        light_alpha = 80 - i * 15
        draw.ellipse(
            [right_window_x + window_width//2 - light_size//2,
             window_y + window_height//2 - light_size//2,
             right_window_x + window_width//2 + light_size//2,
             window_y + window_height//2 + light_size//2],
            fill=(255, 200, 150, light_alpha)
        )
    draw.rectangle(
        [right_window_x, window_y, right_window_x + window_width, window_y + window_height],
        outline=window_frame_color, width=frame_thickness
    )
    draw.line([right_window_x + window_width//2, window_y,
               right_window_x + window_width//2, window_y + window_height],
              fill=window_frame_color, width=frame_thickness)
    draw.line([right_window_x, window_y + window_height//2,
               right_window_x + window_width, window_y + window_height//2],
              fill=window_frame_color, width=frame_thickness)
    
    # 2. 눈 내리는 효과 (더 현실적으로)
    for _ in range(300):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(1, 4)
        # 크기에 따라 투명도 조절 (작은 눈은 더 투명)
        alpha = 150 + size * 20
        # 약간의 블러 효과를 위한 여러 점
        for offset in range(size):
            draw.ellipse(
                [x - size + offset, y - size + offset,
                 x + size - offset, y + size - offset],
                fill=(255, 255, 255, alpha // (offset + 1))
            )
    
    # 3. 별 추가 (반짝이는 효과)
    star_color = (255, 255, 200, 255)
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height // 2)
        size = random.randint(2, 6)
        
        # 별 중심
        draw.ellipse([x-2, y-2, x+2, y+2], fill=star_color)
        
        # 별 빛줄기 (4방향)
        line_length = size * 2
        draw.line([x-line_length, y, x+line_length, y], fill=star_color, width=1)
        draw.line([x, y-line_length, x, y+line_length], fill=star_color, width=1)
        # 대각선
        draw.line([x-line_length//2, y-line_length//2, 
                   x+line_length//2, y+line_length//2], fill=star_color, width=1)
        draw.line([x-line_length//2, y+line_length//2,
                   x+line_length//2, y-line_length//2], fill=star_color, width=1)
    
    # 4. 크리스마스 트리 (더 현실적으로, 그림자 포함)
    tree_x = width // 2
    tree_y = height - 150
    tree_base_color = (20, 60, 20, 255)  # 어두운 초록
    tree_highlight_color = (40, 100, 40, 200)  # 밝은 초록
    
    # 트리 그림자
    shadow_offset = 20
    for i in range(3):
        level_y = tree_y - i * 90
        level_width = 250 - i * 50
        shadow_points = [
            (tree_x + shadow_offset, level_y - 60 + shadow_offset),
            (tree_x - level_width//2 + shadow_offset, level_y + shadow_offset),
            (tree_x + level_width//2 + shadow_offset, level_y + shadow_offset),
        ]
        draw.polygon(shadow_points, fill=(0, 0, 0, 80))
    
    # 트리 삼각형들 (그림자 효과 포함)
    for i in range(3):
        level_y = tree_y - i * 90
        level_width = 250 - i * 50
        
        # 어두운 부분 (왼쪽)
        dark_points = [
            (tree_x, level_y - 60),
            (tree_x - level_width//2, level_y),
            (tree_x - level_width//4, level_y - 30),
        ]
        draw.polygon(dark_points, fill=tree_base_color)
        
        # 밝은 부분 (오른쪽, 조명 효과)
        light_points = [
            (tree_x, level_y - 60),
            (tree_x + level_width//4, level_y - 30),
            (tree_x + level_width//2, level_y),
        ]
        draw.polygon(light_points, fill=tree_highlight_color)
        
        # 전체 외곽선
        points = [
            (tree_x, level_y - 60),
            (tree_x - level_width//2, level_y),
            (tree_x + level_width//2, level_y),
        ]
        draw.polygon(points, outline=(10, 40, 10, 255), width=2)
    
    # 트리 줄기 (그림자 포함)
    trunk_width = 40
    trunk_height = 80
    # 줄기 그림자
    draw.rectangle(
        [tree_x - trunk_width//2 + shadow_offset,
         tree_y + shadow_offset,
         tree_x + trunk_width//2 + shadow_offset,
         tree_y + trunk_height + shadow_offset],
        fill=(0, 0, 0, 100)
    )
    # 줄기
    draw.rectangle(
        [tree_x - trunk_width//2, tree_y,
         tree_x + trunk_width//2, tree_y + trunk_height],
        fill=(60, 30, 15, 255)  # 갈색
    )
    # 줄기 하이라이트
    draw.rectangle(
        [tree_x - trunk_width//4, tree_y,
         tree_x + trunk_width//2, tree_y + trunk_height],
        fill=(80, 40, 20, 200)
    )
    
    # 5. 트리 장식 (더 현실적으로, 반짝이는 효과)
    decoration_colors = [
        (255, 50, 50, 255),    # 빨강
        (255, 220, 0, 255),    # 금색
        (50, 150, 255, 255),   # 파랑
        (255, 140, 0, 255),    # 주황
        (200, 50, 255, 255),   # 보라
    ]
    
    for i in range(3):
        level_y = tree_y - i * 90
        level_width = 250 - i * 50
        num_decorations = 4 + i
        
        for j in range(num_decorations):
            dec_x = tree_x - level_width//2 + (j + 1) * (level_width // (num_decorations + 1))
            dec_y = level_y - 40 + random.randint(-15, 15)
            color = random.choice(decoration_colors)
            size = random.randint(6, 10)
            
            # 장식 구체
            draw.ellipse(
                [dec_x - size, dec_y - size,
                 dec_x + size, dec_y + size],
                fill=color
            )
            # 하이라이트 (반짝임 효과)
            draw.ellipse(
                [dec_x - size//2, dec_y - size//2,
                 dec_x + size//3, dec_y + size//3],
                fill=(255, 255, 255, 180)
            )
    
    # 6. 트리 꼭대기 별
    top_star_x = tree_x
    top_star_y = tree_y - 270
    star_size = 15
    star_gold = (255, 220, 0, 255)
    
    # 별 중심
    draw.ellipse([top_star_x-3, top_star_y-3, top_star_x+3, top_star_y+3], fill=star_gold)
    # 별 빛줄기
    draw.line([top_star_x-star_size*2, top_star_y, top_star_x+star_size*2, top_star_y],
              fill=star_gold, width=3)
    draw.line([top_star_x, top_star_y-star_size*2, top_star_x, top_star_y+star_size*2],
              fill=star_gold, width=3)
    
    # 7. 눈 쌓인 지면 효과
    ground_y = height - 50
    snow_color = (240, 240, 255, 200)
    for x in range(0, width, 20):
        wave_height = random.randint(0, 15)
        draw.ellipse(
            [x - 20, ground_y - wave_height,
             x + 20, ground_y + wave_height],
            fill=snow_color
        )
    
    return img


def build_dalle_prompt_for_preset(preset_name: str) -> Optional[str]:
    """프리셋 정보를 기반으로 DALL·E 프롬프트 생성"""
    preset = load_bgm_preset(preset_name)
    if not preset:
        return None
    
    name = preset.get("name", preset_name).replace("_", " ")
    description = preset.get("description", "")
    style = preset.get("style", "").replace("_", " ")
    tags = preset.get("tags", [])
    tag_phrase = ", ".join(tags[:8]) if tags else ""
    
    color_start, color_end, _ = get_color_scheme_for_bgm_preset(preset_name)
    color_phrase = f"color palette mixing RGB {color_start} to {color_end}"
    
    prompt = (
        f"Ultra realistic, cinematic illustration for a YouTube video background depicting {description}. "
        f"Atmosphere: cozy {name.lower()} with gentle holiday lights, soft depth of field, "
        f"warm bokeh, subtle snowflakes outside the window. Style: {style}. "
        f"Keywords: {tag_phrase}. {color_phrase}. "
        f"No text, no watermark, 4K detailed lighting, perfect for a relaxing music video."
    )
    return prompt


def generate_image_with_dalle(preset_name: str, width: int, height: int) -> Optional[Path]:
    """DALL·E (gpt-image-1)로 이미지 생성"""
    client = get_openai_client()
    if not client:
        return None
    
    prompt = build_dalle_prompt_for_preset(preset_name)
    if not prompt:
        logger.warning("프롬프트를 생성하지 못했습니다. DALL·E 생성을 건너뜁니다.")
        return None
    
    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
    
    try:
        logger.info(f"DALL·E 이미지를 생성 중... (모델: {model}, 사이즈: {size})")
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality="high",
            n=1,
        )
        image_base64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)
        
        with Image.open(io.BytesIO(image_bytes)) as dalle_img:
            dalle_img = dalle_img.convert("RGB")
            dalle_img = resize_and_crop_to_aspect(dalle_img, width, height)
            
            output_dir = project_root / "images"
            output_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{date_str}_{preset_name}_bg.png"
            output_path = output_dir / filename
            dalle_img.save(str(output_path), "PNG", optimize=True)
            logger.info(f"DALL·E 이미지 생성 완료: {output_path}")
            return output_path
    except Exception as e:
        logger.warning(f"DALL·E 이미지 생성 실패: {e}")
        return None


def generate_background_image_for_bgm(preset_name: str) -> Path:
    """
    BGM용 배경 이미지 생성 함수
    먼저 무료 이미지를 다운로드 시도하고, 실패하면 생성합니다.
    
    Args:
        preset_name: BGM 프리셋 이름
    
    Returns:
        생성된 이미지 파일 경로
    """
    try:
        logger.info(f"BGM용 배경 이미지 준비 중... (프리셋: {preset_name})")
        
        # 타겟 해상도
        width, height = 1920, 1080
        
        # 1) DALL·E 이미지 생성 시도
        dalle_image = generate_image_with_dalle(preset_name, width, height)
        if dalle_image:
            return dalle_image
        
        # 2) 무료 이미지 다운로드 시도
        try:
            from scripts.download_public_domain_images import get_background_image_for_preset
            downloaded_image = get_background_image_for_preset(preset_name, width, height)
            if downloaded_image and downloaded_image.exists():
                logger.info(f"다운로드된 이미지 사용: {downloaded_image}")
                return downloaded_image
        except Exception as e:
            logger.debug(f"이미지 다운로드 시도 실패 (생성으로 대체): {e}")
        
        # 3) Pillow 기반 이미지 생성
        logger.info(f"이미지 생성 중... (프리셋: {preset_name})")
        
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
            
            # 크리스마스 요소를 별도 레이어에 그리기
            christmas_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            christmas_layer = add_christmas_elements(christmas_layer)
            
            # 원본 배경에 크리스마스 레이어 합성
            img = Image.alpha_composite(img, christmas_layer)
            
            # RGB로 변환 (PNG 저장용, 알파 채널 제거)
            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (0, 0, 0))
                background.paste(img, mask=img.split()[3])
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

