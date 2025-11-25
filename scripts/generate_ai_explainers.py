"""
AI Explainer 스크립트 생성 스크립트
Claude 3.5 Sonnet을 사용하여 AI & Tech 설명 롱폼 영상용 스크립트 생성
"""
import os
import sys
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from dotenv import load_dotenv

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE, OUTPUT_DIR, PROJECT_ROOT
from scripts.utils import setup_logging, load_yaml_file

# .env 파일 로드
load_dotenv(project_root / ".env")

# 로깅 설정
logger = setup_logging()

# AI Explainer Topics 파일 경로
AI_EXPLAINER_TOPICS_FILE = project_root / "data" / "ai_explainer_topics.yaml"


def load_ai_explainer_topics() -> dict:
    """AI Explainer 주제 파일 로드"""
    return load_yaml_file(AI_EXPLAINER_TOPICS_FILE)


def generate_script_with_claude(
    topic_name: str,
    topic_data: Dict,
    part_number: Optional[int] = None
) -> Dict[str, any]:
    """
    Claude 3.5 Sonnet을 사용하여 AI Explainer 스크립트 생성
    
    Args:
        topic_name: 주제 이름
        topic_data: 주제 데이터 (title, description, keywords 등)
        part_number: 시리즈의 몇 번째 파트인지 (None이면 단독 주제)
    
    Returns:
        {
            "hook": "시작 훅 텍스트",
            "sections": [
                {
                    "title": "섹션 제목",
                    "content": "섹션 내용",
                    "duration_seconds": 120,
                    "broll_timing": [30, 60, 90]  # B-roll 삽입 시점 (초)
                }
            ],
            "outro": "마무리 텍스트",
            "total_duration_seconds": 1200
        }
    """
    try:
        from src.api.api_manager import APIManager
        
        api_manager = APIManager()
        
        # 주제 정보 추출
        title = topic_data.get("title", topic_name)
        description = topic_data.get("description", "")
        keywords = topic_data.get("keywords", [])
        target_audience = topic_data.get("target_audience", "일반인")
        duration_minutes = topic_data.get("duration_minutes", 20)
        
        # 시리즈 정보
        series_info = ""
        if part_number:
            series_info = f"이 영상은 시리즈의 {part_number}부작입니다. "
        
        # 프롬프트 생성
        prompt = f"""AI & Tech 설명 롱폼 YouTube 영상 스크립트를 작성해주세요.

주제: {title}
설명: {description}
키워드: {', '.join(keywords)}
대상: {target_audience}
목표 길이: 약 {duration_minutes}분
{series_info}

스크립트 구조:
1. Hook (시작 부분, 15초): 시청자의 관심을 끄는 강력한 시작
2. Sections (본문, 여러 섹션):
   - 각 섹션은 명확한 주제를 가져야 함
   - 각 섹션은 약 2-4분 길이
   - 각 섹션마다 B-roll 영상 삽입 시점 표시 (30초마다)
   - 실용적인 예시와 코드/스크린샷 설명 포함
3. Outro (마무리, 10초): 요약 및 다음 영상/구독 유도

응답 형식 (JSON):
{{
    "hook": "시작 훅 텍스트 (약 50-100단어)",
    "sections": [
        {{
            "title": "섹션 제목",
            "content": "섹션 내용 (상세하게, 약 300-500단어)",
            "duration_seconds": 180,
            "broll_timing": [30, 60, 90, 120, 150],
            "code_snippets": ["코드 예시 1", "코드 예시 2"],  # 선택사항: Python 코드 스니펫
            "diagrams": ["개념 설명 1", "개념 설명 2"]  # 선택사항: 다이어그램으로 설명할 개념
        }}
    ],
    "outro": "마무리 텍스트 (약 30-50단어)",
    "total_duration_seconds": {duration_minutes * 60}
}}

중요:
- 한국어로 작성
- 전문적이지만 이해하기 쉽게
- 실용적인 예시와 코드 포함
- 시청자가 따라할 수 있는 단계별 설명
- SEO를 고려한 키워드 자연스럽게 포함
- 코드가 필요한 경우 "code_snippets" 배열에 Python 코드 예시 포함
- 시각적 설명이 필요한 경우 "diagrams" 배열에 다이어그램으로 설명할 개념 포함"""
        
        logger.info(f"AI 모델로 스크립트 생성 중... (주제: {title})")
        
        # Claude 시도 (실패 시 OpenAI로 자동 fallback)
        result = None
        
        # 사용 가능한 Claude 모델 우선순위: Opus > Haiku (Sonnet은 권한 문제로 접근 불가)
        claude_models = [
            "claude-3-opus-20240229",  # 가장 강력하지만 deprecated
            "claude-3-5-haiku-20241022",  # 빠르고 효율적
            "claude-3-haiku-20240307",  # 대체 옵션
        ]
        
        for model in claude_models:
            try:
                result = api_manager.generate_json(
                    prompt=prompt,
                    provider="claude",
                    model=model,
                    system_prompt="당신은 AI & Tech 분야의 전문 유튜버입니다. 명확하고 실용적인 설명 스크립트를 작성합니다."
                )
                if result:
                    logger.info(f"Claude 모델 {model} 사용 성공")
                    break
            except Exception as e:
                logger.warning(f"Claude {model} 사용 실패: {e}")
                result = None
                continue
        
        if not result:
            logger.warning("모든 Claude 모델 실패, OpenAI로 대체")
        
        # Claude 실패 시 OpenAI로 대체
        if not result:
            try:
                result = api_manager.generate_json(
                    prompt=prompt,
                    provider="openai",
                    model="gpt-4o",
                    system_prompt="당신은 AI & Tech 분야의 전문 유튜버입니다. 명확하고 실용적인 설명 스크립트를 작성합니다. 반드시 유효한 JSON 형식으로 응답하세요."
                )
            except Exception as e3:
                logger.warning(f"OpenAI generate_json 실패, generate_text로 시도: {e3}")
                # generate_json이 실패하면 generate_text로 시도
                try:
                    result_text = api_manager.generate_text(
                        prompt=prompt,
                        model="gpt-4o",
                        system_prompt="당신은 AI & Tech 분야의 전문 유튜버입니다. 명확하고 실용적인 설명 스크립트를 작성합니다. 반드시 유효한 JSON 형식으로 응답하세요."
                    )
                    # JSON 파싱 시도
                    import json
                    text = result_text.get("text", "")
                    if "```json" in text:
                        json_text = text.split("```json")[1].split("```")[0].strip()
                        result = json.loads(json_text)
                    elif "{" in text and "}" in text:
                        # 첫 번째 JSON 객체 찾기
                        start = text.find("{")
                        end = text.rfind("}") + 1
                        result = json.loads(text[start:end])
                    else:
                        raise ValueError("JSON 형식의 응답을 파싱할 수 없습니다.")
                except Exception as parse_error:
                    logger.error(f"JSON 파싱 실패: {parse_error}")
                    raise ValueError(f"JSON 형식의 응답을 파싱할 수 없습니다: {parse_error}")
        
        if not result:
            raise ValueError("모든 API에서 스크립트를 생성하지 못했습니다.")
        
        logger.info(f"스크립트 생성 완료: {len(result.get('sections', []))}개 섹션")
        return result
        
    except Exception as e:
        logger.error(f"스크립트 생성 중 오류 발생: {e}", exc_info=True)
        raise


