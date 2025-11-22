"""
시니어용 종합 두뇌훈련 영상 클립 생성 및 합성
"""
import os
import sys
import subprocess
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import math
import openai
import base64
import json

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging, check_ffmpeg

# 로깅 설정
logger = setup_logging()


def download_image(url: str, output_path: Path) -> bool:
    """
    URL에서 이미지 다운로드
    
    Args:
        url: 이미지 URL
        output_path: 저장 경로
    
    Returns:
        성공 여부
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
        img.save(output_path, "PNG", optimize=True)
        
        logger.info(f"이미지 다운로드 완료: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"이미지 다운로드 실패: {e}")
        return False


def create_text_image(text: str, color_scheme: Dict, font_size: int, 
                      output_path: Path, subtitle: str = None, 
                      text_en: str = None, subtitle_en: str = None):
    """
    텍스트 이미지 생성 (문제 설명, 힌트 등) - 다국어 지원
    
    Args:
        text: 메인 텍스트 (한글)
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        subtitle: 부제목 (한글, 선택사항)
        text_en: 메인 텍스트 (영어, 선택사항)
        subtitle_en: 부제목 (영어, 선택사항)
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [245, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        try:
            # 한글 폰트
            font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            subtitle_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size // 2)
            # 영어 폰트
            font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size - 10)
            subtitle_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", (font_size - 10) // 2)
        except:
            font_ko = ImageFont.load_default()
            subtitle_font_ko = font_ko
            font_en = font_ko
            subtitle_font_en = font_ko
        
        # 다국어 텍스트가 있는 경우
        if text_en:
            # 한글 텍스트 (위)
            bbox_ko = draw.textbbox((0, 0), text, font=font_ko)
            text_width_ko = bbox_ko[2] - bbox_ko[0]
            text_height_ko = bbox_ko[3] - bbox_ko[1]
            
            x_ko = (1920 - text_width_ko) // 2
            y_ko = (1080 - text_height_ko * 2 - 60) // 2  # 영어 공간 확보
            
            draw.text((x_ko, y_ko), text, fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font_ko)
            
            # 영어 텍스트 (아래)
            bbox_en = draw.textbbox((0, 0), text_en, font=font_en)
            text_width_en = bbox_en[2] - bbox_en[0]
            text_height_en = bbox_en[3] - bbox_en[1]
            
            x_en = (1920 - text_width_en) // 2
            y_en = y_ko + text_height_ko + 30
            
            draw.text((x_en, y_en), text_en, fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font_en)
            
            # 부제목 (한글)
            if subtitle:
                bbox_sub_ko = draw.textbbox((0, 0), subtitle, font=subtitle_font_ko)
                sub_width_ko = bbox_sub_ko[2] - bbox_sub_ko[0]
                sub_x_ko = (1920 - sub_width_ko) // 2
                sub_y_ko = y_en + text_height_en + 20
                draw.text((sub_x_ko, sub_y_ko), subtitle, 
                         fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                         font=subtitle_font_ko)
            
            # 부제목 (영어)
            if subtitle_en:
                bbox_sub_en = draw.textbbox((0, 0), subtitle_en, font=subtitle_font_en)
                sub_width_en = bbox_sub_en[2] - bbox_sub_en[0]
                sub_x_en = (1920 - sub_width_en) // 2
                sub_y_en = y_en + text_height_en + (40 if subtitle else 20)
                draw.text((sub_x_en, sub_y_en), subtitle_en, 
                         fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                         font=subtitle_font_en)
        else:
            # 단일 언어 (기존 로직)
            bbox = draw.textbbox((0, 0), text, font=font_ko)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1920 - text_width) // 2
            y = (1080 - text_height) // 2 if not subtitle else (1080 - text_height) // 2 - 50
            
            draw.text((x, y), text, fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font_ko)
            
            # 부제목
            if subtitle:
                bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font_ko)
                sub_width = bbox[2] - bbox[0]
                sub_x = (1920 - sub_width) // 2
                sub_y = y + text_height + 40
                draw.text((sub_x, sub_y), subtitle, 
                         fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                         font=subtitle_font_ko)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"텍스트 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"텍스트 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_number_display_image(number: str, color_scheme: Dict, font_size: int, 
                                output_path: Path):
    """
    숫자 표시 이미지 생성
    
    Args:
        number: 표시할 숫자
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [245, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size * 2)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), number, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2
        
        # 그림자 효과
        shadow_offset = 8
        draw.text((x + shadow_offset, y + shadow_offset), number, 
                 fill=(150, 150, 150), font=font)
        
        # 메인 텍스트
        draw.text((x, y), number, 
                 fill=tuple(color_scheme.get('highlight', [100, 150, 200])), 
                 font=font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"숫자 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"숫자 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_countdown_image(seconds: int, color_scheme: Dict, font_size: int, 
                          output_path: Path):
    """
    카운트다운 이미지 생성
    
    Args:
        seconds: 카운트다운 초
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [245, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size * 2)
        except:
            font = ImageFont.load_default()
        
        text = str(seconds)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2
        
        # 그림자
        shadow_offset = 8
        draw.text((x + shadow_offset, y + shadow_offset), text, 
                 fill=(150, 150, 150), font=font)
        
        # 메인 텍스트
        draw.text((x, y), text, 
                 fill=tuple(color_scheme.get('countdown', [200, 80, 60])), 
                 font=font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"카운트다운 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"카운트다운 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_missing_object_image(base_image_path: Path, output_path: Path, missing_objects: List[str]):
    """
    원본 이미지에서 사라진 물건을 가린 수정본 이미지 생성
    
    Args:
        base_image_path: 원본 이미지 경로
        output_path: 출력 이미지 경로
        missing_objects: 사라진 물건 리스트
    """
    try:
        # 원본 이미지 로드
        img = Image.open(base_image_path).copy()
        draw = ImageDraw.Draw(img)
        
        # GPT Vision API로 물건 위치 찾기
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("OPENAI_API_KEY가 없어 물건 위치를 찾을 수 없습니다. 전체 이미지를 사용합니다.")
                # 폴백: 이미지 중앙 부분을 가리기
                width, height = img.size
                for i, obj in enumerate(missing_objects):
                    # 간단한 폴백: 이미지를 여러 영역으로 나누어 일부 영역 가리기
                    region_width = width // (len(missing_objects) + 1)
                    x = region_width * (i + 1)
                    y = height // 2
                    radius = min(region_width // 3, 100)
                    
                    # 배경색으로 가리기 (원본 이미지의 평균 색상 사용)
                    avg_color = img.resize((1, 1)).getpixel((0, 0))
                    draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                               fill=avg_color, outline=avg_color)
            else:
                # GPT Vision API로 물건 위치 찾기
                import base64
                
                # 이미지를 base64로 인코딩
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Vision API 호출
                client = openai.OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"이 이미지에서 다음 물건들의 위치를 찾아주세요: {', '.join(missing_objects)}. 각 물건의 중심 좌표 (x, y)와 대략적인 크기(반지름)를 JSON 형식으로 알려주세요. 형식: {{\"objects\": [{{\"name\": \"물건명\", \"x\": x좌표, \"y\": y좌표, \"radius\": 반지름}}]}}"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )
                
                # 응답 파싱
                import json
                try:
                    result_text = response.choices[0].message.content
                    # JSON 추출
                    if "```json" in result_text:
                        json_start = result_text.find("```json") + 7
                        json_end = result_text.find("```", json_start)
                        result_text = result_text[json_start:json_end].strip()
                    elif "{" in result_text:
                        json_start = result_text.find("{")
                        json_end = result_text.rfind("}") + 1
                        result_text = result_text[json_start:json_end]
                    
                    locations = json.loads(result_text)
                    objects_data = locations.get('objects', [])
                    
                    # 각 물건의 위치에 배경색으로 가리기
                    for obj_data in objects_data:
                        if obj_data.get('name') in missing_objects:
                            x = int(obj_data.get('x', img.size[0] // 2))
                            y = int(obj_data.get('y', img.size[1] // 2))
                            radius = int(obj_data.get('radius', 80))
                            
                            # 주변 배경색으로 가리기 (인페인팅 스타일)
                            # 원본 이미지의 해당 영역 주변 색상 평균 계산
                            bbox = (max(0, x - radius*2), max(0, y - radius*2), 
                                   min(img.size[0], x + radius*2), min(img.size[1], y + radius*2))
                            region = img.crop(bbox)
                            
                            # 가장자리 픽셀들의 평균 색상 계산
                            edge_pixels = []
                            for px in range(region.size[0]):
                                edge_pixels.append(region.getpixel((px, 0)))
                                edge_pixels.append(region.getpixel((px, region.size[1]-1)))
                            for py in range(region.size[1]):
                                edge_pixels.append(region.getpixel((0, py)))
                                edge_pixels.append(region.getpixel((region.size[0]-1, py)))
                            
                            if edge_pixels:
                                avg_r = sum(p[0] for p in edge_pixels) // len(edge_pixels)
                                avg_g = sum(p[1] for p in edge_pixels) // len(edge_pixels)
                                avg_b = sum(p[2] for p in edge_pixels) // len(edge_pixels)
                                fill_color = (avg_r, avg_g, avg_b)
                            else:
                                fill_color = img.getpixel((x, y))
                            
                            # 원형으로 가리기
                            mask = Image.new('L', img.size, 0)
                            mask_draw = ImageDraw.Draw(mask)
                            mask_draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=255)
                            
                            # 가려진 영역을 배경색으로 채우기
                            overlay = Image.new('RGB', img.size, fill_color)
                            img = Image.composite(overlay, img, mask)
                            draw = ImageDraw.Draw(img)
                            
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"물건 위치 파싱 실패: {e}. 폴백 방법 사용.")
                    # 폴백: 이미지 중앙 부분을 가리기
                    width, height = img.size
                    for i, obj in enumerate(missing_objects):
                        region_width = width // (len(missing_objects) + 1)
                        x = region_width * (i + 1)
                        y = height // 2
                        radius = min(region_width // 3, 100)
                        avg_color = img.resize((1, 1)).getpixel((0, 0))
                        draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                                   fill=avg_color, outline=avg_color)
        
        except Exception as e:
            logger.warning(f"GPT Vision API 사용 실패: {e}. 폴백 방법 사용.")
            # 폴백: 이미지 중앙 부분을 가리기
            width, height = img.size
            for i, obj in enumerate(missing_objects):
                region_width = width // (len(missing_objects) + 1)
                x = region_width * (i + 1)
                y = height // 2
                radius = min(region_width // 3, 100)
                avg_color = img.resize((1, 1)).getpixel((0, 0))
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                           fill=avg_color, outline=avg_color)
        
        # 수정본 이미지 저장
        img.save(output_path, "PNG", optimize=True)
        logger.info(f"사라진 물건 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"사라진 물건 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_comparison_image(base_image: Path, modified_image: Path, output_path: Path):
    """
    원본과 수정본 이미지를 좌우로 배치한 비교 이미지 생성
    
    Args:
        base_image: 원본 이미지 경로
        modified_image: 수정본 이미지 경로
        output_path: 출력 이미지 경로
    """
    try:
        base_img = Image.open(base_image)
        modified_img = Image.open(modified_image)
        
        # 두 이미지 모두 960x540으로 리사이즈 (16:9 비율 유지)
        base_img = base_img.resize((960, 540), Image.Resampling.LANCZOS)
        modified_img = modified_img.resize((960, 540), Image.Resampling.LANCZOS)
        
        # 1920x1080 캔버스 생성
        canvas = Image.new('RGB', (1920, 1080), (240, 240, 235))
        
        # 좌우 배치 (상하 중앙 정렬)
        y_offset = (1080 - 540) // 2  # 270
        canvas.paste(base_img, (0, y_offset))
        canvas.paste(modified_img, (960, y_offset))
        
        # 중앙 구분선
        draw = ImageDraw.Draw(canvas)
        draw.line([(960, y_offset), (960, y_offset + 540)], fill=(200, 200, 200), width=3)
        
        # 라벨 추가
        try:
            font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 48)
        except:
            font = ImageFont.load_default()
        
        draw.text((480, y_offset + 50), "원본", fill=(50, 50, 50), font=font, anchor="mm")
        draw.text((1440, y_offset + 50), "수정본", fill=(50, 50, 50), font=font, anchor="mm")
        
        canvas.save(output_path, "PNG", optimize=True)
        logger.info(f"비교 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"비교 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_clock_image(hour: int, minute: int, color_scheme: Dict, 
                      font_size: int, output_path: Path):
    """
    시계 이미지 생성 (아날로그 시계)
    
    Args:
        hour: 시 (1-12)
        minute: 분 (0-59)
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [245, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        # 시계 중심 및 반지름
        center_x, center_y = 960, 540
        radius = 300
        
        # 시계 외곽 원
        draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            outline=tuple(color_scheme.get('text', [40, 40, 40])),
            width=10,
            fill=tuple(color_scheme.get('background', [255, 255, 255]))
        )
        
        # 숫자 표시 (12, 3, 6, 9)
        try:
            num_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 60)
        except:
            num_font = ImageFont.load_default()
        
        for i in [12, 3, 6, 9]:
            angle = (i - 3) * 30 - 90  # 12시가 위쪽
            rad = math.radians(angle)
            x = center_x + (radius - 40) * math.cos(rad)
            y = center_y + (radius - 40) * math.sin(rad)
            draw.text((x, y), str(i), fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                     font=num_font, anchor="mm")
        
        # 시침 (짧은 바늘)
        hour_angle = math.radians((hour % 12) * 30 + minute * 0.5 - 90)
        hour_length = radius * 0.5
        hour_x = center_x + hour_length * math.cos(hour_angle)
        hour_y = center_y + hour_length * math.sin(hour_angle)
        draw.line([(center_x, center_y), (hour_x, hour_y)], 
                 fill=tuple(color_scheme.get('text', [40, 40, 40])), width=8)
        
        # 분침 (긴 바늘)
        minute_angle = math.radians(minute * 6 - 90)
        minute_length = radius * 0.7
        minute_x = center_x + minute_length * math.cos(minute_angle)
        minute_y = center_y + minute_length * math.sin(minute_angle)
        draw.line([(center_x, center_y), (minute_x, minute_y)], 
                 fill=tuple(color_scheme.get('highlight', [100, 150, 200])), width=6)
        
        # 중심점
        draw.ellipse([center_x - 10, center_y - 10, center_x + 10, center_y + 10],
                    fill=tuple(color_scheme.get('text', [40, 40, 40])))
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"시계 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"시계 이미지 생성 실패: {e}", exc_info=True)
        raise


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """
    텍스트를 주어진 너비에 맞게 줄바꿈
    
    Args:
        text: 원본 텍스트
        font: 폰트
        max_width: 최대 너비
    
    Returns:
        줄바꿈된 텍스트 리스트
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [text]


def create_answer_image(answer_text: str, explanation: str, color_scheme: Dict,
                       font_size: int, output_path: Path,
                       answer_en: str = None, explanation_en: str = None):
    """
    정답 화면 이미지 생성 (긴 텍스트 자동 줄바꿈, 다국어 지원)
    
    Args:
        answer_text: 정답 텍스트 (한글)
        explanation: 설명 (한글)
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        answer_en: 정답 텍스트 (영어, 선택사항)
        explanation_en: 설명 (영어, 선택사항)
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [245, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        try:
            # 한글 폰트
            title_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            answer_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size * 2)
            exp_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size // 2)
            # 영어 폰트
            title_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size - 10)
            answer_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int((font_size - 10) * 1.8))
            exp_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", (font_size - 10) // 2)
        except:
            title_font_ko = answer_font_ko = exp_font_ko = ImageFont.load_default()
            title_font_en = answer_font_en = exp_font_en = ImageFont.load_default()
        
        y_pos = 100
        
        # "정답" 제목 (한글)
        title_ko = "정답"
        bbox = draw.textbbox((0, 0), title_ko, font=title_font_ko)
        title_width = bbox[2] - bbox[0]
        draw.text(((1920 - title_width) // 2, y_pos), title_ko, 
                 fill=tuple(color_scheme.get('correct', [80, 160, 80])), 
                 font=title_font_ko)
        
        # "Answer" 제목 (영어, 다국어인 경우)
        if answer_en:
            title_en = "Answer"
            bbox_en = draw.textbbox((0, 0), title_en, font=title_font_en)
            title_width_en = bbox_en[2] - bbox_en[0]
            draw.text(((1920 - title_width_en) // 2, y_pos + 50), title_en, 
                     fill=tuple(color_scheme.get('correct', [80, 160, 80])), 
                     font=title_font_en)
            y_pos += 120
        else:
            y_pos += 100
        
        # 정답 텍스트 (한글, 줄바꿈 처리)
        answer_max_width = 1800
        answer_lines_ko = wrap_text(str(answer_text), answer_font_ko, answer_max_width)
        answer_line_height = int(font_size * 2.5)
        
        for line in answer_lines_ko:
            bbox = draw.textbbox((0, 0), line, font=answer_font_ko)
            line_width = bbox[2] - bbox[0]
            draw.text(((1920 - line_width) // 2, y_pos), line, 
                     fill=tuple(color_scheme.get('highlight', [100, 150, 200])), 
                     font=answer_font_ko)
            y_pos += answer_line_height
        
        # 정답 텍스트 (영어, 다국어인 경우)
        if answer_en:
            y_pos += 20
            answer_lines_en = wrap_text(str(answer_en), answer_font_en, answer_max_width)
            answer_line_height_en = int((font_size - 10) * 2.2)
            
            for line in answer_lines_en:
                bbox = draw.textbbox((0, 0), line, font=answer_font_en)
                line_width = bbox[2] - bbox[0]
                draw.text(((1920 - line_width) // 2, y_pos), line, 
                         fill=tuple(color_scheme.get('highlight', [100, 150, 200])), 
                         font=answer_font_en)
                y_pos += answer_line_height_en
        
        y_pos += 50
        
        # 설명 (한글, 줄바꿈 처리)
        exp_max_width = 1800
        exp_lines_ko = wrap_text(str(explanation), exp_font_ko, exp_max_width)
        exp_line_height = int(font_size * 1.5)
        
        for line in exp_lines_ko:
            bbox = draw.textbbox((0, 0), line, font=exp_font_ko)
            line_width = bbox[2] - bbox[0]
            draw.text(((1920 - line_width) // 2, y_pos), line, 
                     fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                     font=exp_font_ko)
            y_pos += exp_line_height
            
            # 화면을 벗어나지 않도록 제한
            if y_pos > 900:
                break
        
        # 설명 (영어, 다국어인 경우)
        if explanation_en:
            y_pos += 20
            exp_lines_en = wrap_text(str(explanation_en), exp_font_en, exp_max_width)
            exp_line_height_en = int((font_size - 10) * 1.3)
            
            for line in exp_lines_en:
                bbox = draw.textbbox((0, 0), line, font=exp_font_en)
                line_width = bbox[2] - bbox[0]
                draw.text(((1920 - line_width) // 2, y_pos), line, 
                         fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                         font=exp_font_en)
                y_pos += exp_line_height_en
                
                # 화면을 벗어나지 않도록 제한
                if y_pos > 1000:
                    break
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"정답 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"정답 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_image_clip(image_path: Path, duration: int, output_path: Path):
    """
    정적 이미지를 비디오 클립으로 변환
    
    Args:
        image_path: 이미지 경로
        duration: 클립 길이 (초)
        output_path: 출력 비디오 경로
    """
    try:
        if not check_ffmpeg():
            raise RuntimeError("FFmpeg가 설치되지 않았습니다.")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080",
            "-t", str(duration),
            "-r", "30",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        logger.debug(f"이미지 클립 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"이미지 클립 생성 실패: {e}")
        raise


def create_problem_clip(problem_data: Dict, preset: Dict, output_dir: Path) -> List[Path]:
    """
    하나의 문제 세트에 대한 클립들 생성
    
    Args:
        problem_data: 문제 데이터
        preset: 프리셋 설정
        output_dir: 출력 디렉토리
    
    Returns:
        생성된 클립 파일 경로 리스트
    """
    try:
        clips = []
        problem_num = problem_data.get('problem_number', 1)
        module = problem_data.get('module', 'unknown')
        color_scheme = preset.get('color_scheme', {})
        font_size = preset.get('font_size', 84)
        
        # 1. 문제 소개 화면 (언어 옵션에 따라 단일 언어로 표시)
        intro_path = output_dir / f"problem_{problem_num}_intro.png"
        # 프리셋의 언어 설정 확인 (첫 번째 언어만 사용)
        preset_languages = preset.get('languages', ['ko'])
        use_language = preset_languages[0] if preset_languages else 'ko'
        
        if use_language == 'en':
            # 영어 전용
            problem_text = problem_data.get('problem_text_en') or problem_data.get('problem_text', '')
            problem_text_en = None
        else:
            # 한글 전용 (기본값)
            problem_text = problem_data.get('problem_text_ko') or problem_data.get('problem_text', '')
            problem_text_en = None
        
        create_text_image(
            problem_text,
            color_scheme,
            font_size,
            intro_path,
            text_en=problem_text_en
        )
        intro_clip = output_dir / f"problem_{problem_num}_intro.mp4"
        create_image_clip(intro_path, 3, intro_clip)
        clips.append(intro_clip)
        
        # 2. 문제 화면 (모듈별 처리)
        if module == "number_memory":
            # 숫자 표시
            number_path = output_dir / f"problem_{problem_num}_number.png"
            create_number_display_image(
                problem_data['problem_data']['number'],
                color_scheme,
                font_size,
                number_path
            )
            number_clip = output_dir / f"problem_{problem_num}_number.mp4"
            create_image_clip(number_path, problem_data['display_seconds'], number_clip)
            clips.append(number_clip)
            
        elif module == "missing_object":
            # 원본 이미지 다운로드
            base_img_path = output_dir / f"problem_{problem_num}_base.png"
            download_image(problem_data['problem_data']['base_image_url'], base_img_path)
            
            # 수정본 이미지 다운로드 (DALL-E로 생성된 이미지)
            modified_img_path = output_dir / f"problem_{problem_num}_modified.png"
            if 'modified_image_url' in problem_data['problem_data']:
                # DALL-E로 생성된 수정본 이미지 다운로드
                download_image(problem_data['problem_data']['modified_image_url'], modified_img_path)
            else:
                # 폴백: 기존 방식 (물건 가리기)
                missing_objects = problem_data['problem_data'].get('missing_objects', [])
                create_missing_object_image(base_img_path, modified_img_path, missing_objects)
            
            # 비교 이미지 생성 (좌우 배치)
            comparison_img_path = output_dir / f"problem_{problem_num}_comparison.png"
            create_comparison_image(base_img_path, modified_img_path, comparison_img_path)
            
            # 비교 화면 클립
            comparison_clip = output_dir / f"problem_{problem_num}_comparison.mp4"
            create_image_clip(comparison_img_path, problem_data['display_seconds'], comparison_clip)
            clips.append(comparison_clip)
            
        elif module == "pattern_sequence":
            # 패턴 표시 이미지 생성
            pattern = problem_data['problem_data'].get('pattern', [])
            choices = problem_data['problem_data'].get('choices', [])
            
            pattern_text = " → ".join(str(p) for p in pattern) + " → ?"
            choices_text = " / ".join(str(c) for c in choices)
            
            pattern_path = output_dir / f"problem_{problem_num}_pattern.png"
            create_text_image(
                pattern_text,
                color_scheme,
                font_size,
                pattern_path,
                subtitle=f"선택지: {choices_text}"
            )
            pattern_clip = output_dir / f"problem_{problem_num}_pattern.mp4"
            create_image_clip(pattern_path, problem_data['display_seconds'], pattern_clip)
            clips.append(pattern_clip)
            
        elif module == "word_association":
            # 단어 연상 문제 표시
            keyword = problem_data['problem_data'].get('keyword', '')
            choices = problem_data['problem_data'].get('choices', [])
            
            choices_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(choices)])
            
            word_path = output_dir / f"problem_{problem_num}_word.png"
            create_text_image(
                f"'{keyword}'와 관련된 단어는?",
                color_scheme,
                font_size,
                word_path,
                subtitle=choices_text
            )
            word_clip = output_dir / f"problem_{problem_num}_word.mp4"
            create_image_clip(word_path, problem_data['display_seconds'], word_clip)
            clips.append(word_clip)
            
        elif module == "clock_reading":
            # 시계 이미지 생성 (PIL로 간단한 시계 그리기)
            hour = problem_data['problem_data'].get('hour', 12)
            minute = problem_data['problem_data'].get('minute', 0)
            
            clock_path = output_dir / f"problem_{problem_num}_clock.png"
            create_clock_image(hour, minute, color_scheme, font_size, clock_path)
            clock_clip = output_dir / f"problem_{problem_num}_clock.mp4"
            create_image_clip(clock_path, problem_data['display_seconds'], clock_clip)
            clips.append(clock_clip)
            
        elif module == "korean_word_puzzle":
            # 한글 퍼즐 표시
            initial_sounds = problem_data['problem_data'].get('initial_sounds', '')
            hints = problem_data['problem_data'].get('hints', [])
            
            hints_text = "\n".join([f"• {h}" for h in hints])
            
            puzzle_path = output_dir / f"problem_{problem_num}_puzzle.png"
            create_text_image(
                f"초성: {initial_sounds}",
                color_scheme,
                font_size,
                puzzle_path,
                subtitle=hints_text
            )
            puzzle_clip = output_dir / f"problem_{problem_num}_puzzle.mp4"
            create_image_clip(puzzle_path, problem_data['display_seconds'], puzzle_clip)
            clips.append(puzzle_clip)
        
        # 3. 카운트다운 클립들
        countdown_seconds = problem_data.get('countdown_seconds', 10)
        for i in range(countdown_seconds, 0, -1):
            countdown_path = output_dir / f"problem_{problem_num}_countdown_{i}.png"
            create_countdown_image(i, color_scheme, font_size, countdown_path)
            
            countdown_clip = output_dir / f"problem_{problem_num}_countdown_{i}.mp4"
            create_image_clip(countdown_path, 1, countdown_clip)
            clips.append(countdown_clip)
        
        # 4. 정답 화면 (언어 옵션에 따라 단일 언어로 표시)
        answer_path = output_dir / f"problem_{problem_num}_answer.png"
        # 프리셋의 언어 설정 확인 (첫 번째 언어만 사용)
        preset_languages = preset.get('languages', ['ko'])
        use_language = preset_languages[0] if preset_languages else 'ko'
        
        if use_language == 'en':
            # 영어 전용
            answer = str(problem_data['answer_data'].get('correct_answer_en') or problem_data['answer_data'].get('correct_answer', ''))
            explanation = problem_data['answer_data'].get('explanation_en') or problem_data['answer_data'].get('explanation', '')
            answer_en = None
            explanation_en = None
        else:
            # 한글 전용 (기본값)
            answer = str(problem_data['answer_data'].get('correct_answer', ''))
            explanation = problem_data['answer_data'].get('explanation_ko') or problem_data['answer_data'].get('explanation', '')
            answer_en = None
            explanation_en = None
        
        create_answer_image(
            answer,
            explanation,
            color_scheme,
            font_size,
            answer_path,
            answer_en=answer_en,
            explanation_en=explanation_en
        )
        
        answer_clip = output_dir / f"problem_{problem_num}_answer.mp4"
        create_image_clip(answer_path, 5, answer_clip)
        clips.append(answer_clip)
        
        return clips
        
    except Exception as e:
        logger.error(f"문제 클립 생성 실패: {e}", exc_info=True)
        return []


def combine_clips(clips: List[Path], output_path: Path, bgm_path: Optional[Path] = None):
    """
    여러 클립을 하나의 영상으로 합성
    
    Args:
        clips: 클립 파일 경로 리스트
        output_path: 출력 영상 경로
        bgm_path: BGM 파일 경로 (선택사항)
    """
    try:
        if not check_ffmpeg():
            raise RuntimeError("FFmpeg가 설치되지 않았습니다.")
        
        # 클립 리스트 파일 생성
        list_file = output_path.parent / "clips_list.txt"
        with open(list_file, 'w') as f:
            for clip in clips:
                if clip.exists():
                    f.write(f"file '{clip.absolute()}'\n")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
        ]
        
        if bgm_path and bgm_path.exists():
            cmd.extend(["-i", str(bgm_path)])
            cmd.extend(["-c:v", "copy"])
            cmd.extend(["-c:a", "aac"])
            cmd.extend(["-map", "0:v:0"])
            cmd.extend(["-map", "1:a:0"])
            cmd.extend(["-shortest"])
        else:
            cmd.extend(["-c:v", "copy"])
        
        cmd.append(str(output_path))
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 임시 파일 삭제
        list_file.unlink()
        
        logger.info(f"영상 합성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"영상 합성 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # 테스트 코드
    pass
