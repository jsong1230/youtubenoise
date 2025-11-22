"""
틀린그림찾기용 메타데이터 생성 스크립트
GPT API를 활용하여 자막, 내레이션, 챕터 정보 생성
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from scripts.utils import setup_logging

# 로깅 설정
logger = setup_logging()

_openai_client: Optional[OpenAI] = None


def get_openai_client() -> Optional[OpenAI]:
    """OpenAI 클라이언트를 생성/캐싱"""
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return None
    
    _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def generate_problem_text(problem_number: int, num_differences: int, theme: str) -> Dict[str, str]:
    """
    문제 시작 텍스트 생성
    
    Args:
        problem_number: 문제 번호
        num_differences: 차이점 개수
        theme: 이미지 주제
    
    Returns:
        {"narration": "...", "subtitle": "..."}
    """
    try:
        client = get_openai_client()
        if not client:
            return {
                "narration": f"{problem_number}번 문제입니다. {num_differences}개의 차이점을 찾아보세요.",
                "subtitle": f"{problem_number}번 문제 - {num_differences}개 찾기"
            }
        
        prompt = (
            f"시니어를 위한 틀린그림찾기 게임의 {problem_number}번 문제 시작 안내 문구를 생성해주세요. "
            f"주제는 '{theme}'입니다. "
            f"차이점은 {num_differences}개입니다. "
            f"따뜻하고 친절한 톤으로, 간단명료하게 작성해주세요. "
            f"JSON 형식으로 'narration'(내레이션용)과 'subtitle'(자막용)을 제공해주세요."
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어 친화적인 콘텐츠 제작 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "narration": result.get("narration", f"{problem_number}번 문제입니다."),
            "subtitle": result.get("subtitle", f"{problem_number}번 문제")
        }
        
    except Exception as e:
        logger.warning(f"문제 텍스트 생성 실패, 기본값 사용: {e}")
        return {
            "narration": f"{problem_number}번 문제입니다. {num_differences}개의 차이점을 찾아보세요.",
            "subtitle": f"{problem_number}번 문제 - {num_differences}개 찾기"
        }


def generate_answer_text(problem_number: int, differences: List[Dict]) -> Dict[str, str]:
    """
    정답 화면 텍스트 생성
    
    Args:
        problem_number: 문제 번호
        differences: 차이점 정보 리스트
    
    Returns:
        {"narration": "...", "subtitle": "..."}
    """
    try:
        client = get_openai_client()
        if not client:
            return {
                "narration": "정답입니다. 잘 찾으셨나요?",
                "subtitle": "정답"
            }
        
        diff_descriptions = [d.get('description', '') for d in differences]
        
        prompt = (
            f"틀린그림찾기 게임의 {problem_number}번 문제 정답 안내 문구를 생성해주세요. "
            f"차이점은 다음과 같습니다: {', '.join(diff_descriptions)}. "
            f"시니어에게 따뜻하고 격려하는 톤으로 작성해주세요. "
            f"JSON 형식으로 'narration'과 'subtitle'을 제공해주세요."
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어 친화적인 콘텐츠 제작 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "narration": result.get("narration", "정답입니다."),
            "subtitle": result.get("subtitle", "정답")
        }
        
    except Exception as e:
        logger.warning(f"정답 텍스트 생성 실패, 기본값 사용: {e}")
        return {
            "narration": "정답입니다. 잘 찾으셨나요?",
            "subtitle": "정답"
        }


def generate_video_metadata(num_problems: int, themes: List[str]) -> Dict[str, str]:
    """
    영상 전체 메타데이터 생성 (제목, 설명, 챕터)
    
    Args:
        num_problems: 문제 개수
        themes: 사용된 주제 리스트
    
    Returns:
        {"title": "...", "description": "...", "chapters": [...]}
    """
    try:
        client = get_openai_client()
        if not client:
            return {
                "title": f"시니어용 틀린그림찾기 {num_problems}문제",
                "description": f"시니어를 위한 틀린그림찾기 게임 영상입니다.",
                "chapters": []
            }
        
        prompt = (
            f"시니어용 틀린그림찾기 롱폼 영상의 메타데이터를 생성해주세요. "
            f"문제 개수: {num_problems}개, 주제: {', '.join(themes)}. "
            f"JSON 형식으로 'title'(제목), 'description'(설명), 'chapters'(챕터 리스트)를 제공해주세요. "
            f"챕터는 각 문제별로 구성해주세요."
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어 친화적인 콘텐츠 제작 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "title": result.get("title", f"시니어용 틀린그림찾기 {num_problems}문제"),
            "description": result.get("description", ""),
            "chapters": result.get("chapters", [])
        }
        
    except Exception as e:
        logger.warning(f"영상 메타데이터 생성 실패, 기본값 사용: {e}")
        return {
            "title": f"시니어용 틀린그림찾기 {num_problems}문제",
            "description": f"시니어를 위한 틀린그림찾기 게임 영상입니다.",
            "chapters": []
        }


if __name__ == "__main__":
    # 테스트
    problem_text = generate_problem_text(1, 3, "집안 풍경")
    print(f"문제 텍스트: {problem_text}")
    
    answer_text = generate_answer_text(1, [
        {"description": "컵의 색상이 파란색에서 빨간색으로 변경됨"},
        {"description": "테이블 위에 레몬 하나 추가됨"}
    ])
    print(f"정답 텍스트: {answer_text}")

