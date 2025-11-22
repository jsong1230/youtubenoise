"""
AI Explainer 영상 제작 스크립트
스크립트 데이터를 기반으로 Hook → Sections → Outro 구조의 영상 생성
"""
import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE, OUTPUT_DIR, PROJECT_ROOT
from scripts.utils import setup_logging, check_ffmpeg

# .env 파일 로드
load_dotenv(project_root / ".env")

# 로깅 설정
logger = setup_logging()


def create_text_image(
    text: str,
    title: str = None,
    output_path: Path = None,
    width: int = 1920,
    height: int = 1080,
    background_color: tuple = (30, 30, 40),
    text_color: tuple = (255, 255, 255),
    title_color: tuple = (100, 150, 255)
) -> Path:
    """
    텍스트 이미지 생성 (AI Explainer용)
    
    Args:
        text: 메인 텍스트
        title: 제목 (선택사항)
        output_path: 출력 경로
        width: 이미지 너비
        height: 이미지 높이
        background_color: 배경색
        text_color: 텍스트 색상
        title_color: 제목 색상
    
    Returns:
        생성된 이미지 파일 경로
    """
    try:
        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # 폰트 로드 시도
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 72)
            text_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 48)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
        
        y_offset = 100
        
        # 제목 그리기
        if title:
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, y_offset), title, fill=title_color, font=title_font)
            y_offset += 120
        
        # 텍스트 줄바꿈 처리
        words = text.split()
        lines = []
        current_line = []
        max_width = width - 200
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=text_font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # 텍스트 그리기
        line_height = 70
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=text_font)
            line_width = bbox[2] - bbox[0]
            text_x = (width - line_width) // 2
            
            if y_offset + line_height > height - 100:
                break
            
            draw.text((text_x, y_offset), line, fill=text_color, font=text_font)
            y_offset += line_height
        
        # 이미지 저장
        if output_path is None:
            output_path = OUTPUT_DIR / "images" / "ai_explainer" / f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", optimize=True)
        
        return output_path
        
    except Exception as e:
        logger.error(f"텍스트 이미지 생성 실패: {e}", exc_info=True)
        raise


