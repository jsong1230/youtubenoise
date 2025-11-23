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


def download_image(url: str, output_path: Path, max_retries: int = 3) -> bool:
    """
    URL에서 이미지 다운로드 (재시도 로직 포함)
    
    Args:
        url: 이미지 URL
        output_path: 저장 경로
        max_retries: 최대 재시도 횟수
    
    Returns:
        성공 여부
    """
    import time
    from requests.exceptions import Timeout, ConnectionError, RequestException
    
    retryable_exceptions = (Timeout, ConnectionError, RequestException)
    
    for attempt in range(max_retries + 1):
        try:
            # 타임아웃 설정 (재시도할수록 타임아웃 증가)
            timeout_seconds = 30 + (attempt * 10)  # 30초, 40초, 50초...
            
            if attempt > 0:
                logger.info(f"이미지 다운로드 재시도 ({attempt}/{max_retries}): {url}")
                time.sleep(2 ** attempt)  # 지수 백오프: 2초, 4초, 8초...
            
            response = requests.get(url, timeout=timeout_seconds, stream=True)
            response.raise_for_status()
            
            # 이미지 다운로드 및 처리
            img = Image.open(BytesIO(response.content))
            img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            
            # 출력 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG", optimize=True)
            
            logger.info(f"이미지 다운로드 완료: {output_path}")
            return True
            
        except retryable_exceptions as e:
            if attempt < max_retries:
                logger.warning(
                    f"이미지 다운로드 실패 (시도 {attempt + 1}/{max_retries + 1}): {type(e).__name__}: {e}. "
                    f"재시도 중..."
                )
                continue
            else:
                logger.error(f"이미지 다운로드 최종 실패 ({max_retries + 1}회 시도): {type(e).__name__}: {e}")
                return False
                
        except Exception as e:
            # 재시도 불가능한 에러 (예: 이미지 파싱 에러)
            logger.error(f"이미지 다운로드 실패 (재시도 불가): {type(e).__name__}: {e}")
            return False
    
    return False


