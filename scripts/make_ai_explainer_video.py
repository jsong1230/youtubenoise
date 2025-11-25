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


def create_image_clip(
    image_path: Path, 
    duration: int, 
    output_path: Path,
    fade_in: float = 0.5,
    fade_out: float = 0.5
):
    """
    이미지를 지정된 길이의 비디오 클립으로 변환 (애니메이션 효과 포함)
    
    Args:
        image_path: 이미지 파일 경로
        duration: 클립 길이 (초)
        output_path: 출력 비디오 파일 경로
        fade_in: 페이드 인 시간 (초)
        fade_out: 페이드 아웃 시간 (초)
    """
    try:
        if not check_ffmpeg():
            raise RuntimeError("FFmpeg가 설치되지 않았습니다.")
        
        # 페이드 효과 계산
        fade_in_frame = int(fade_in * 30)  # 30fps 기준
        fade_out_frame = int(fade_out * 30)
        total_frames = int(duration * 30)
        
        # 페이드 필터 생성
        if fade_in > 0 and fade_out > 0 and duration > fade_in + fade_out:
            # 페이드 인 + 페이드 아웃
            fade_filter = f"fade=t=in:st=0:d={fade_in},fade=t=out:st={duration-fade_out}:d={fade_out}"
        elif fade_in > 0:
            # 페이드 인만
            fade_filter = f"fade=t=in:st=0:d={fade_in}"
        elif fade_out > 0:
            # 페이드 아웃만
            fade_filter = f"fade=t=out:st={duration-fade_out}:d={fade_out}"
        else:
            fade_filter = None
        
        # 비디오 필터 조합
        if fade_filter:
            vf = f"scale=1920:1080,{fade_filter}"
        else:
            vf = "scale=1920:1080"
        
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", vf,
            "-r", "30",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        logger.debug(f"이미지 클립 생성 완료: {output_path} ({duration}초, fade_in={fade_in}s, fade_out={fade_out}s)")
        
    except Exception as e:
        logger.error(f"이미지 클립 생성 실패: {e}")
        raise


