"""
제목·설명·태그 자동 생성 스크립트
OpenAI API를 사용하여 유튜브 영상 메타데이터 생성
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE, BGM_PRESETS_FILE, CONFIG_JSON_FILE, OUTPUT_DIR, PROJECT_ROOT
from scripts.utils import setup_logging, load_json_file

# .env 파일 로드
load_dotenv(project_root / ".env")

# 로깅 설정
logger = setup_logging()

# API Manager import
try:
    from src.api.api_manager import APIManager
    API_MANAGER_AVAILABLE = True
except ImportError:
    API_MANAGER_AVAILABLE = False
    logger.warning("API Manager를 사용할 수 없습니다. OpenAI만 사용합니다.")


def load_config() -> dict:
    """config.json 파일 로드"""
    return load_json_file(CONFIG_JSON_FILE)


def get_noise_type_display_name(noise_type: str) -> str:
    """노이즈 타입의 표시 이름 반환"""
    display_names = {
        "white_noise": "White Noise",
        "brown_noise": "Brown Noise",
        "pink_noise": "Pink Noise",
        "rain": "Rain Sounds",
        "ocean": "Ocean Waves",
        "fireplace": "Fireplace Sounds",
        "lofi": "Lofi Hip Hop",
        "asmr": "ASMR",
    }
    return display_names.get(noise_type, noise_type.replace("_", " ").title())


def get_use_cases_for_noise_type(noise_type: str) -> str:
    """노이즈 타입에 따른 사용 사례 반환"""
    use_cases = {
        "white_noise": "sleep, study, focus, relaxation, meditation, and blocking out distractions",
        "brown_noise": "deep sleep, concentration, stress relief, and creating a calming atmosphere",
        "pink_noise": "sleep, focus, relaxation, and improving concentration",
        "rain": "sleep, study, relaxation, meditation, and creating a peaceful atmosphere",
        "ocean": "deep sleep, meditation, stress relief, and creating a serene environment",
        "fireplace": "cozy relaxation, study, reading, and creating a warm, comforting atmosphere",
        "lofi": "study, focus, concentration, work, reading, and creating a productive atmosphere",
        "asmr": "relaxation, sleep, stress relief, meditation, tingles, and creating a calming experience",
    }
    return use_cases.get(noise_type, "sleep, study, focus, and relaxation")




def generate_bilingual_metadata_for_bgm(
    preset_name: str,
    duration_minutes: int,
    language_primary: str = "en",
    language_secondary: str = "ko",
    region: str = "NA"
) -> Dict[str, any]:
    """
    BGM용 이중언어 메타데이터 생성 함수
    
    Args:
        preset_name: BGM 프리셋 이름
        duration_minutes: 길이 (분)
        language_primary: 주 언어 ("ko" 또는 "en")
        language_secondary: 보조 언어 ("ko" 또는 "en")
        region: 타겟 지역 ("KR", "NA", "Global")
    
    Returns:
        {title, description, tags} 딕셔너리 (이중언어 포함)
    """
    try:
        import yaml
        
        # 프리셋 정보 로드
        presets_path = BGM_PRESETS_FILE
        with open(presets_path, 'r', encoding='utf-8') as f:
            presets_data = yaml.safe_load(f)
            presets = presets_data.get("presets", {})
            
        if preset_name not in presets:
            raise ValueError(f"프리셋을 찾을 수 없습니다: {preset_name}")
        
        preset = presets[preset_name]
        preset_name_display = preset.get("name", preset_name)
        preset_description = preset.get("description", "")
        preset_tags = preset.get("tags", [])
        style = preset.get("style", "")
        
        # 프리셋에서 언어 설정 확인 (없으면 파라미터 사용)
        preset_languages = preset.get("languages", [language_primary, language_secondary])
        preset_regions = preset.get("region_targets", [region])
        
        # 시간 포맷팅
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        if hours > 0:
            duration_str_ko = f"{hours}시간 {minutes}분" if minutes > 0 else f"{hours}시간"
            duration_str_en = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        else:
            duration_str_ko = f"{minutes}분"
            duration_str_en = f"{minutes}min"
        
        # 이중언어 프롬프트 생성
        lang_names = {"ko": "한국어", "en": "영어"}
        region_names = {"KR": "한국", "NA": "북미", "Global": "글로벌"}
        
        prompt = f"""Create bilingual YouTube video metadata for a long-form BGM (Background Music) video.

