"""
시니어용 종합 두뇌훈련 콘텐츠 생성 (GPT API 활용)
각 모듈별 문제 생성 및 이미지 생성
"""
import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
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


def generate_number_memory_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    숫자 기억 문제 생성
    
    Args:
        settings: 문제 설정 (digit_count, display_seconds 등)
        languages: 지원 언어 리스트 (예: ["ko", "en"])
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        digit_count = settings.get('digit_count', 4)
        languages = languages or ["ko"]
        
        # 랜덤 숫자 생성
        number = ''.join([str(random.randint(0, 9)) for _ in range(digit_count)])
        
        # 다국어 텍스트 생성
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            # GPT로 다국어 텍스트 생성
            try:
                prompt = f"""Create bilingual text for a number memory problem.

Digit count: {digit_count}
Number to remember: {number}

Return JSON with:
{{
  "problem_text_ko": "화면에 나오는 {digit_count}자리 숫자를 기억해보세요.",
  "problem_text_en": "Remember the {digit_count}-digit number shown on screen.",
  "explanation_ko": "보여드린 숫자는 {number}입니다.",
  "explanation_en": "The number shown was {number}."
}}"""
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator for senior brain training."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(response.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", f"화면에 나오는 {digit_count}자리 숫자를 기억해보세요.")
                problem_text_en = text_data.get("problem_text_en", f"Remember the {digit_count}-digit number shown on screen.")
                explanation_ko = text_data.get("explanation_ko", f"보여드린 숫자는 {number}입니다.")
                explanation_en = text_data.get("explanation_en", f"The number shown was {number}.")
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
                problem_text_ko = f"화면에 나오는 {digit_count}자리 숫자를 기억해보세요."
                problem_text_en = f"Remember the {digit_count}-digit number shown on screen."
                explanation_ko = f"보여드린 숫자는 {number}입니다."
                explanation_en = f"The number shown was {number}."
        else:
            problem_text_ko = f"화면에 나오는 {digit_count}자리 숫자를 기억해보세요."
            problem_text_en = f"Remember the {digit_count}-digit number shown on screen."
            explanation_ko = f"보여드린 숫자는 {number}입니다."
            explanation_en = f"The number shown was {number}."
        
        return {
            "module": "number_memory",
            "display_seconds": settings.get('display_seconds', 5),
            "countdown_seconds": settings.get('countdown_seconds', 10),
            "problem_text": problem_text_ko,  # 기본값
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "number": number,
                "digit_count": digit_count
            },
            "answer_data": {
                "correct_answer": number,
                "explanation": explanation_ko,  # 기본값
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
    except Exception as e:
        logger.error(f"숫자 기억 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_missing_object_problem(settings: Dict, theme: str) -> Dict:
    """
    사라진 물건 찾기 문제 생성 (GPT Image API 활용)
    
    Args:
        settings: 문제 설정
        theme: 장면 테마
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        num_objects = settings.get('num_objects', 8)
        num_missing = settings.get('num_missing', 2)
        
        # GPT로 장면 설명 및 물건 목록 생성
        prompt = f"""
시니어를 위한 '사라진 물건 찾기' 문제를 만들어주세요.

테마: {theme}
물건 개수: {num_objects}개
사라질 물건: {num_missing}개

다음 형식의 JSON으로 응답해주세요:
{{
  "scene_description": "장면 설명 (한글)",
  "objects": ["물건1", "물건2", ...],
  "missing_objects": ["사라질물건1", "사라질물건2"]
}}

물건은 시니어가 쉽게 알아볼 수 있는 일상적인 것들로 선택해주세요.
"""
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        
        content_data = json.loads(response.choices[0].message.content)
        
        # 이미지 생성 프롬프트
        image_prompt = f"""
Warm, clear, simple illustration for seniors showing: {content_data['scene_description']}
Objects visible: {', '.join(content_data['objects'])}
Style: high contrast, large objects, senior-friendly, cozy atmosphere, pastel colors
"""
        
        # 원본 이미지 생성 (모든 물건 포함)
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        
        base_image_url = image_response.data[0].url
        
        # 수정본 이미지 생성 (특정 물건이 없는 버전)
        # 같은 장면이지만 missing_objects가 없는 버전을 생성
        remaining_objects = [obj for obj in content_data['objects'] 
                            if obj not in content_data['missing_objects']]
        
        modified_image_prompt = f"""
Warm, clear, simple illustration for seniors showing: {content_data['scene_description']}
Objects visible: {', '.join(remaining_objects)}
Objects NOT visible (removed): {', '.join(content_data['missing_objects'])}
Style: high contrast, large objects, senior-friendly, cozy atmosphere, pastel colors
Same scene and composition as the original, but without the removed objects.
"""
        
        modified_image_response = openai.images.generate(
            model="dall-e-3",
            prompt=modified_image_prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        
        modified_image_url = modified_image_response.data[0].url
        
        return {
            "module": "missing_object",
            "display_seconds": settings.get('display_seconds', 10),
            "countdown_seconds": settings.get('countdown_seconds', 15),
            "problem_text": f"두 그림을 비교하여 사라진 물건 {num_missing}개를 찾아보세요.",
            "problem_data": {
                "theme": theme,
                "base_image_url": base_image_url,
                "modified_image_url": modified_image_url,  # 수정본 이미지 URL 추가
                "all_objects": content_data['objects'],
                "missing_objects": content_data['missing_objects'],
                "scene_description": content_data['scene_description']
            },
            "answer_data": {
                "correct_answer": content_data['missing_objects'],
                "explanation": f"사라진 물건은 {', '.join(content_data['missing_objects'])}입니다."
            }
        }
        
    except Exception as e:
        logger.error(f"사라진 물건 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_pattern_sequence_problem(settings: Dict, problem_index: int = 0, languages: List[str] = None) -> Dict:
    """
    패턴 순서 맞추기 문제 생성
    
    Args:
        settings: 문제 설정
        problem_index: 문제 인덱스 (다양성을 위해 사용)
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        sequence_length = settings.get('sequence_length', 4)
        pattern_type = settings.get('pattern_type', 'shapes')
        
        # 패턴 타입 다양화 (문제 인덱스에 따라)
        pattern_types = ['shapes', 'colors', 'numbers', 'letters', 'symbols']
        actual_pattern_type = pattern_types[problem_index % len(pattern_types)]
        
        # 언어 설정 확인
        languages = languages or ["ko"]
        is_english_only = languages and languages[0] == "en"
        
        # GPT로 패턴 생성 (언어에 따라 프롬프트 변경)
        if is_english_only:
            prompt = f"""
Create a pattern sequence problem for seniors.

Pattern type: {actual_pattern_type}
Pattern length: {sequence_length}
Problem number: {problem_index + 1}
Problem index: {problem_index} (Use this value to generate a completely different pattern)

**Important**: 
- Create a unique pattern that matches problem index {problem_index}.
- Use a completely different pattern rule from previous problems.
- Use different pattern types and rules.
(Examples: color sequence, shape size, number increase/decrease, alphabet sequence, etc.)

Return JSON in the following format:
{{
  "pattern": ["Element1", "Element2", "Element3", "Element4"],
  "next_element": "NextElement",
  "choices": ["Choice1", "Choice2", "Choice3"],
  "explanation": "Pattern explanation in English"
}}

Create a simple pattern rule that seniors can easily understand.
Use English words, letters, numbers, or symbols only. Do not use Korean characters.
"""
            system_content = "You are a content creator for senior brain training. Create completely different patterns for each problem. Always use English only."
        else:
            prompt = f"""
시니어를 위한 패턴 순서 맞추기 문제를 만들어주세요.

패턴 타입: {actual_pattern_type}
패턴 길이: {sequence_length}
문제 번호: {problem_index + 1}
문제 인덱스: {problem_index} (이 값을 활용하여 완전히 다른 패턴을 생성하세요)

**중요**: 
- 문제 인덱스 {problem_index}에 맞는 고유한 패턴을 만들어주세요.
- 이전 문제들과 완전히 다른 패턴 규칙을 사용하세요.
- 패턴 타입도 다르게, 규칙도 다르게 해주세요.
(예: 색상 순서, 도형 크기, 숫자 증가/감소, 알파벳 순서 등)

다음 형식의 JSON으로 응답해주세요:
{{
  "pattern": ["요소1", "요소2", "요소3", "요소4"],
  "next_element": "다음요소",
  "choices": ["선택1", "선택2", "선택3"],
  "explanation": "패턴 설명"
}}

패턴은 시니어가 쉽게 이해할 수 있는 단순한 규칙으로 만들어주세요.
"""
            system_content = "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다. 각 문제마다 완전히 다른 패턴을 만들어야 합니다."
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=1.0  # 다양성을 위해 temperature 증가
        )
        
        pattern_data = json.loads(response.choices[0].message.content)
        
        # 패턴 검증: 명백히 잘못된 패턴은 재생성
        pattern = pattern_data.get('pattern', [])
        next_element = pattern_data.get('next_element', '')
        choices = pattern_data.get('choices', [])
        
        # 기본 검증: 필수 필드 존재 확인
        if not pattern or not next_element or not choices:
            logger.warning(f"패턴 데이터 필수 필드 누락, 재생성 시도")
            # 간단한 재시도 (최대 1회)
            try:
                retry_response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다. 논리적이고 명확한 패턴을 만들어야 합니다."},
                        {"role": "user", "content": prompt + "\n\n**중요**: 반드시 논리적이고 명확한 패턴 규칙을 만들어주세요. 예를 들어, 색상 순서라면 빨강-주황-노랑-초록-파랑-남색-보라 같은 명확한 순서를 사용하세요."}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                pattern_data = json.loads(retry_response.choices[0].message.content)
                pattern = pattern_data.get('pattern', [])
                next_element = pattern_data.get('next_element', '')
                choices = pattern_data.get('choices', [])
            except Exception as e:
                logger.error(f"패턴 재생성 실패: {e}")
        
        # 패턴 설명 검증: 설명이 너무 모호하거나 논리적이지 않은 경우 경고
        explanation = pattern_data.get('explanation', '')
        if explanation and len(explanation) < 20:
            logger.warning(f"패턴 설명이 너무 짧거나 모호합니다: {explanation}")
        
        # 다국어 텍스트 생성
        languages = languages or ["ko"]
        is_english_only = languages and languages[0] == "en"
        problem_text_ko = "패턴의 규칙을 찾아 다음에 올 것을 골라보세요."
        problem_text_en = "Find the pattern rule and choose what comes next."
        
        # 언어에 따라 설명 텍스트 선택
        if is_english_only:
            explanation_ko = ''
            explanation_en = pattern_data.get('explanation', '')
        else:
            explanation_ko = pattern_data.get('explanation', '')
            explanation_en = ''
        
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            try:
                text_prompt = f"""Create bilingual text for a pattern sequence problem.

Pattern: {pattern_data['pattern']}
Next element: {pattern_data['next_element']}
Explanation (Korean): {explanation_ko}

Return JSON with:
{{
  "problem_text_ko": "패턴의 규칙을 찾아 다음에 올 것을 골라보세요.",
  "problem_text_en": "Find the pattern rule and choose what comes next.",
  "explanation_ko": "{explanation_ko}",
  "explanation_en": "English explanation of the pattern"
}}"""
                
                text_response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator."},
                        {"role": "user", "content": text_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(text_response.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", problem_text_ko)
                problem_text_en = text_data.get("problem_text_en", problem_text_en)
                explanation_ko = text_data.get("explanation_ko", explanation_ko)
                explanation_en = text_data.get("explanation_en", '')
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
        
        return {
            "module": "pattern_sequence",
            "display_seconds": settings.get('display_seconds', 8),
            "countdown_seconds": settings.get('countdown_seconds', 12),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "pattern": pattern_data['pattern'],
                "choices": pattern_data['choices']
            },
            "answer_data": {
                "correct_answer": pattern_data['next_element'],
                "explanation": explanation_en if is_english_only else explanation_ko,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"패턴 순서 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_word_association_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    단어 연상 게임 문제 생성
    
    Args:
        settings: 문제 설정
        languages: 지원 언어 리스트
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        category = settings.get('word_category', '일상')
        num_choices = settings.get('num_choices', 3)
        languages = languages or ["ko"]
        is_english_only = languages and languages[0] == "en"
        
        # GPT로 단어 연상 문제 생성 (언어에 따라 프롬프트 변경)
        if is_english_only:
            prompt = f"""
Create a word association problem for seniors.

Category: {category}
Number of choices: {num_choices}
Problem number: {problem_index + 1}
Problem index: {problem_index} (Use this value to generate a completely different keyword)

**Important**: 
- Choose a unique keyword that matches problem index {problem_index}.
- Use completely different keywords and words from previous problems.
- Use different keywords even within the same category.

Return JSON in the following format:
{{
  "keyword": "Keyword (English word only)",
  "correct_answer": "Correct answer (English word only)",
  "choices": ["Choice1", "Choice2", "Choice3"],
  "explanation": "Explanation in English"
}}

Use familiar English words that seniors can easily associate with.
Do not use Korean characters. Use English words only.
"""
            system_content = "You are a content creator for senior brain training. Use completely different keywords and words for each problem. Always use English words only."
        else:
            prompt = f"""
시니어를 위한 단어 연상 게임 문제를 만들어주세요.

카테고리: {category}
선택지 개수: {num_choices}
문제 번호: {problem_index + 1}
문제 인덱스: {problem_index} (이 값을 활용하여 완전히 다른 키워드를 생성하세요)

**중요**: 
- 문제 인덱스 {problem_index}에 맞는 고유한 키워드를 선택하세요.
- 이전 문제들과 완전히 다른 키워드와 단어를 사용해주세요.
- 같은 카테고리라도 다른 키워드를 사용하세요.

다음 형식의 JSON으로 응답해주세요:
{{
  "keyword": "키워드",
  "correct_answer": "정답",
  "choices": ["선택1", "선택2", "선택3"],
  "explanation": "설명"
}}

시니어가 쉽게 연상할 수 있는 친숙한 단어들로 구성해주세요.
"""
            system_content = "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다. 각 문제마다 완전히 다른 키워드와 단어를 사용해야 합니다."
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=1.0  # 다양성을 위해 temperature 증가
        )
        
        word_data = json.loads(response.choices[0].message.content)
        
        # 다국어 텍스트 생성
        if is_english_only:
            problem_text_ko = f"Which word is related to '{word_data['keyword']}'?"
            problem_text_en = f"Which word is related to '{word_data['keyword']}'?"
            explanation_ko = word_data.get('explanation', '')
            explanation_en = word_data.get('explanation', '')
        else:
            problem_text_ko = f"'{word_data['keyword']}'와 관련된 단어를 골라보세요."
            problem_text_en = f"Which word is related to '{word_data['keyword']}'?"
            explanation_ko = word_data.get('explanation', '')
            explanation_en = ''
        
        return {
            "module": "word_association",
            "display_seconds": settings.get('display_seconds', 10),
            "countdown_seconds": settings.get('countdown_seconds', 15),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "keyword": word_data['keyword'],
                "choices": word_data['choices']
            },
            "answer_data": {
                "correct_answer": word_data['correct_answer'],
                "explanation": explanation_ko if not is_english_only else explanation_en,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"단어 연상 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_clock_reading_problem(settings: Dict, problem_index: int = 0, languages: List[str] = None) -> Dict:
    """
    시계 읽기 문제 생성
    
    Args:
        settings: 문제 설정
        problem_index: 문제 인덱스 (다양성을 위해 사용)
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        time_type = settings.get('time_type', 'hour_half')
        
        # 시간 생성 (문제 인덱스를 사용하여 다양성 확보)
        # 12시간 * 2분(0, 30) = 24가지 조합을 순환
        hour = ((problem_index % 12) + 1)
        
        if time_type == 'hour':
            minute = 0
        elif time_type == 'hour_half':
            # 0분과 30분을 번갈아가며
            minute = 0 if (problem_index % 2 == 0) else 30
        elif time_type == 'hour_quarter':
            minutes_list = [0, 15, 30, 45]
            minute = minutes_list[problem_index % len(minutes_list)]
        else:  # exact
            # 0-59분을 순환
            minute = problem_index % 60
        
        # 시간 텍스트 생성
        languages = languages or ["ko"]
        if minute == 0:
            time_text_ko = f"{hour}시"
            time_text_en = f"{hour}:00"
        elif minute == 30:
            time_text_ko = f"{hour}시 30분"
            time_text_en = f"{hour}:30"
        else:
            time_text_ko = f"{hour}시 {minute}분"
            time_text_en = f"{hour}:{minute:02d}"
        
        # 다국어 텍스트 생성
        problem_text_ko = "시계가 가리키는 시간을 맞춰보세요."
        problem_text_en = "What time does the clock show?"
        explanation_ko = f"시계가 가리키는 시간은 {time_text_ko}입니다."
        explanation_en = f"The clock shows {time_text_en}."
        
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            try:
                text_prompt = f"""Create bilingual text for a clock reading problem.

Time: {hour}:{minute:02d}
Korean time text: {time_text_ko}
English time text: {time_text_en}

Return JSON with:
{{
  "problem_text_ko": "시계가 가리키는 시간을 맞춰보세요.",
  "problem_text_en": "What time does the clock show?",
  "explanation_ko": "시계가 가리키는 시간은 {time_text_ko}입니다.",
  "explanation_en": "The clock shows {time_text_en}."
}}"""
                
                text_response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator."},
                        {"role": "user", "content": text_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(text_response.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", problem_text_ko)
                problem_text_en = text_data.get("problem_text_en", problem_text_en)
                explanation_ko = text_data.get("explanation_ko", explanation_ko)
                explanation_en = text_data.get("explanation_en", explanation_en)
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
        
        return {
            "module": "clock_reading",
            "display_seconds": settings.get('display_seconds', 8),
            "countdown_seconds": settings.get('countdown_seconds', 12),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "hour": hour,
                "minute": minute
            },
            "answer_data": {
                "correct_answer": time_text_ko,
                "correct_answer_en": time_text_en,
                "explanation": explanation_ko,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"시계 읽기 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_korean_word_puzzle_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    한글 단어 퍼즐 문제 생성 (한글 전용 모듈)
    
    Args:
        settings: 문제 설정
        languages: 지원 언어 리스트 (영어일 경우 None 반환)
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리 (영어일 경우 None)
    """
    # 영어 버전에서는 이 모듈을 사용하지 않음
    if languages and languages[0] == "en":
        return None
    
    try:
        puzzle_type = settings.get('puzzle_type', 'initial_sound')
        word_length = settings.get('word_length', 3)
        num_hints = settings.get('num_hints', 2)
        
        # GPT로 한글 퍼즐 생성
        prompt = f"""
시니어를 위한 한글 단어 퍼즐 문제를 만들어주세요.

퍼즐 타입: {puzzle_type}
단어 길이: {word_length}글자
힌트 개수: {num_hints}개
문제 번호: {problem_index + 1}
문제 인덱스: {problem_index} (이 값을 활용하여 완전히 다른 단어를 생성하세요)

**중요**: 
- 문제 인덱스 {problem_index}에 맞는 고유한 단어를 선택하세요.
- 이전 문제들과 완전히 다른 단어를 사용해주세요.
- 같은 카테고리라도 다른 단어를 사용하세요.

다음 형식의 JSON으로 응답해주세요:
{{
  "word": "정답단어",
  "initial_sounds": "ㅊㅅ",
  "hints": ["힌트1", "힌트2"],
  "explanation": "설명"
}}

시니어가 쉽게 맞출 수 있는 친숙한 단어로 만들어주세요.
"""
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다. 각 문제마다 완전히 다른 단어를 사용해야 합니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=1.0  # 다양성을 위해 temperature 증가
        )
        
        puzzle_data = json.loads(response.choices[0].message.content)
        
        return {
            "module": "korean_word_puzzle",
            "display_seconds": settings.get('display_seconds', 10),
            "countdown_seconds": settings.get('countdown_seconds', 15),
            "problem_text": "힌트를 보고 단어를 맞춰보세요.",
            "problem_text_ko": "힌트를 보고 단어를 맞춰보세요.",
            "problem_data": {
                "initial_sounds": puzzle_data['initial_sounds'],
                "hints": puzzle_data['hints']
            },
            "answer_data": {
                "correct_answer": puzzle_data['word'],
                "explanation": puzzle_data['explanation']
            }
        }
        
    except Exception as e:
        logger.error(f"한글 퍼즐 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_color_memory_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    색상 기억 문제 생성
    
    Args:
        settings: 문제 설정 (num_colors, display_seconds 등)
        languages: 지원 언어 리스트
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        num_colors = settings.get('num_colors', 4)
        languages = languages or ["ko"]
        
        # 색상 리스트 (RGB 값) - 명확하게 구분되도록 밝고 선명한 색상 사용
        color_list = [
            ("빨강", "Red", (255, 0, 0)),           # 밝은 빨강
            ("파랑", "Blue", (0, 100, 255)),        # 밝은 파랑 (더 선명하게)
            ("초록", "Green", (0, 200, 0)),         # 밝은 초록 (더 선명하게)
            ("노랑", "Yellow", (255, 255, 0)),      # 밝은 노랑
            ("주황", "Orange", (255, 140, 0)),      # 밝은 주황 (더 선명하게)
            ("보라", "Purple", (180, 0, 180)),      # 밝은 보라 (더 선명하게)
            ("분홍", "Pink", (255, 100, 150)),      # 밝은 분홍 (더 선명하게)
            ("갈색", "Brown", (139, 69, 19)),       # 갈색 (더 선명하게)
            ("하늘색", "Sky Blue", (135, 206, 250)), # 하늘색 추가
            ("연두색", "Lime", (200, 255, 0)),      # 연두색 추가
        ]
        
        # 문제 인덱스에 따라 다양한 색상 조합 생성
        random.seed(problem_index)
        selected_colors = random.sample(color_list, num_colors)
        random.seed()  # 시드 초기화
        
        # 다국어 텍스트 생성
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            try:
                prompt = f"""Create bilingual text for a color memory problem.

Number of colors: {num_colors}
Colors to remember: {', '.join([c[0] for c in selected_colors])}

Return JSON with:
{{
  "problem_text_ko": "화면에 나타나는 {num_colors}개의 색상을 순서대로 기억해보세요.",
  "problem_text_en": "Remember the {num_colors} colors shown on screen in order.",
  "explanation_ko": "색상 순서는 {', '.join([c[0] for c in selected_colors])}입니다.",
  "explanation_en": "The color order is {', '.join([c[1] for c in selected_colors])}."
}}"""
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator for senior brain training."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(response.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", f"화면에 나타나는 {num_colors}개의 색상을 순서대로 기억해보세요.")
                problem_text_en = text_data.get("problem_text_en", f"Remember the {num_colors} colors shown on screen in order.")
                explanation_ko = text_data.get("explanation_ko", f"색상 순서는 {', '.join([c[0] for c in selected_colors])}입니다.")
                explanation_en = text_data.get("explanation_en", f"The color order is {', '.join([c[1] for c in selected_colors])}.")
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
                problem_text_ko = f"화면에 나타나는 {num_colors}개의 색상을 순서대로 기억해보세요."
                problem_text_en = f"Remember the {num_colors} colors shown on screen in order."
                explanation_ko = f"색상 순서는 {', '.join([c[0] for c in selected_colors])}입니다."
                explanation_en = f"The color order is {', '.join([c[1] for c in selected_colors])}."
        else:
            if languages and languages[0] == "en":
                problem_text_ko = f"Remember the {num_colors} colors shown on screen in order."
                problem_text_en = f"Remember the {num_colors} colors shown on screen in order."
                explanation_ko = f"The color order is {', '.join([c[1] for c in selected_colors])}."
                explanation_en = f"The color order is {', '.join([c[1] for c in selected_colors])}."
            else:
                problem_text_ko = f"화면에 나타나는 {num_colors}개의 색상을 순서대로 기억해보세요."
                problem_text_en = f"Remember the {num_colors} colors shown on screen in order."
                explanation_ko = f"색상 순서는 {', '.join([c[0] for c in selected_colors])}입니다."
                explanation_en = f"The color order is {', '.join([c[1] for c in selected_colors])}."
        
        return {
            "module": "color_memory",
            "display_seconds": settings.get('display_seconds', 5),
            "countdown_seconds": settings.get('countdown_seconds', 10),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "colors": [{"name_ko": c[0], "name_en": c[1], "rgb": c[2]} for c in selected_colors]
            },
            "answer_data": {
                "correct_answer": [c[0] for c in selected_colors] if (languages and languages[0] != "en") else [c[1] for c in selected_colors],
                "explanation": explanation_ko if (languages and languages[0] != "en") else explanation_en,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"색상 기억 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_simple_calculation_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    간단한 계산 문제 생성
    
    Args:
        settings: 문제 설정 (operation_type, max_number 등)
        languages: 지원 언어 리스트
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        operation_type = settings.get('operation_type', 'addition')  # addition, subtraction
        max_number = settings.get('max_number', 50)
        languages = languages or ["ko"]
        
        # 문제 인덱스에 따라 다양한 문제 생성 (더 다양한 조합)
        random.seed(problem_index * 7 + 13)  # 더 다양한 시드 조합
        
        # 문제 인덱스에 따라 덧셈/뺄셈 번갈아가며
        use_addition = (problem_index % 2 == 0) if operation_type == 'addition' else False
        use_subtraction = (problem_index % 2 == 1) if operation_type == 'subtraction' else False
        
        # 혼합 모드: 문제 인덱스에 따라 덧셈/뺄셈 선택
        if operation_type not in ['addition', 'subtraction']:
            use_addition = (problem_index % 2 == 0)
        
        if use_addition or (operation_type == 'addition' and not use_subtraction):
            # 덧셈 문제 - 더 다양한 범위
            base_num = 10 + (problem_index % 20)  # 10-29 범위
            num1 = base_num + random.randint(0, max_number // 3)
            num2 = random.randint(10, max_number - num1)
            answer = num1 + num2
            operation_symbol = "+"
            operation_text_ko = "더하기"
            operation_text_en = "plus"
        else:
            # 뺄셈 문제 - 더 다양한 범위
            base_num = 20 + (problem_index % 30)  # 20-49 범위
            num1 = base_num + random.randint(0, max_number // 2)
            num2 = random.randint(5, min(num1 - 5, max_number // 2))
            answer = num1 - num2
            operation_symbol = "-"
            operation_text_ko = "빼기"
            operation_text_en = "minus"
        
        random.seed()  # 시드 초기화
        
        # 다국어 텍스트 생성
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            try:
                prompt = f"""Create bilingual text for a simple calculation problem.

Problem: {num1} {operation_symbol} {num2} = ?
Answer: {answer}

Return JSON with:
{{
  "problem_text_ko": "{num1} {operation_symbol} {num2} = ?",
  "problem_text_en": "{num1} {operation_symbol} {num2} = ?",
  "explanation_ko": "정답은 {answer}입니다.",
  "explanation_en": "The answer is {answer}."
}}"""
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator for senior brain training."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(response.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", f"{num1} {operation_symbol} {num2} = ?")
                problem_text_en = text_data.get("problem_text_en", f"{num1} {operation_symbol} {num2} = ?")
                explanation_ko = text_data.get("explanation_ko", f"정답은 {answer}입니다.")
                explanation_en = text_data.get("explanation_en", f"The answer is {answer}.")
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
                problem_text_ko = f"{num1} {operation_symbol} {num2} = ?"
                problem_text_en = f"{num1} {operation_symbol} {num2} = ?"
                explanation_ko = f"정답은 {answer}입니다."
                explanation_en = f"The answer is {answer}."
        else:
            if languages and languages[0] == "en":
                problem_text_ko = f"{num1} {operation_symbol} {num2} = ?"
                problem_text_en = f"{num1} {operation_symbol} {num2} = ?"
                explanation_ko = f"The answer is {answer}."
                explanation_en = f"The answer is {answer}."
            else:
                problem_text_ko = f"{num1} {operation_symbol} {num2} = ?"
                problem_text_en = f"{num1} {operation_symbol} {num2} = ?"
                explanation_ko = f"정답은 {answer}입니다."
                explanation_en = f"The answer is {answer}."
        
        return {
            "module": "simple_calculation",
            "display_seconds": settings.get('display_seconds', 8),
            "countdown_seconds": settings.get('countdown_seconds', 15),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "num1": num1,
                "num2": num2,
                "operation": operation_symbol,
                "answer": answer
            },
            "answer_data": {
                "correct_answer": str(answer),
                "explanation": explanation_ko if (languages and languages[0] != "en") else explanation_en,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"간단한 계산 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_direction_memory_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    방향 기억 문제 생성
    
    Args:
        settings: 문제 설정 (num_directions, display_seconds 등)
        languages: 지원 언어 리스트
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        num_directions = settings.get('num_directions', 4)
        languages = languages or ["ko"]
        
        # 방향 리스트
        directions = [
            ("위", "Up", "↑"),
            ("아래", "Down", "↓"),
            ("왼쪽", "Left", "←"),
            ("오른쪽", "Right", "→"),
        ]
        
        # 문제 인덱스에 따라 다양한 방향 조합 생성
        random.seed(problem_index)
        selected_directions = [random.choice(directions) for _ in range(num_directions)]
        random.seed()  # 시드 초기화
        
        # 다국어 텍스트 생성
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            try:
                prompt = f"""Create bilingual text for a direction memory problem.

Number of directions: {num_directions}
Directions to remember: {', '.join([d[0] for d in selected_directions])}

Return JSON with:
{{
  "problem_text_ko": "화면에 나타나는 {num_directions}개의 화살표 방향을 순서대로 기억해보세요.",
  "problem_text_en": "Remember the {num_directions} arrow directions shown on screen in order.",
  "explanation_ko": "방향 순서는 {', '.join([d[0] for d in selected_directions])}입니다.",
  "explanation_en": "The direction order is {', '.join([d[1] for d in selected_directions])}."
}}"""
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator for senior brain training."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(response.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", f"화면에 나타나는 {num_directions}개의 화살표 방향을 순서대로 기억해보세요.")
                problem_text_en = text_data.get("problem_text_en", f"Remember the {num_directions} arrow directions shown on screen in order.")
                explanation_ko = text_data.get("explanation_ko", f"방향 순서는 {', '.join([d[0] for d in selected_directions])}입니다.")
                explanation_en = text_data.get("explanation_en", f"The direction order is {', '.join([d[1] for d in selected_directions])}.")
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
                problem_text_ko = f"화면에 나타나는 {num_directions}개의 화살표 방향을 순서대로 기억해보세요."
                problem_text_en = f"Remember the {num_directions} arrow directions shown on screen in order."
                explanation_ko = f"방향 순서는 {', '.join([d[0] for d in selected_directions])}입니다."
                explanation_en = f"The direction order is {', '.join([d[1] for d in selected_directions])}."
        else:
            if languages and languages[0] == "en":
                problem_text_ko = f"Remember the {num_directions} arrow directions shown on screen in order."
                problem_text_en = f"Remember the {num_directions} arrow directions shown on screen in order."
                explanation_ko = f"The direction order is {', '.join([d[1] for d in selected_directions])}."
                explanation_en = f"The direction order is {', '.join([d[1] for d in selected_directions])}."
            else:
                problem_text_ko = f"화면에 나타나는 {num_directions}개의 화살표 방향을 순서대로 기억해보세요."
                problem_text_en = f"Remember the {num_directions} arrow directions shown on screen in order."
                explanation_ko = f"방향 순서는 {', '.join([d[0] for d in selected_directions])}입니다."
                explanation_en = f"The direction order is {', '.join([d[1] for d in selected_directions])}."
        
        return {
            "module": "direction_memory",
            "display_seconds": settings.get('display_seconds', 5),
            "countdown_seconds": settings.get('countdown_seconds', 10),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "directions": [{"name_ko": d[0], "name_en": d[1], "symbol": d[2]} for d in selected_directions]
            },
            "answer_data": {
                "correct_answer": [d[0] for d in selected_directions] if (languages and languages[0] != "en") else [d[1] for d in selected_directions],
                "explanation": explanation_ko if (languages and languages[0] != "en") else explanation_en,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"방향 기억 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_category_classification_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    카테고리 분류 문제 생성
    
    Args:
        settings: 문제 설정 (num_items, category_type 등)
        languages: 지원 언어 리스트
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        num_items = settings.get('num_items', 4)
        category_type = settings.get('category_type', 'random')  # random, food, animal, object 등
        languages = languages or ["ko"]
        is_english_only = languages and languages[0] == "en"
        
        # GPT로 카테고리 분류 문제 생성 (언어에 따라 프롬프트 변경)
        if is_english_only:
            prompt = f"""
Create a category classification problem for seniors.

Number of items: {num_items}
Category type: {category_type}

Return JSON in the following format:
{{
  "category": "Category name (e.g., Fruit, Animal, Vehicle, etc.)",
  "items": ["Item1", "Item2", "Item3", "Item4"],
  "wrong_item": "Item that does not belong to the category",
  "wrong_item_index": 0
}}

One of the {num_items} items should not belong to the category.
Choose everyday categories and items that seniors can easily understand.
Problem index: {problem_index} (Generate a completely different problem)
"""
            system_content = "You are a content creator for senior brain training. Always respond in English."
        else:
            prompt = f"""
시니어를 위한 카테고리 분류 문제를 만들어주세요.

항목 개수: {num_items}개
카테고리 유형: {category_type}

다음 형식의 JSON으로 응답해주세요:
{{
  "category": "카테고리 이름 (예: 과일, 동물, 교통수단 등)",
  "items": ["항목1", "항목2", "항목3", "항목4"],
  "wrong_item": "카테고리에 속하지 않는 항목",
  "wrong_item_index": 0
}}

{num_items}개 항목 중 하나는 카테고리에 속하지 않아야 합니다.
시니어가 쉽게 이해할 수 있는 일상적인 카테고리와 항목으로 선택해주세요.
문제 인덱스: {problem_index} (다양한 문제를 생성해주세요)
"""
            system_content = "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다."
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8 + (problem_index % 3) * 0.1  # 다양성을 위해 temperature 조정
        )
        
        content_data = json.loads(response.choices[0].message.content)
        
        # 다국어 텍스트 생성
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            try:
                prompt_text = f"""Create bilingual text for a category classification problem.

Category: {content_data['category']}
Items: {', '.join(content_data['items'])}
Wrong item (does not belong to category): {content_data['wrong_item']}

Return JSON with:
{{
  "problem_text_ko": "다음 항목 중 {content_data['category']}이(가) 아닌 것은?",
  "problem_text_en": "Which of the following is NOT a {content_data['category']}?",
  "explanation_ko": "정답은 '{content_data['wrong_item']}'입니다. 이것은 {content_data['category']}이(가) 아닙니다.",
  "explanation_en": "The answer is '{content_data['wrong_item']}'. This is not a {content_data['category']}."
}}"""
                
                response_text = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator for senior brain training."},
                        {"role": "user", "content": prompt_text}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(response_text.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", f"다음 항목 중 {content_data['category']}이(가) 아닌 것은?")
                problem_text_en = text_data.get("problem_text_en", f"Which of the following is NOT a {content_data['category']}?")
                explanation_ko = text_data.get("explanation_ko", f"정답은 '{content_data['wrong_item']}'입니다.")
                explanation_en = text_data.get("explanation_en", f"The answer is '{content_data['wrong_item']}'.")
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
                problem_text_ko = f"다음 항목 중 {content_data['category']}이(가) 아닌 것은?"
                problem_text_en = f"Which of the following is NOT a {content_data['category']}?"
                explanation_ko = f"정답은 '{content_data['wrong_item']}'입니다."
                explanation_en = f"The answer is '{content_data['wrong_item']}'."
        else:
            if languages and languages[0] == "en":
                problem_text_ko = f"Which of the following is NOT a {content_data['category']}?"
                problem_text_en = f"Which of the following is NOT a {content_data['category']}?"
                explanation_ko = f"The answer is '{content_data['wrong_item']}'."
                explanation_en = f"The answer is '{content_data['wrong_item']}'."
            else:
                problem_text_ko = f"다음 항목 중 {content_data['category']}이(가) 아닌 것은?"
                problem_text_en = f"Which of the following is NOT a {content_data['category']}?"
                explanation_ko = f"정답은 '{content_data['wrong_item']}'입니다."
                explanation_en = f"The answer is '{content_data['wrong_item']}'."
        
        return {
            "module": "category_classification",
            "display_seconds": settings.get('display_seconds', 10),
            "countdown_seconds": settings.get('countdown_seconds', 15),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "category": content_data['category'],
                "items": content_data['items'],
                "wrong_item": content_data['wrong_item'],
                "wrong_item_index": content_data.get('wrong_item_index', 0)
            },
            "answer_data": {
                "correct_answer": content_data['wrong_item'],
                "explanation": explanation_ko if (languages and languages[0] != "en") else explanation_en,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"카테고리 분류 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_shape_matching_problem(settings: Dict, languages: List[str] = None, problem_index: int = 0) -> Dict:
    """
    도형 매칭 문제 생성
    
    Args:
        settings: 문제 설정 (num_shapes, shape_types 등)
        languages: 지원 언어 리스트
        problem_index: 문제 인덱스
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        num_shapes = settings.get('num_shapes', 4)
        languages = languages or ["ko"]
        
        # 도형 타입 및 색상
        shape_types = ["circle", "square", "triangle", "rectangle", "star", "diamond"]
        colors = [
            ("빨강", "Red", (255, 0, 0)),
            ("파랑", "Blue", (0, 0, 255)),
            ("초록", "Green", (0, 128, 0)),
            ("노랑", "Yellow", (255, 255, 0)),
            ("주황", "Orange", (255, 165, 0)),
            ("보라", "Purple", (128, 0, 128)),
        ]
        
        # 문제 인덱스에 따라 다양한 조합 생성
        random.seed(problem_index)
        
        # 타겟 도형 선택
        target_shape = random.choice(shape_types)
        target_color = random.choice(colors)
        
        # 선택지 생성 (하나만 정답, 나머지는 다른 도형 또는 색상)
        choices = []
        correct_index = random.randint(0, num_shapes - 1)
        
        for i in range(num_shapes):
            if i == correct_index:
                # 정답: 같은 도형, 같은 색상
                choices.append({
                    "shape": target_shape,
                    "color": {"name_ko": target_color[0], "name_en": target_color[1], "rgb": target_color[2]},
                    "is_correct": True
                })
            else:
                # 오답: 다른 도형 또는 다른 색상
                if random.random() < 0.5:
                    # 다른 도형, 같은 색상
                    other_shape = random.choice([s for s in shape_types if s != target_shape])
                    choices.append({
                        "shape": other_shape,
                        "color": {"name_ko": target_color[0], "name_en": target_color[1], "rgb": target_color[2]},
                        "is_correct": False
                    })
                else:
                    # 같은 도형, 다른 색상
                    other_color = random.choice([c for c in colors if c != target_color])
                    choices.append({
                        "shape": target_shape,
                        "color": {"name_ko": other_color[0], "name_en": other_color[1], "rgb": other_color[2]},
                        "is_correct": False
                    })
        
        random.shuffle(choices)  # 선택지 섞기
        correct_index = next(i for i, c in enumerate(choices) if c['is_correct'])
        
        random.seed()  # 시드 초기화
        
        # 도형 이름 한글 변환 (먼저 정의)
        shape_names_ko = {
            "circle": "원",
            "square": "사각형",
            "triangle": "삼각형",
            "rectangle": "직사각형",
            "star": "별",
            "diamond": "다이아몬드"
        }
        
        # 한글 도형 이름 사용
        target_shape_ko = shape_names_ko.get(target_shape, target_shape)
        
        # 다국어 텍스트 생성
        if len(languages) >= 2 and "ko" in languages and "en" in languages:
            try:
                prompt = f"""Create bilingual text for a shape matching problem.

Target: {target_color[0]} {target_shape_ko} (Korean) / {target_color[1].lower()} {target_shape} (English)
Number of choices: {num_shapes}

Return JSON with:
{{
  "problem_text_ko": "다음 중 {target_color[0]} {target_shape_ko}와(과) 같은 것은?",
  "problem_text_en": "Which of the following matches the {target_color[1].lower()} {target_shape}?",
  "explanation_ko": "정답은 {correct_index + 1}번입니다.",
  "explanation_en": "The answer is choice {correct_index + 1}."
}}

**중요**: problem_text_ko에는 반드시 한글 도형 이름({target_shape_ko})을 사용하세요. 영어 단어를 사용하지 마세요."""
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a bilingual content creator for senior brain training. Always use Korean shape names in Korean text."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                text_data = json.loads(response.choices[0].message.content)
                problem_text_ko = text_data.get("problem_text_ko", f"다음 중 {target_color[0]} {target_shape_ko}와(과) 같은 것은?")
                problem_text_en = text_data.get("problem_text_en", f"Which of the following matches the {target_color[1].lower()} {target_shape}?")
                explanation_ko = text_data.get("explanation_ko", f"정답은 {correct_index + 1}번입니다.")
                explanation_en = text_data.get("explanation_en", f"The answer is choice {correct_index + 1}.")
                
                # 한글 텍스트에 영어가 섞여있는지 검증 및 수정
                if target_shape in problem_text_ko:
                    problem_text_ko = problem_text_ko.replace(target_shape, target_shape_ko)
            except Exception as e:
                logger.warning(f"다국어 텍스트 생성 실패, 기본값 사용: {e}")
                problem_text_ko = f"다음 중 {target_color[0]} {target_shape_ko}와(과) 같은 것은?"
                problem_text_en = f"Which of the following matches the {target_color[1].lower()} {target_shape}?"
                explanation_ko = f"정답은 {correct_index + 1}번입니다."
                explanation_en = f"The answer is choice {correct_index + 1}."
        else:
            if languages and languages[0] == "en":
                problem_text_ko = f"Which of the following matches the {target_color[1].lower()} {target_shape}?"
                problem_text_en = f"Which of the following matches the {target_color[1].lower()} {target_shape}?"
                explanation_ko = f"The answer is choice {correct_index + 1}."
                explanation_en = f"The answer is choice {correct_index + 1}."
            else:
                problem_text_ko = f"다음 중 {target_color[0]} {target_shape_ko}와(과) 같은 것은?"
                problem_text_en = f"Which of the following matches the {target_color[1].lower()} {target_shape}?"
                explanation_ko = f"정답은 {correct_index + 1}번입니다."
                explanation_en = f"The answer is choice {correct_index + 1}."
        
        return {
            "module": "shape_matching",
            "display_seconds": settings.get('display_seconds', 8),
            "countdown_seconds": settings.get('countdown_seconds', 12),
            "problem_text": problem_text_ko,
            "problem_text_ko": problem_text_ko,
            "problem_text_en": problem_text_en,
            "problem_data": {
                "target_shape": target_shape,
                "target_shape_ko": shape_names_ko.get(target_shape, target_shape),
                "target_color": {"name_ko": target_color[0], "name_en": target_color[1], "rgb": target_color[2]},
                "choices": choices,
                "correct_index": correct_index
            },
            "answer_data": {
                "correct_answer": str(correct_index + 1),
                "explanation": explanation_ko if (languages and languages[0] != "en") else explanation_en,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"도형 매칭 문제 생성 실패: {e}", exc_info=True)
        return None


# 모듈별 생성 함수 매핑
MODULE_GENERATORS = {
    "number_memory": generate_number_memory_problem,
    # "missing_object": generate_missing_object_problem,  # 비활성화됨 - 틀린그림 찾기는 구현이 어려워 사용하지 않음
    "pattern_sequence": generate_pattern_sequence_problem,
    "word_association": generate_word_association_problem,
    "clock_reading": generate_clock_reading_problem,
    "korean_word_puzzle": generate_korean_word_puzzle_problem,
    "color_memory": generate_color_memory_problem,
    "simple_calculation": generate_simple_calculation_problem,
    "direction_memory": generate_direction_memory_problem,
    "category_classification": generate_category_classification_problem,
    "shape_matching": generate_shape_matching_problem
}


if __name__ == "__main__":
    # 테스트 코드
    test_settings = {
        "digit_count": 4,
        "display_seconds": 5,
        "countdown_seconds": 10
    }
    
    problem = generate_number_memory_problem(test_settings)
    print(json.dumps(problem, ensure_ascii=False, indent=2))
