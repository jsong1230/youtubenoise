"""
시니어용 종합 두뇌훈련 메타데이터 생성 (GPT API 활용)
YouTube 업로드용 제목, 설명, 챕터 생성
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from dotenv import load_dotenv
import openai

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging

# OpenAI API 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 로깅 설정
logger = setup_logging()


def generate_video_metadata(preset_name: str, num_problems: int, 
                           module_counts: Dict[str, int],
                           languages: List[str] = None) -> Dict:
    """
    영상 메타데이터 생성 (제목, 설명, 태그) - 다국어 지원
    
    Args:
        preset_name: 프리셋 이름
        num_problems: 총 문제 수
        module_counts: 모듈별 문제 수
        languages: 지원 언어 리스트 (예: ["ko", "en"])
    
    Returns:
        메타데이터 딕셔너리
    """
    languages = languages or ["ko"]
    is_bilingual = len(languages) >= 2 and "ko" in languages and "en" in languages
    is_english_only = languages and len(languages) == 1 and languages[0] == "en"
    
    try:
        # 모듈 정보 텍스트 생성 (언어에 따라)
        if is_english_only:
            module_info = ", ".join([f"{module}: {count} problems" 
                                    for module, count in module_counts.items()])
        else:
            module_info = ", ".join([f"{module}: {count}문제" 
                                    for module, count in module_counts.items()])
        
        # 다국어 메타데이터 생성
        if is_bilingual:
            prompt = f"""Create bilingual YouTube video metadata for a senior (60-80 years old) dementia prevention brain training video.

Preset: {preset_name}
Total problems: {num_problems}
Module composition: {module_info}
Primary Language: Korean
Secondary Language: English

Return JSON with:
{{
  "title": "English Title | Korean Title (max 100 characters total)",
  "description": "Section 1 (English description, 2-3 paragraphs)...\n\n---\n\nSection 2 (Korean description, 2-3 paragraphs)...\n\n---\n\nSection 3 (Mixed section with key info in both languages)...",
  "tags": ["tag1", "tag2", "태그1", "태그2", ...] (mix both languages, 15-20 tags)
}}

IMPORTANT: Title format must ALWAYS be "English Title | Korean Title" (English first, then Korean).
Description must ALWAYS have English section first, then Korean section.
Description should include:
- Purpose of the video
- What viewers will learn
- Module composition
- Benefits for seniors
- Hashtags at the end in both languages

Tags should mix Korean and English terms for SEO.
"""
        elif is_english_only:
            # 영어 전용 메타데이터 생성
            prompt = f"""Create YouTube video metadata for a senior (60-80 years old) dementia prevention brain training video.

Preset: {preset_name}
Total problems: {num_problems}
Module composition: {module_info}

Return JSON with:
{{
  "title": "YouTube Title (max 100 characters, senior-friendly)",
  "description": "YouTube description (detailed, with line breaks)",
  "tags": ["tag1", "tag2", ...] (15-20 tags in English)
}}

Title should be SEO-optimized but easy for seniors to understand.
Description should include:
- Purpose of the video
- What viewers will learn
- Module composition
- Benefits for seniors
- Hashtags at the end

Tags should be in English only, optimized for SEO.
"""
        else:
            # 한글 전용 메타데이터 생성
            prompt = f"""
시니어(60~80대)를 위한 치매 예방 두뇌훈련 영상의 YouTube 메타데이터를 생성해주세요.

프리셋: {preset_name}
총 문제 수: {num_problems}
모듈 구성: {module_info}

다음 형식의 JSON으로 응답해주세요:
{{
  "title": "YouTube 제목 (60자 이내, 시니어 친화적)",
  "description": "YouTube 설명 (상세하게, 줄바꿈 포함)",
  "tags": ["태그1", "태그2", ...]
}}