Preset Information:
- Name: {preset_name_display}
- Description: {preset_description}
- Style: {style}
- Duration: {duration_str_ko} ({duration_minutes} minutes)
- Primary Language: {lang_names.get(language_primary, language_primary)}
- Secondary Language: {lang_names.get(language_secondary, language_secondary)}
- Target Region: {region_names.get(region, region)}

IMPORTANT: This is original, copyright-free music generated algorithmically. It is NOT a cover or remix of any existing copyrighted song.

Requirements:
1. Title: Create a bilingual title ALWAYS in the format "English | Korean" (English first, then Korean)
   Example: "Christmas Cafe Background Music ({duration_str_en}) | 크리스마스 카페 BGM"
   Or: "Brain Workout ({duration_str_en}) | 시니어 두뇌운동"
   IMPORTANT: English must always come first, regardless of language_primary setting.
   Maximum 100 characters total.

2. Description: Create a bilingual description with 3 sections (English first, then Korean):
   - Section 1: English description (2-3 paragraphs) - MUST come first
   - Section 2: Korean description (2-3 paragraphs) - MUST come second
   - Section 3: Mixed section with key information in both languages
   IMPORTANT: English section must always come before Korean section, regardless of language_primary setting.
   Include:
     * Introduction about this original, copyright-free BGM
     * Style and atmosphere
     * What it's good for: cafe, study, work, relaxation, background music
     * Note that this is original music, not a cover
     * Simple timeline (e.g., "00:00:00 - Start")
     * Hashtags at the end in both languages

3. Tags: Provide a list of 15-20 relevant tags as a JSON array, mixing both languages.
   Include: {', '.join(preset_tags[:5])} and related terms in both languages.
   Example: ["bgm", "background music", "배경음악", "cafe", "카페", "study", "공부", ...]

Return the response as a JSON object with the following structure:
{{
    "title": "English Title (duration) | 한국어 제목",
    "description": "Section 1 (English)...\n\n---\n\nSection 2 (Korean)...\n\n---\n\nSection 3 (Mixed)...",
    "tags": ["tag1", "tag2", ...]
}}"""

        # API Manager 사용 (Claude Haiku 우선)
        if API_MANAGER_AVAILABLE:
            try:
                api_manager = APIManager()
                logger.info("API Manager로 이중언어 메타데이터 생성 중... (Claude Haiku 우선)")
                
                result = api_manager.generate_json(
                    prompt=prompt,
                    provider="claude",  # Claude 우선
                    model="claude-3-5-haiku-20241022",
                    system_prompt="You are a helpful assistant that creates engaging bilingual YouTube video metadata for original, copyright-free background music. Always respond with valid JSON only."
                )
                
                if result:
                    metadata = result
                else:
                    raise ValueError("API Manager에서 결과를 받지 못했습니다.")
                    
            except Exception as e:
                logger.warning(f"API Manager 사용 실패: {e}, OpenAI로 전환")
                # OpenAI로 폴백
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                
                client = OpenAI(api_key=api_key)
                config = load_config()
                model = config.get("openai_model", "gpt-4o-mini")
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates engaging bilingual YouTube video metadata for original, copyright-free background music. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                )
                
                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                
                metadata = json.loads(content)
        else:
            # OpenAI 직접 사용
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            
            client = OpenAI(api_key=api_key)
            config = load_config()
            model = config.get("openai_model", "gpt-4o-mini")
            
            logger.info(f"OpenAI API로 이중언어 메타데이터 생성 중... (모델: {model})")
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates engaging bilingual YouTube video metadata for original, copyright-free background music. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
            
            metadata = json.loads(content)
        
        # 프리셋 태그 추가
        if isinstance(metadata.get("tags"), list):
            metadata["tags"] = list(set(metadata["tags"] + preset_tags))  # 중복 제거
        
        logger.info(f"이중언어 BGM 메타데이터 생성 완료")
        logger.info(f"제목: {metadata.get('title', 'N/A')}")
        logger.info(f"태그 수: {len(metadata.get('tags', []))}")
        
        return metadata
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        logger.error(f"응답 내용: {content if 'content' in locals() else 'N/A'}")
        # 폴백 메타데이터 반환
        return generate_fallback_bilingual_metadata_for_bgm(preset_name, duration_minutes, language_primary, language_secondary)
    except Exception as e:
        logger.error(f"이중언어 BGM 메타데이터 생성 중 오류 발생: {e}", exc_info=True)
        # 폴백 메타데이터 반환
        return generate_fallback_bilingual_metadata_for_bgm(preset_name, duration_minutes, language_primary, language_secondary)


def generate_fallback_bilingual_metadata_for_bgm(
    preset_name: str,
    duration_minutes: int,
    language_primary: str = "en",
    language_secondary: str = "ko"
) -> Dict[str, any]:
    """이중언어 BGM API 실패 시 사용할 기본 메타데이터"""
    import yaml
    presets_path = BGM_PRESETS_FILE
    try:
        with open(presets_path, 'r', encoding='utf-8') as f:
            presets_data = yaml.safe_load(f)
            presets = presets_data.get("presets", {})
            preset = presets.get(preset_name, {})
    except:
        preset = {}
    
    preset_name_display = preset.get("name", preset_name.replace("_", " ").title())
    preset_tags = preset.get("tags", ["bgm", "background music", "music"])
    
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    if hours > 0:
        duration_str_ko = f"{hours}시간 {minutes}분" if minutes > 0 else f"{hours}시간"
        duration_str_en = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    else:
        duration_str_ko = f"{minutes}분"
        duration_str_en = f"{minutes}min"
    
    # 항상 영어가 먼저 오도록 수정
    title = f"{preset_name_display} - {duration_str_en} Long Form BGM | {preset_name_display} - {duration_str_ko} 롱폼 BGM"
    
    description_en = f"""Welcome to {duration_str_en} of original, copyright-free background music: {preset_name_display}.

