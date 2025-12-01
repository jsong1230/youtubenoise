"""
~/Downloads 폴더에서 이미지 파일을 찾아서 썸네일로 사용
파일 크기만 조정하여 YouTube 썸네일 형식으로 변환
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils import setup_logging

# 로깅 설정
logger = setup_logging()

# 지원하는 이미지 확장자
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


def find_image_in_downloads() -> Optional[Path]:
    """
    ~/Downloads 폴더에서 썸네일용 이미지 파일 찾기
    파일명 패턴으로 구분: thumb_, thumbnail_, 썸네일_ 접두사 우선
    
    Returns:
        찾은 이미지 파일 경로 (없으면 None)
    """
    downloads_dir = Path.home() / "Downloads"
    
    if not downloads_dir.exists():
        logger.warning(f"Downloads 폴더를 찾을 수 없습니다: {downloads_dir}")
        return None
    
    # 썸네일용 패턴 (접두사 또는 파일명에 포함)
    thumb_patterns = ['thumb_', 'thumbnail_', '썸네일_', '썸네일이미지_']
    thumb_keywords = ['thumbnail', 'thumb', '썸네일']
    
    # 모든 이미지 파일 찾기
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        image_files.extend(downloads_dir.glob(f"*{ext}"))
        image_files.extend(downloads_dir.glob(f"*{ext.upper()}"))
    
    if not image_files:
        logger.warning(f"Downloads 폴더에서 이미지 파일을 찾을 수 없습니다.")
        return None
    
    # 1순위: 썸네일 패턴이 있는 파일 찾기
    thumb_files = []
    for img_file in image_files:
        filename_lower = img_file.name.lower()
        # 접두사로 시작하거나 파일명에 키워드가 포함된 경우
        if (any(filename_lower.startswith(pattern.lower()) for pattern in thumb_patterns) or
            any(keyword in filename_lower for keyword in thumb_keywords)):
            # 배경 키워드는 제외
            if not any(bg_keyword in filename_lower for bg_keyword in ['background', 'bg', '배경']):
                thumb_files.append(img_file)
    
    if thumb_files:
        # 썸네일 파일이 있으면 가장 최근 것 사용
        thumb_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        selected_image = thumb_files[0]
        logger.info(f"Downloads에서 썸네일 이미지 파일 발견 (접두사 매칭): {selected_image.name}")
        logger.info(f"   경로: {selected_image}")
        logger.info(f"   크기: {selected_image.stat().st_size / 1024:.1f} KB")
        return selected_image
    
    # 2순위: 썸네일 접두사가 없으면 가장 최근 이미지 사용
    image_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    selected_image = image_files[0]
    logger.info(f"Downloads에서 썸네일 이미지 파일 발견 (가장 최근): {selected_image.name}")
    logger.info(f"   경로: {selected_image}")
    logger.info(f"   크기: {selected_image.stat().st_size / 1024:.1f} KB")
    
    return selected_image


def resize_image_to_thumbnail(
    image_path: Path,
    output_path: Optional[Path] = None,
    target_size: tuple[int, int] = (1280, 720),
    quality: int = 90
) -> Path:
    """
    이미지를 YouTube 썸네일 크기로 리사이즈
    
    Args:
        image_path: 원본 이미지 경로
        output_path: 출력 경로 (None이면 자동 생성)
        target_size: 목표 크기 (width, height)
        quality: JPEG 품질 (1-100)
    
    Returns:
        리사이즈된 이미지 경로
    """
    try:
        # 이미지 열기
        logger.info(f"이미지 로드 중: {image_path}")
        img = Image.open(image_path)
        img = img.convert("RGB")  # RGB로 변환 (JPEG 저장을 위해)
        
        original_size = img.size
        logger.info(f"원본 크기: {original_size[0]}x{original_size[1]}")
        
        # 비율 유지하면서 리사이즈
        target_width, target_height = target_size
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # 1280x720 크기의 캔버스 생성 (중앙 정렬)
        thumbnail = Image.new("RGB", target_size, (0, 0, 0))  # 검은 배경
        
        # 이미지를 중앙에 배치
        x_offset = (target_width - img.size[0]) // 2
        y_offset = (target_height - img.size[1]) // 2
        thumbnail.paste(img, (x_offset, y_offset))
        
        # 출력 경로 설정
        if output_path is None:
            output_dir = project_root / "output" / "thumbnails"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{image_path.stem}_thumbnail.jpg"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # JPEG로 저장 (YouTube 권장 형식)
        thumbnail.save(str(output_path), "JPEG", quality=quality, optimize=True)
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"썸네일 생성 완료: {output_path}")
        logger.info(f"   크기: {target_width}x{target_height}")
        logger.info(f"   파일 크기: {file_size_mb:.2f} MB")
        
        return output_path
        
    except Exception as e:
        logger.error(f"이미지 리사이즈 실패: {e}", exc_info=True)
        raise


def create_thumbnail_from_downloads(
    output_path: Optional[Path] = None,
    target_size: tuple[int, int] = (1280, 720),
    quality: int = 90
) -> Optional[Path]:
    """
    ~/Downloads 폴더에서 이미지를 찾아서 썸네일 생성
    
    Args:
        output_path: 출력 경로 (None이면 자동 생성)
        target_size: 목표 크기 (width, height)
        quality: JPEG 품질 (1-100)
    
    Returns:
        생성된 썸네일 경로 (실패 시 None)
    """
    try:
        # Downloads에서 이미지 찾기
        image_path = find_image_in_downloads()
        if not image_path:
            logger.warning("Downloads 폴더에서 이미지를 찾을 수 없습니다.")
            return None
        
        # 썸네일 생성
        thumbnail_path = resize_image_to_thumbnail(
            image_path,
            output_path=output_path,
            target_size=target_size,
            quality=quality
        )
        
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"썸네일 생성 실패: {e}", exc_info=True)
        return None


def main():
    """메인 실행 함수"""
    try:
        import argparse
        
        parser = argparse.ArgumentParser(description="Downloads 폴더에서 이미지를 찾아 썸네일 생성")
        parser.add_argument("--output", type=str, help="출력 경로")
        parser.add_argument("--width", type=int, default=1280, help="썸네일 너비 (기본값: 1280)")
        parser.add_argument("--height", type=int, default=720, help="썸네일 높이 (기본값: 720)")
        parser.add_argument("--quality", type=int, default=90, help="JPEG 품질 (1-100, 기본값: 90)")
        
        args = parser.parse_args()
        
        output_path = Path(args.output) if args.output else None
        target_size = (args.width, args.height)
        
        thumbnail_path = create_thumbnail_from_downloads(
            output_path=output_path,
            target_size=target_size,
            quality=args.quality
        )
        
        if thumbnail_path:
            print(f"\n썸네일 생성 완료: {thumbnail_path}")
            return thumbnail_path
        else:
            print("\n썸네일 생성 실패")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()




