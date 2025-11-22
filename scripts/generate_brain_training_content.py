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
        
        # GPT로 패턴 생성 (다양성을 위해 문제 인덱스와 랜덤 요소 추가)
        prompt = f"""
시니어를 위한 패턴 순서 맞추기 문제를 만들어주세요.

패턴 타입: {actual_pattern_type}
패턴 길이: {sequence_length}
문제 번호: {problem_index + 1}

**중요**: 이전 문제와 완전히 다른 패턴을 만들어주세요. 패턴 규칙도 다르게 해주세요.
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
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다. 각 문제마다 완전히 다른 패턴을 만들어야 합니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=1.0  # 다양성을 위해 temperature 증가
        )
        
        pattern_data = json.loads(response.choices[0].message.content)
        
        # 다국어 텍스트 생성
        languages = languages or ["ko"]
        problem_text_ko = "패턴의 규칙을 찾아 다음에 올 것을 골라보세요."
        problem_text_en = "Find the pattern rule and choose what comes next."
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
                "explanation": explanation_ko,
                "explanation_ko": explanation_ko,
                "explanation_en": explanation_en
            }
        }
        
    except Exception as e:
        logger.error(f"패턴 순서 문제 생성 실패: {e}", exc_info=True)
        return None


def generate_word_association_problem(settings: Dict, problem_index: int = 0) -> Dict:
    """
    단어 연상 게임 문제 생성
    
    Args:
        settings: 문제 설정
    
    Returns:
        문제 데이터 딕셔너리
    """
    try:
        category = settings.get('word_category', '일상')
        num_choices = settings.get('num_choices', 3)
        
        # GPT로 단어 연상 문제 생성
        prompt = f"""
시니어를 위한 단어 연상 게임 문제를 만들어주세요.

카테고리: {category}
선택지 개수: {num_choices}
문제 번호: {problem_index + 1}

**중요**: 이전 문제와 완전히 다른 키워드와 단어를 사용해주세요.

다음 형식의 JSON으로 응답해주세요:
{{
  "keyword": "키워드",
  "correct_answer": "정답",
  "choices": ["선택1", "선택2", "선택3"],
  "explanation": "설명"
}}

시니어가 쉽게 연상할 수 있는 친숙한 단어들로 구성해주세요.
"""
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어용 두뇌훈련 콘텐츠 제작 전문가입니다. 각 문제마다 완전히 다른 키워드와 단어를 사용해야 합니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=1.0  # 다양성을 위해 temperature 증가
        )
        
        word_data = json.loads(response.choices[0].message.content)
        
        return {
            "module": "word_association",
            "display_seconds": settings.get('display_seconds', 10),
            "countdown_seconds": settings.get('countdown_seconds', 15),
            "problem_text": f"'{word_data['keyword']}'와 관련된 단어를 골라보세요.",
            "problem_data": {
                "keyword": word_data['keyword'],
                "choices": word_data['choices']
            },
            "answer_data": {
                "correct_answer": word_data['correct_answer'],
                "explanation": word_data['explanation']
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


def generate_korean_word_puzzle_problem(settings: Dict, problem_index: int = 0) -> Dict:
    """
    한글 단어 퍼즐 문제 생성
    
    Args:
        settings: 문제 설정
    
    Returns:
        문제 데이터 딕셔너리
    """
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


# 모듈별 생성 함수 매핑
MODULE_GENERATORS = {
    "number_memory": generate_number_memory_problem,
    "missing_object": generate_missing_object_problem,
    "pattern_sequence": generate_pattern_sequence_problem,
    "word_association": generate_word_association_problem,
    "clock_reading": generate_clock_reading_problem,
    "korean_word_puzzle": generate_korean_word_puzzle_problem
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