This algorithmically generated original music is perfect for:
- Cafe ambiance
- Study and work
- Relaxation
- Background music for your videos
- Creating a peaceful atmosphere

This is original music, not a cover or remix of any existing copyrighted song.

Timeline:
00:00:00 - Start"""
    
    description_ko = f"""환영합니다! {duration_str_ko} 길이의 오리지널, 저작권 없는 배경음악: {preset_name_display}입니다.

이 알고리즘으로 생성된 오리지널 음악은 다음과 같은 용도에 완벽합니다:
- 카페 분위기
- 공부 및 업무
- 휴식
- 영상 배경음악
- 평화로운 분위기 조성

이것은 기존 저작권이 있는 곡의 커버나 리믹스가 아닌 오리지널 음악입니다.

타임라인:
00:00:00 - 시작"""
    
    # 영어가 먼저 오도록 수정
    description = f"{description_en}\n\n---\n\n{description_ko}\n\n#bgm #backgroundmusic #배경음악 #music #음악 #cafe #카페 #study #공부 #work #업무 #relaxation #휴식"
    
    tags = preset_tags + ["bgm", "background music", "배경음악", "original music", "오리지널 음악", "copyright free", "저작권 없음", "instrumental", "기악", "ambient", "앰비언트", "study music", "공부 음악", "cafe music", "카페 음악"]
    
    logger.warning("이중언어 BGM 폴백 메타데이터 사용")
    return {
        "title": title,
        "description": description,
        "tags": list(set(tags))
    }


def generate_metadata_for_bgm(preset_name: str, duration_minutes: int, use_bilingual: bool = True) -> Dict[str, any]:
    """
    BGM용 메타데이터 생성 함수 (이중언어 지원)
    
    Args:
        preset_name: BGM 프리셋 이름
        duration_minutes: 길이 (분)
        use_bilingual: 이중언어 메타데이터 사용 여부 (기본값: True)
    
    Returns:
        {title, description, tags} 딕셔너리
    """
    try:
        import yaml
        
        # 프리셋 정보 로드
        presets_path = BGM_PRESETS_FILE
        with open(presets_path, 'r', encoding='utf-8') as f:
            presets_data = yaml.safe_load(f)
            presets = presets_data.get("presets", {})
            
        if preset_name not in presets:
            raise ValueError(f"프리셋을 찾을 수 없습니다: {preset_name}")
        
        preset = presets[preset_name]
        
        # 프리셋에서 언어 설정 확인 (기본값: 영어 우선)
        preset_languages = preset.get("languages", ["en", "ko"])
        preset_regions = preset.get("region_targets", ["NA", "KR"])
        
        # 이중언어 메타데이터 생성
        if use_bilingual and len(preset_languages) >= 2:
            language_primary = preset_languages[0]
            language_secondary = preset_languages[1]
            region = preset_regions[0] if preset_regions else "KR"
            
            return generate_bilingual_metadata_for_bgm(
                preset_name=preset_name,
                duration_minutes=duration_minutes,
                language_primary=language_primary,
                language_secondary=language_secondary,
                region=region
            )
        
        # 단일 언어 메타데이터 생성 (기존 방식)
        # OpenAI API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        client = OpenAI(api_key=api_key)
        
        # 설정 로드
        config = load_config()
        model = config.get("openai_model", "gpt-4o-mini")
        
        preset_name_display = preset.get("name", preset_name)
        preset_description = preset.get("description", "")
        preset_tags = preset.get("tags", [])
        style = preset.get("style", "")
        
        # 시간 포맷팅 (기본값: 영어)
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        if hours > 0:
            duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        else:
            duration_str = f"{minutes}min"
        
        # 프롬프트 생성 (기본값: 영어)
        prompt = f"""Create YouTube video metadata for a long-form BGM (Background Music) video.

