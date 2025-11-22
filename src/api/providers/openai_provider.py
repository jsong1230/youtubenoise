"""
OpenAI API Provider
GPT-4o, GPT-4o-mini, DALL-E 3 지원
"""
import os
import sys
import logging
import base64
import io
from pathlib import Path
from typing import Optional, Dict, List
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from PIL import Image

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import IMAGES_DIR
from scripts.utils import retry_with_backoff

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI API 래퍼"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        OpenAI Provider 초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI Provider 초기화 완료")
    
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
        model: str = "gpt-4o-mini",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, any]:
        """
        텍스트 생성 (Chat Completion)
        
        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름 (gpt-4o, gpt-4o-mini 등)
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0-2.0)
            system_prompt: 시스템 프롬프트
        
        Returns:
            {
                "text": 생성된 텍스트,
                "model": 사용된 모델,
                "usage": 토큰 사용량 정보
            }
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        logger.info(f"OpenAI 텍스트 생성 중... (모델: {model})")
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        text = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        logger.info(f"텍스트 생성 완료 (토큰: {usage['total_tokens']})")
        
        return {
            "text": text,
            "model": model,
            "usage": usage
        }
    
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        output_path: Optional[Path] = None,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None
    ) -> Optional[Path]:
        """
        DALL-E 3로 이미지 생성
        
        Args:
            prompt: 이미지 생성 프롬프트
            size: 이미지 크기 ("1024x1024", "1792x1024", "1024x1792")
            quality: 품질 ("standard", "hd")
            output_path: 저장 경로 (None이면 자동 생성)
            target_width: 리사이즈할 목표 너비 (None이면 원본 크기 유지)
            target_height: 리사이즈할 목표 높이 (None이면 원본 크기 유지)
        
        Returns:
            저장된 이미지 파일 경로
        """
        try:
            logger.info(f"DALL-E 3 이미지 생성 중... (프롬프트: {prompt[:50]}...)")
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
            
            image_url = response.data[0].url
            
            # 이미지 다운로드
            import requests
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # PIL Image로 변환
            img = Image.open(io.BytesIO(img_response.content))
            img = img.convert("RGB")
            
            # 목표 크기가 지정된 경우 리사이즈 (16:9 비율 유지하며 크롭)
            if target_width and target_height:
                from scripts.generate_image import resize_and_crop_to_aspect
                img = resize_and_crop_to_aspect(img, target_width, target_height)
                logger.info(f"DALL-E 이미지를 {target_width}x{target_height}로 리사이즈 완료")
            
            # 저장 경로 설정
            if output_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                output_path = IMAGES_DIR / f"dalle_{timestamp}.png"
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG")
            
            logger.info(f"이미지 생성 완료: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"DALL-E 3 이미지 생성 실패: {e}", exc_info=True)
            return None
    
    def generate_json(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
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