def create_image_clip(image_path: Path, duration: int, output_path: Path):
    """
    이미지를 지정된 길이의 비디오 클립으로 변환
    
    Args:
        image_path: 이미지 파일 경로
        duration: 클립 길이 (초)
        output_path: 출력 비디오 파일 경로
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
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080",
            "-r", "30",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        logger.debug(f"이미지 클립 생성 완료: {output_path} ({duration}초)")
        
    except Exception as e:
        logger.error(f"이미지 클립 생성 실패: {e}")
        raise


def create_broll_clip(
    query: str,
    duration: int,
    output_path: Path,
    width: int = 1920,
    height: int = 1080
) -> Optional[Path]:
    """
    B-roll 이미지를 다운로드하고 클립으로 변환
    
    Args:
        query: 이미지 검색어
        duration: 클립 길이 (초)
        output_path: 출력 비디오 파일 경로
        width: 이미지 너비
        height: 이미지 높이
    
    Returns:
        생성된 클립 파일 경로 (실패 시 None)
    """
    try:
        from src.api.api_manager import APIManager
        
        api_manager = APIManager()
        
        # 무료 이미지 API로 이미지 다운로드
        image_path = api_manager.generate_image(
            prompt=query,
            use_dalle=False,
            width=width,
            height=height
        )
        
        if image_path and image_path.exists():
            # 이미지를 클립으로 변환
            create_image_clip(image_path, duration, output_path)
            return output_path
        else:
            logger.warning(f"B-roll 이미지 다운로드 실패: {query}")
            return None
            
    except Exception as e:
        logger.warning(f"B-roll 클립 생성 실패: {e}")
        return None


def create_section_clips(
    section: Dict,
    section_number: int,
    output_dir: Path,
    use_broll: bool = True
) -> List[Path]:
    """
    섹션의 클립들을 생성
    
    Args:
        section: 섹션 데이터
        section_number: 섹션 번호
        output_dir: 출력 디렉토리
        use_broll: B-roll 사용 여부
    
    Returns:
        생성된 클립 파일 경로 리스트
    """
    clips = []
    
    try:
        title = section.get("title", f"Section {section_number}")
        content = section.get("content", "")
        duration_seconds = section.get("duration_seconds", 180)
        broll_timing = section.get("broll_timing", [])
        
        # 섹션 시작 텍스트 이미지 (제목)
        title_image_path = output_dir / f"section_{section_number}_title.png"
        create_text_image(
            text=title,
            output_path=title_image_path,
            title=None
        )
        
        title_clip_path = output_dir / f"section_{section_number}_title.mp4"
        create_image_clip(title_image_path, 3, title_clip_path)
        clips.append(title_clip_path)
        
        # 본문 텍스트 이미지
        content_image_path = output_dir / f"section_{section_number}_content.png"
        create_text_image(
            text=content,
            title=title,
            output_path=content_image_path
        )
        
        # B-roll 타이밍에 따라 클립 분할
        if use_broll and broll_timing:
            current_time = 0
            for i, broll_time in enumerate(broll_timing):
                # 텍스트 클립 (B-roll 전까지)
                if current_time < broll_time:
                    text_duration = min(broll_time - current_time, duration_seconds - current_time)
                    if text_duration > 0:
                        text_clip_path = output_dir / f"section_{section_number}_text_{i}.mp4"
                        create_image_clip(content_image_path, text_duration, text_clip_path)
                        clips.append(text_clip_path)
                        current_time += text_duration
                
                # B-roll 클립 (5초)
                if current_time < duration_seconds:
                    broll_query = f"{title} {content[:50]}"  # 간단한 검색어
                    broll_clip_path = output_dir / f"section_{section_number}_broll_{i}.mp4"
                    broll_clip = create_broll_clip(broll_query, 5, broll_clip_path)
                    if broll_clip:
                        clips.append(broll_clip)
                        current_time += 5
                    else:
                        # B-roll 실패 시 텍스트 클립으로 대체
                        text_clip_path = output_dir / f"section_{section_number}_text_broll_{i}.mp4"
                        create_image_clip(content_image_path, 5, text_clip_path)
                        clips.append(text_clip_path)
                        current_time += 5
            
            # 남은 시간 처리
            if current_time < duration_seconds:
                remaining = duration_seconds - current_time
                text_clip_path = output_dir / f"section_{section_number}_text_final.mp4"
                create_image_clip(content_image_path, remaining, text_clip_path)
                clips.append(text_clip_path)
        else:
            # B-roll 없이 전체 텍스트 클립
            content_clip_path = output_dir / f"section_{section_number}_content.mp4"
            create_image_clip(content_image_path, duration_seconds, content_clip_path)
            clips.append(content_clip_path)
        
        logger.info(f"섹션 {section_number} 클립 생성 완료: {len(clips)}개 클립")
        return clips
        
    except Exception as e:
        logger.error(f"섹션 클립 생성 실패: {e}", exc_info=True)
        return clips


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
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-c:a", "aac"])
            cmd.extend(["-map", "0:v:0"])
            cmd.extend(["-map", "1:a:0"])
            cmd.extend(["-shortest"])
        else:
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-c:a", "copy"])
        
        cmd.append(str(output_path))
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 임시 파일 삭제
        list_file.unlink()
        
        logger.info(f"영상 합성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"영상 합성 실패: {e}", exc_info=True)
        raise


def make_ai_explainer_video(
    script_path: Path,
    output_path: Optional[Path] = None,
    bgm_path: Optional[Path] = None,
    use_broll: bool = True
) -> Path:
    """
    AI Explainer 영상 제작 메인 함수
    
    Args:
        script_path: 스크립트 JSON 파일 경로
        output_path: 출력 영상 파일 경로 (None이면 자동 생성)
        bgm_path: BGM 파일 경로 (선택사항)
        use_broll: B-roll 사용 여부
    
    Returns:
        생성된 영상 파일 경로
    """
    try:
        # 스크립트 로드
        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        
        metadata = script_data.get("metadata", {})
        topic_name = metadata.get("topic_name", "ai_explainer")
        
        # 출력 경로 설정
        if output_path is None:
            output_dir = OUTPUT_DIR / "videos" / "ai_explainers"
            output_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_path = output_dir / f"{date_str}_{topic_name}.mp4"
        
        temp_dir = output_path.parent / f"{output_path.stem}_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AI Explainer 영상 제작 시작: {metadata.get('title', topic_name)}")
        
        all_clips = []
        
        # 1. Hook 클립 생성
        hook = script_data.get("hook", "")
        if hook:
            logger.info("Hook 클립 생성 중...")
            hook_image_path = temp_dir / "hook.png"
            create_text_image(
                text=hook,
                title="시작",
                output_path=hook_image_path
            )
            hook_clip_path = temp_dir / "hook.mp4"
            create_image_clip(hook_image_path, 15, hook_clip_path)
            all_clips.append(hook_clip_path)
        
        # 2. Sections 클립 생성
        sections = script_data.get("sections", [])
        logger.info(f"섹션 클립 생성 중... ({len(sections)}개 섹션)")
        
        for i, section in enumerate(sections, 1):
            logger.info(f"  섹션 {i}/{len(sections)}: {section.get('title', '')}")
            section_clips = create_section_clips(section, i, temp_dir, use_broll)
            all_clips.extend(section_clips)
        
        # 3. Outro 클립 생성
        outro = script_data.get("outro", "")
        if outro:
            logger.info("Outro 클립 생성 중...")
            outro_image_path = temp_dir / "outro.png"
            create_text_image(
                text=outro,
                title="마무리",
                output_path=outro_image_path
            )
            outro_clip_path = temp_dir / "outro.mp4"
            create_image_clip(outro_image_path, 10, outro_clip_path)
            all_clips.append(outro_clip_path)
        
        # 4. 영상 합성
        logger.info(f"\n전체 영상 합성 중... ({len(all_clips)}개 클립)")
        combine_clips(all_clips, output_path, bgm_path)
        
        logger.info(f"\n영상 제작 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"영상 제작 중 오류 발생: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Explainer 영상 제작",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 스크립트 파일로부터 영상 제작
  python scripts/make_ai_explainer_video.py --script output/scripts/ai_explainers/2025-11-22_ChatGPT로_코딩하기_실전_팁_script.json
  
  # BGM 추가
  python scripts/make_ai_explainer_video.py --script script.json --bgm audio/bgm.mp3
  
  # B-roll 비활성화
  python scripts/make_ai_explainer_video.py --script script.json --no-broll
        """
    )
    
    parser.add_argument(
        "--script",
        type=str,
        required=True,
        help="스크립트 JSON 파일 경로"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="출력 영상 파일 경로 (None이면 자동 생성)"
    )
    
    parser.add_argument(
        "--bgm",
        type=str,
        help="BGM 파일 경로 (선택사항)"
    )
    
    parser.add_argument(
        "--no-broll",
        action="store_true",
        help="B-roll 사용 안 함"
    )
    
    args = parser.parse_args()
    
    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = PROJECT_ROOT / script_path
    
    output_path = Path(args.output) if args.output else None
    if output_path and not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    
    bgm_path = Path(args.bgm) if args.bgm else None
    if bgm_path and not bgm_path.is_absolute():
        bgm_path = PROJECT_ROOT / bgm_path
    
    make_ai_explainer_video(
        script_path=script_path,
        output_path=output_path,
        bgm_path=bgm_path,
        use_broll=not args.no_broll
    )