Preset Information:
- Name: {preset_name_display}
- Description: {preset_description}
- Style: {style}
- Duration: {duration_str} ({duration_minutes} minutes)

IMPORTANT: This is original, copyright-free music generated algorithmically. It is NOT a cover or remix of any existing copyrighted song.

Requirements:
1. Title: Should be engaging, SEO-friendly, and include the duration. Maximum 100 characters.
   Example format: "{preset_name_display} - {duration_str} Long Form BGM"
   Or: "{preset_name_display} Background Music ({duration_str})"

2. Description: Should include:
   - A brief introduction about this original, copyright-free BGM
   - The style and atmosphere (e.g., "Christmas-inspired jazz", "cafe ambiance", "classical")
   - What it's good for: cafe, study, work, relaxation, background music
   - A note that this is original music, not a cover
   - A simple timeline (e.g., "00:00:00 - Start")
   - Hashtags at the end
   - Keep it natural and engaging, around 3-5 paragraphs

3. Tags: Provide a list of 10-15 relevant tags as a JSON array. Include: {', '.join(preset_tags[:5])} and related terms.
   Example: {preset_tags}

Return the response as a JSON object with the following structure:
{{
    "title": "...",
    "description": "...",
    "tags": ["tag1", "tag2", ...]
}}"""

        logger.info(f"OpenAI API로 BGM 메타데이터 생성 중... (모델: {model})")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates engaging YouTube video metadata for original, copyright-free background music. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        content = response.choices[0].message.content.strip()
        
        # JSON 파싱 (마크다운 코드 블록 제거)
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
        
        # JSON 파싱
        metadata = json.loads(content)
        
        # 프리셋 태그 추가
        if isinstance(metadata.get("tags"), list):
            metadata["tags"] = list(set(metadata["tags"] + preset_tags))  # 중복 제거
        
        logger.info(f"BGM 메타데이터 생성 완료")
        logger.info(f"제목: {metadata.get('title', 'N/A')}")
        logger.info(f"태그 수: {len(metadata.get('tags', []))}")
        
        return metadata
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        logger.error(f"응답 내용: {content if 'content' in locals() else 'N/A'}")
        # 폴백 메타데이터 반환
        return generate_fallback_metadata_for_bgm(preset_name, duration_minutes)
    except Exception as e:
        logger.error(f"BGM 메타데이터 생성 중 오류 발생: {e}", exc_info=True)
        # 폴백 메타데이터 반환
        return generate_fallback_metadata_for_bgm(preset_name, duration_minutes)


def generate_fallback_metadata_for_bgm(preset_name: str, duration_minutes: int) -> Dict[str, any]:
    """BGM API 실패 시 사용할 기본 메타데이터"""
    import yaml
    presets_path = BGM_PRESETS_FILE
    try:
        with open(presets_path, 'r', encoding='utf-8') as f:
            presets_data = yaml.safe_load(f)
            presets = presets_data.get("presets", {})
            preset = presets.get(preset_name, {})
    except:
        preset = {}
    
    preset_name_display = preset.get("name", preset_name.replace("_", " ").title())
    preset_tags = preset.get("tags", ["bgm", "background music", "music"])
    
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    if hours > 0:
        duration_str = f"{hours}시간 {minutes}분" if minutes > 0 else f"{hours}시간"
    else:
        duration_str = f"{minutes}분"
    
    title = f"{preset_name_display} - {duration_str} Long Form BGM"
    
    description = f"""Welcome to {duration_str} of original, copyright-free background music: {preset_name_display}.

