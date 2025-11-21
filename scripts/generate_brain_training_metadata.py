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

# OpenAI API 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 로깅 설정
log_file = project_root / "logs" / "app.log"
log_file.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_video_metadata(preset_name: str, num_problems: int, 
                           module_counts: Dict[str, int]) -> Dict:
    """
    영상 메타데이터 생성 (제목, 설명, 태그)
    
    Args:
        preset_name: 프리셋 이름
        num_problems: 총 문제 수
        module_counts: 모듈별 문제 수
    
    Returns:
        메타데이터 딕셔너리
    """
    try:
        # 모듈 정보 텍스트 생성
        module_info = ", ".join([f"{module}: {count}문제" 
                                for module, count in module_counts.items()])
        
        # GPT로 메타데이터 생성
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
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 시니어용 YouTube 콘텐츠 메타데이터 작성 전문가입니다."},
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
        # 기본 메타데이터 반환
        return {
            "title": f"시니어 두뇌훈련 - {preset_name} ({num_problems}문제)",
            "description": f"치매 예방을 위한 두뇌훈련 영상입니다.\n총 {num_problems}개의 문제로 구성되어 있습니다.",
            "tags": ["시니어", "두뇌훈련", "치매예방", "인지훈련", "노인", "기억력"]
        }


def generate_chapters(problems: List[Dict]) -> List[Dict]:
    """
    챕터 마커 생성 (문제별 타임스탬프)
    
    Args:
        problems: 문제 리스트
    
    Returns:
        챕터 리스트 (timestamp, title)
    """
    try:
        chapters = []
        current_time = 0
        
        # 인트로
        chapters.append({
            "timestamp": "0:00",
            "title": "시작"
        })
        current_time += 5  # 인트로 5초
        
        # 각 문제
        for i, problem in enumerate(problems, 1):
            minutes = current_time // 60
            seconds = current_time % 60
            timestamp = f"{minutes}:{seconds:02d}"
            
            module = problem.get('module', 'unknown')
            module_names = {
                "number_memory": "숫자 기억",
                "missing_object": "사라진 물건 찾기",
                "pattern_sequence": "패턴 순서",
                "word_association": "단어 연상",
                "clock_reading": "시계 읽기",
                "korean_word_puzzle": "한글 퍼즐"
            }
            
            title = f"문제 {i}: {module_names.get(module, module)}"
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


def format_chapters_for_youtube(chapters: List[Dict]) -> str:
    """
    YouTube 설명란에 넣을 챕터 텍스트 포맷
    
    Args:
        chapters: 챕터 리스트
    
    Returns:
        포맷된 챕터 텍스트
    """
    lines = ["📚 목차 (Chapters)"]
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