def create_broll_clip(
    query: str,
    duration: int,
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    use_dalle: bool = False
) -> Optional[Path]:
    """
    B-roll 이미지를 다운로드하고 클립으로 변환 (개선: DALL-E 옵션 추가)
    
    Args:
        query: 이미지 검색어
        duration: 클립 길이 (초)
        output_path: 출력 비디오 파일 경로
        width: 이미지 너비
        height: 이미지 높이
        use_dalle: DALL-E 사용 여부 (True면 DALL-E, False면 무료 API)
    
    Returns:
        생성된 클립 파일 경로 (실패 시 None)
    """
    try:
        from src.api.api_manager import APIManager
        
        api_manager = APIManager()
        
        # 이미지 다운로드 (DALL-E 또는 무료 API)
        image_path = api_manager.generate_image(
            prompt=query,
            use_dalle=use_dalle,
            width=width,
            height=height
        )
        
        if image_path and image_path.exists():
            # 이미지를 클립으로 변환 (페이드 효과 포함)
            create_image_clip(image_path, duration, output_path, fade_in=0.3, fade_out=0.3)
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
    use_broll: bool = True,
    use_tts: bool = False,
    use_code_snippets: bool = True,
    use_diagrams: bool = True,
    language: str = "ko"
) -> List[Path]:
    """
    섹션의 클립들을 생성 (개선: 코드 스니펫, 다이어그램, TTS 지원)
    
    Args:
        section: 섹션 데이터
        section_number: 섹션 번호
        output_dir: 출력 디렉토리
        use_broll: B-roll 사용 여부
        use_tts: TTS 사용 여부
        use_code_snippets: 코드 스니펫 사용 여부
        use_diagrams: 다이어그램 사용 여부
        language: 언어 (ko, en)
    
    Returns:
        생성된 클립 파일 경로 리스트
    """
    clips = []
    
    try:
        title = section.get("title", f"Section {section_number}")
        content = section.get("content", "")
        duration_seconds = section.get("duration_seconds", 180)
        broll_timing = section.get("broll_timing", [])
        code_snippets = section.get("code_snippets", [])  # 코드 스니펫 리스트
        diagrams = section.get("diagrams", [])  # 다이어그램 리스트
        
        # 섹션 시작 텍스트 이미지 (제목) - 페이드 효과 포함
        title_image_path = output_dir / f"section_{section_number}_title.png"
        create_text_image(
            text=title,
            output_path=title_image_path,
            title=None
        )
        
        title_clip_path = output_dir / f"section_{section_number}_title.mp4"
        create_image_clip(title_image_path, 3, title_clip_path, fade_in=0.3, fade_out=0.3)
        clips.append(title_clip_path)
        
        # 본문 텍스트 이미지
        content_image_path = output_dir / f"section_{section_number}_content.png"
        create_text_image(
            text=content,
            title=title,
            output_path=content_image_path
        )
        
        # 코드 스니펫 이미지 생성 (있는 경우)
        code_images = []
        if use_code_snippets and code_snippets:
            try:
                from scripts.create_code_snippet_image import create_code_snippet_image
                for i, code in enumerate(code_snippets):
                    code_image_path = output_dir / f"section_{section_number}_code_{i}.png"
                    create_code_snippet_image(
                        code=code,
                        language="python",
                        output_path=code_image_path
                    )
                    code_images.append(code_image_path)
                    logger.info(f"코드 스니펫 이미지 생성: {code_image_path}")
            except Exception as e:
                logger.warning(f"코드 스니펫 이미지 생성 실패: {e}")
        
        # 다이어그램 이미지 생성 (있는 경우)
        diagram_images = []
        if use_diagrams and diagrams:
            try:
                from scripts.create_diagram_image import create_diagram_image
                for i, diagram_concept in enumerate(diagrams):
                    diagram_image_path = output_dir / f"section_{section_number}_diagram_{i}.png"
                    create_diagram_image(
                        concept=diagram_concept,
                        diagram_type="flowchart",
                        output_path=diagram_image_path,
                        language=language
                    )
                    diagram_images.append(diagram_image_path)
                    logger.info(f"다이어그램 이미지 생성: {diagram_image_path}")
            except Exception as e:
                logger.warning(f"다이어그램 이미지 생성 실패: {e}")
        
        # B-roll 타이밍에 따라 클립 분할
        if use_broll and broll_timing:
            current_time = 0
            code_idx = 0
            diagram_idx = 0
            
            for i, broll_time in enumerate(broll_timing):
                # 텍스트 클립 (B-roll 전까지)
                if current_time < broll_time:
                    text_duration = min(broll_time - current_time, duration_seconds - current_time)
                    if text_duration > 0:
                        text_clip_path = output_dir / f"section_{section_number}_text_{i}.mp4"
                        create_image_clip(content_image_path, text_duration, text_clip_path, fade_in=0.3, fade_out=0.3)
                        clips.append(text_clip_path)
                        current_time += text_duration
                
                # 코드 스니펫 또는 다이어그램 삽입 (우선순위: 코드 > 다이어그램 > B-roll)
                if current_time < duration_seconds:
                    if code_idx < len(code_images):
                        # 코드 스니펫 클립 (7초)
                        code_clip_path = output_dir / f"section_{section_number}_code_clip_{code_idx}.mp4"
                        create_image_clip(code_images[code_idx], 7, code_clip_path, fade_in=0.3, fade_out=0.3)
                        clips.append(code_clip_path)
                        current_time += 7
                        code_idx += 1
                    elif diagram_idx < len(diagram_images):
                        # 다이어그램 클립 (7초)
                        diagram_clip_path = output_dir / f"section_{section_number}_diagram_clip_{diagram_idx}.mp4"
                        create_image_clip(diagram_images[diagram_idx], 7, diagram_clip_path, fade_in=0.3, fade_out=0.3)
                        clips.append(diagram_clip_path)
                        current_time += 7
                        diagram_idx += 1
                    else:
                        # B-roll 클립 (5초) - 더 정확한 검색어 생성
                        broll_query = f"{title} {content[:100]}"  # 검색어 개선
                        broll_clip_path = output_dir / f"section_{section_number}_broll_{i}.mp4"
                        # DALL-E 사용 옵션 (무료 API 실패 시)
                        broll_clip = create_broll_clip(broll_query, 5, broll_clip_path, use_dalle=False)
                        if not broll_clip:
                            # DALL-E로 재시도
                            broll_clip = create_broll_clip(broll_query, 5, broll_clip_path, use_dalle=True)
                        if broll_clip:
                            clips.append(broll_clip)
                            current_time += 5
                        else:
                            # B-roll 실패 시 텍스트 클립으로 대체
                            text_clip_path = output_dir / f"section_{section_number}_text_broll_{i}.mp4"
                            create_image_clip(content_image_path, 5, text_clip_path, fade_in=0.3, fade_out=0.3)
                            clips.append(text_clip_path)
                            current_time += 5
            
            # 남은 코드/다이어그램 삽입
            while code_idx < len(code_images) and current_time < duration_seconds:
                code_clip_path = output_dir / f"section_{section_number}_code_clip_{code_idx}.mp4"
                remaining = min(7, duration_seconds - current_time)
                if remaining > 0:
                    create_image_clip(code_images[code_idx], remaining, code_clip_path, fade_in=0.3, fade_out=0.3)
                    clips.append(code_clip_path)
                    current_time += remaining
                code_idx += 1
            
            while diagram_idx < len(diagram_images) and current_time < duration_seconds:
                diagram_clip_path = output_dir / f"section_{section_number}_diagram_clip_{diagram_idx}.mp4"
                remaining = min(7, duration_seconds - current_time)
                if remaining > 0:
                    create_image_clip(diagram_images[diagram_idx], remaining, diagram_clip_path, fade_in=0.3, fade_out=0.3)
                    clips.append(diagram_clip_path)
                    current_time += remaining
                diagram_idx += 1
            
            # 남은 시간 처리
            if current_time < duration_seconds:
                remaining = duration_seconds - current_time
                text_clip_path = output_dir / f"section_{section_number}_text_final.mp4"
                create_image_clip(content_image_path, remaining, text_clip_path, fade_in=0.3, fade_out=0.3)
                clips.append(text_clip_path)
        else:
            # B-roll 없이 전체 텍스트 클립 (코드/다이어그램은 삽입)
            if code_images or diagram_images:
                # 코드/다이어그램이 있으면 분할
                current_time = 0
                code_idx = 0
                diagram_idx = 0
                
                # 텍스트와 코드/다이어그램을 번갈아가며 삽입
                while current_time < duration_seconds:
                    # 텍스트 클립 (30초씩)
                    if current_time < duration_seconds:
                        text_duration = min(30, duration_seconds - current_time)
                        if text_duration > 0:
                            text_clip_path = output_dir / f"section_{section_number}_text_{current_time}.mp4"
                            create_image_clip(content_image_path, text_duration, text_clip_path, fade_in=0.3, fade_out=0.3)
                            clips.append(text_clip_path)
                            current_time += text_duration
                    
                    # 코드 스니펫 삽입
                    if code_idx < len(code_images) and current_time < duration_seconds:
                        code_clip_path = output_dir / f"section_{section_number}_code_clip_{code_idx}.mp4"
                        code_duration = min(7, duration_seconds - current_time)
                        if code_duration > 0:
                            create_image_clip(code_images[code_idx], code_duration, code_clip_path, fade_in=0.3, fade_out=0.3)
                            clips.append(code_clip_path)
                            current_time += code_duration
                        code_idx += 1
                    
                    # 다이어그램 삽입
                    if diagram_idx < len(diagram_images) and current_time < duration_seconds:
                        diagram_clip_path = output_dir / f"section_{section_number}_diagram_clip_{diagram_idx}.mp4"
                        diagram_duration = min(7, duration_seconds - current_time)
                        if diagram_duration > 0:
                            create_image_clip(diagram_images[diagram_idx], diagram_duration, diagram_clip_path, fade_in=0.3, fade_out=0.3)
                            clips.append(diagram_clip_path)
                            current_time += diagram_duration
                        diagram_idx += 1
            else:
                # 코드/다이어그램 없이 전체 텍스트 클립
                content_clip_path = output_dir / f"section_{section_number}_content.mp4"
                create_image_clip(content_image_path, duration_seconds, content_clip_path, fade_in=0.3, fade_out=0.3)
                clips.append(content_clip_path)
        
        logger.info(f"섹션 {section_number} 클립 생성 완료: {len(clips)}개 클립")
        return clips
        
    except Exception as e:
        logger.error(f"섹션 클립 생성 실패: {e}", exc_info=True)
        return clips