This is algorithmically generated original music, perfect for:
- Cafe ambiance
- Study and work
- Relaxation
- Background music for your videos
- Creating a peaceful atmosphere

This is original music, not a cover or remix of any existing copyrighted song.

Timeline:
00:00:00 - Start

#bgm #backgroundmusic #music #cafe #study #work #relaxation #ambient #instrumental"""
    
    tags = preset_tags + ["bgm", "background music", "original music", "copyright free", "instrumental", "ambient", "study music", "cafe music"]
    
    logger.warning("BGM 폴백 메타데이터 사용")
    return {
        "title": title,
        "description": description,
        "tags": list(set(tags))
    }


def generate_metadata(noise_type: str, duration_hours: int) -> Dict[str, any]:
    """
    메타데이터 생성 함수
    
    Args:
        noise_type: 노이즈 타입
        duration_hours: 길이 (시간)
    
    Returns:
        {title, description, tags} 딕셔너리
    """
    try:
        # OpenAI API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        client = OpenAI(api_key=api_key)
        
        # 설정 로드
        config = load_config()
        model = config.get("openai_model", "gpt-4o-mini")
        
        # 노이즈 타입 정보
        display_name = get_noise_type_display_name(noise_type)
        use_cases = get_use_cases_for_noise_type(noise_type)
        
        # 프롬프트 생성
        prompt = f"""Create YouTube video metadata for a {display_name} audio video that is {duration_hours} hours long.

Requirements:
1. Title: Should be engaging, SEO-friendly, and include the duration. Maximum 100 characters.
   Example format: "{display_name} for Deep Sleep ({duration_hours} Hours)"

2. Description: Should include:
   - A brief introduction paragraph about the audio
   - What it's good for: {use_cases}
   - A simple timeline (e.g., "00:00:00 - Start")
   - Hashtags at the end (e.g., #whitenoise #sleep #relax #asmr)
   - Keep it natural and engaging, around 3-5 paragraphs

3. Tags: Provide a list of 10-15 relevant tags as a JSON array. Include variations and related terms.
   Example: ["white noise", "sleep sounds", "relaxation", "study music", "focus", "asmr", "meditation", "deep sleep", "calm", "peaceful"]

Return the response as a JSON object with the following structure:
{{
    "title": "...",
    "description": "...",
    "tags": ["tag1", "tag2", ...]
}}"""

        logger.info(f"OpenAI API로 메타데이터 생성 중... (모델: {model})")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates engaging YouTube video metadata. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        content = response.choices[0].message.content.strip()
        
        # JSON 파싱 (마크다운 코드 블록 제거)
        if content.startswith("```"):
            # 코드 블록 제거
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
        
        # JSON 파싱
        metadata = json.loads(content)
        
        # 기본 태그 추가 (config에서)
        default_tags = config.get("youtube", {}).get("default_tags", [])
        if isinstance(metadata.get("tags"), list):
            metadata["tags"] = list(set(metadata["tags"] + default_tags))  # 중복 제거
        
        logger.info(f"메타데이터 생성 완료")
        logger.info(f"제목: {metadata.get('title', 'N/A')}")
        logger.info(f"태그 수: {len(metadata.get('tags', []))}")
        
        return metadata
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        logger.error(f"응답 내용: {content}")
        # 폴백 메타데이터 반환
        return generate_fallback_metadata(noise_type, duration_hours)
    except Exception as e:
        logger.error(f"메타데이터 생성 중 오류 발생: {e}", exc_info=True)
        # 폴백 메타데이터 반환
        return generate_fallback_metadata(noise_type, duration_hours)


