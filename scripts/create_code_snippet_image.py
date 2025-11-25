"""
코드 스니펫 이미지 생성 스크립트
PIL을 사용하여 코드 블록을 시각적으로 표현한 이미지 생성
"""
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import OUTPUT_DIR
from scripts.utils import setup_logging

# 로깅 설정
logger = setup_logging()


def create_code_snippet_image(
    code: str,
    language: str = "python",
    output_path: Optional[Path] = None,
    width: int = 1920,
    height: int = 1080,
    background_color: Tuple[int, int, int] = (30, 30, 40),
    code_color: Tuple[int, int, int] = (220, 220, 220),
    keyword_color: Tuple[int, int, int] = (86, 156, 214),
    string_color: Tuple[int, int, int] = (206, 145, 120),
    comment_color: Tuple[int, int, int] = (106, 153, 85),
    line_number_color: Tuple[int, int, int] = (128, 128, 128)
) -> Path:
    """
    코드 스니펫 이미지 생성
    
    Args:
        code: 코드 텍스트
        language: 프로그래밍 언어 (syntax highlighting용)
        output_path: 출력 경로
        width: 이미지 너비
        height: 이미지 높이
        background_color: 배경색
        code_color: 코드 기본 색상
        keyword_color: 키워드 색상
        string_color: 문자열 색상
        comment_color: 주석 색상
        line_number_color: 줄 번호 색상
    
    Returns:
        생성된 이미지 파일 경로
    """
    try:
        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # 폰트 로드 시도
        try:
            # macOS
            code_font = ImageFont.truetype("/Library/Fonts/Menlo.ttc", 32)
            line_font = ImageFont.truetype("/Library/Fonts/Menlo.ttc", 28)
        except:
            try:
                # Linux
                code_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
                line_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)
            except:
                code_font = ImageFont.load_default()
                line_font = ImageFont.load_default()
        
        # 코드 줄 분할
        lines = code.split('\n')
        
        # 간단한 syntax highlighting (Python 키워드)
        python_keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 
                          'for', 'while', 'return', 'try', 'except', 'finally', 
                          'with', 'as', 'pass', 'break', 'continue', 'yield', 
                          'lambda', 'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is']
        
        # 줄 번호 영역 너비
        line_number_width = 80
        code_start_x = line_number_width + 20
        code_width = width - code_start_x - 40
        
        # 줄 높이
        line_height = 50
        start_y = 100
        max_lines = (height - start_y - 100) // line_height
        
        # 표시할 줄 수 제한
        display_lines = lines[:max_lines]
        
        y = start_y
        
        for line_num, line in enumerate(display_lines, 1):
            # 줄 번호 그리기
            line_num_text = str(line_num).rjust(3)
            draw.text((20, y), line_num_text, fill=line_number_color, font=line_font)
            
            # 코드 그리기 (간단한 syntax highlighting)
            x = code_start_x
            
            # 주석 처리
            if line.strip().startswith('#'):
                draw.text((x, y), line, fill=comment_color, font=code_font)
            else:
                # 문자열 처리
                words = line.split()
                current_x = x
                
                for word in words:
                    # 키워드 체크
                    clean_word = word.strip('.,()[]{}:;')
                    if clean_word in python_keywords:
                        draw.text((current_x, y), word, fill=keyword_color, font=code_font)
                    elif word.startswith('"') or word.startswith("'") or word.startswith('f"') or word.startswith("f'"):
                        draw.text((current_x, y), word, fill=string_color, font=code_font)
                    else:
                        draw.text((current_x, y), word, fill=code_color, font=code_font)
                    
                    # 다음 단어 위치 계산
                    bbox = draw.textbbox((0, 0), word, font=code_font)
                    word_width = bbox[2] - bbox[0]
                    current_x += word_width + 10  # 단어 간격
            
            y += line_height
        
        # 이미지 저장
        if output_path is None:
            output_dir = OUTPUT_DIR / "images" / "code_snippets"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", optimize=True)
        
        logger.info(f"코드 스니펫 이미지 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"코드 스니펫 이미지 생성 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="코드 스니펫 이미지 생성")
    parser.add_argument("--code", type=str, help="코드 텍스트")
    parser.add_argument("--file", type=str, help="코드 파일 경로")
    parser.add_argument("--output", type=str, help="출력 이미지 경로")
    parser.add_argument("--language", type=str, default="python", help="프로그래밍 언어")
    
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        parser.error("--code 또는 --file이 필요합니다.")
    
    output_path = Path(args.output) if args.output else None
    create_code_snippet_image(
        code=code,
        language=args.language,
        output_path=output_path
    )
    print(f"코드 스니펫 이미지 생성 완료: {output_path}")

