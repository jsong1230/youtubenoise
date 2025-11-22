"""
Claude API Provider (Anthropic)
Claude 3.5 Sonnet, Claude 3 Haiku 지원
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils import retry_with_backoff

logger = logging.getLogger(__name__)


class ClaudeProvider:
    """Anthropic Claude API 래퍼"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Claude Provider 초기화
        
        Args:
            api_key: Anthropic API 키 (None이면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY 또는 CLAUDE_API_KEY가 설정되지 않았습니다.")
        
        self.client = Anthropic(api_key=self.api_key)
        logger.info("Claude Provider 초기화 완료")
    
    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(APIError, RateLimitError, APIConnectionError),
        logger=None
    )
    def generate_text(
        self,
        prompt: str,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, any]:
        """
        텍스트 생성 (Message API)
        
        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름
                - claude-3-5-sonnet-20241022: 긴 콘텐츠, 복잡한 작업
                - claude-3-5-haiku-20241022: 빠른 메타데이터, 간단한 작업
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0-1.0)
            system_prompt: 시스템 프롬프트
        
        Returns:
            {
                "text": 생성된 텍스트,
                "model": 사용된 모델,
                "usage": 토큰 사용량 정보
            }
        """
        logger.info(f"Claude 텍스트 생성 중... (모델: {model})")
        
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        text = response.content[0].text
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }
        
        logger.info(f"텍스트 생성 완료 (토큰: {usage['total_tokens']})")
        
        return {
            "text": text,
            "model": model,
            "usage": usage
        }
    
    def generate_json(
        self,
        prompt: str,
        model: str = "claude-3-5-haiku-20241022",
        system_prompt: Optional[str] = None
    ) -> Optional[Dict]:
        """
        JSON 형식 응답 생성
        
        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름
            system_prompt: 시스템 프롬프트
        
        Returns:
            파싱된 JSON 딕셔너리
        """
        try:
            json_prompt = f"{prompt}\n\n응답은 반드시 유효한 JSON 형식으로만 반환해주세요."
            
            result = self.generate_text(
                prompt=json_prompt,
                model=model,
                system_prompt=system_prompt or "You are a helpful assistant that returns only valid JSON."
            )
            
            import json
            text = result["text"].strip()
            
            # JSON 코드 블록 제거 (```json ... ```)
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            
            return json.loads(text)
            
        except Exception as e:
            logger.error(f"JSON 생성 실패: {e}", exc_info=True)
            return None

