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

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE, CONFIG_JSON_FILE, OUTPUT_DIR, PROJECT_ROOT
from scripts.utils import setup_logging, load_json_file

# 로깅 설정
logger = setup_logging()


def load_config() -> dict:
    """config.json 파일 로드"""
    return load_json_file(CONFIG_JSON_FILE)


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


def generate_lofi(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """로파이 힙합 비트 생성"""
    logger.info(f"로파이 힙합 비트 생성 중... (길이: {duration_sec}초)")
    samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, samples)
    
    # 기본 드럼 비트 (킥, 스네어, 하이햇)
    kick_freq = 60  # 저주파 킥
    snare_freq = 200  # 스네어 주파수
    hihat_freq = 8000  # 하이햇 주파수
    
    # 킥 드럼 (매 4박마다)
    beat_length = 60.0 / 85.0  # 85 BPM (로파이의 전형적인 BPM)
    kick_pattern = np.zeros(samples)
    for i in range(int(duration_sec / beat_length)):
        beat_start = int(i * beat_length * sample_rate)
        if i % 4 == 0:  # 매 4박마다 킥
            kick_duration = int(0.1 * sample_rate)
            kick_end = min(beat_start + kick_duration, samples)
            kick_envelope = np.exp(-np.linspace(0, 5, kick_end - beat_start))
            kick_wave = np.sin(2 * np.pi * kick_freq * t[beat_start:kick_end])
            kick_pattern[beat_start:kick_end] = kick_wave * kick_envelope * 0.6
    
    # 스네어 (2, 4박)
    snare_pattern = np.zeros(samples)
    for i in range(int(duration_sec / beat_length)):
        beat_start = int(i * beat_length * sample_rate)
        if i % 4 in [1, 3]:  # 2, 4박
            snare_duration = int(0.05 * sample_rate)
            snare_end = min(beat_start + snare_duration, samples)
            snare_noise = np.random.randn(snare_end - beat_start).astype(np.float32)
            snare_wave = np.sin(2 * np.pi * snare_freq * t[beat_start:snare_end])
            snare_pattern[beat_start:snare_end] = (snare_wave * 0.3 + snare_noise * 0.7) * 0.4
    
    # 하이햇 (매 박마다)
    hihat_pattern = np.zeros(samples)
    for i in range(int(duration_sec / beat_length)):
        beat_start = int(i * beat_length * sample_rate)
        hihat_duration = int(0.02 * sample_rate)
        hihat_end = min(beat_start + hihat_duration, samples)
        hihat_noise = np.random.randn(hihat_end - beat_start).astype(np.float32)
        # 고주파 필터링
        hihat_fft = np.fft.rfft(hihat_noise)
        hihat_freqs = np.fft.rfftfreq(len(hihat_noise), 1/sample_rate)
        highpass = hihat_freqs > 3000
        hihat_fft[~highpass] *= 0.1
        hihat_filtered = np.fft.irfft(hihat_fft, n=len(hihat_noise))
        hihat_pattern[beat_start:hihat_end] = hihat_filtered * 0.2
    
    # 베이스라인 (간단한 멜로디)
    bass_pattern = np.zeros(samples)
    bass_notes = [60, 65, 67, 65]  # C, F, G, F (간단한 코드 진행)
    note_duration = beat_length * 2  # 2박씩
    for i, note in enumerate(bass_notes * (int(duration_sec / (note_duration * len(bass_notes))) + 1)):
        note_start = int(i * note_duration * sample_rate)
        if note_start >= samples:
            break
        note_end = min(note_start + int(note_duration * sample_rate), samples)
        # MIDI 노트를 주파수로 변환
        freq = 440 * (2 ** ((note - 69) / 12))
        bass_wave = np.sin(2 * np.pi * freq * t[note_start:note_end])
        bass_envelope = np.exp(-np.linspace(0, 2, note_end - note_start))
        bass_pattern[note_start:note_end] = bass_wave * bass_envelope * 0.3
    
    # 피아노/멜로디 (고주파, 부드러운 사인파)
    melody_pattern = np.zeros(samples)
    melody_notes = [72, 74, 76, 77, 76, 74, 72, 70]  # 간단한 멜로디
    for i, note in enumerate(melody_notes * (int(duration_sec / (beat_length * 2 * len(melody_notes))) + 1)):
        note_start = int(i * beat_length * 2 * sample_rate)
        if note_start >= samples:
            break
        note_end = min(note_start + int(beat_length * 2 * sample_rate), samples)
        freq = 440 * (2 ** ((note - 69) / 12))
        melody_wave = np.sin(2 * np.pi * freq * t[note_start:note_end])
        melody_envelope = np.exp(-np.linspace(0, 3, note_end - note_start))
        melody_pattern[note_start:note_end] = melody_wave * melody_envelope * 0.15
    
    # 비닐 크랙/노이즈 (로파이 느낌)
    vinyl_noise = np.random.randn(samples).astype(np.float32) * 0.05
    # 저주파 필터링
    vinyl_fft = np.fft.rfft(vinyl_noise)
    vinyl_freqs = np.fft.rfftfreq(len(vinyl_noise), 1/sample_rate)
    lowpass = vinyl_freqs < 500
    vinyl_fft[~lowpass] *= 0.1
    vinyl_filtered = np.fft.irfft(vinyl_fft, n=len(vinyl_noise))
    
    # 모든 요소 결합
    lofi = (kick_pattern + snare_pattern + hihat_pattern + 
            bass_pattern + melody_pattern + vinyl_filtered)
    
    # 정규화 및 볼륨 조절
    lofi = lofi / np.max(np.abs(lofi)) * 0.8
    
    audio_array = (lofi * 32767).astype(np.int16)
    audio_segment = AudioSegment(
        audio_array.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    return audio_segment


def generate_asmr(duration_sec: int, sample_rate: int = 44100) -> AudioSegment:
    """ASMR 소리 생성 (부드러운 속삭임, 타이핑, 물소리 등)"""
    logger.info(f"ASMR 소리 생성 중... (길이: {duration_sec}초)")
    samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, samples)
    
    # 기본: 부드러운 화이트 노이즈 (속삭임 느낌)
    whisper_base = np.random.randn(samples).astype(np.float32)
    # 고주파 필터링 (부드러운 느낌)
    whisper_fft = np.fft.rfft(whisper_base)
    whisper_freqs = np.fft.rfftfreq(len(whisper_base), 1/sample_rate)
    # 200Hz ~ 4000Hz 대역 강조 (인간 목소리 대역)
    bandpass = (whisper_freqs > 200) & (whisper_freqs < 4000)
    whisper_fft[~bandpass] *= 0.1
    whisper_filtered = np.fft.irfft(whisper_fft, n=len(whisper_base))
    
    # 타이핑 소리 (간헐적 클릭)
    typing_pattern = np.zeros(samples)
    for i in range(0, samples, sample_rate // 2):  # 0.5초마다
        if random.random() > 0.4:
            click_start = i
            click_duration = int(0.01 * sample_rate)  # 10ms 클릭
            click_end = min(click_start + click_duration, samples)
            # 고주파 클릭 소리
            click_freq = 3000 + random.randint(-500, 500)
            click_wave = np.sin(2 * np.pi * click_freq * t[click_start:click_end])
            click_envelope = np.exp(-np.linspace(0, 10, click_end - click_start))
            typing_pattern[click_start:click_end] = click_wave * click_envelope * 0.3
    
    # 물소리/물방울 (간헐적)
    water_pattern = np.zeros(samples)
    for i in range(0, samples, sample_rate):  # 1초마다
        if random.random() > 0.6:
            water_start = i
            water_duration = int(0.1 * sample_rate)
            water_end = min(water_start + water_duration, samples)
            # 고주파 물방울 소리
            water_freq = 5000 + random.randint(-1000, 1000)
            water_wave = np.sin(2 * np.pi * water_freq * t[water_start:water_end])
            water_envelope = np.exp(-np.linspace(0, 5, water_end - water_start))
            water_pattern[water_start:water_end] = water_wave * water_envelope * 0.2
    
    # 부드러운 브러싱/스크래칭 소리
    brushing = np.random.randn(samples).astype(np.float32) * 0.1
    # 중주파 대역 강조
    brushing_fft = np.fft.rfft(brushing)
    brushing_freqs = np.fft.rfftfreq(len(brushing), 1/sample_rate)
    midpass = (brushing_freqs > 1000) & (brushing_freqs < 8000)
    brushing_fft[~midpass] *= 0.2
    brushing_filtered = np.fft.irfft(brushing_fft, n=len(brushing))
    
    # 모든 요소 결합
    asmr = (whisper_filtered * 0.5 + typing_pattern + 
            water_pattern + brushing_filtered * 0.3)
    
    # 정규화 및 볼륨 조절 (ASMR은 부드럽게)
    asmr = asmr / np.max(np.abs(asmr)) * 0.6
    
    audio_array = (asmr * 32767).astype(np.int16)
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
        noise_type: 노이즈 타입 (white_noise, brown_noise, pink_noise, rain, ocean, fireplace, lofi, asmr)
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
            "lofi": generate_lofi,
            "asmr": generate_asmr,
        }
        
        if noise_type not in generators:
            raise ValueError(f"지원하지 않는 노이즈 타입: {noise_type}")
        
        # 오디오 생성
        audio_segment = generators[noise_type](duration_sec)
        
        # 스테레오로 변환 (모노 -> 스테레오)
        if audio_segment.channels == 1:
            audio_segment = audio_segment.set_channels(2)
        
        # 출력 디렉토리 확인
        output_dir = OUTPUT_DIR / "audio"
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
        
        # 명령행 인자로 노이즈 타입 지정 가능
        if len(sys.argv) > 1:
            noise_type = sys.argv[1]
            if noise_type not in ["white_noise", "brown_noise", "pink_noise", "rain", "ocean", "fireplace", "lofi", "asmr"]:
                logger.error(f"지원하지 않는 노이즈 타입: {noise_type}")
                logger.info(f"지원하는 타입: white_noise, brown_noise, pink_noise, rain, ocean, fireplace, lofi, asmr")
                sys.exit(1)
        else:
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

