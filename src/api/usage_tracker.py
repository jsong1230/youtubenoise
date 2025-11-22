"""
API 사용량 및 비용 추적 시스템
일별/월별 비용 계산 및 data/api_usage.json에 저장
"""
import json
import sys
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Optional
from collections import defaultdict

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_DIR

logger = logging.getLogger(__name__)


# API 비용 (USD per 1M tokens or per image)
COST_PER_MILLION_TOKENS = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "dall-e-3": {"image": 0.04},  # per image (1024x1024)
    
    # Claude
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
}

# 무료 API는 비용 0
FREE_APIS = ["unsplash", "pexels", "pixabay"]


class UsageTracker:
    """API 사용량 및 비용 추적"""
    
    def __init__(self, usage_file: Optional[Path] = None):
        """
        Usage Tracker 초기화
        
        Args:
            usage_file: 사용량 파일 경로 (None이면 data/api_usage.json)
        """
        self.usage_file = usage_file or (DATA_DIR / "api_usage.json")
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 기존 데이터 로드
        self.data = self._load_data()
        logger.info(f"Usage Tracker 초기화 완료: {self.usage_file}")
    
    def _load_data(self) -> Dict:
        """사용량 데이터 로드"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"사용량 파일 로드 실패: {e}, 새로 생성합니다.")
        
        return {
            "daily": {},
            "monthly": {},
            "total": {
                "cost": 0.0,
                "requests": 0
            }
        }
    
    def _save_data(self):
        """사용량 데이터 저장"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"사용량 파일 저장 실패: {e}", exc_info=True)
    
    def _calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        images: Optional[int] = None
    ) -> float:
        """
        API 비용 계산
        
        Args:
            provider: API 제공자 ("openai", "claude", "unsplash" 등)
            model: 모델 이름
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            images: 이미지 수 (DALL-E의 경우)
        
        Returns:
            계산된 비용 (USD)
        """
        if provider.lower() in FREE_APIS:
            return 0.0
        
        cost_key = model.lower()
        if cost_key not in COST_PER_MILLION_TOKENS:
            logger.warning(f"알 수 없는 모델: {model}, 비용 계산 불가")
            return 0.0
        
        cost_info = COST_PER_MILLION_TOKENS[cost_key]
        
        # DALL-E 이미지 비용
        if "image" in cost_info and images:
            return cost_info["image"] * images
        
        # 텍스트 생성 비용
        total_cost = 0.0
        if input_tokens:
            total_cost += (input_tokens / 1_000_000) * cost_info.get("input", 0)
        if output_tokens:
            total_cost += (output_tokens / 1_000_000) * cost_info.get("output", 0)
        
        return total_cost
    
    def track_text_generation(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ):
        """
        텍스트 생성 사용량 추적
        
        Args:
            provider: API 제공자
            model: 모델 이름
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
        """
        cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
        
        today = date.today().isoformat()
        month = today[:7]  # YYYY-MM
        
        # 일별 통계
        if today not in self.data["daily"]:
            self.data["daily"][today] = {
                "cost": 0.0,
                "requests": 0,
                "providers": {}
            }
        
        self.data["daily"][today]["cost"] += cost
        self.data["daily"][today]["requests"] += 1
        
        if provider not in self.data["daily"][today]["providers"]:
            self.data["daily"][today]["providers"][provider] = {
                "cost": 0.0,
                "requests": 0,
                "models": {}
            }
        
        self.data["daily"][today]["providers"][provider]["cost"] += cost
        self.data["daily"][today]["providers"][provider]["requests"] += 1
        
        if model not in self.data["daily"][today]["providers"][provider]["models"]:
            self.data["daily"][today]["providers"][provider]["models"][model] = {
                "cost": 0.0,
                "requests": 0,
                "tokens": {"input": 0, "output": 0}
            }
        
        self.data["daily"][today]["providers"][provider]["models"][model]["cost"] += cost
        self.data["daily"][today]["providers"][provider]["models"][model]["requests"] += 1
        self.data["daily"][today]["providers"][provider]["models"][model]["tokens"]["input"] += input_tokens
        self.data["daily"][today]["providers"][provider]["models"][model]["tokens"]["output"] += output_tokens
        
        # 월별 통계
        if month not in self.data["monthly"]:
            self.data["monthly"][month] = {
                "cost": 0.0,
                "requests": 0
            }
        
        self.data["monthly"][month]["cost"] += cost
        self.data["monthly"][month]["requests"] += 1
        
        # 전체 통계
        self.data["total"]["cost"] += cost
        self.data["total"]["requests"] += 1
        
        self._save_data()
        
        logger.debug(f"사용량 추적: {provider}/{model} - ${cost:.4f} ({input_tokens + output_tokens} tokens)")
    
    def track_image_generation(
        self,
        provider: str,
        model: str,
        images: int = 1
    ):
        """
        이미지 생성 사용량 추적
        
        Args:
            provider: API 제공자
            model: 모델 이름
            images: 생성된 이미지 수
        """
        cost = self._calculate_cost(provider, model, images=images)
        
        today = date.today().isoformat()
        month = today[:7]
        
        # 일별 통계
        if today not in self.data["daily"]:
            self.data["daily"][today] = {
                "cost": 0.0,
                "requests": 0,
                "providers": {}
            }
        
        self.data["daily"][today]["cost"] += cost
        self.data["daily"][today]["requests"] += 1
        
        # 월별 통계
        if month not in self.data["monthly"]:
            self.data["monthly"][month] = {
                "cost": 0.0,
                "requests": 0
            }
        
        self.data["monthly"][month]["cost"] += cost
        self.data["monthly"][month]["requests"] += 1
        
        # 전체 통계
        self.data["total"]["cost"] += cost
        self.data["total"]["requests"] += 1
        
        self._save_data()
        
        logger.debug(f"이미지 생성 추적: {provider}/{model} - ${cost:.4f} ({images} images)")
    
    def get_daily_stats(self, date_str: Optional[str] = None) -> Dict:
        """
        일별 통계 조회
        
        Args:
            date_str: 날짜 문자열 (YYYY-MM-DD), None이면 오늘
        
        Returns:
            일별 통계 딕셔너리
        """
        if date_str is None:
            date_str = date.today().isoformat()
        
        return self.data["daily"].get(date_str, {
            "cost": 0.0,
            "requests": 0,
            "providers": {}
        })
    
    def get_monthly_stats(self, month_str: Optional[str] = None) -> Dict:
        """
        월별 통계 조회
        
        Args:
            month_str: 월 문자열 (YYYY-MM), None이면 이번 달
        
        Returns:
            월별 통계 딕셔너리
        """
        if month_str is None:
            month_str = date.today().strftime("%Y-%m")
        
        return self.data["monthly"].get(month_str, {
            "cost": 0.0,
            "requests": 0
        })
    
    def get_total_stats(self) -> Dict:
        """전체 통계 조회"""
        return self.data["total"].copy()

