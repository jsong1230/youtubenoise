"""
오디오 자동 생성 스크립트
화이트노이즈/자연음/환경음을 코드로 자동 생성
"""
import os
import sys
import json
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import numpy as np
from pydub import AudioSegment
from pydub.generators import WhiteNoise, Sine

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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


def load_config() -> dict:
    """config.json 파일 로드"""
    config_path = project_root / "config" / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"설정 파일 파싱 오류: {e}")
        raise


def generate_white_noise(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """화이트 노이즈 생성"""
    logger.info(f"화이트 노이즈 생성 중... (길이: {duration_sec}초)")
    noise = WhiteNoise().to_audio_segment(duration=duration_sec * 1000)
    return noise


def generate_brown_noise(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """브라운 노이즈 생성"""
    logger.info(f"브라운 노이즈 생성 중... (길이: {duration_sec}초)")
    # 브라운 노이즈는 1/f^2 스펙트럼을 가짐
    samples = int(duration_sec * sample_rate)
    # 간단한 구현: 적분된 화이트 노이즈
    white = np.random.randn(samples).astype(np.float32)
    brown = np.cumsum(white)
    brown = brown / np.max(np.abs(brown))  # 정규화
    
    # AudioSegment로 변환
    audio_array = (brown * 32767).astype(np.int16)
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    return audio_segment


def generate_pink_noise(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """핑크 노이즈 생성 (1/f 노이즈)"""
    logger.info(f"핑크 노이즈 생성 중... (길이: {duration_sec}초)")
    samples = int(duration_sec * sample_rate)
    
    # 간단한 핑크 노이즈 생성 (Voss-McCartney 알고리즘의 단순화 버전)
    white = np.random.randn(samples).astype(np.float32)
    # 주파수 도메인에서 필터링
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(len(white), 1/sample_rate)
    # 1/f 필터 적용
    filter_ = 1.0 / np.sqrt(freqs + 1e-10)
    filter_[0] = 0  # DC 제거
    fft_filtered = fft * filter_
    pink = np.fft.irfft(fft_filtered, n=len(white))
    pink = pink / np.max(np.abs(pink))  # 정규화
    
    audio_array = (pink * 32767).astype(np.int16)
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    return audio_segment


def generate_rain(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """빗소리 생성"""
    logger.info(f"빗소리 생성 중... (길이: {duration_sec}초)")
    # 빗소리는 화이트 노이즈 + 저주파 필터링 + 간헐적 패턴
    samples = int(duration_sec * sample_rate)
    
    # 기본 화이트 노이즈
    white = np.random.randn(samples).astype(np.float32)
    
    # 저주파 필터링 (고주파 강조)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(len(white), 1/sample_rate)
    # 고주파 강조 필터
    filter_ = np.sqrt(freqs / (freqs.max() + 1e-10))
    filter_[0] = 0
    fft_filtered = fft * filter_
    rain_base = np.fft.irfft(fft_filtered, n=len(white))
    
    # 간헐적 강도 변화 (빗방울 떨어지는 느낌)
    envelope = np.ones(samples)
    for i in range(0, samples, sample_rate // 2):  # 0.5초마다
        if random.random() > 0.3:
            start = i
            end = min(i + sample_rate // 10, samples)  # 0.1초 펄스
            envelope[start:end] = 1.5
    
    rain = rain_base * envelope
    rain = rain / np.max(np.abs(rain)) * 0.7  # 정규화 및 볼륨 조절
    
    audio_array = (rain * 32767).astype(np.int16)
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    return audio_segment


def generate_ocean(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """파도 소리 생성"""
    logger.info(f"파도 소리 생성 중... (길이: {duration_sec}초)")
    samples = int(duration_sec * sample_rate)
    
    # 여러 주파수의 사인파 조합 + 노이즈
    t = np.linspace(0, duration_sec, samples)
    
    # 저주파 파도 패턴
    wave_freq = 0.1  # 0.1 Hz (10초 주기)
    wave = np.sin(2 * np.pi * wave_freq * t)
    
    # 중간 주파수 파도
    wave2 = np.sin(2 * np.pi * 0.3 * t)
    
    # 화이트 노이즈 (파도 부서지는 소리)
    noise = np.random.randn(samples).astype(np.float32) * 0.3
    
    # 고주파 필터링된 노이즈 (거품 소리)
    fft_noise = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(len(noise), 1/sample_rate)
    highpass = freqs > 500  # 500Hz 이상만
    fft_noise[~highpass] *= 0.1
    filtered_noise = np.fft.irfft(fft_noise, n=len(noise))
    
    # 조합
    ocean = (wave * 0.4 + wave2 * 0.2 + filtered_noise * 0.4)
    ocean = ocean / np.max(np.abs(ocean)) * 0.8
    
    audio_array = (ocean * 32767).astype(np.int16)
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    return audio_segment


def generate_fireplace(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """벽난로 소리 생성"""
    logger.info(f"벽난로 소리 생성 중... (길이: {duration_sec}초)")
    samples = int(duration_sec * sample_rate)
    
    # 화이트 노이즈 기반
    white = np.random.randn(samples).astype(np.float32)
    
    # 저주파 필터링 (따뜻한 느낌)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(len(white), 1/sample_rate)
    # 저주파 강조
    filter_ = 1.0 / (1.0 + freqs / 1000.0)
    filter_[0] = 0
    fft_filtered = fft * filter_
    base = np.fft.irfft(fft_filtered, n=len(white))
    
    # 간헐적 크랙 소리 (불꽃 튀는 소리)
    envelope = np.ones(samples)
    for i in range(0, samples, sample_rate // 3):  # 0.33초마다
        if random.random() > 0.5:
            start = i
            end = min(i + sample_rate // 20, samples)  # 0.05초 펄스
            envelope[start:end] = 2.0
    
    fireplace = base * envelope
    fireplace = fireplace / np.max(np.abs(fireplace)) * 0.75
    
    audio_array = (fireplace * 32767).astype(np.int16)
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    return audio_segment


def generate_noise(noise_type: str, duration_sec: int) -> Path:
    """
    노이즈 생성 함수
    
    Args:
        noise_type: 노이즈 타입 (white_noise, brown_noise, pink_noise, rain, ocean, fireplace)
        duration_sec: 길이 (초)
    
    Returns:
        생성된 오디오 파일 경로
    """
    try:
        # 노이즈 타입에 따라 생성
        generators = {
            "white_noise": generate_white_noise,
            "brown_noise": generate_brown_noise,
            "pink_noise": generate_pink_noise,
            "rain": generate_rain,
            "ocean": generate_ocean,
            "fireplace": generate_fireplace,
        }
        
        if noise_type not in generators:
            raise ValueError(f"지원하지 않는 노이즈 타입: {noise_type}")
        
        # 오디오 생성
        audio_segment = generators[noise_type](duration_sec)
        
        # 스테레오로 변환 (모노 -> 스테레오)
        if audio_segment.channels == 1:
            audio_segment = audio_segment.set_channels(2)
        
        # 출력 디렉토리 확인
        output_dir = project_root / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        date_str = datetime.now().strftime("%Y-%m-%d")
        duration_hours = duration_sec // 3600
        filename = f"{date_str}_{noise_type}_{duration_hours}h.mp3"
        output_path = output_dir / filename
        
        # MP3로 저장
        audio_segment.export(str(output_path), format="mp3", bitrate="192k")
        
        logger.info(f"오디오 파일 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"오디오 생성 중 오류 발생: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        # 설정 로드
        config = load_config()
        audio_length_sec = config.get("audio_length_sec", 14400)
        noise_types = config.get("noise_types", ["white_noise"])
        
        # 랜덤으로 노이즈 타입 선택
        noise_type = random.choice(noise_types)
        logger.info(f"선택된 노이즈 타입: {noise_type}")
        
        # 오디오 생성
        output_path = generate_noise(noise_type, audio_length_sec)
        logger.info(f"생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

