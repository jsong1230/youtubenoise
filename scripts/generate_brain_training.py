"""
시니어용 종합 두뇌훈련 롱폼 영상 생성 메인 파이프라인
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
from collections import Counter

from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from config import LOG_FILE, OUTPUT_DIR, PROJECT_ROOT, DATA_DIR
from scripts.utils import setup_logging, load_yaml_file

# 로깅 설정
logger = setup_logging()


def load_brain_training_presets() -> dict:
    """두뇌훈련 프리셋 설정 파일 로드"""
    # config 디렉토리에서 프리셋 파일 로드
    presets_path = PROJECT_ROOT / "config" / "brain_training_presets.yaml"
    return load_yaml_file(presets_path)


def select_problems_by_weight(modules: List[Dict], num_problems: int) -> List[str]:
    """
    가중치에 따라 문제 모듈 선택
    
    Args:
        modules: 모듈 리스트 (type, weight)
        num_problems: 총 문제 수
    
    Returns:
        선택된 모듈 타입 리스트
    """
    selected = []
    
    # 가중치 기반 문제 수 계산
    total_weight = sum(m['weight'] for m in modules)
    for module in modules:
        count = int(num_problems * module['weight'] / total_weight)
        selected.extend([module['type']] * count)
    
    # 남은 문제는 랜덤으로 채우기
    while len(selected) < num_problems:
        module = random.choice(modules)
        selected.append(module['type'])
    
    # 섞기
    random.shuffle(selected)
    
    return selected[:num_problems]


def generate_brain_training_video(preset_name: str, output_path: Optional[Path] = None) -> Path:
    """
    시니어용 종합 두뇌훈련 롱폼 영상 생성
    
    Args:
        preset_name: 프리셋 이름
        output_path: 출력 파일 경로 (None이면 자동 생성)
    
    Returns:
        생성된 영상 파일 경로
    """
    try:
        # 프리셋 로드
        presets_data = load_brain_training_presets()
        presets = presets_data.get("presets", {})
        defaults = presets_data.get("defaults", {})
        
        if preset_name not in presets:
            raise ValueError(f"프리셋을 찾을 수 없습니다: {preset_name}")
        
        preset = presets[preset_name]
        logger.info(f"두뇌훈련 영상 생성 시작: {preset['name']}")
        
        modules = preset.get('modules', [])
        problem_settings = preset.get('problem_settings', {})
        themes = preset.get('themes', [])
        languages = preset.get('languages', ['ko'])  # 다국어 지원
        
        # 목표 영상 길이 기반으로 문제 수 자동 계산
        target_duration_minutes = preset.get('target_duration_minutes', None)
        if target_duration_minutes:
            # 기본 시간 설정
            intro_duration = defaults.get('intro_duration', 10)
            outro_duration = defaults.get('outro_duration', 10)
            problem_intro_duration = defaults.get('problem_intro_duration', 8)
            answer_display_duration = defaults.get('answer_display_duration', 15)
            
            # 각 문제당 평균 시간 계산 (모듈별 설정의 평균값 사용)
            avg_display_seconds = 0
            avg_countdown_seconds = 0
            count = 0
            
            for module in modules:
                module_type = module.get('type')
                if module_type == 'missing_object':
                    continue
                settings = problem_settings.get(module_type, {})
                avg_display_seconds += settings.get('display_seconds', 14)
                avg_countdown_seconds += settings.get('countdown_seconds', 15)
                count += 1
            
            if count > 0:
                avg_display_seconds = avg_display_seconds / count
                avg_countdown_seconds = avg_countdown_seconds / count
            else:
                avg_display_seconds = 14
                avg_countdown_seconds = 15
            
            # 문제당 평균 시간
            avg_problem_duration = problem_intro_duration + avg_display_seconds + avg_countdown_seconds + answer_display_duration
            
            # 목표 시간에서 인트로/아웃트로 제외
            target_seconds = target_duration_minutes * 60
            available_seconds = target_seconds - intro_duration - outro_duration
            
            # 필요한 문제 수 계산
            num_problems = int(available_seconds / avg_problem_duration)
            
            logger.info(f"목표 영상 길이: {target_duration_minutes}분")
            logger.info(f"문제당 평균 시간: {avg_problem_duration:.1f}초 (소개 {problem_intro_duration}초 + 표시 {avg_display_seconds:.1f}초 + 카운트다운 {avg_countdown_seconds:.1f}초 + 정답 {answer_display_duration}초)")
            logger.info(f"계산된 문제 수: {num_problems}개 (예상 영상 길이: {num_problems * avg_problem_duration + intro_duration + outro_duration:.0f}초 = {((num_problems * avg_problem_duration + intro_duration + outro_duration) / 60):.1f}분)")
        else:
            # 목표 길이가 없으면 프리셋의 num_problems 사용
            num_problems = preset.get('num_problems', 20)
            logger.info(f"프리셋 설정 문제 수: {num_problems}개")
        
        # 출력 디렉토리 설정
        if output_path is None:
            output_dir = OUTPUT_DIR / "videos" / "brain_training"
            output_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            # 언어 정보를 파일명에 포함 (한글/영어 구분)
            languages = preset.get('languages', ['ko'])
            lang_code = languages[0] if languages else 'ko'  # 첫 번째 언어 사용
            output_path = output_dir / f"{date_str}_{preset_name}_{lang_code}_ep01.mp4"
        
        temp_dir = output_path.parent / f"{output_path.stem}_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 문제 모듈 선택
        selected_modules = select_problems_by_weight(modules, num_problems)
        
        # missing_object 모듈 필터링 (비활성화됨)
        selected_modules = [m for m in selected_modules if m != "missing_object"]
        
        # 영어 버전에서는 korean_word_puzzle 모듈 제외 (한글 전용 모듈)
        if languages and languages[0] == "en":
            selected_modules = [m for m in selected_modules if m != "korean_word_puzzle"]
            logger.info("영어 버전이므로 korean_word_puzzle 모듈을 제외합니다.")
        
        # 필터링 후 문제 수가 부족하면 다시 선택
        if len(selected_modules) < num_problems:
            logger.warning(f"모듈 제거 후 문제 수 부족 ({len(selected_modules)}/{num_problems}), 다시 선택합니다.")
            # 제외할 모듈 목록
            excluded_modules = ["missing_object"]
            if languages and languages[0] == "en":
                excluded_modules.append("korean_word_puzzle")
            # 제외할 모듈을 제외한 모듈로 다시 선택
            filtered_modules = [m for m in modules if m['type'] not in excluded_modules]
            if filtered_modules:
                selected_modules = select_problems_by_weight(filtered_modules, num_problems)
            else:
                logger.error("사용 가능한 모듈이 없습니다.")
                raise ValueError("사용 가능한 모듈이 없습니다.")
        
        module_counts = Counter(selected_modules)
        
        logger.info(f"총 {num_problems}개의 문제 생성 중...")
        logger.info(f"모듈 구성: {dict(module_counts)}")
        
        # 문제 생성
        from scripts.generate_brain_training_content import MODULE_GENERATORS
        from scripts.make_brain_training_video import create_problem_clip, combine_clips
        
        all_clips = []
        all_problems = []
        
        for i, module_type in enumerate(selected_modules, 1):
            logger.info(f"\n[문제 {i}/{num_problems}] {module_type} 생성 중...")
            
            # 모듈별 설정 가져오기
            settings = problem_settings.get(module_type, {})
            
            # 문제 생성
            generator = MODULE_GENERATORS.get(module_type)
            if not generator:
                logger.warning(f"지원하지 않는 모듈: {module_type}")
                continue
            
            # missing_object 모듈은 비활성화됨
            if module_type == "missing_object":
                logger.warning(f"missing_object 모듈은 비활성화되어 있습니다. 건너뜁니다.")
                continue
            
            # 영어 버전에서는 korean_word_puzzle 모듈 제외
            if module_type == "korean_word_puzzle" and languages and languages[0] == "en":
                logger.warning(f"korean_word_puzzle 모듈은 영어 버전에서 사용할 수 없습니다. 건너뜁니다.")
                continue
            
            # 문제 인덱스와 언어를 전달하여 다양성 및 다국어 지원 확보
            import inspect
            sig = inspect.signature(generator)
            params = sig.parameters
            kwargs = {}
            if 'languages' in params:
                kwargs['languages'] = languages
            if 'problem_index' in params:
                kwargs['problem_index'] = i-1
            
            # problem_data 초기화 및 생성
            problem_data = None
            try:
                if kwargs:
                    problem_data = generator(settings, **kwargs)
                else:
                    problem_data = generator(settings)
            except Exception as e:
                logger.error(f"문제 생성 중 오류 발생: {e}")
                problem_data = None
            
            if not problem_data:
                logger.warning(f"문제 {i} 생성 실패, 건너뜁니다.")
                continue
            
            # 문제 번호 추가
            problem_data['problem_number'] = i
            all_problems.append(problem_data)
            
            # 클립 생성
            logger.info(f"  - 클립 생성 중...")
            clips = create_problem_clip(problem_data, preset, temp_dir)
            all_clips.extend(clips)
            
            logger.info(f"  - 문제 {i} 완료 ({len(clips)}개 클립)")
        
        # 영상 합성
        logger.info(f"\n전체 영상 합성 중... ({len(all_clips)}개 클립)")
        bgm_path = None
        
        # BGM 경로 확인
        if defaults.get('bgm_path'):
            bgm_path = PROJECT_ROOT / defaults['bgm_path']
            if not bgm_path.exists():
                logger.warning(f"설정된 BGM 파일을 찾을 수 없습니다: {bgm_path}")
                bgm_path = None
        
        # BGM이 없으면 자동으로 생성 (항상 piano 폴더 사용)
        if not bgm_path:
            logger.info("BGM이 설정되지 않아 piano 폴더에서 자동으로 생성합니다...")
            try:
                from scripts.generate_bgm import generate_bgm
                # 영상 길이 계산 (문제 수와 설정 기반)
                intro_duration = defaults.get('intro_duration', 10)
                outro_duration = defaults.get('outro_duration', 10)
                problem_intro = defaults.get('problem_intro_duration', 8)
                answer_duration = defaults.get('answer_display_duration', 15)
                
                # 각 문제당 평균 시간 계산
                avg_display = 14  # 평균 display_seconds
                avg_countdown = 15  # 평균 countdown_seconds
                avg_problem_duration = problem_intro + avg_display + avg_countdown + answer_duration
                
                # 총 영상 길이 계산 (초)
                total_seconds = intro_duration + outro_duration + (num_problems * avg_problem_duration)
                estimated_duration_minutes = max(30, int(total_seconds / 60) + 1)  # 최소 30분, 여유있게 +1분
                
                logger.info(f"예상 영상 길이: {total_seconds}초 ({estimated_duration_minutes}분)")
                # piano 프리셋 사용 (public_domain_subdir: "piano"로 설정됨)
                bgm_path = generate_bgm("piano", estimated_duration_minutes)
                logger.info(f"BGM 생성 완료 (piano 폴더 사용): {bgm_path}")
            except Exception as e:
                logger.warning(f"BGM 자동 생성 실패: {e}. BGM 없이 진행합니다.")
                bgm_path = None
        
        combine_clips(all_clips, output_path, bgm_path)
        
        # 메타데이터 생성 및 저장
        logger.info("메타데이터 생성 중...")
        from scripts.generate_brain_training_metadata import (
            generate_video_metadata,
            generate_chapters,
            format_chapters_for_youtube
        )
        
        metadata = generate_video_metadata(preset_name, len(all_problems), dict(module_counts), languages)
        chapters = generate_chapters(all_problems, languages)
        
        metadata_dir = output_path.parent
        full_metadata = {
            "video_path": str(output_path),
            "preset": preset_name,
            "created_at": datetime.now().isoformat(),
            "num_problems": len(all_problems),
            "module_counts": dict(module_counts),
            "title": metadata['title'],
            "description": metadata['description'],
            "tags": metadata['tags'],
            "chapters": chapters
        }
        
        # 메타데이터 파일 저장
        metadata_path = metadata_dir / f"{output_path.stem}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(full_metadata, f, ensure_ascii=False, indent=2)
        
        # 텍스트 파일들 저장
        title_path = metadata_dir / f"{output_path.stem}_title.txt"
        with open(title_path, 'w', encoding='utf-8') as f:
            f.write(metadata['title'])
        
        # 설명 + 챕터
        description_with_chapters = metadata['description'] + "\n\n" + format_chapters_for_youtube(chapters, languages)
        description_path = metadata_dir / f"{output_path.stem}_description.txt"
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write(description_with_chapters)
        
        # 태그
        tags_path = metadata_dir / f"{output_path.stem}_tags.txt"
        with open(tags_path, 'w', encoding='utf-8') as f:
            f.write(", ".join(metadata['tags']))
        
        # 썸네일 자동 생성
        logger.info("썸네일 생성 중...")
        try:
            from scripts.create_thumbnail_dalle import create_thumbnail_with_dalle
            
            # 언어 설정 확인
            lang_code = "ko"
            if languages and languages[0] == "en":
                lang_code = "en"
            
            thumbnail_path = metadata_dir / f"{output_path.stem}_thumbnail.jpg"
            create_thumbnail_with_dalle(
                metadata['title'],
                language=lang_code,
                output_path=thumbnail_path
            )
            logger.info(f"썸네일 생성 완료: {thumbnail_path}")
            
            # 메타데이터에 썸네일 경로 추가
            full_metadata['thumbnail_path'] = str(thumbnail_path)
            
            # 메타데이터 파일 업데이트
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(full_metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"썸네일 생성 실패 (영상은 생성됨): {e}")
            # 썸네일 생성 실패해도 영상 생성은 성공으로 처리
        
        logger.info(f"\n영상 생성 완료: {output_path}")
        logger.info(f"제목: {metadata['title']}")
        logger.info(f"메타데이터: {metadata_path}")
        if 'thumbnail_path' in locals():
            logger.info(f"썸네일: {thumbnail_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"영상 생성 중 오류 발생: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        if len(sys.argv) < 2:
            print("사용법: python generate_brain_training.py <preset_name> [output_path]")
            print("예시: python generate_brain_training.py number_memory_senior")
            sys.exit(1)
        
        preset_name = sys.argv[1]
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        
        output_path = generate_brain_training_video(preset_name, output_path)
        logger.info(f"생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
