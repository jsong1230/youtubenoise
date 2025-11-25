"""
TTS (Text-to-Speech) 음성 생성 스크립트
OpenAI TTS API를 사용하여 텍스트를 음성으로 변환
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from dotenv import load_dotenv
import openai

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import OUTPUT_DIR, PROJECT_ROOT
from scripts.utils import setup_logging

# .env 파일 로드
load_dotenv(project_root / ".env")

# 로깅 설정
logger = setup_logging()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_tts_audio(
    text: str,
    output_path: Optional[Path] = None,
    voice: str = "alloy",
    model: str = "tts-1",
    speed: float = 1.0,
    language: str = "ko"
) -> Path:
    """
    OpenAI TTS API를 사용하여 텍스트를 음성으로 변환
    
    Args:
        text: 변환할 텍스트
        output_path: 출력 오디오 파일 경로 (None이면 자동 생성)
        voice: 음성 종류 (alloy, echo, fable, onyx, nova, shimmer)
        model: 모델 (tts-1: 빠름, tts-1-hd: 고품질)
        speed: 재생 속도 (0.25 ~ 4.0)
        language: 언어 코드 (ko, en 등)
    
    Returns:
        생성된 오디오 파일 경로
    """
    try:
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        # 출력 경로 설정
        if output_path is None:
            output_dir = OUTPUT_DIR / "audio" / "tts"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"tts_{timestamp}.mp3"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TTS 음성 생성 중... (모델: {model}, 음성: {voice})")
        logger.debug(f"텍스트 길이: {len(text)}자")
        
        # OpenAI TTS API 호출
        response = openai.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed
        )
        
        # 오디오 파일 저장
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"TTS 음성 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"TTS 음성 생성 실패: {e}", exc_info=True)
        raise


def generate_tts_for_script(
    script_data: Dict,
    output_dir: Optional[Path] = None,
    voice: str = "alloy",
    model: str = "tts-1",
    speed: float = 1.0,
    language: str = "ko"
) -> Dict[str, Path]:
    """
    스크립트 전체에 대한 TTS 음성 생성
    
    Args:
        script_data: 스크립트 데이터 (hook, sections, outro 포함)
        output_dir: 출력 디렉토리
        voice: 음성 종류
        model: 모델
        speed: 재생 속도
        language: 언어 코드
    
    Returns:
        {
            "hook": Path,
            "sections": [Path, ...],
            "outro": Path
        }
    """
    try:
        if output_dir is None:
            output_dir = OUTPUT_DIR / "audio" / "tts"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        tts_files = {
            "hook": None,
            "sections": [],
            "outro": None
        }
        
        # Hook TTS 생성
        hook = script_data.get("hook", "")
        if hook:
            logger.info("Hook TTS 생성 중...")
            hook_path = output_dir / "hook.mp3"
            generate_tts_audio(
                text=hook,
                output_path=hook_path,
                voice=voice,
                model=model,
                speed=speed,
                language=language
            )
            tts_files["hook"] = hook_path
        
        # Sections TTS 생성
        sections = script_data.get("sections", [])
        logger.info(f"Sections TTS 생성 중... ({len(sections)}개 섹션)")
        
        for i, section in enumerate(sections, 1):
            title = section.get("title", "")
            content = section.get("content", "")
            
            # 제목과 내용을 합쳐서 TTS 생성
            section_text = f"{title}. {content}" if title else content
            
            section_path = output_dir / f"section_{i}.mp3"
            generate_tts_audio(
                text=section_text,
                output_path=section_path,
                voice=voice,
                model=model,
                speed=speed,
                language=language
            )
            tts_files["sections"].append(section_path)
        
        # Outro TTS 생성
        outro = script_data.get("outro", "")
        if outro:
            logger.info("Outro TTS 생성 중...")
            outro_path = output_dir / "outro.mp3"
            generate_tts_audio(
                text=outro,
                output_path=outro_path,
                voice=voice,
                model=model,
                speed=speed,
                language=language
            )
            tts_files["outro"] = outro_path
        
        logger.info(f"전체 TTS 생성 완료: {len(tts_files['sections'])}개 섹션")
        return tts_files
        
    except Exception as e:
        logger.error(f"스크립트 TTS 생성 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TTS 음성 생성")
    parser.add_argument("--text", type=str, help="변환할 텍스트")
    parser.add_argument("--output", type=str, help="출력 파일 경로")
    parser.add_argument("--voice", type=str, default="alloy", 
                       choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                       help="음성 종류")
    parser.add_argument("--model", type=str, default="tts-1",
                       choices=["tts-1", "tts-1-hd"],
                       help="모델 (tts-1: 빠름, tts-1-hd: 고품질)")
    parser.add_argument("--speed", type=float, default=1.0,
                       help="재생 속도 (0.25 ~ 4.0)")
    
    args = parser.parse_args()
    
    if args.text:
        output_path = Path(args.output) if args.output else None
        generate_tts_audio(
            text=args.text,
            output_path=output_path,
            voice=args.voice,
            model=args.model,
            speed=args.speed
        )
        print(f"TTS 생성 완료: {output_path}")
    else:
        parser.error("--text가 필요합니다.")

