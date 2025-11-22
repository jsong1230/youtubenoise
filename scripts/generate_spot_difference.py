"""
시니어용 틀린그림찾기 롱폼 영상 생성 메인 파이프라인
"""
import os
import sys
import json
import logging
import yaml
import random
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from config import LOG_FILE, OUTPUT_DIR, PROJECT_ROOT, DATA_DIR
from scripts.utils import setup_logging, load_yaml_file

# 로깅 설정
logger = setup_logging()


def load_spot_difference_presets() -> dict:
    """틀린그림찾기 프리셋 설정 파일 로드"""
    presets_path = DATA_DIR / "spot_difference_presets.yaml"
    return load_yaml_file(presets_path)


def generate_spot_difference_video(preset_name: str, output_path: Optional[Path] = None) -> Path:
    """
    시니어용 틀린그림찾기 롱폼 영상 생성
    
    Args:
        preset_name: 프리셋 이름
        output_path: 출력 파일 경로 (None이면 자동 생성)
    
    Returns:
        생성된 영상 파일 경로
    """
    try:
        # 프리셋 로드
        presets_data = load_spot_difference_presets()
        presets = presets_data.get("presets", {})
        defaults = presets_data.get("defaults", {})
        
        if preset_name not in presets:
            raise ValueError(f"프리셋을 찾을 수 없습니다: {preset_name}")
        
        preset = presets[preset_name]
        logger.info(f"틀린그림찾기 영상 생성 시작: {preset['name']}")
        
        num_problems = preset.get('num_problems', 15)
        num_differences = preset.get('num_differences', 3)
        countdown_seconds = preset.get('countdown_seconds', 10)
        themes = preset.get('themes', [])
        style = preset.get('image_style', '')
        
        # 출력 디렉토리 설정
        if output_path is None:
            output_dir = OUTPUT_DIR / "videos" / "spot_difference"
            output_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_path = output_dir / f"{date_str}_{preset_name}_ep01.mp4"
        
        temp_dir = output_path.parent / f"{output_path.stem}_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 문제 세트 생성
        from scripts.generate_spot_difference_image import generate_spot_difference_images
        from scripts.generate_spot_difference_metadata import (
            generate_problem_text,
            generate_answer_text,
            generate_video_metadata
        )
        from scripts.make_spot_difference_video import (
            create_problem_clip,
            combine_clips
        )
        
        all_clips = []
        used_themes = []
        
        logger.info(f"총 {num_problems}개의 문제 세트 생성 중...")
        
        for i in range(1, num_problems + 1):
            logger.info(f"\n[문제 {i}/{num_problems}] 생성 중...")
            
            # 주제 선택
            theme = random.choice(themes) if themes else "일상 풍경"
            used_themes.append(theme)
            
            # 1. 이미지 쌍 생성
            logger.info(f"  - 이미지 생성 중 (주제: {theme})...")
            image_data = generate_spot_difference_images(theme, num_differences, style)
            if not image_data:
                logger.warning(f"문제 {i} 이미지 생성 실패, 건너뜁니다.")
                continue
            
            # 2. 텍스트 생성
            logger.info(f"  - 텍스트 생성 중...")
            problem_text = generate_problem_text(i, num_differences, theme)
            answer_text = generate_answer_text(i, image_data['differences'])
            
            # 3. 문제 클립 생성
            logger.info(f"  - 클립 생성 중...")
            problem_data = {
                'problem_number': i,
                'base_image': image_data['base_image'],
                'modified_image': image_data['modified_image'],
                'differences': image_data['differences'],
                'problem_text': problem_text,
                'answer_text': answer_text['subtitle']
            }
            
            clips = create_problem_clip(problem_data, preset, temp_dir)
            all_clips.extend(clips)
            
            logger.info(f"  - 문제 {i} 완료 ({len(clips)}개 클립)")
        
        # 4. 영상 합성
        logger.info(f"\n전체 영상 합성 중... ({len(all_clips)}개 클립)")
        bgm_path = None
        if defaults.get('bgm_path'):
            bgm_path = PROJECT_ROOT / defaults['bgm_path']
        
        combine_clips(all_clips, output_path, bgm_path)
        
        # 5. 메타데이터 생성 및 저장
        logger.info("메타데이터 생성 중...")
        metadata = generate_video_metadata(num_problems, list(set(used_themes)))
        
        metadata_dir = output_path.parent
        metadata['video_path'] = str(output_path)
        metadata['preset'] = preset_name
        metadata['created_at'] = datetime.now().isoformat()
        
        # 메타데이터 파일 저장
        metadata_path = metadata_dir / f"{output_path.stem}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 텍스트 파일들 저장
        title_path = metadata_dir / f"{output_path.stem}_title.txt"
        with open(title_path, 'w', encoding='utf-8') as f:
            f.write(metadata['title'])
        
        description_path = metadata_dir / f"{output_path.stem}_description.txt"
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write(metadata['description'])
        
        logger.info(f"\n영상 생성 완료: {output_path}")
        logger.info(f"제목: {metadata['title']}")
        logger.info(f"메타데이터: {metadata_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"영상 생성 중 오류 발생: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        if len(sys.argv) < 2:
            print("사용법: python generate_spot_difference.py <preset_name> [output_path]")
            print("예시: python generate_spot_difference.py senior_easy")
            sys.exit(1)
        
        preset_name = sys.argv[1]
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        
        output_path = generate_spot_difference_video(preset_name, output_path)
        logger.info(f"생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

