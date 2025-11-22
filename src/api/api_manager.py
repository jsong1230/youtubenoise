"""
API Manager
모든 AI/이미지 API 통합 관리 및 최적 API 자동 선택
"""
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, List

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .providers.openai_provider import OpenAIProvider
from .providers.claude_provider import ClaudeProvider
from .providers.image_provider import ImageProvider
from .usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class APIManager:
    """API 통합 관리자"""
    
    def __init__(self):
        """API Manager 초기화"""
        self.openai_provider: Optional[OpenAIProvider] = None
        self.claude_provider: Optional[ClaudeProvider] = None
        self.image_provider: Optional[ImageProvider] = None
        self.usage_tracker = UsageTracker()
        
        # Provider 초기화 (에러 발생 시 None으로 유지)
        try:
            self.openai_provider = OpenAIProvider()
        except Exception as e:
            logger.warning(f"OpenAI Provider 초기화 실패: {e}")
        
        try:
            self.claude_provider = ClaudeProvider()
        except Exception as e:
            logger.warning(f"Claude Provider 초기화 실패: {e}")
        
        self.image_provider = ImageProvider()
        
        logger.info("API Manager 초기화 완료")
    
    def generate_text(
        self,
        prompt: str,
        length: str = "short",
        priority: str = "cost",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, any]:
        """
        텍스트 생성 (자동으로 최적 API 선택)
        
        Args:
            prompt: 사용자 프롬프트
            length: 텍스트 길이 ("short", "medium", "long")
            priority: 우선순위 ("cost", "quality", "speed")
            model: 특정 모델 지정 (None이면 자동 선택)
            system_prompt: 시스템 프롬프트
        
        Returns:
            {
                "text": 생성된 텍스트,
                "provider": 사용된 제공자,
                "model": 사용된 모델,
                "usage": 토큰 사용량 정보
            }
        """
        # 모델 자동 선택
        if model is None:
            if length == "long" and priority == "cost":
                # 긴 콘텐츠 + 비용 우선: Claude Sonnet
                if self.claude_provider:
                    model = "claude-3-5-sonnet-20241022"
                    provider = "claude"
                elif self.openai_provider:
                    model = "gpt-4o-mini"
                    provider = "openai"
                else:
                    raise ValueError("사용 가능한 텍스트 생성 API가 없습니다.")
            elif length == "short" and priority == "speed":
                # 짧은 콘텐츠 + 속도 우선: Claude Haiku
                if self.claude_provider:
                    model = "claude-3-5-haiku-20241022"
                    provider = "claude"
                elif self.openai_provider:
                    model = "gpt-4o-mini"
                    provider = "openai"
                else:
                    raise ValueError("사용 가능한 텍스트 생성 API가 없습니다.")
            elif priority == "cost":
                # 비용 우선: Claude Haiku 또는 GPT-4o-mini
                if self.claude_provider:
                    model = "claude-3-5-haiku-20241022"
                    provider = "claude"
                elif self.openai_provider:
                    model = "gpt-4o-mini"
                    provider = "openai"
                else:
                    raise ValueError("사용 가능한 텍스트 생성 API가 없습니다.")
            else:
                # 기본: GPT-4o-mini
                if self.openai_provider:
                    model = "gpt-4o-mini"
                    provider = "openai"
                elif self.claude_provider:
                    model = "claude-3-5-haiku-20241022"
                    provider = "claude"
                else:
                    raise ValueError("사용 가능한 텍스트 생성 API가 없습니다.")
        else:
            # 모델 지정 시 provider 자동 감지
            if model.startswith("gpt") or model.startswith("dall-e"):
                provider = "openai"
            elif model.startswith("claude"):
                provider = "claude"
            else:
                raise ValueError(f"알 수 없는 모델: {model}")
        
        # 텍스트 생성
        try:
            if provider == "openai":
                if not self.openai_provider:
                    raise ValueError("OpenAI Provider가 초기화되지 않았습니다.")
                result = self.openai_provider.generate_text(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt
                )
                usage = result["usage"]
                self.usage_tracker.track_text_generation(
                    provider="openai",
                    model=model,
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0)
                )
            elif provider == "claude":
                if not self.claude_provider:
                    raise ValueError("Claude Provider가 초기화되지 않았습니다.")
                result = self.claude_provider.generate_text(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt
                )
                usage = result["usage"]
                self.usage_tracker.track_text_generation(
                    provider="claude",
                    model=model,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0)
                )
            else:
                raise ValueError(f"알 수 없는 제공자: {provider}")
            
            return {
                "text": result["text"],
                "provider": provider,
                "model": model,
                "usage": usage
            }
            
        except Exception as e:
            logger.error(f"텍스트 생성 실패: {e}", exc_info=True)
            raise
    
    def generate_image(
        self,
        prompt: str,
        use_dalle: bool = False,
        width: int = 1920,
        height: int = 1080,
        priority: List[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        이미지 생성 (무료 API 우선, 필요시 DALL-E)
        
        Args:
            prompt: 이미지 검색어 또는 생성 프롬프트
            use_dalle: True면 DALL-E 강제 사용
            width: 이미지 너비
            height: 이미지 높이
            priority: 무료 API 우선순위 (["unsplash", "pexels", "pixabay"])
            output_path: 저장 경로
        
        Returns:
            저장된 이미지 파일 경로
        """
        if use_dalle:
            # DALL-E 강제 사용
            if not self.openai_provider:
                raise ValueError("OpenAI Provider가 초기화되지 않았습니다.")
            
            # DALL-E 3는 1920x1080을 지원하지 않으므로, 1792x1024로 생성 후 리사이즈
            # DALL-E 지원 크기: 1024x1024, 1024x1792, 1792x1024
            dalle_size = "1792x1024"  # 16:9에 가장 가까운 크기
            target_width, target_height = width, height
            
            logger.info("DALL-E 3로 이미지 생성 중...")
            result = self.openai_provider.generate_image(
                prompt=prompt,
                size=dalle_size,
                output_path=output_path,
                target_width=target_width,
                target_height=target_height
            )
            
            if result:
                self.usage_tracker.track_image_generation(
                    provider="openai",
                    model="dall-e-3",
                    images=1
                )
            
            return result
        
        # 무료 API 시도
        if priority is None:
            priority = ["unsplash", "pexels", "pixabay"]
        
        logger.info(f"무료 이미지 API로 이미지 검색 중... (검색어: {prompt})")
        result = self.image_provider.download_image(
            query=prompt,
            width=width,
            height=height,
            priority=priority,
            output_path=output_path
        )
        
        if result:
            # 무료 API는 비용 0이므로 추적하지 않음
            return result
        
        # 최후의 수단: DALL-E
        logger.info("무료 API 실패, DALL-E 3로 이미지 생성 중...")
        if not self.openai_provider:
            logger.error("OpenAI Provider가 초기화되지 않았습니다.")
            return None
        
        # DALL-E 3는 1920x1080을 지원하지 않으므로, 1792x1024로 생성 후 리사이즈
        dalle_size = "1792x1024"  # 16:9에 가장 가까운 크기
        result = self.openai_provider.generate_image(
            prompt=prompt,
            size=dalle_size,
            output_path=output_path,
            target_width=width,
            target_height=height
        )
        
        if result:
            self.usage_tracker.track_image_generation(
                provider="openai",
                model="dall-e-3",
                images=1
            )
        
        return result
    
    def generate_json(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Optional[Dict]:
        """
        JSON 형식 응답 생성
        
        Args:
            prompt: 사용자 프롬프트
            provider: 제공자 지정 ("openai", "claude"), None이면 자동 선택
            model: 모델 지정, None이면 자동 선택
            system_prompt: 시스템 프롬프트
        
        Returns:
            파싱된 JSON 딕셔너리
        """
        if provider == "openai" or (provider is None and self.openai_provider):
            if not self.openai_provider:
                raise ValueError("OpenAI Provider가 초기화되지 않았습니다.")
            return self.openai_provider.generate_json(
                prompt=prompt,
                model=model or "gpt-4o-mini",
                system_prompt=system_prompt
            )
        elif provider == "claude" or (provider is None and self.claude_provider):
            if not self.claude_provider:
                raise ValueError("Claude Provider가 초기화되지 않았습니다.")
            return self.claude_provider.generate_json(
                prompt=prompt,
                model=model or "claude-3-5-haiku-20241022",
                system_prompt=system_prompt
            )
        else:
            raise ValueError("사용 가능한 JSON 생성 API가 없습니다.")

