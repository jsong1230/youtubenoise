"""
틀린그림찾기 영상 생성 스크립트
이미지 쌍, 카운트다운, 정답 화면을 조합하여 최종 영상 생성
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging, check_ffmpeg

# 로깅 설정
logger = setup_logging()


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
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except:
            font = ImageFont.load_default()
        
        draw.text((480, y_offset + 50), "원본", fill=(50, 50, 50), font=font, anchor="mm")
        draw.text((1440, y_offset + 50), "수정본", fill=(50, 50, 50), font=font, anchor="mm")
        
        canvas.save(output_path, "PNG", optimize=True)
        logger.info(f"비교 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"비교 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_countdown_image(seconds: int, color_scheme: Dict, font_size: int, output_path: Path):
    """
    카운트다운 이미지 생성
    
    Args:
        seconds: 카운트다운 초
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 이미지 경로
    """
    try:
        img = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [240, 240, 235])))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default()
        
        text = str(seconds)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2
        
        # 텍스트 그림자 효과
        shadow_offset = 5
        draw.text((x + shadow_offset, y + shadow_offset), text, 
                 fill=(100, 100, 100), font=font)
        
        # 메인 텍스트
        draw.text((x, y), text, 
                 fill=tuple(color_scheme.get('countdown', [200, 50, 50])), 
                 font=font)
        
        img.save(output_path, "PNG", optimize=True)
        logger.info(f"카운트다운 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"카운트다운 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_answer_image(base_image: Path, differences: List[Dict], 
                       answer_text: str, color_scheme: Dict, font_size: int, 
                       output_path: Path):
    """
    정답 화면 이미지 생성 (차이점 하이라이트)
    
    Args:
        base_image: 원본 이미지 경로
        differences: 차이점 정보 리스트
        answer_text: 정답 안내 텍스트
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 이미지 경로
    """
    try:
        img = Image.open(base_image).copy()
        draw = ImageDraw.Draw(img)
        
        # 차이점 하이라이트
        highlight_color = tuple(color_scheme.get('highlight', [255, 200, 100]))
        for diff in differences:
            x = diff.get('x', 0)
            y = diff.get('y', 0)
            radius = diff.get('radius', 40)
            
            # 반투명 원 그리기
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=(*highlight_color, 150),
                outline=(*highlight_color, 255),
                width=4
            )
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # 번호 표시
            try:
                num_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                num_font = ImageFont.load_default()
            
            diff_num = differences.index(diff) + 1
            draw.text((x, y - radius - 20), str(diff_num), 
                     fill=(255, 255, 255), font=num_font, anchor="mm")
        
        # 정답 텍스트 오버레이
        try:
            text_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            text_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), answer_text, font=text_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 텍스트 배경 박스
        padding = 20
        box_x = (1920 - text_width) // 2 - padding
        box_y = 100
        box_w = text_width + padding * 2
        box_h = text_height + padding * 2
        
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            fill=(0, 0, 0, 180)
        )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # 텍스트
        draw.text((1920 // 2, box_y + box_h // 2), answer_text,
                 fill=tuple(color_scheme.get('text', [255, 255, 255])),
                 font=text_font, anchor="mm")
        
        img.save(output_path, "PNG", optimize=True)
        logger.info(f"정답 화면 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"정답 화면 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_problem_clip(problem_data: Dict, preset: Dict, output_dir: Path) -> List[Path]:
    """
    하나의 문제 세트에 대한 클립들 생성
    
    Args:
        problem_data: 문제 데이터 (base_image, modified_image, differences, texts 등)
        preset: 프리셋 설정
        output_dir: 출력 디렉토리
    
    Returns:
        생성된 클립 파일 경로 리스트
    """
    try:
        clips = []
        problem_num = problem_data.get('problem_number', 1)
        
        # 1. 비교 이미지 생성
        comparison_path = output_dir / f"problem_{problem_num}_comparison.png"
        create_comparison_image(
            problem_data['base_image'],
            problem_data['modified_image'],
            comparison_path
        )
        
        # 비교 화면 클립 (7초)
        comparison_clip = output_dir / f"problem_{problem_num}_comparison.mp4"
        create_image_clip(comparison_path, 7, comparison_clip)
        clips.append(comparison_clip)
        
        # 2. 카운트다운 클립들 생성
        countdown_seconds = preset.get('countdown_seconds', 10)
        for i in range(countdown_seconds, 0, -1):
            countdown_path = output_dir / f"problem_{problem_num}_countdown_{i}.png"
            create_countdown_image(
                i,
                preset.get('color_scheme', {}),
                preset.get('font_size', 72),
                countdown_path
            )
            
            countdown_clip = output_dir / f"problem_{problem_num}_countdown_{i}.mp4"
            create_image_clip(countdown_path, 1, countdown_clip)
            clips.append(countdown_clip)
        
        # 3. 정답 화면 클립 생성
        answer_path = output_dir / f"problem_{problem_num}_answer.png"
        create_answer_image(
            problem_data['base_image'],
            problem_data['differences'],
            problem_data['answer_text'],
            preset.get('color_scheme', {}),
            preset.get('font_size', 64),
            answer_path
        )
        
        answer_clip = output_dir / f"problem_{problem_num}_answer.mp4"
        create_image_clip(answer_path, 5, answer_clip)
        clips.append(answer_clip)
        
        return clips
        
    except Exception as e:
        logger.error(f"문제 클립 생성 실패: {e}", exc_info=True)
        return []


def create_image_clip(image_path: Path, duration: int, output_path: Path):
    """
    정적 이미지를 지정된 길이의 비디오 클립으로 변환
    
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
    # 테스트 코드는 generate_spot_difference.py에서 사용
    pass