def save_script(script_data: Dict, topic_name: str, output_dir: Optional[Path] = None) -> Path:
    """
    생성된 스크립트를 파일로 저장
    
    Args:
        script_data: 생성된 스크립트 데이터
        topic_name: 주제 이름
        output_dir: 출력 디렉토리 (None이면 자동 생성)
    
    Returns:
        저장된 스크립트 파일 경로
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR / "scripts" / "ai_explainers"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일명 생성
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{topic_name}_script.json"
    output_path = output_dir / filename
    
    # JSON 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    
    # 텍스트 파일도 생성 (읽기 쉽게)
    text_filename = f"{date_str}_{topic_name}_script.txt"
    text_path = output_dir / text_filename
    
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("HOOK (시작 부분)\n")
        f.write("=" * 60 + "\n")
        f.write(script_data.get("hook", "") + "\n\n")
        
        f.write("=" * 60 + "\n")
        f.write("SECTIONS (본문)\n")
        f.write("=" * 60 + "\n")
        for i, section in enumerate(script_data.get("sections", []), 1):
            f.write(f"\n[섹션 {i}] {section.get('title', '')}\n")
            f.write(f"길이: {section.get('duration_seconds', 0)}초\n")
            f.write(f"B-roll 시점: {section.get('broll_timing', [])}\n")
            f.write("-" * 60 + "\n")
            f.write(section.get("content", "") + "\n\n")
        
        f.write("=" * 60 + "\n")
        f.write("OUTRO (마무리)\n")
        f.write("=" * 60 + "\n")
        f.write(script_data.get("outro", "") + "\n\n")
        
        f.write("=" * 60 + "\n")
        f.write(f"총 길이: {script_data.get('total_duration_seconds', 0)}초 ({script_data.get('total_duration_seconds', 0) // 60}분)\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"스크립트 저장 완료:")
    logger.info(f"  JSON: {output_path}")
    logger.info(f"  텍스트: {text_path}")
    
    return output_path


def generate_ai_explainer_script(
    topic_name: str,
    part_number: Optional[int] = None
) -> Dict[str, any]:
    """
    AI Explainer 스크립트 생성 메인 함수
    
    Args:
        topic_name: 주제 이름 (topics.yaml의 키 또는 standalone_topics의 name)
        part_number: 시리즈의 몇 번째 파트인지 (None이면 단독 주제)
    
    Returns:
        생성된 스크립트 데이터
    """
    try:
        # 주제 파일 로드
        topics_data = load_ai_explainer_topics()
        topics = topics_data.get("topics", {})
        standalone_topics = topics_data.get("standalone_topics", [])
        
        # 주제 찾기
        topic_data = None
        
        # 시리즈에서 찾기
        if part_number:
            for series_name, series_info in topics.items():
                if series_info.get("name") == topic_name or series_name == topic_name:
                    parts = series_info.get("parts", [])
                    for part in parts:
                        if part.get("part") == part_number:
                            topic_data = part
                            break
                    if topic_data:
                        break
        
        # 단독 주제에서 찾기
        if not topic_data:
            for topic in standalone_topics:
                if topic.get("name") == topic_name:
                    topic_data = topic
                    break
        
        if not topic_data:
            raise ValueError(f"주제를 찾을 수 없습니다: {topic_name}")
        
        logger.info(f"AI Explainer 스크립트 생성 시작: {topic_data.get('title', topic_name)}")
        
        # 스크립트 생성
        script_data = generate_script_with_claude(topic_name, topic_data, part_number)
        
        # 메타데이터 추가
        script_data["metadata"] = {
            "topic_name": topic_name,
            "title": topic_data.get("title", topic_name),
            "description": topic_data.get("description", ""),
            "keywords": topic_data.get("keywords", []),
            "target_audience": topic_data.get("target_audience", "일반인"),
            "part_number": part_number,
            "created_at": datetime.now().isoformat()
        }
        
        # 스크립트 저장
        script_file_path = save_script(script_data, topic_name)
        
        logger.info(f"스크립트 생성 완료: {len(script_data.get('sections', []))}개 섹션")
        logger.info(f"스크립트 파일: {script_file_path}")
        
        # 스크립트 파일 경로를 메타데이터에 추가
        script_data["script_file_path"] = str(script_file_path)
        
        return script_data
        
    except Exception as e:
        logger.error(f"스크립트 생성 중 오류 발생: {e}", exc_info=True)
        raise


def list_topics():
    """사용 가능한 주제 목록 출력"""
    try:
        topics_data = load_ai_explainer_topics()
        topics = topics_data.get("topics", {})
        standalone_topics = topics_data.get("standalone_topics", [])
        
        print("\n" + "=" * 60)
        print("AI Explainer 주제 목록")
        print("=" * 60)
        
        print("\n[시리즈]")
        for series_name, series_info in topics.items():
            print(f"\n  {series_info.get('name', series_name)}")
            print(f"    설명: {series_info.get('description', '')}")
            print(f"    파트 수: {series_info.get('series_parts', 0)}")
            for part in series_info.get("parts", []):
                print(f"      - Part {part.get('part')}: {part.get('title', '')}")
        
        print("\n[단독 주제]")
        for topic in standalone_topics:
            print(f"  - {topic.get('name', '')}")
            print(f"    설명: {topic.get('description', '')}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        logger.error(f"주제 목록 출력 중 오류 발생: {e}")
        print("주제 목록을 불러올 수 없습니다.")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Explainer 스크립트 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 주제 목록 보기
  python scripts/generate_ai_explainers.py --list-topics
  
  # 단독 주제 스크립트 생성
  python scripts/generate_ai_explainers.py --topic "ChatGPT로 코딩하기: 실전 팁"
  
  # 시리즈 파트 스크립트 생성
  python scripts/generate_ai_explainers.py --topic "개발자를 위한 AI 자동화" --part 1
        """
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        help="주제 이름"
    )
    
    parser.add_argument(
        "--part",
        type=int,
        help="시리즈의 몇 번째 파트인지 (시리즈인 경우)"
    )
    
    parser.add_argument(
        "--list-topics",
        action="store_true",
        help="사용 가능한 주제 목록 출력"
    )
    
    args = parser.parse_args()
    
    if args.list_topics:
        list_topics()
        return
    
    if not args.topic:
        parser.error("--topic이 필요합니다. --list-topics로 사용 가능한 주제를 확인하세요.")
    
    # 스크립트 생성
    script_data = generate_ai_explainer_script(args.topic, args.part)
    
    print("\n" + "=" * 60)
    print("스크립트 생성 완료!")
    print("=" * 60)
    print(f"제목: {script_data['metadata']['title']}")
    print(f"섹션 수: {len(script_data.get('sections', []))}")
    print(f"총 길이: {script_data.get('total_duration_seconds', 0) // 60}분")
    print("=" * 60)


if __name__ == "__main__":
    main()