def create_text_image(text: str, color_scheme: Dict, font_size: int, 
                      output_path: Path, subtitle: str = None, 
                      text_en: str = None, subtitle_en: str = None,
                      language: str = "ko"):
    """
    텍스트 이미지 생성 (문제 설명, 힌트 등) - 다국어 지원, 텍스트 줄바꿈 포함
    
    Args:
        text: 메인 텍스트 (한글)
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        subtitle: 부제목 (한글, 선택사항)
        text_en: 메인 텍스트 (영어, 선택사항)
        subtitle_en: 부제목 (영어, 선택사항)
        language: 언어 설정 ("ko" 또는 "en")
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        try:
            # 한글 폰트
            font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            subtitle_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", int(font_size * 0.6))
            # 영어 폰트 - 문제 소개 화면과 일관성 유지 (font_size - 10 제거)
            font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            subtitle_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(font_size * 0.6))
        except Exception as e:
            logger.warning(f"폰트 로딩 실패, 기본 폰트 사용: {e}")
            # 기본 폰트 사용 (더 큰 크기로)
            font_ko = ImageFont.load_default()
            subtitle_font_ko = ImageFont.load_default()
            font_en = ImageFont.load_default()
            subtitle_font_en = ImageFont.load_default()
        
        # 언어별로 단일 언어만 표시 (겹침 방지)
        if language == "en":
            # 영어 전용
            font = font_en
            subtitle_font = subtitle_font_en
            text_to_show = text_en if text_en else text
            subtitle_to_show = subtitle_en if subtitle_en else subtitle
        else:
            # 한글 전용
            font = font_ko
            subtitle_font = subtitle_font_ko
            text_to_show = text
            subtitle_to_show = subtitle
        
        # 다국어 텍스트가 있는 경우 (레거시 지원, 하지만 사용하지 않음)
        if text_en and language != "en" and language != "ko":
            # 한글 텍스트 (위) - 줄바꿈 처리
            max_width = 1800
            text_lines_ko = wrap_text(text, font_ko, max_width, "ko")
            text_height_ko = len(text_lines_ko) * int(font_size * 1.3)
            
            y_ko = (1080 - text_height_ko * 2 - 60) // 2  # 영어 공간 확보
            
            # 한글 텍스트 그리기 (여러 줄)
            for i, line in enumerate(text_lines_ko):
                bbox = draw.textbbox((0, 0), line, font=font_ko)
                line_width = bbox[2] - bbox[0]
                x_ko = (1920 - line_width) // 2
                line_y = y_ko + i * int(font_size * 1.3)
                draw.text((x_ko, line_y), line, 
                         fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                         font=font_ko)
            
            # 영어 텍스트 (아래) - 줄바꿈 처리
            text_lines_en = wrap_text(text_en, font_en, max_width, "en")
            text_height_en = len(text_lines_en) * int(font_size * 1.3)
            
            y_en = y_ko + text_height_ko + 30
            
            # 영어 텍스트 그리기 (여러 줄)
            for i, line in enumerate(text_lines_en):
                bbox = draw.textbbox((0, 0), line, font=font_en)
                line_width = bbox[2] - bbox[0]
                x_en = (1920 - line_width) // 2
                line_y = y_en + i * int(font_size * 1.3)
                draw.text((x_en, line_y), line, 
                         fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                         font=font_en)
            
            # 부제목 (한글) - 줄바꿈 처리
            if subtitle:
                subtitle_lines_ko = wrap_text(subtitle, subtitle_font_ko, max_width, "ko")
                sub_y_ko = y_en + text_height_en + 20
                for i, line in enumerate(subtitle_lines_ko):
                    bbox = draw.textbbox((0, 0), line, font=subtitle_font_ko)
                    line_width = bbox[2] - bbox[0]
                    sub_x_ko = (1920 - line_width) // 2
                    line_y = sub_y_ko + i * int((font_size // 2) * 1.3)
                    draw.text((sub_x_ko, line_y), line, 
                             fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                             font=subtitle_font_ko)
            
            # 부제목 (영어) - 줄바꿈 처리
            if subtitle_en:
                subtitle_lines_en = wrap_text(subtitle_en, subtitle_font_en, max_width, "en")
                sub_y_en = y_en + text_height_en + (40 if subtitle else 20)
                for i, line in enumerate(subtitle_lines_en):
                    bbox = draw.textbbox((0, 0), line, font=subtitle_font_en)
                    line_width = bbox[2] - bbox[0]
                    sub_x_en = (1920 - line_width) // 2
                    line_y = sub_y_en + i * int((font_size * 0.6 * 1.3))
                    draw.text((sub_x_en, line_y), line, 
                             fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                             font=subtitle_font_en)
        else:
            # 단일 언어 (줄바꿈 처리) - 언어별로 분리된 처리
            max_width = 1800
            text_lines = wrap_text(text_to_show, font, max_width, language)
            text_height = len(text_lines) * int(font_size * 1.3)
            
            y = (1080 - text_height) // 2 if not subtitle_to_show else (1080 - text_height) // 2 - 50
            
            # 메인 텍스트 그리기 (여러 줄)
            for i, line in enumerate(text_lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x = (1920 - line_width) // 2
                line_y = y + i * int(font_size * 1.3)
                draw.text((x, line_y), line, 
                         fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                         font=font)
            
            # 부제목 - 줄바꿈 처리
            if subtitle_to_show:
                subtitle_lines = wrap_text(subtitle_to_show, subtitle_font, max_width, language)
                sub_y = y + text_height + 40
                subtitle_line_height = int(font_size * 0.6 * 1.3)
                for i, line in enumerate(subtitle_lines):
                    bbox = draw.textbbox((0, 0), line, font=subtitle_font)
                    line_width = bbox[2] - bbox[0]
                    sub_x = (1920 - line_width) // 2
                    line_y = sub_y + i * subtitle_line_height
                    draw.text((sub_x, line_y), line, 
                             fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                             font=subtitle_font)
        
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
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
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
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
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
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
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
            # 12시가 위쪽(-90도), 3시가 오른쪽(0도), 6시가 아래쪽(90도), 9시가 왼쪽(180도)
            # 시계 숫자 위치: 12시 = -90도, 3시 = 0도, 6시 = 90도, 9시 = 180도
            if i == 12:
                angle = -90  # 위쪽
            elif i == 3:
                angle = 0    # 오른쪽
            elif i == 6:
                angle = 90   # 아래쪽
            else:  # 9
                angle = 180  # 왼쪽
            
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


def create_color_display_image(colors: List[Dict], color_scheme: Dict, font_size: int, output_path: Path):
    """
    색상 표시 이미지 생성
    
    Args:
        colors: 색상 리스트 (각각 {"name_ko": str, "name_en": str, "rgb": tuple})
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        num_colors = len(colors)
        box_size = 200
        spacing = 50
        total_width = (box_size + spacing) * num_colors - spacing
        start_x = (1920 - total_width) // 2
        y = 1080 // 2 - box_size // 2
        
        for i, color_info in enumerate(colors):
            x = start_x + i * (box_size + spacing)
            rgb = color_info.get('rgb', (255, 255, 255))
            
            # RGB 튜플이 리스트인 경우 튜플로 변환
            if isinstance(rgb, list):
                rgb = tuple(rgb)
            
            # 색상 박스 그리기 (더 명확한 테두리와 그림자)
            # 그림자 효과
            shadow_offset = 5
            draw.rectangle([x + shadow_offset, y + shadow_offset, 
                          x + box_size + shadow_offset, y + box_size + shadow_offset], 
                         fill=(100, 100, 100), outline=(100, 100, 100))
            
            # 메인 색상 박스
            draw.rectangle([x, y, x + box_size, y + box_size], 
                         fill=rgb, outline=(0, 0, 0), width=8)
            
            # 내부 테두리 (색상 대비 강화)
            inner_border = 10
            # 밝은 색상인 경우 어두운 테두리, 어두운 색상인 경우 밝은 테두리
            avg_brightness = sum(rgb) / 3
            border_color = (0, 0, 0) if avg_brightness > 128 else (255, 255, 255)
            draw.rectangle([x + inner_border, y + inner_border, 
                          x + box_size - inner_border, y + box_size - inner_border], 
                         outline=border_color, width=3)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"색상 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"색상 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_direction_display_image(directions: List[Dict], color_scheme: Dict, font_size: int, output_path: Path):
    """
    방향 표시 이미지 생성
    
    Args:
        directions: 방향 리스트 (각각 {"name_ko": str, "name_en": str, "symbol": str})
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size * 2)
        except:
            font = ImageFont.load_default()
        
        num_directions = len(directions)
        arrow_size = 150
        spacing = 80
        total_width = (arrow_size + spacing) * num_directions - spacing
        start_x = (1920 - total_width) // 2
        y = 1080 // 2 - arrow_size // 2
        
        for i, direction_info in enumerate(directions):
            x = start_x + i * (arrow_size + spacing)
            symbol = direction_info['symbol']
            
            # 화살표 텍스트 그리기
            text = symbol
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = x + (arrow_size - text_width) // 2
            text_y = y + (arrow_size - text_height) // 2
            
            # 그림자
            shadow_offset = 5
            draw.text((text_x + shadow_offset, text_y + shadow_offset), text,
                     fill=(150, 150, 150), font=font)
            
            # 메인 텍스트
            draw.text((text_x, text_y), text,
                     fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"방향 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"방향 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_calculation_display_image(num1: int, num2: int, operation: str, color_scheme: Dict, font_size: int, output_path: Path, language: str = "ko"):
    """
    계산 문제 표시 이미지 생성
    
    Args:
        num1: 첫 번째 숫자
        num2: 두 번째 숫자
        operation: 연산 기호 (+, -)
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        language: 언어 설정 ("ko" 또는 "en")
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        # 계산 문제는 시니어 분들의 시력을 고려하여 폰트 크기를 더 크게 설정
        # 기본 폰트 크기의 1.5배로 설정 (84 -> 126, 96 -> 144 등)
        calculation_font_size = int(font_size * 1.5)
        
        try:
            # 문제 소개 화면과 동일한 폰트 사용 (언어별로, 크기만 더 크게)
            if language == "en":
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", calculation_font_size)
            else:
                # 한글 폰트 - 계산 문제는 더 큰 폰트 사용
                font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", calculation_font_size)
        except Exception as e:
            logger.warning(f"폰트 로딩 실패, 기본 폰트 사용: {e}")
            font = ImageFont.load_default()
        
        # 계산식 텍스트 (더 큰 폰트로 표시)
        text = f"{num1} {operation} {num2} = ?"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height_actual = bbox[3] - bbox[1]
        
        # 화면 중앙에 배치 (더 큰 폰트에 맞춰 위치 조정)
        text_height = int(calculation_font_size * 1.3)  # 더 큰 폰트에 맞춘 줄 높이
        y = (1080 - text_height) // 2  # 화면 중앙
        
        x = (1920 - text_width) // 2
        
        # 텍스트 위치 고정 (문제 소개 화면과 완전히 동일한 위치)
        draw.text((x, y), text,
                 fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"계산 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"계산 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_pattern_sequence_image(pattern_text: str, choices_text: str, color_scheme: Dict, 
                                  font_size: int, output_path: Path, language: str = "ko"):
    """
    패턴 시퀀스 문제 표시 이미지 생성 (줄바꿈 없이 한 줄로 표시)
    
    Args:
        pattern_text: 패턴 텍스트 (예: "5 -> 10 -> 15 -> 20 -> ?")
        choices_text: 선택지 텍스트 (예: "25 / 30 / 35")
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        language: 언어 설정 ("ko" 또는 "en")
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        # 언어에 따라 폰트 선택 (한글 지원 여부에 따라)
        font = None
        subtitle_font = None
        
        if language == "en":
            # 영어 버전: Helvetica (숫자, 문자, 기호 렌더링 안정적)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(font_size * 0.7))
            except Exception as e:
                logger.warning(f"Helvetica 폰트 로딩 실패, 대체 폰트 시도: {e}")
                try:
                    # 대체 영어 폰트
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", int(font_size * 0.7))
                except:
                    font = ImageFont.load_default()
                    subtitle_font = ImageFont.load_default()
        else:
            # 한글 버전: AppleSDGothicNeo (한글, 숫자, 문자 모두 지원)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
                subtitle_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", int(font_size * 0.7))
            except Exception as e:
                logger.warning(f"AppleSDGothicNeo 폰트 로딩 실패, 대체 폰트 시도: {e}")
                try:
                    # 대체 한글 폰트
                    font = ImageFont.truetype("/System/Library/Fonts/AppleGothic.ttf", font_size)
                    subtitle_font = ImageFont.truetype("/System/Library/Fonts/AppleGothic.ttf", int(font_size * 0.7))
                except:
                    try:
                        # 또 다른 대체 한글 폰트
                        font = ImageFont.truetype("/Library/Fonts/AppleGothic.ttf", font_size)
                        subtitle_font = ImageFont.truetype("/Library/Fonts/AppleGothic.ttf", int(font_size * 0.7))
                    except:
                        logger.error(f"모든 한글 폰트 로딩 실패, 기본 폰트 사용 (한글 깨짐 가능)")
                        font = ImageFont.load_default()
                        subtitle_font = ImageFont.load_default()
        
        # 패턴 텍스트 (한 줄로 표시, 줄바꿈 없음)
        bbox = draw.textbbox((0, 0), pattern_text, font=font)
        pattern_width = bbox[2] - bbox[0]
        pattern_height = bbox[3] - bbox[1]
        
        # 화면 중앙에 패턴 텍스트 배치
        pattern_x = (1920 - pattern_width) // 2
        pattern_y = (1080 - pattern_height) // 2 - 60  # 선택지 공간 확보
        
        draw.text((pattern_x, pattern_y), pattern_text,
                 fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font)
        
        # 선택지 텍스트 (패턴 아래에 표시)
        if choices_text:
            subtitle_label = "Options: " if language == "en" else "선택지: "
            full_subtitle = subtitle_label + choices_text
            
            bbox = draw.textbbox((0, 0), full_subtitle, font=subtitle_font)
            subtitle_width = bbox[2] - bbox[0]
            subtitle_height = bbox[3] - bbox[1]
            
            subtitle_x = (1920 - subtitle_width) // 2
            subtitle_y = pattern_y + pattern_height + 40
            
            draw.text((subtitle_x, subtitle_y), full_subtitle,
                     fill=tuple(color_scheme.get('text', [40, 40, 40])), font=subtitle_font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"패턴 시퀀스 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"패턴 시퀀스 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_category_display_image(category: str, items: List[str], color_scheme: Dict, font_size: int, output_path: Path, languages: List[str] = None, problem_data: Dict = None):
    """
    카테고리 분류 문제 표시 이미지 생성
    
    Args:
        category: 카테고리 이름 (기본값, 언어별로 오버라이드 가능)
        items: 항목 리스트 (기본값, 언어별로 오버라이드 가능)
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        languages: 언어 리스트
        problem_data: 문제 데이터 (category_ko, category_en, items_ko, items_en 포함)
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        # 언어 설정 확인
        use_language = languages[0] if languages else "ko"
        
        # 언어에 따라 카테고리와 항목 선택
        if use_language == "en":
            # 영어 버전: 영어 카테고리와 항목 사용 (절대 한글 사용 안 함)
            if problem_data:
                # category_en이 있으면 사용, 없으면 category 사용 (하지만 category가 한글일 수 있으므로 주의)
                display_category = problem_data.get('category_en')
                if not display_category:
                    # category_en이 없으면 category를 사용하되, 한글이 아닌지 확인
                    fallback_category = problem_data.get('category', category)
                    # 한글 문자 체크 (유니코드 범위: AC00-D7A3)
                    if any('\uAC00' <= char <= '\uD7A3' for char in str(fallback_category)):
                        logger.error(f"영어 버전인데 한글 카테고리가 전달됨: {fallback_category}")
                        display_category = "Category"  # 폴백
                    else:
                        display_category = fallback_category
                
                display_items = problem_data.get('items_en')
                if not display_items:
                    fallback_items = problem_data.get('items', items)
                    # 한글 체크
                    if fallback_items and any(any('\uAC00' <= char <= '\uD7A3' for char in str(item)) for item in fallback_items):
                        logger.error(f"영어 버전인데 한글 항목이 전달됨: {fallback_items}")
                        display_items = []  # 폴백
                    else:
                        display_items = fallback_items
            else:
                # problem_data가 없으면 전달받은 category, items 사용 (한글 체크)
                if any('\uAC00' <= char <= '\uD7A3' for char in str(category)):
                    logger.error(f"영어 버전인데 한글 카테고리가 전달됨: {category}")
                    display_category = "Category"
                else:
                    display_category = category
                
                if items and any(any('\uAC00' <= char <= '\uD7A3' for char in str(item)) for item in items):
                    logger.error(f"영어 버전인데 한글 항목이 전달됨: {items}")
                    display_items = []
                else:
                    display_items = items
            
            # 영어 폰트 사용
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                item_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(font_size * 0.8))
            except Exception as e:
                logger.warning(f"영어 폰트 로딩 실패, 기본 폰트 사용: {e}")
                font = ImageFont.load_default()
                item_font = font
            
            category_text = f"Category: {display_category}"
        else:
            # 한글 버전: 한글 카테고리와 항목 사용
            if problem_data:
                display_category = problem_data.get('category_ko') or problem_data.get('category', category)
                display_items = problem_data.get('items_ko') or problem_data.get('items', items)
            else:
                display_category = category
                display_items = items
            
            # 한글 폰트 사용
            try:
                font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
                item_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", int(font_size * 0.8))
            except Exception as e:
                logger.warning(f"한글 폰트 로딩 실패, 기본 폰트 사용: {e}")
                font = ImageFont.load_default()
                item_font = font
            
            category_text = f"카테고리: {display_category}"
        
        # 카테고리 텍스트 표시
        bbox = draw.textbbox((0, 0), category_text, font=font)
        category_width = bbox[2] - bbox[0]
        category_x = (1920 - category_width) // 2
        category_y = 200
        
        draw.text((category_x, category_y), category_text,
                 fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font)
        
        # 항목 리스트 표시 (줄바꿈 처리)
        max_width = 1800
        items_lines = []
        for i, item in enumerate(display_items):
            item_text = f"{i+1}. {item}"
            item_lines = wrap_text(item_text, item_font, max_width, use_language)
            items_lines.extend(item_lines)
        
        items_y = category_y + 150
        item_line_height = int(font_size * 0.8 * 1.3)
        
        for i, line in enumerate(items_lines):
            bbox = draw.textbbox((0, 0), line, font=item_font)
            line_width = bbox[2] - bbox[0]
            line_x = (1920 - line_width) // 2
            line_y = items_y + i * item_line_height
            draw.text((line_x, line_y), line,
                     fill=tuple(color_scheme.get('text', [40, 40, 40])), font=item_font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"카테고리 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"카테고리 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_shape_matching_image(target_shape: str, target_color: Dict, choices: List[Dict], 
                                color_scheme: Dict, font_size: int, output_path: Path, language: str = "ko"):
    """
    도형 매칭 문제 표시 이미지 생성
    
    Args:
        target_shape: 타겟 도형 타입
        target_color: 타겟 색상 {"name_ko": str, "name_en": str, "rgb": tuple}
        choices: 선택지 리스트 (각각 {"shape": str, "color": Dict, "is_correct": bool})
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        language: 언어 설정 ("ko" 또는 "en")
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        try:
            # 언어별 폰트 선택
            if language == "en":
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            else:
                font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
        except:
            font = ImageFont.load_default()
        
        # 도형 이름 변환 (언어별)
        shape_names_ko = {
            "circle": "원",
            "square": "사각형",
            "triangle": "삼각형",
            "rectangle": "직사각형",
            "star": "별",
            "diamond": "다이아몬드"
        }
        shape_names_en = {
            "circle": "Circle",
            "square": "Square",
            "triangle": "Triangle",
            "rectangle": "Rectangle",
            "star": "Star",
            "diamond": "Diamond"
        }
        
        # 타겟 도형 표시 (상단 중앙)
        target_size = 150
        target_x = 1920 // 2 - target_size // 2
        target_y = 200
        
        target_rgb = target_color['rgb']
        
        # 타겟 도형 그리기
        if target_shape == "circle":
            draw.ellipse([target_x, target_y, target_x + target_size, target_y + target_size],
                        fill=target_rgb, outline=(0, 0, 0), width=5)
        elif target_shape == "square":
            draw.rectangle([target_x, target_y, target_x + target_size, target_y + target_size],
                          fill=target_rgb, outline=(0, 0, 0), width=5)
        elif target_shape == "triangle":
            points = [
                (target_x + target_size // 2, target_y),
                (target_x, target_y + target_size),
                (target_x + target_size, target_y + target_size)
            ]
            draw.polygon(points, fill=target_rgb, outline=(0, 0, 0))
        elif target_shape == "rectangle":
            rect_width = target_size * 1.5
            rect_height = target_size
            draw.rectangle([target_x, target_y, target_x + rect_width, target_y + rect_height],
                          fill=target_rgb, outline=(0, 0, 0), width=5)
        elif target_shape == "star":
            # 별 그리기 (간단한 5각형)
            center_x = target_x + target_size // 2
            center_y = target_y + target_size // 2
            radius = target_size // 2
            points = []
            for i in range(5):
                angle = math.radians(i * 144 - 90)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            draw.polygon(points, fill=target_rgb, outline=(0, 0, 0))
        elif target_shape == "diamond":
            center_x = target_x + target_size // 2
            center_y = target_y + target_size // 2
            points = [
                (center_x, target_y),
                (target_x + target_size, center_y),
                (center_x, target_y + target_size),
                (target_x, center_y)
            ]
            draw.polygon(points, fill=target_rgb, outline=(0, 0, 0))
        
        # 타겟 설명 텍스트 (언어별)
        if language == "en":
            color_name = target_color.get('name_en', target_color.get('name_ko', ''))
            shape_name = shape_names_en.get(target_shape, target_shape)
        else:
            color_name = target_color.get('name_ko', target_color.get('name_en', ''))
            shape_name = shape_names_ko.get(target_shape, target_shape)
        
        target_text = f"{color_name} {shape_name}"
        bbox = draw.textbbox((0, 0), target_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (1920 - text_width) // 2
        text_y = target_y + target_size + 30
        draw.text((text_x, text_y), target_text,
                 fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font)
        
        # 선택지 도형들 (하단에 배치)
        num_choices = len(choices)
        choice_size = 120
        spacing = 60
        total_width = (choice_size + spacing) * num_choices - spacing
        start_x = (1920 - total_width) // 2
        choice_y = 600
        
        for i, choice in enumerate(choices):
            x = start_x + i * (choice_size + spacing)
            shape = choice['shape']
            color_rgb = choice['color']['rgb']
            
            # 도형 그리기
            if shape == "circle":
                draw.ellipse([x, choice_y, x + choice_size, choice_y + choice_size],
                            fill=color_rgb, outline=(0, 0, 0), width=3)
            elif shape == "square":
                draw.rectangle([x, choice_y, x + choice_size, choice_y + choice_size],
                              fill=color_rgb, outline=(0, 0, 0), width=3)
            elif shape == "triangle":
                points = [
                    (x + choice_size // 2, choice_y),
                    (x, choice_y + choice_size),
                    (x + choice_size, choice_y + choice_size)
                ]
                draw.polygon(points, fill=color_rgb, outline=(0, 0, 0))
            elif shape == "rectangle":
                rect_width = choice_size * 1.3
                rect_height = choice_size
                draw.rectangle([x, choice_y, x + rect_width, choice_y + rect_height],
                              fill=color_rgb, outline=(0, 0, 0), width=3)
            elif shape == "star":
                center_x = x + choice_size // 2
                center_y = choice_y + choice_size // 2
                radius = choice_size // 2
                points = []
                for j in range(5):
                    angle = math.radians(j * 144 - 90)
                    px = center_x + radius * math.cos(angle)
                    py = center_y + radius * math.sin(angle)
                    points.append((px, py))
                draw.polygon(points, fill=color_rgb, outline=(0, 0, 0))
            elif shape == "diamond":
                center_x = x + choice_size // 2
                center_y = choice_y + choice_size // 2
                points = [
                    (center_x, choice_y),
                    (x + choice_size, center_y),
                    (center_x, choice_y + choice_size),
                    (x, center_y)
                ]
                draw.polygon(points, fill=color_rgb, outline=(0, 0, 0))
            
            # 번호 표시
            num_text = str(i + 1)
            bbox = draw.textbbox((0, 0), num_text, font=font)
            num_width = bbox[2] - bbox[0]
            num_height = bbox[3] - bbox[1]
            num_x = x + (choice_size - num_width) // 2
            num_y = choice_y + choice_size + 20
            draw.text((num_x, num_y), num_text,
                     fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.debug(f"도형 매칭 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"도형 매칭 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_gradient_background(color_scheme: Dict, width: int = 1920, height: int = 1080) -> Image.Image:
    """
    그라데이션 배경 이미지 생성 (효율적인 방법)
    
    Args:
        color_scheme: 색상 스킴
        width: 이미지 너비
        height: 이미지 높이
    
    Returns:
        배경 이미지
    """
    bg_color = tuple(color_scheme.get('background', [245, 240, 235]))
    
    # 그라데이션을 위한 시작/끝 색상 (더 명확한 변화)
    start_color = tuple(max(0, min(255, c - 15)) for c in bg_color)  # 상단: 더 밝게
    end_color = tuple(max(0, min(255, c + 25)) for c in bg_color)  # 하단: 더 어둡게
    
    # 효율적인 그라데이션 생성 (numpy 스타일, 하지만 PIL만 사용)
    # 1픽셀 높이의 이미지를 여러 개 만들어서 합치기
    gradient_strip = Image.new('RGB', (width, 1))
    gradient_pixels = []
    
    for x in range(width):
        # 수평 그라데이션도 약간 추가
        ratio_x = x / width
        ratio_y = 0.5  # 중간값 사용
        
        r = int(start_color[0] * (1 - ratio_y) + end_color[0] * ratio_y)
        g = int(start_color[1] * (1 - ratio_y) + end_color[1] * ratio_y)
        b = int(start_color[2] * (1 - ratio_y) + end_color[2] * ratio_y)
        gradient_pixels.append((r, g, b))
    
    gradient_strip.putdata(gradient_pixels)
    
    # 수직 그라데이션을 위해 여러 줄 생성
    img = Image.new('RGB', (width, height))
    for y in range(height):
        ratio = y / height
        # 각 줄의 색상 계산
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        
        # 한 줄씩 그리기 (더 효율적)
        line_img = Image.new('RGB', (width, 1), (r, g, b))
        img.paste(line_img, (0, y))
    
    # 미묘한 패턴 추가
    draw = ImageDraw.Draw(img)
    
    # 상단/하단에 미묘한 선 추가
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # 상단 선 (더 부드러운 그라데이션)
    for i in range(5):
        alpha = max(0, 15 - i * 3)
        overlay_draw.rectangle([0, i, width, i + 1], fill=(0, 0, 0, alpha))
    
    # 하단 선
    for i in range(5):
        alpha = max(0, 15 - i * 3)
        overlay_draw.rectangle([0, height - 5 + i, width, height - 5 + i + 1], fill=(0, 0, 0, alpha))
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    return img


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, language: str = "ko") -> List[str]:
    """
    텍스트를 주어진 너비에 맞게 줄바꿈 (한글/영어 모두 지원)
    
    Args:
        text: 원본 텍스트
        font: 폰트
        max_width: 최대 너비
        language: 언어 ("ko" 또는 "en")
    
    Returns:
        줄바꿈된 텍스트 리스트
    """
    # 한글의 경우 공백 없이도 줄바꿈 필요
    if language == "ko" or any('\uAC00' <= char <= '\uD7A3' for char in text):
        # 한글 처리: 문자 단위로 줄바꿈
        lines = []
        current_line = ""
        
        for char in text:
            test_line = current_line + char
            # 임시 이미지로 텍스트 크기 측정
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    else:
        # 영어 처리: 단어 단위로 줄바꿈
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
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
                       answer_en: str = None, explanation_en: str = None,
                       language: str = "ko"):
    """
    정답 화면 이미지 생성 (긴 텍스트 자동 줄바꿈, 다국어 지원)
    
    Args:
        answer_text: 정답 텍스트
        explanation: 설명
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        answer_en: 정답 텍스트 (영어, 선택사항)
        explanation_en: 설명 (영어, 선택사항)
        language: 언어 설정 ("ko" 또는 "en")
    """
    try:
        # 그라데이션 배경 생성
        img = create_gradient_background(color_scheme)
        draw = ImageDraw.Draw(img)
        
        try:
            # 한글 폰트
            title_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            answer_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size * 2)
            exp_font_ko = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size // 2)
            # 영어 폰트 - 문제 소개 화면과 일관성 유지 (font_size - 10 제거)
            title_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            answer_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(font_size * 1.8))
            exp_font_en = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size // 2)
        except Exception as e:
            logger.warning(f"폰트 로딩 실패, 기본 폰트 사용: {e}")
            title_font_ko = answer_font_ko = exp_font_ko = ImageFont.load_default()
            title_font_en = answer_font_en = exp_font_en = ImageFont.load_default()
        
        # 1. 상단: 제목 표시
        title_y = 80
        if language == "en":
            title = "Answer"
            title_font = title_font_en
        else:
            title = "정답"
            title_font = title_font_ko
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        title_height = bbox[3] - bbox[1]
        draw.text(((1920 - title_width) // 2, title_y), title, 
                 fill=tuple(color_scheme.get('correct', [80, 160, 80])), 
                 font=title_font)
        
        # 2. 하단: 설명 높이 계산 (먼저 계산하여 중앙 계산에 사용)
        exp_max_width = 1800
        if language == "en":
            exp_font = exp_font_en
            explanation_to_show = explanation
            exp_line_height = int(font_size * 1.3)
        else:
            exp_font = exp_font_ko
            explanation_to_show = explanation
            exp_line_height = int(font_size * 1.5)
        
        exp_lines = wrap_text(str(explanation_to_show), exp_font, exp_max_width, language)
        exp_total_height = len(exp_lines) * exp_line_height
        exp_bottom_y = 1080 - 80  # 하단 여백 80px
        exp_start_y = exp_bottom_y - exp_total_height
        
        # 3. 중앙: 정답 텍스트 (제목과 설명 사이의 중앙에 배치)
        answer_max_width = 1800
        if language == "en":
            answer_font = answer_font_en
            answer_text_to_show = answer_text
            answer_line_height = int(font_size * 2.2)
        else:
            answer_font = answer_font_ko
            answer_text_to_show = answer_text
            answer_line_height = int(font_size * 2.5)
        
        answer_lines = wrap_text(str(answer_text_to_show), answer_font, answer_max_width, language)
        answer_total_height = len(answer_lines) * answer_line_height
        
        # 정답을 제목과 설명 사이의 중앙에 배치
        title_bottom = title_y + title_height + 40  # 제목 하단 + 여백
        available_space = exp_start_y - title_bottom
        answer_start_y = title_bottom + (available_space - answer_total_height) // 2
        
        # 정답 텍스트 그리기
        answer_y = answer_start_y
        for line in answer_lines:
            bbox = draw.textbbox((0, 0), line, font=answer_font)
            line_width = bbox[2] - bbox[0]
            draw.text(((1920 - line_width) // 2, answer_y), line, 
                     fill=tuple(color_scheme.get('highlight', [100, 150, 200])), 
                     font=answer_font)
            answer_y += answer_line_height
        
        # 4. 하단: 설명 텍스트 그리기
        exp_y = exp_start_y
        for line in exp_lines:
            bbox = draw.textbbox((0, 0), line, font=exp_font)
            line_width = bbox[2] - bbox[0]
            draw.text(((1920 - line_width) // 2, exp_y), line, 
                     fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                     font=exp_font)
            exp_y += exp_line_height
        
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
        
        # 계산 문제는 소개 화면부터 큰 폰트 사용 (시니어 분들의 시력 고려)
        intro_font_size = int(font_size * 1.5) if module == "simple_calculation" else font_size
        
        create_text_image(
            problem_text,
            color_scheme,
            intro_font_size,
            intro_path,
            text_en=problem_text_en,
            language=use_language
        )
        intro_clip = output_dir / f"problem_{problem_num}_intro.mp4"
        # 문제 소개 화면 시간: 프리셋에서 설정 가능 (기본값 3초, 30분 영상은 5초)
        intro_duration = preset.get('problem_intro_duration', 3)
        create_image_clip(intro_path, intro_duration, intro_clip)
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
            preset_languages = preset.get('languages', ['ko'])
            use_language = preset_languages[0] if preset_languages else 'ko'
            
            # 언어에 따라 적절한 패턴과 선택지 선택
            if use_language == "en":
                # 영어 버전: 영어 패턴과 선택지 사용
                pattern = problem_data['problem_data'].get('pattern_en') or problem_data['problem_data'].get('pattern', [])
                choices = problem_data['problem_data'].get('choices_en') or problem_data['problem_data'].get('choices', [])
                # 한글 체크 및 빈 리스트 체크
                if not pattern:
                    logger.error(f"영어 버전인데 패턴이 비어있음")
                    pattern = ["?", "?", "?", "?"]
                elif any(any('\uAC00' <= char <= '\uD7A3' for char in str(p)) for p in pattern):
                    logger.error(f"영어 버전인데 한글 패턴 전달됨: {pattern}")
                    pattern = ["?", "?", "?", "?"]
                if not choices:
                    logger.error(f"영어 버전인데 선택지가 비어있음")
                    choices = ["?", "?", "?"]
                elif any(any('\uAC00' <= char <= '\uD7A3' for char in str(c)) for c in choices):
                    logger.error(f"영어 버전인데 한글 선택지 전달됨: {choices}")
                    choices = ["?", "?", "?"]
            else:
                # 한글 버전: 한글 패턴과 선택지 사용
                pattern = problem_data['problem_data'].get('pattern_ko') or problem_data['problem_data'].get('pattern', [])
                choices = problem_data['problem_data'].get('choices_ko') or problem_data['problem_data'].get('choices', [])
                if not pattern:
                    logger.error(f"한글 버전인데 패턴이 비어있음")
                    pattern = ["?", "?", "?", "?"]
                if not choices:
                    logger.error(f"한글 버전인데 선택지가 비어있음")
                    choices = ["?", "?", "?"]
            
            # 패턴 데이터 검증 및 로깅
            logger.info(f"패턴 데이터: {pattern}, 타입: {type(pattern)}")
            logger.info(f"선택지 데이터: {choices}, 타입: {type(choices)}")
            
            # 패턴이 리스트가 아닌 경우 처리
            if not isinstance(pattern, list):
                logger.error(f"패턴이 리스트가 아님: {pattern}, 타입: {type(pattern)}")
                pattern = [str(pattern)] if pattern else ["?", "?", "?", "?"]
            if not isinstance(choices, list):
                logger.error(f"선택지가 리스트가 아님: {choices}, 타입: {type(choices)}")
                choices = [str(choices)] if choices else ["?", "?", "?"]
            
            # 빈 리스트 체크
            if not pattern or len(pattern) == 0:
                logger.error(f"패턴이 비어있음")
                pattern = ["A", "B", "C", "D"]  # 기본값
            if not choices or len(choices) == 0:
                logger.error(f"선택지가 비어있음")
                choices = ["E", "F", "G"]  # 기본값
            
            # 패턴 텍스트 생성: 특수 문자 대신 간단한 화살표 사용
            pattern_text = " -> ".join(str(p) for p in pattern) + " -> ?"
            choices_text = " / ".join(str(c) for c in choices)
            
            logger.info(f"생성된 패턴 텍스트: {pattern_text}")
            logger.info(f"생성된 선택지 텍스트: {choices_text}")
            
            pattern_path = output_dir / f"problem_{problem_num}_pattern.png"
            
            # 패턴 시퀀스는 별도 함수로 직접 렌더링 (줄바꿈 없이 한 줄로)
            create_pattern_sequence_image(
                pattern_text,
                choices_text,
                color_scheme,
                font_size,
                pattern_path,
                language=use_language
            )
            pattern_clip = output_dir / f"problem_{problem_num}_pattern.mp4"
            create_image_clip(pattern_path, problem_data['display_seconds'], pattern_clip)
            clips.append(pattern_clip)
            
        elif module == "word_association":
            # 단어 연상 문제 표시
            keyword = problem_data['problem_data'].get('keyword', '')
            choices = problem_data['problem_data'].get('choices', [])
            
            # 언어 설정 확인
            preset_languages = preset.get('languages', ['ko'])
            use_language = preset_languages[0] if preset_languages else 'ko'
            
            if use_language == 'en':
                question_text = f"Which word is related to '{keyword}'?"
                question_text_ko = None
                choices_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(choices)])
                choices_text_en = choices_text
            else:
                question_text = f"'{keyword}'와 관련된 단어는?"
                question_text_ko = question_text
                choices_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(choices)])
                choices_text_en = None
            
            word_path = output_dir / f"problem_{problem_num}_word.png"
            create_text_image(
                question_text,
                color_scheme,
                font_size,
                word_path,
                subtitle=choices_text,
                text_en=question_text_ko if use_language == 'en' else None,
                subtitle_en=choices_text_en if use_language == 'en' else None,
                language=use_language
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
            
        elif module == "color_memory":
            # 색상 표시 이미지 생성
            colors = problem_data['problem_data'].get('colors', [])
            color_path = output_dir / f"problem_{problem_num}_color.png"
            create_color_display_image(colors, color_scheme, font_size, color_path)
            color_clip = output_dir / f"problem_{problem_num}_color.mp4"
            create_image_clip(color_path, problem_data['display_seconds'], color_clip)
            clips.append(color_clip)
            
        elif module == "simple_calculation":
            # 계산 문제 표시 이미지 생성
            num1 = problem_data['problem_data'].get('num1', 0)
            num2 = problem_data['problem_data'].get('num2', 0)
            operation = problem_data['problem_data'].get('operation', '+')
            calc_path = output_dir / f"problem_{problem_num}_calc.png"
            # 언어 파라미터 전달 (프리셋에서 가져오기)
            preset_language = preset.get('languages', ['ko'])[0] if isinstance(preset.get('languages', ['ko']), list) else preset.get('languages', 'ko')
            create_calculation_display_image(num1, num2, operation, color_scheme, font_size, calc_path, language=preset_language)
            calc_clip = output_dir / f"problem_{problem_num}_calc.mp4"
            create_image_clip(calc_path, problem_data['display_seconds'], calc_clip)
            clips.append(calc_clip)
            
        elif module == "direction_memory":
            # 방향 표시 이미지 생성
            directions = problem_data['problem_data'].get('directions', [])
            direction_path = output_dir / f"problem_{problem_num}_direction.png"
            create_direction_display_image(directions, color_scheme, font_size, direction_path)
            direction_clip = output_dir / f"problem_{problem_num}_direction.mp4"
            create_image_clip(direction_path, problem_data['display_seconds'], direction_clip)
            clips.append(direction_clip)
            
        elif module == "category_classification":
            # 카테고리 분류 문제 표시
            preset_languages = preset.get('languages', ['ko'])
            use_language = preset_languages[0] if preset_languages else 'ko'
            
            # 언어에 따라 적절한 카테고리와 항목 선택
            if use_language == "en":
                # 영어 버전: 영어 데이터 우선 사용
                category = problem_data['problem_data'].get('category_en') or problem_data['problem_data'].get('category', '')
                items = problem_data['problem_data'].get('items_en') or problem_data['problem_data'].get('items', [])
                # 한글 체크
                if any('\uAC00' <= char <= '\uD7A3' for char in str(category)):
                    logger.error(f"영어 버전인데 한글 카테고리 전달됨: {category}")
                    category = "Category"
                if items and any(any('\uAC00' <= char <= '\uD7A3' for char in str(item)) for item in items):
                    logger.error(f"영어 버전인데 한글 항목 전달됨: {items}")
                    items = []
            else:
                # 한글 버전: 한글 데이터 우선 사용
                category = problem_data['problem_data'].get('category_ko') or problem_data['problem_data'].get('category', '')
                items = problem_data['problem_data'].get('items_ko') or problem_data['problem_data'].get('items', [])
            
            category_path = output_dir / f"problem_{problem_num}_category.png"
            create_category_display_image(category, items, color_scheme, font_size, category_path, preset_languages, problem_data['problem_data'])
            category_clip = output_dir / f"problem_{problem_num}_category.mp4"
            create_image_clip(category_path, problem_data['display_seconds'], category_clip)
            clips.append(category_clip)
            
        elif module == "shape_matching":
            # 도형 매칭 문제 표시
            target_shape = problem_data['problem_data'].get('target_shape', 'circle')
            target_color = problem_data['problem_data'].get('target_color', {})
            choices = problem_data['problem_data'].get('choices', [])
            shape_path = output_dir / f"problem_{problem_num}_shape.png"
            # 언어 파라미터 전달
            preset_language = preset.get('languages', ['ko'])[0] if isinstance(preset.get('languages', ['ko']), list) else preset.get('languages', 'ko')
            create_shape_matching_image(target_shape, target_color, choices, color_scheme, font_size, shape_path, language=preset_language)
            shape_clip = output_dir / f"problem_{problem_num}_shape.mp4"
            create_image_clip(shape_path, problem_data['display_seconds'], shape_clip)
            clips.append(shape_clip)
        
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
            explanation_en=explanation_en,
            language=use_language
        )
        
        answer_clip = output_dir / f"problem_{problem_num}_answer.mp4"
        # 정답 화면 시간: 30분 영상의 경우 10초로 증가 (기본값 5초)
        answer_duration = preset.get('answer_display_duration', 10)
        create_image_clip(answer_path, answer_duration, answer_clip)
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
            # BGM을 루프로 반복하여 영상 길이만큼 재생
            cmd.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
            cmd.extend(["-c:v", "copy"])
            cmd.extend(["-c:a", "aac"])
            cmd.extend(["-b:a", "128k"])  # 오디오 비트레이트 설정
            cmd.extend(["-map", "0:v:0"])
            cmd.extend(["-map", "1:a:0"])
            cmd.extend(["-af", "volume=0.3"])  # BGM 볼륨을 30%로 낮춤 (집중 방해 최소화)
            # -shortest 제거: 영상 길이에 맞춰 BGM을 루프로 반복
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
