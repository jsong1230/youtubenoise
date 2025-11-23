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


def create_comparison_image(base_image: Path, modified_image: Path, output_path: Path,
                           problem_number: int = 1, num_differences: int = 3,
                           color_scheme: Optional[Dict] = None, layout_type: str = "side_by_side"):
    """
    원본과 수정본 이미지를 배치한 비교 이미지 생성 (시니어 친화적 레이아웃)
    
    Args:
        base_image: 원본 이미지 경로
        modified_image: 수정본 이미지 경로
        output_path: 출력 이미지 경로
        problem_number: 문제 번호
        num_differences: 차이점 개수
        color_scheme: 색상 스킴
        layout_type: 레이아웃 타입 ("side_by_side" 또는 "top_bottom")
    """
    try:
        base_img = Image.open(base_image)
        modified_img = Image.open(modified_image)
        
        if color_scheme is None:
            color_scheme = {
                'background': [240, 240, 235],
                'text': [50, 50, 50],
                'highlight': [255, 200, 100]
            }
        
        # 1920x1080 캔버스 생성
        canvas = Image.new('RGB', (1920, 1080), tuple(color_scheme.get('background', [240, 240, 235])))
        draw = ImageDraw.Draw(canvas)
        
        # 폰트 설정
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 80)
            font_medium = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 64)
            font_label = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 56)
        except:
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 64)
                font_label = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
            except:
                font_large = ImageFont.load_default()
                font_medium = font_large
                font_label = font_large
        
        # 상단 문제 번호 및 안내 텍스트
        problem_text = f"문제 {problem_number}"
        instruction_text = f"차이점 {num_differences}개를 찾아보세요"
        
        # 문제 번호
        bbox = draw.textbbox((0, 0), problem_text, font=font_large)
        text_width = bbox[2] - bbox[0]
        draw.text((60, 40), problem_text, 
                 fill=tuple(color_scheme.get('highlight', [255, 200, 100])), 
                 font=font_large)
        
        # 안내 텍스트
        bbox = draw.textbbox((0, 0), instruction_text, font=font_medium)
        draw.text((60, 140), instruction_text,
                 fill=tuple(color_scheme.get('text', [50, 50, 50])),
                 font=font_medium)
        
        if layout_type == "side_by_side":
            # 좌우 배치 (개선된 레이아웃)
            # 이미지 크기: 900x506 (더 크게)
            img_width = 900
            img_height = 506
            
            base_img_resized = base_img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            modified_img_resized = modified_img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            
            # 상단 여백 220px, 하단 여백 354px
            y_offset = 220
            x_left = 60
            x_right = 1920 - 60 - img_width
            
            canvas.paste(base_img_resized, (x_left, y_offset))
            canvas.paste(modified_img_resized, (x_right, y_offset))
            
            # 중앙 구분선 (더 두껍게)
            line_x = 1920 // 2
            draw.line([(line_x, y_offset - 10), (line_x, y_offset + img_height + 10)], 
                     fill=(180, 180, 180), width=5)
            
            # 라벨 (더 크고 명확하게)
            label_y = y_offset - 80
            draw.text((x_left + img_width // 2, label_y), "원본", 
                     fill=tuple(color_scheme.get('text', [50, 50, 50])), 
                     font=font_label, anchor="mm")
            draw.text((x_right + img_width // 2, label_y), "수정본", 
                     fill=tuple(color_scheme.get('text', [50, 50, 50])), 
                     font=font_label, anchor="mm")
            
        else:  # top_bottom
            # 상하 배치
            img_width = 1600
            img_height = 400
            
            base_img_resized = base_img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            modified_img_resized = modified_img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            
            x_center = (1920 - img_width) // 2
            y_top = 220
            y_bottom = 1080 - 220 - img_height
            
            canvas.paste(base_img_resized, (x_center, y_top))
            canvas.paste(modified_img_resized, (x_center, y_bottom))
            
            # 중앙 구분선
            line_y = (y_top + img_height + y_bottom) // 2
            draw.line([(x_center - 10, line_y), (x_center + img_width + 10, line_y)], 
                     fill=(180, 180, 180), width=5)
            
            # 라벨
            draw.text((x_center + img_width // 2, y_top - 60), "원본", 
                     fill=tuple(color_scheme.get('text', [50, 50, 50])), 
                     font=font_label, anchor="mm")
            draw.text((x_center + img_width // 2, y_bottom + img_height + 60), "수정본", 
                     fill=tuple(color_scheme.get('text', [50, 50, 50])), 
                     font=font_label, anchor="mm")
        
        canvas.save(output_path, "PNG", optimize=True)
        logger.info(f"비교 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"비교 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_countdown_image(seconds: int, color_scheme: Dict, font_size: int, output_path: Path):
    """
    카운트다운 이미지 생성 (시니어 친화적 레이아웃)
    
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
            font_large = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            font_medium = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 64)
        except:
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 64)
            except:
                font_large = ImageFont.load_default()
                font_medium = font_large
        
        # 메인 카운트다운 숫자
        text = str(seconds)
        bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2 - 80  # 안내 텍스트 공간 확보
        
        # 텍스트 그림자 효과 (더 진하게)
        shadow_offset = 8
        draw.text((x + shadow_offset, y + shadow_offset), text, 
                 fill=(80, 80, 80), font=font_large)
        
        # 메인 텍스트
        draw.text((x, y), text, 
                 fill=tuple(color_scheme.get('countdown', [200, 50, 50])), 
                 font=font_large)
        
        # 하단 안내 텍스트
        if seconds > 0:
            instruction_text = "차이점을 찾아보세요"
        else:
            instruction_text = "시간이 끝났습니다"
        
        bbox_inst = draw.textbbox((0, 0), instruction_text, font=font_medium)
        inst_width = bbox_inst[2] - bbox_inst[0]
        inst_height = bbox_inst[3] - bbox_inst[1]
        
        inst_x = (1920 - inst_width) // 2
        inst_y = y + text_height + 60
        
        # 안내 텍스트 배경 박스
        padding = 20
        box_x = inst_x - padding
        box_y = inst_y - padding
        box_w = inst_width + padding * 2
        box_h = inst_height + padding * 2
        
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            fill=(255, 255, 255, 200)
        )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        draw.text((inst_x, inst_y), instruction_text,
                 fill=tuple(color_scheme.get('text', [50, 50, 50])),
                 font=font_medium)
        
        img.save(output_path, "PNG", optimize=True)
        logger.info(f"카운트다운 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"카운트다운 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_answer_image(base_image: Path, differences: List[Dict], 
                       answer_text: str, color_scheme: Dict, font_size: int, 
                       output_path: Path, problem_number: int = 1):
    """
    정답 화면 이미지 생성 (차이점 하이라이트) - 시니어 친화적 레이아웃
    
    Args:
        base_image: 원본 이미지 경로
        differences: 차이점 정보 리스트
        answer_text: 정답 안내 텍스트
        color_scheme: 색상 스킴
        font_size: 폰트 크기
        output_path: 출력 이미지 경로
        problem_number: 문제 번호
    """
    try:
        img = Image.open(base_image).copy()
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", font_size)
            font_medium = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 64)
            font_number = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 56)
        except:
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 64)
                font_number = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
            except:
                font_large = ImageFont.load_default()
                font_medium = font_large
                font_number = font_large
        
        # 차이점 하이라이트 (더 크고 명확하게)
        highlight_color = tuple(color_scheme.get('highlight', [255, 200, 100]))
        for i, diff in enumerate(differences):
            x = diff.get('x', 0)
            y = diff.get('y', 0)
            radius = diff.get('radius', 60)  # 40 -> 60으로 증가
            
            # 반투명 원 그리기 (더 진하게)
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=(*highlight_color, 180),  # 150 -> 180으로 증가
                outline=(*highlight_color, 255),
                width=6  # 4 -> 6으로 증가
            )
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # 번호 표시 (더 크고 명확하게)
            diff_num = i + 1
            # 번호 배경 원
            num_bg_radius = 35
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.ellipse(
                [x - num_bg_radius, y - radius - num_bg_radius - 10,
                 x + num_bg_radius, y - radius + num_bg_radius - 10],
                fill=(0, 0, 0, 200),
                outline=(*highlight_color, 255),
                width=3
            )
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # 번호 텍스트
            draw.text((x, y - radius - 10), str(diff_num), 
                     fill=(255, 255, 255), font=font_number, anchor="mm")
        
        # 상단 정답 텍스트 오버레이 (더 크고 명확하게)
        bbox = draw.textbbox((0, 0), answer_text, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 텍스트 배경 박스 (더 큰 padding)
        padding = 30  # 20 -> 30으로 증가
        box_x = (1920 - text_width) // 2 - padding
        box_y = 50  # 100 -> 50으로 상단 이동
        box_w = text_width + padding * 2
        box_h = text_height + padding * 2
        
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        # 둥근 모서리 효과를 위한 사각형
        overlay_draw.rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            fill=(0, 0, 0, 220)  # 180 -> 220으로 더 진하게
        )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # 텍스트
        draw.text((1920 // 2, box_y + box_h // 2), answer_text,
                 fill=tuple(color_scheme.get('text', [255, 255, 255])),
                 font=font_large, anchor="mm")
        
        # 하단 문제 번호 표시
        problem_text = f"문제 {problem_number} 정답"
        bbox = draw.textbbox((0, 0), problem_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 하단 배경 박스
        bottom_padding = 20
        bottom_box_x = (1920 - text_width) // 2 - bottom_padding
        bottom_box_y = 1080 - text_height - bottom_padding - 40
        bottom_box_w = text_width + bottom_padding * 2
        bottom_box_h = text_height + bottom_padding * 2
        
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [bottom_box_x, bottom_box_y, bottom_box_x + bottom_box_w, bottom_box_y + bottom_box_h],
            fill=(*highlight_color, 200)
        )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        draw.text((1920 // 2, bottom_box_y + bottom_box_h // 2), problem_text,
                 fill=(255, 255, 255), font=font_medium, anchor="mm")
        
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
        num_differences = len(problem_data.get('differences', []))
        layout_type = preset.get('layout_type', 'side_by_side')
        
        # 1. 비교 이미지 생성
        comparison_path = output_dir / f"problem_{problem_num}_comparison.png"
        create_comparison_image(
            problem_data['base_image'],
            problem_data['modified_image'],
            comparison_path,
            problem_number=problem_num,
            num_differences=num_differences,
            color_scheme=preset.get('color_scheme', {}),
            layout_type=layout_type
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
            problem_data.get('answer_text', '정답'),
            preset.get('color_scheme', {}),
            preset.get('font_size', 64),
            answer_path,
            problem_number=problem_num
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

