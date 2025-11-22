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
                      output_path: Path, subtitle: str = None):
    """
    텍스트 이미지 생성 (문제 설명, 힌트 등)
    
    Args:
        text: 메인 텍스트
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
        subtitle: 부제목 (선택사항)
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [245, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size // 2)
        except:
            font = ImageFont.load_default()
            subtitle_font = font
        
        # 메인 텍스트
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2 if not subtitle else (1080 - text_height) // 2 - 50
        
        draw.text((x, y), text, fill=tuple(color_scheme.get('text', [40, 40, 40])), font=font)
        
        # 부제목
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            sub_width = bbox[2] - bbox[0]
            sub_x = (1920 - sub_width) // 2
            sub_y = y + text_height + 40
            draw.text((sub_x, sub_y), subtitle, 
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


def create_answer_image(answer_text: str, explanation: str, color_scheme: Dict, 
                       font_size: int, output_path: Path):
    """
    정답 화면 이미지 생성
    
    Args:
        answer_text: 정답 텍스트
        explanation: 설명
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 경로
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [245, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            answer_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size * 2)
            exp_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size // 2)
        except:
            title_font = answer_font = exp_font = ImageFont.load_default()
        
        # "정답" 제목
        title = "정답"
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        draw.text(((1920 - title_width) // 2, 200), title, 
                 fill=tuple(color_scheme.get('correct', [80, 160, 80])), 
                 font=title_font)
        
        # 정답 텍스트
        bbox = draw.textbbox((0, 0), answer_text, font=answer_font)
        answer_width = bbox[2] - bbox[0]
        draw.text(((1920 - answer_width) // 2, 400), answer_text, 
                 fill=tuple(color_scheme.get('highlight', [100, 150, 200])), 
                 font=answer_font)
        
        # 설명
        bbox = draw.textbbox((0, 0), explanation, font=exp_font)
        exp_width = bbox[2] - bbox[0]
        draw.text(((1920 - exp_width) // 2, 700), explanation, 
                 fill=tuple(color_scheme.get('text', [40, 40, 40])), 
                 font=exp_font)
        
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
        
        # 1. 문제 소개 화면
        intro_path = output_dir / f"problem_{problem_num}_intro.png"
        create_text_image(
            problem_data['problem_text'],
            color_scheme,
            font_size,
            intro_path
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
            # 이미지 다운로드 및 클립 생성
            base_img_path = output_dir / f"problem_{problem_num}_base.png"
            modified_img_path = output_dir / f"problem_{problem_num}_modified.png"
            
            download_image(problem_data['problem_data']['base_image_url'], base_img_path)
            download_image(problem_data['problem_data']['modified_image_url'], modified_img_path)
            
            # 비교 화면 클립
            comparison_clip = output_dir / f"problem_{problem_num}_comparison.mp4"
            create_image_clip(base_img_path, problem_data['display_seconds'], comparison_clip)
            clips.append(comparison_clip)
        
        # 3. 카운트다운 클립들
        countdown_seconds = problem_data.get('countdown_seconds', 10)
        for i in range(countdown_seconds, 0, -1):
            countdown_path = output_dir / f"problem_{problem_num}_countdown_{i}.png"
            create_countdown_image(i, color_scheme, font_size, countdown_path)
            
            countdown_clip = output_dir / f"problem_{problem_num}_countdown_{i}.mp4"
            create_image_clip(countdown_path, 1, countdown_clip)
            clips.append(countdown_clip)
        
        # 4. 정답 화면
        answer_path = output_dir / f"problem_{problem_num}_answer.png"
        create_answer_image(
            str(problem_data['answer_data']['correct_answer']),
            problem_data['answer_data']['explanation'],
            color_scheme,
            font_size,
            answer_path
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