제목은 검색 최적화(SEO)를 고려하되 시니어가 이해하기 쉽게 작성해주세요.
설명에는 영상의 목적, 구성, 효과 등을 포함해주세요.
"""
        
        if is_bilingual:
            system_prompt = "You are a bilingual YouTube content metadata expert for senior brain training videos."
        elif is_english_only:
            system_prompt = "You are a YouTube content metadata expert for senior brain training videos. Create metadata in English only."
        else:
            system_prompt = "당신은 시니어용 YouTube 콘텐츠 메타데이터 작성 전문가입니다."
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        metadata = json.loads(response.choices[0].message.content)
        
        logger.info(f"메타데이터 생성 완료: {metadata['title']}")
        return metadata
        
    except Exception as e:
        logger.error(f"메타데이터 생성 실패: {e}", exc_info=True)
        # 기본 메타데이터 반환 (영어가 먼저 오도록 수정)
        if is_bilingual:
            return {
                "title": f"Senior Brain Training - {preset_name} ({num_problems} Problems) | 시니어 두뇌훈련 ({num_problems}문제)",
                "description": f"Dementia prevention brain training video.\n\n---\n\n치매 예방을 위한 두뇌훈련 영상입니다.\n\nTotal {num_problems} problems included.\n총 {num_problems}개의 문제로 구성되어 있습니다.",
                "tags": ["senior", "brain training", "dementia prevention", "cognitive training", "시니어", "두뇌훈련", "치매예방", "인지훈련"]
            }
        elif is_english_only:
            return {
                "title": f"Senior Brain Training - {preset_name} ({num_problems} Problems)",
                "description": f"Dementia prevention brain training video for seniors.\n\nTotal {num_problems} problems included.",
                "tags": ["senior", "brain training", "dementia prevention", "cognitive training", "memory", "elderly", "mental exercise"]
            }
        else:
            return {
                "title": f"시니어 두뇌훈련 - {preset_name} ({num_problems}문제)",
                "description": f"치매 예방을 위한 두뇌훈련 영상입니다.\n총 {num_problems}개의 문제로 구성되어 있습니다.",
                "tags": ["시니어", "두뇌훈련", "치매예방", "인지훈련", "노인", "기억력"]
            }


def generate_chapters(problems: List[Dict], languages: List[str] = None) -> List[Dict]:
    """
    챕터 마커 생성 (문제별 타임스탬프)
    
    Args:
        problems: 문제 리스트
        languages: 지원 언어 리스트 (기본값: ['ko'])
    
    Returns:
        챕터 리스트 (timestamp, title)
    """
    try:
        languages = languages or ["ko"]
        is_english_only = languages and len(languages) == 1 and languages[0] == "en"
        
        chapters = []
        current_time = 0
        
        # 인트로
        intro_title = "Start" if is_english_only else "시작"
        chapters.append({
            "timestamp": "0:00",
            "title": intro_title
        })
        current_time += 5  # 인트로 5초
        
        # 각 문제
        module_names_ko = {
            "number_memory": "숫자 기억",
            "missing_object": "사라진 물건 찾기",
            "pattern_sequence": "패턴 순서",
            "word_association": "단어 연상",
            "clock_reading": "시계 읽기",
            "korean_word_puzzle": "한글 퍼즐",
            "color_memory": "색상 기억",
            "simple_calculation": "간단한 계산",
            "direction_memory": "방향 기억",
            "category_classification": "카테고리 분류",
            "shape_matching": "도형 매칭"
        }
        
        module_names_en = {
            "number_memory": "Number Memory",
            "missing_object": "Missing Object",
            "pattern_sequence": "Pattern Sequence",
            "word_association": "Word Association",
            "clock_reading": "Clock Reading",
            "korean_word_puzzle": "Korean Word Puzzle",
            "color_memory": "Color Memory",
            "simple_calculation": "Simple Calculation",
            "direction_memory": "Direction Memory",
            "category_classification": "Category Classification",
            "shape_matching": "Shape Matching"
        }
        
        module_names = module_names_en if is_english_only else module_names_ko
        problem_prefix = "Problem" if is_english_only else "문제"
        
        for i, problem in enumerate(problems, 1):
            minutes = current_time // 60
            seconds = current_time % 60
            timestamp = f"{minutes}:{seconds:02d}"
            
            module = problem.get('module', 'unknown')
            module_name = module_names.get(module, module)
            
            title = f"{problem_prefix} {i}: {module_name}"
            chapters.append({
                "timestamp": timestamp,
                "title": title
            })
            
            # 다음 문제까지의 시간 계산
            problem_duration = (
                3 +  # 문제 소개
                problem.get('display_seconds', 5) +  # 문제 표시
                problem.get('countdown_seconds', 10) +  # 카운트다운
                5  # 정답 화면
            )
            current_time += problem_duration
        
        logger.info(f"챕터 생성 완료: {len(chapters)}개")
        return chapters
        
    except Exception as e:
        logger.error(f"챕터 생성 실패: {e}", exc_info=True)
        return []


def format_chapters_for_youtube(chapters: List[Dict], languages: List[str] = None) -> str:
    """
    YouTube 설명란에 넣을 챕터 텍스트 포맷
    
    Args:
        chapters: 챕터 리스트
        languages: 지원 언어 리스트 (기본값: ['ko'])
    
    Returns:
        포맷된 챕터 텍스트
    """
    languages = languages or ["ko"]
    is_english_only = languages and len(languages) == 1 and languages[0] == "en"
    
    header = "📚 Chapters" if is_english_only else "📚 목차 (Chapters)"
    lines = [header]
    for chapter in chapters:
        lines.append(f"{chapter['timestamp']} - {chapter['title']}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 테스트 코드
    metadata = generate_video_metadata(
        "mixed_brain_training_senior",
        30,
        {
            "number_memory": 8,
            "missing_object": 6,
            "pattern_sequence": 5,
            "word_association": 6,
            "clock_reading": 3,
            "korean_word_puzzle": 2
        }
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