def generate_fallback_metadata(noise_type: str, duration_hours: int) -> Dict[str, any]:
    """API 실패 시 사용할 기본 메타데이터"""
    display_name = get_noise_type_display_name(noise_type)
    use_cases = get_use_cases_for_noise_type(noise_type)
    
    title = f"{display_name} for Deep Sleep ({duration_hours} Hours)"
    
    description = f"""Welcome to {duration_hours} hours of {display_name.lower()} for deep sleep, relaxation, and focus.

This calming audio is perfect for {use_cases}. Whether you're trying to fall asleep, need background noise for studying, or want to create a peaceful atmosphere, this {display_name.lower()} will help you relax and unwind.

Simply press play and let the soothing sounds wash over you. No interruptions, no ads in the middle - just pure, continuous audio to help you rest, focus, or meditate.

Timeline:
00:00:00 - Start

#whitenoise #sleep #relax #asmr #meditation #studymusic #focus #peaceful #calm #sleepsounds #relaxation #backgroundnoise #sleepaid #deepsleep #ambient"""
    
    # 기본 태그
    base_tags = ["sleep", "relax", "study", "focus", "meditation", "peaceful", "calm"]
    type_specific_tags = {
        "white_noise": ["white noise", "sleep sounds", "background noise", "sleep aid", "deep sleep", "relaxation", "asmr", "ambient"],
        "brown_noise": ["brown noise", "sleep sounds", "deep sleep", "concentration", "stress relief", "calming", "relaxation"],
        "pink_noise": ["pink noise", "sleep sounds", "focus music", "relaxation", "concentration", "study music"],
        "rain": ["rain sounds", "rain", "sleep sounds", "nature sounds", "relaxation", "meditation", "peaceful"],
        "ocean": ["ocean waves", "ocean sounds", "waves", "sleep sounds", "meditation", "nature sounds", "serene"],
        "fireplace": ["fireplace", "fireplace sounds", "cozy", "warm", "relaxation", "sleep sounds", "ambient"],
        "lofi": ["lofi", "lofi hip hop", "lofi music", "study music", "chill beats", "focus music", "lofi beats", "chill", "productivity", "work music", "study beats"],
        "asmr": ["asmr", "asmr sounds", "tingles", "relaxation", "sleep", "whisper", "soft sounds", "asmr trigger", "stress relief", "calming"],
    }
    
    tags = base_tags + type_specific_tags.get(noise_type, [])
    tags = list(set(tags))  # 중복 제거
    
    logger.warning("폴백 메타데이터 사용")
    return {
        "title": title,
        "description": description,
        "tags": tags
    }


def generate_metadata_for_ai_explainer(
    topic_name: str,
    topic_data: Dict,
    script_data: Dict,
    language_primary: str = "en",
    language_secondary: str = "ko",
    region: str = "NA"
) -> Dict[str, any]:
    """
    AI Explainer용 이중언어 메타데이터 생성 함수
    
    Args:
        topic_name: 주제 이름
        topic_data: 주제 데이터
        script_data: 생성된 스크립트 데이터
        language_primary: 주 언어
        language_secondary: 보조 언어
        region: 타겟 지역
    
    Returns:
        {title, description, tags} 딕셔너리 (이중언어 포함)
    """
    try:
        from src.api.api_manager import APIManager
        
        api_manager = APIManager()
        
        title = topic_data.get("title", topic_name)
        description = topic_data.get("description", "")
        keywords = topic_data.get("keywords", [])
        target_audience = topic_data.get("target_audience", "일반인")
        num_sections = len(script_data.get("sections", []))
        duration_minutes = script_data.get("total_duration_seconds", 0) // 60
        
        lang_names = {"ko": "한국어", "en": "영어"}
        region_names = {"KR": "한국", "NA": "북미", "Global": "글로벌"}
        
        prompt = f"""Create bilingual YouTube video metadata for an AI & Tech explainer video.

Topic Information:
- Title: {title}
- Description: {description}
- Keywords: {', '.join(keywords)}
- Target Audience: {target_audience}
- Number of Sections: {num_sections}
- Duration: {duration_minutes} minutes
- Primary Language: {lang_names.get(language_primary, language_primary)}
- Secondary Language: {lang_names.get(language_secondary, language_secondary)}
- Target Region: {region_names.get(region, region)}

Requirements:
1. Title: Create a bilingual title ALWAYS in the format "English | Korean" (English first, then Korean)
   Example: "Complete Guide to AI Automation | AI 자동화 완벽 가이드"
   IMPORTANT: English must always come first, regardless of language_primary setting.
   Maximum 100 characters total.

2. Description: Create a bilingual description with 3 sections (English first, then Korean):
   - Section 1: English description (2-3 paragraphs) - MUST come first
   - Section 2: Korean description (2-3 paragraphs) - MUST come second
   - Section 3: Mixed section with key information in both languages
   IMPORTANT: English section must always come before Korean section, regardless of language_primary setting.
   Include:
     * Introduction about the topic
     * What viewers will learn
     * Key points covered
     * Who this video is for
     * Timeline/chapters if applicable
     * Hashtags at the end in both languages

3. Tags: Provide a list of 15-20 relevant tags as a JSON array, mixing both languages.
   Include: {', '.join(keywords)} and related terms in both languages.

Return the response as a JSON object with the following structure:
{{
    "title": "English Title | 한국어 제목",
    "description": "Section 1 (English)...\n\n---\n\nSection 2 (Korean)...\n\n---\n\nSection 3 (Mixed)...",
    "tags": ["tag1", "tag2", ...]
}}"""

        logger.info("API Manager로 AI Explainer 이중언어 메타데이터 생성 중...")
        
        result = api_manager.generate_json(
            prompt=prompt,
            provider="claude",
            model="claude-3-5-haiku-20241022",
            system_prompt="You are a helpful assistant that creates engaging bilingual YouTube video metadata for AI & Tech explainer videos. Always respond with valid JSON only."
        )
        
        if result:
            # 키워드 태그 추가
            if isinstance(result.get("tags"), list):
                result["tags"] = list(set(result["tags"] + keywords))
            
            logger.info(f"AI Explainer 메타데이터 생성 완료")
            return result
        else:
            raise ValueError("API Manager에서 결과를 받지 못했습니다.")
            
    except Exception as e:
        logger.error(f"AI Explainer 메타데이터 생성 중 오류 발생: {e}", exc_info=True)
        # 폴백 메타데이터 반환
        return generate_fallback_metadata_for_ai_explainer(topic_name, topic_data, script_data, language_primary, language_secondary)