def combine_clips(
    clips: List[Path], 
    output_path: Path, 
    bgm_path: Optional[Path] = None,
    tts_files: Optional[Dict[str, Path]] = None,
    subtitles_file: Optional[Path] = None
):
    """
    여러 클립을 하나의 영상으로 합성 (개선: TTS, 자막 지원)
    
    Args:
        clips: 클립 파일 경로 리스트
        output_path: 출력 영상 경로
        bgm_path: BGM 파일 경로 (선택사항)
        tts_files: TTS 오디오 파일 딕셔너리 (hook, sections, outro)
        subtitles_file: 자막 파일 경로 (SRT 형식)
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
        
        # TTS 오디오 파일 리스트 생성 (있는 경우)
        tts_list_file = None
        if tts_files:
            tts_clips = []
            if tts_files.get("hook"):
                tts_clips.append(tts_files["hook"])
            if tts_files.get("sections"):
                tts_clips.extend(tts_files["sections"])
            if tts_files.get("outro"):
                tts_clips.append(tts_files["outro"])
            
            if tts_clips:
                tts_list_file = output_path.parent / "tts_list.txt"
                with open(tts_list_file, 'w') as f:
                    for tts_clip in tts_clips:
                        if tts_clip and tts_clip.exists():
                            f.write(f"file '{tts_clip.absolute()}'\n")
                
                cmd.extend(["-f", "concat", "-safe", "0", "-i", str(tts_list_file)])
        
        # BGM 추가
        if bgm_path and bgm_path.exists():
            cmd.extend(["-i", str(bgm_path)])
        
        # 비디오 필터 (자막 포함)
        video_filters = []
        if subtitles_file and subtitles_file.exists():
            # 자막 필터 (경로 이스케이프 처리)
            subtitle_path = str(subtitles_file).replace("\\", "\\\\").replace(":", "\\:")
            video_filters.append(f"subtitles='{subtitle_path}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'")
        
        # 비디오/오디오 매핑
        if tts_list_file and bgm_path and bgm_path.exists():
            # TTS + BGM: TTS를 메인으로, BGM을 배경으로 (볼륨 낮춤)
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-c:a", "aac"])
            cmd.extend(["-map", "0:v:0"])  # 비디오
            cmd.extend(["-map", "1:a:0"])  # TTS
            cmd.extend(["-map", "2:a:0"])  # BGM
            # 비디오 필터 적용
            if video_filters:
                cmd.extend(["-vf", ",".join(video_filters)])
            # 오디오 필터: BGM 볼륨 낮춤 후 TTS와 믹싱
            cmd.extend(["-filter_complex", "[2:a]volume=0.3[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2"])
        elif tts_list_file:
            # TTS만
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-c:a", "aac"])
            cmd.extend(["-map", "0:v:0"])
            cmd.extend(["-map", "1:a:0"])
            # 비디오 필터 적용
            if video_filters:
                cmd.extend(["-vf", ",".join(video_filters)])
            cmd.extend(["-shortest"])
        elif bgm_path and bgm_path.exists():
            # BGM만
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-c:a", "aac"])
            cmd.extend(["-map", "0:v:0"])
            cmd.extend(["-map", "1:a:0"])
            # 비디오 필터 적용
            if video_filters:
                cmd.extend(["-vf", ",".join(video_filters)])
            cmd.extend(["-shortest"])
        else:
            # 오디오 없음
            cmd.extend(["-c:v", "libx264"])
            cmd.extend(["-c:a", "copy"])
            # 비디오 필터 적용
            if video_filters:
                cmd.extend(["-vf", ",".join(video_filters)])
        
        cmd.append(str(output_path))
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 임시 파일 삭제
        list_file.unlink()
        if tts_list_file and tts_list_file.exists():
            tts_list_file.unlink()
        
        logger.info(f"영상 합성 완료: {output_path}")
        
    except Exception as e:
        logger.error(f"영상 합성 실패: {e}", exc_info=True)
        raise


def create_subtitles_file(
    script_data: Dict,
    output_path: Path,
    language: str = "ko"
) -> Path:
    """
    SRT 형식의 자막 파일 생성
    
    Args:
        script_data: 스크립트 데이터
        output_path: 출력 자막 파일 경로
        language: 언어 (ko, en)
    
    Returns:
        생성된 자막 파일 경로
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            current_time = 0
            
            # Hook 자막
            hook = script_data.get("hook", "")
            if hook:
                start_time = current_time
                end_time = current_time + 15
                f.write(f"{subtitle_index}\n")
                f.write(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n")
                f.write(f"{hook}\n\n")
                subtitle_index += 1
                current_time = end_time
            
            # Sections 자막
            sections = script_data.get("sections", [])
            for section in sections:
                title = section.get("title", "")
                content = section.get("content", "")
                duration = section.get("duration_seconds", 180)
                
                # 제목 자막
                if title:
                    start_time = current_time
                    end_time = current_time + 3
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n")
                    f.write(f"{title}\n\n")
                    subtitle_index += 1
                    current_time = end_time
                
                # 내용 자막 (문장 단위로 분할)
                sentences = content.split('. ')
                sentence_duration = max(3, duration / max(1, len(sentences)))
                
                for sentence in sentences:
                    if sentence.strip():
                        start_time = current_time
                        end_time = current_time + sentence_duration
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n")
                        f.write(f"{sentence.strip()}.\n\n")
                        subtitle_index += 1
                        current_time = end_time
                
                current_time += duration - (current_time - (current_time - duration))
            
            # Outro 자막
            outro = script_data.get("outro", "")
            if outro:
                start_time = current_time
                end_time = current_time + 10
                f.write(f"{subtitle_index}\n")
                f.write(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n")
                f.write(f"{outro}\n\n")
        
        logger.info(f"자막 파일 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"자막 파일 생성 실패: {e}", exc_info=True)
        raise


def format_srt_time(seconds: float) -> str:
    """SRT 시간 형식으로 변환 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def make_ai_explainer_video(
    script_path: Path,
    output_path: Optional[Path] = None,
    bgm_path: Optional[Path] = None,
    use_broll: bool = True,
    use_tts: bool = True,
    use_code_snippets: bool = True,
    use_diagrams: bool = True,
    use_subtitles: bool = True,
    language: str = "ko"
) -> Path:
    """
    AI Explainer 영상 제작 메인 함수 (개선: TTS, 코드 스니펫, 다이어그램, 자막 지원)
    
    Args:
        script_path: 스크립트 JSON 파일 경로
        output_path: 출력 영상 파일 경로 (None이면 자동 생성)
        bgm_path: BGM 파일 경로 (선택사항)
        use_broll: B-roll 사용 여부
        use_tts: TTS 내레이션 사용 여부
        use_code_snippets: 코드 스니펫 이미지 생성 여부
        use_diagrams: 다이어그램 이미지 생성 여부
        use_subtitles: 자막 생성 여부
        language: 언어 (ko, en)
    
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
        tts_files = None
        subtitles_file = None
        
        # 0. TTS 생성 (선택사항)
        if use_tts:
            try:
                logger.info("TTS 음성 생성 중...")
                from scripts.generate_tts import generate_tts_for_script
                tts_files = generate_tts_for_script(
                    script_data=script_data,
                    output_dir=temp_dir / "tts",
                    voice="alloy",
                    model="tts-1",
                    speed=1.0,
                    language=language
                )
                logger.info("TTS 음성 생성 완료")
            except Exception as e:
                logger.warning(f"TTS 생성 실패 (영상은 계속 생성됨): {e}")
                use_tts = False
        
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
            create_image_clip(hook_image_path, 15, hook_clip_path, fade_in=0.5, fade_out=0.3)
            all_clips.append(hook_clip_path)
        
        # 2. Sections 클립 생성
        sections = script_data.get("sections", [])
        logger.info(f"섹션 클립 생성 중... ({len(sections)}개 섹션)")
        
        for i, section in enumerate(sections, 1):
            logger.info(f"  섹션 {i}/{len(sections)}: {section.get('title', '')}")
            section_clips = create_section_clips(
                section, i, temp_dir, 
                use_broll=use_broll,
                use_tts=use_tts,
                use_code_snippets=use_code_snippets,
                use_diagrams=use_diagrams,
                language=language
            )
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
            create_image_clip(outro_image_path, 10, outro_clip_path, fade_in=0.3, fade_out=0.5)
            all_clips.append(outro_clip_path)
        
        # 4. 자막 파일 생성 (선택사항)
        if use_subtitles:
            try:
                logger.info("자막 파일 생성 중...")
                subtitles_file = temp_dir / "subtitles.srt"
                create_subtitles_file(script_data, subtitles_file, language=language)
                logger.info("자막 파일 생성 완료")
            except Exception as e:
                logger.warning(f"자막 파일 생성 실패 (영상은 계속 생성됨): {e}")
                subtitles_file = None
        
        # 5. 영상 합성
        logger.info(f"\n전체 영상 합성 중... ({len(all_clips)}개 클립)")
        combine_clips(
            clips=all_clips, 
            output_path=output_path, 
            bgm_path=bgm_path,
            tts_files=tts_files if use_tts else None,
            subtitles_file=subtitles_file
        )
        
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
    
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="TTS 사용 안 함"
    )
    
    parser.add_argument(
        "--no-code-snippets",
        action="store_true",
        help="코드 스니펫 사용 안 함"
    )
    
    parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="다이어그램 사용 안 함"
    )
    
    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        help="자막 사용 안 함"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        default="ko",
        choices=["ko", "en"],
        help="언어 (ko: 한국어, en: 영어)"
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
        use_broll=not args.no_broll,
        use_tts=not args.no_tts,
        use_code_snippets=not args.no_code_snippets,
        use_diagrams=not args.no_diagrams,
        use_subtitles=not args.no_subtitles,
        language=args.language
    )