def generate_fallback_metadata_for_ai_explainer(
    topic_name: str,
    topic_data: Dict,
    script_data: Dict,
    language_primary: str = "en",
    language_secondary: str = "ko"
) -> Dict[str, any]:
    """AI Explainer API 실패 시 사용할 기본 메타데이터"""
    title = topic_data.get("title", topic_name)
    description = topic_data.get("description", "")
    keywords = topic_data.get("keywords", [])
    duration_minutes = script_data.get("total_duration_seconds", 0) // 60
    
    if language_primary == "ko":
        title_bilingual = f"{title} | {title} (AI & Tech Guide)"
    else:
        title_bilingual = f"{title} | {title} (AI & Tech 가이드)"
    
    description_ko = f"""환영합니다! {title} 영상입니다.

{description}

이 영상에서는 다음을 다룹니다:
- 실용적인 예시와 코드
- 단계별 설명
- 실전 활용 팁

총 {duration_minutes}분 길이의 상세한 가이드입니다."""
    
    description_en = f"""Welcome to {title}!

{description}

In this video, we cover:
- Practical examples and code
- Step-by-step explanations
- Real-world tips

A comprehensive {duration_minutes}-minute guide."""
    
    description_full = f"{description_ko}\n\n---\n\n{description_en}\n\n#AI #Tech #가이드 #Guide #튜토리얼 #Tutorial"
    
    tags = keywords + ["AI", "Tech", "가이드", "Guide", "튜토리얼", "Tutorial", "자동화", "Automation"]
    
    logger.warning("AI Explainer 폴백 메타데이터 사용")
    return {
        "title": title_bilingual,
        "description": description_full,
        "tags": list(set(tags))
    }


def main():
    """메인 실행 함수"""
    try:
        # 명령행 인자 확인
        if len(sys.argv) < 3:
            print("사용법: python generate_title_description.py <noise_type> <duration_hours>")
            print("예시: python generate_title_description.py white_noise 4")
            sys.exit(1)
        
        noise_type = sys.argv[1]
        duration_hours = int(sys.argv[2])
        
        # 메타데이터 생성
        metadata = generate_metadata(noise_type, duration_hours)
        
        # 결과 출력
        print("\n=== 생성된 메타데이터 ===")
        print(f"\n제목:\n{metadata['title']}")
        print(f"\n설명:\n{metadata['description']}")
        print(f"\n태그:\n{', '.join(metadata['tags'])}")
        
        # JSON 파일로 저장 (선택사항)
        output_file = OUTPUT_DIR / "logs" / f"metadata_{noise_type}_{duration_hours}h.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"메타데이터 저장 완료: {output_file}")
        
        return metadata
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

