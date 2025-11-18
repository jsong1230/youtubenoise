"""
롱폼 BGM 자동 생성 스크립트
저작권 문제 없는 오리지널 음악 생성 (알고리즘 기반 또는 Public Domain 음악 사용)
"""
import os
import sys
import json
import random
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine, Triangle, Sawtooth, WhiteNoise
from dotenv import load_dotenv
from scripts.public_domain_catalog import (
    build_public_domain_catalog,
    filter_tracks_by_category,
)

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드
load_dotenv(project_root / ".env")

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


def load_bgm_presets() -> dict:
    """BGM 프리셋 설정 파일 로드"""
    presets_path = project_root / "config" / "bgm_presets.yaml"
    try:
        with open(presets_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"BGM 프리셋 파일을 찾을 수 없습니다: {presets_path}")
        raise
    except Exception as e:
        logger.error(f"BGM 프리셋 파일 로드 오류: {e}")
        raise


def midi_to_freq(midi_note: int) -> float:
    """MIDI 노트 번호를 주파수로 변환"""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def generate_waveform(waveform_type: str, freq: float, duration_ms: int, sample_rate: int = 44100) -> np.ndarray:
    """파형 생성"""
    samples = int(duration_ms * sample_rate / 1000.0)
    t = np.linspace(0, duration_ms / 1000.0, samples)
    
    if waveform_type == "sine":
        return np.sin(2 * np.pi * freq * t)
    elif waveform_type == "triangle":
        return 2.0 / np.pi * np.arcsin(np.sin(2 * np.pi * freq * t))
    elif waveform_type == "sawtooth":
        return 2.0 * (t * freq - np.floor(t * freq + 0.5))
    elif waveform_type == "noise":
        return np.random.randn(samples).astype(np.float32)
    else:
        return np.sin(2 * np.pi * freq * t)  # 기본값: 사인파


def apply_envelope(signal: np.ndarray, attack: float, decay: float, sustain: float, release: float, sample_rate: int = 44100) -> np.ndarray:
    """ADSR 엔벨로프 적용"""
    total_samples = len(signal)
    attack_samples = int(attack * sample_rate)
    decay_samples = int(decay * sample_rate)
    release_samples = int(release * sample_rate)
    
    # release가 전체 길이를 초과하지 않도록 조정
    if attack_samples + decay_samples + release_samples > total_samples:
        # 사용 가능한 샘플 수에 비례하여 조정
        available_samples = total_samples - attack_samples - decay_samples
        if available_samples > 0:
            release_samples = min(release_samples, available_samples)
        else:
            # 너무 짧은 경우 attack과 decay만 사용
            release_samples = 0
            if attack_samples + decay_samples > total_samples:
                decay_samples = max(0, total_samples - attack_samples)
                if attack_samples > total_samples:
                    attack_samples = total_samples
    
    sustain_samples = total_samples - attack_samples - decay_samples - release_samples
    
    envelope = np.ones(total_samples)
    
    # Attack
    if attack_samples > 0 and attack_samples <= total_samples:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # Decay
    if decay_samples > 0:
        start = attack_samples
        end = min(start + decay_samples, total_samples)
        if end > start:
            envelope[start:end] = np.linspace(1, sustain, end - start)
    
    # Sustain
    if sustain_samples > 0:
        start = attack_samples + decay_samples
        end = min(start + sustain_samples, total_samples)
        if end > start:
            envelope[start:end] = sustain
    
    # Release
    if release_samples > 0:
        start = max(0, total_samples - release_samples)
        if start < total_samples:
            envelope[start:] = np.linspace(sustain, 0, total_samples - start)
    
    return signal * envelope


def generate_chord_progression(style: str, key: str, num_chords: int = 4) -> List[List[int]]:
    """코드 진행 생성 (저작권 문제 없는 오리지널 진행)"""
    # 키에 따른 스케일 정의
    key_to_scale = {
        "C_major": [60, 62, 64, 65, 67, 69, 71],  # C, D, E, F, G, A, B
        "G_major": [67, 69, 71, 72, 74, 76, 78],  # G, A, B, C, D, E, F#
        "F_major": [65, 67, 69, 70, 72, 74, 76],  # F, G, A, Bb, C, D, E
        "D_major": [62, 64, 66, 67, 69, 71, 73],  # D, E, F#, G, A, B, C#
        "A_major": [69, 71, 73, 74, 76, 78, 80],  # A, B, C#, D, E, F#, G#
    }
    
    scale = key_to_scale.get(key, key_to_scale["C_major"])
    
    # 스타일별 코드 진행 패턴 (오리지널, 기존 곡 복제 아님)
    if style == "jazz_christmas" or style == "jazz_standard":
        # 재즈 스타일: ii-V-I 진행 변형
        progressions = [
            [scale[1], scale[4], scale[0], scale[3]],  # Dm-G-C-F
            [scale[0], scale[3], scale[6], scale[2]],  # C-F-B-E
            [scale[2], scale[5], scale[1], scale[4]],  # Em-Am-Dm-G
        ]
    elif style == "classical_christmas" or style == "classical_progression":
        # 클래식 스타일: I-vi-IV-V 변형
        progressions = [
            [scale[0], scale[5], scale[3], scale[4]],  # C-Am-F-G
            [scale[0], scale[2], scale[4], scale[6]],  # C-Em-G-B
            [scale[0], scale[3], scale[5], scale[1]],  # C-F-Am-Dm
        ]
    elif style == "ambient_drone":
        # 앰비언트: 드론 스타일
        progressions = [
            [scale[0], scale[0], scale[0], scale[0]],  # 단일 코드 유지
        ]
    else:
        # 기본 진행
        progressions = [
            [scale[0], scale[3], scale[4], scale[0]],  # C-F-G-C
        ]
    
    # 랜덤 선택
    base_progression = random.choice(progressions)
    
    # 코드를 3음화음으로 확장
    chords = []
    for root in base_progression:
        chord = [root, root + 4, root + 7]  # 메이저 트라이어드
        chords.append(chord)
    
    return chords


def generate_piano_part(chord_progression: List[List[int]], duration_sec: int, tempo_bpm: int, 
                       volume: float = 0.6, style: str = "gentle_chord_progression") -> np.ndarray:
    """피아노 파트 생성"""
    sample_rate = 44100
    samples = int(duration_sec * sample_rate)
    output = np.zeros(samples, dtype=np.float32)
    
    beat_duration = 60.0 / tempo_bpm
    chord_duration = beat_duration * 4  # 4박자당 코드 변경
    
    t = np.linspace(0, duration_sec, samples)
    
    for i, chord in enumerate(chord_progression * (int(duration_sec / chord_duration) + 1)):
        start_time = i * chord_duration
        if start_time >= duration_sec:
            break
        
        start_sample = int(start_time * sample_rate)
        end_sample = min(int((start_time + chord_duration) * sample_rate), samples)
        chord_samples = end_sample - start_sample
        
        # 각 코드 음을 아르페지오로
        if style == "classical_arpeggio":
            # 클래식 아르페지오
            for j, note in enumerate(chord):
                note_freq = midi_to_freq(note)
                note_wave = generate_waveform("sine", note_freq, chord_duration * 1000, sample_rate)
                note_wave = apply_envelope(note_wave, 0.1, 0.3, 0.5, 0.5, sample_rate)
                # 각 음을 약간씩 지연시켜 아르페지오 효과
                delay = int(j * 0.05 * sample_rate)
                if delay < chord_samples:
                    output[start_sample + delay:end_sample] += note_wave[:chord_samples - delay] * volume * 0.3
        elif style == "jazz_chords":
            # 재즈 코드: 동시에 연주
            for note in chord:
                note_freq = midi_to_freq(note)
                note_wave = generate_waveform("sine", note_freq, chord_duration * 1000, sample_rate)
                note_wave = apply_envelope(note_wave, 0.1, 0.2, 0.6, 0.3, sample_rate)
                output[start_sample:end_sample] += note_wave[:chord_samples] * volume * 0.25
        else:
            # 기본: 부드러운 코드 진행
            for note in chord:
                note_freq = midi_to_freq(note)
                note_wave = generate_waveform("sine", note_freq, chord_duration * 1000, sample_rate)
                note_wave = apply_envelope(note_wave, 0.1, 0.3, 0.5, 0.5, sample_rate)
                output[start_sample:end_sample] += note_wave[:chord_samples] * volume * 0.3
    
    return output


def generate_strings_part(chord_progression: List[List[int]], duration_sec: int, tempo_bpm: int,
                           volume: float = 0.3, style: str = "warm_pad") -> np.ndarray:
    """스트링 파트 생성"""
    sample_rate = 44100
    samples = int(duration_sec * sample_rate)
    output = np.zeros(samples, dtype=np.float32)
    
    beat_duration = 60.0 / tempo_bpm
    chord_duration = beat_duration * 8  # 더 긴 코드 유지
    
    for i, chord in enumerate(chord_progression * (int(duration_sec / chord_duration) + 1)):
        start_time = i * chord_duration
        if start_time >= duration_sec:
            break
        
        start_sample = int(start_time * sample_rate)
        end_sample = min(int((start_time + chord_duration) * sample_rate), samples)
        chord_samples = end_sample - start_sample
        
        # 패드 스타일: 긴 서스테인
        for note in chord:
            note_freq = midi_to_freq(note)
            note_wave = generate_waveform("sine", note_freq, chord_duration * 1000, sample_rate)
            note_wave = apply_envelope(note_wave, 1.0, 0.5, 0.7, 2.0, sample_rate)
            output[start_sample:end_sample] += note_wave[:chord_samples] * volume * 0.2
    
    return output


def generate_bells_part(chord_progression: List[List[int]], duration_sec: int, tempo_bpm: int,
                       volume: float = 0.2, style: str = "soft_chimes") -> np.ndarray:
    """벨 파트 생성 (크리스마스 분위기)"""
    sample_rate = 44100
    samples = int(duration_sec * sample_rate)
    output = np.zeros(samples, dtype=np.float32)
    
    beat_duration = 60.0 / tempo_bpm
    # 간헐적으로 벨 소리
    bell_interval = beat_duration * 8  # 8박자마다
    
    t = np.linspace(0, duration_sec, samples)
    
    for i in range(int(duration_sec / bell_interval)):
        if random.random() > 0.3:  # 70% 확률로 벨 소리
            start_time = i * bell_interval
            start_sample = int(start_time * sample_rate)
            
            # 랜덤 코드 음 선택
            chord = random.choice(chord_progression)
            note = random.choice(chord)
            note_freq = midi_to_freq(note + 12)  # 옥타브 위
            
            # 짧은 벨 소리
            bell_duration = 0.5
            bell_samples = int(bell_duration * sample_rate)
            end_sample = min(start_sample + bell_samples, samples)
            
            bell_wave = generate_waveform("sine", note_freq, bell_duration * 1000, sample_rate)
            bell_wave = apply_envelope(bell_wave, 0.05, 0.2, 0.3, 1.5, sample_rate)
            
            if end_sample - start_sample > 0:
                output[start_sample:end_sample] += bell_wave[:end_sample - start_sample] * volume
    
    return output


def combine_multiple_audio_files(audio_files: List[Path], duration_minutes: int) -> Optional[Path]:
    """
    여러 오디오 파일을 조합하여 하나의 긴 음악 생성
    
    Args:
        audio_files: 오디오 파일 경로 리스트
        duration_minutes: 원하는 길이 (분)
    
    Returns:
        조합된 오디오 파일 경로
    """
    try:
        if not audio_files:
            return None
        
        logger.info(f"{len(audio_files)}개의 음악 파일을 조합 중...")
        
        duration_sec = duration_minutes * 60 * 1000  # 밀리초
        combined_audio = AudioSegment.empty()
        
        # 파일들을 순차적으로 조합
        file_index = 0
        while len(combined_audio) < duration_sec:
            audio_file = audio_files[file_index % len(audio_files)]
            logger.info(f"파일 추가 중: {audio_file.name}")
            
            try:
                segment = AudioSegment.from_file(str(audio_file))
                combined_audio += segment
                file_index += 1
            except Exception as e:
                logger.warning(f"파일 로드 실패 ({audio_file}): {e}, 건너뜁니다")
                file_index += 1
                if file_index >= len(audio_files):
                    break
                continue
        
        # 원하는 길이로 자르기
        if len(combined_audio) > duration_sec:
            combined_audio = combined_audio[:duration_sec]
        
        # 출력 경로
        output_dir = project_root / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = output_dir / f"{date_str}_combined_{duration_minutes}min.wav"
        
        # 저장
        combined_audio.export(str(output_path), format="wav")
        logger.info(f"음악 파일 조합 완료: {output_path} ({len(combined_audio)/1000:.1f}초)")
        
        return output_path
        
    except Exception as e:
        logger.error(f"음악 파일 조합 실패: {e}")
        return None


def load_external_audio(audio_path: Path, duration_minutes: int) -> Optional[Path]:
    """
    외부 Public Domain 음악 파일 로드 및 길이 조정
    
    Args:
        audio_path: 외부 오디오 파일 경로
        duration_minutes: 원하는 길이 (분)
    
    Returns:
        조정된 오디오 파일 경로 (None이면 실패)
    """
    try:
        if not audio_path.exists():
            logger.warning(f"외부 오디오 파일을 찾을 수 없습니다: {audio_path}")
            return None
        
        logger.info(f"외부 Public Domain 음악 파일 로드: {audio_path}")
        
        # 오디오 로드
        audio_segment = AudioSegment.from_file(str(audio_path))
        duration_sec = duration_minutes * 60 * 1000  # 밀리초
        
        # 길이 조정 (루프 또는 자르기)
        if len(audio_segment) < duration_sec:
            # 루프하여 길이 맞추기
            loops_needed = int(duration_sec / len(audio_segment)) + 1
            audio_segment = audio_segment * loops_needed
        
        # 원하는 길이로 자르기
        audio_segment = audio_segment[:duration_sec]
        
        # 출력 경로
        output_dir = project_root / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = output_dir / f"{date_str}_external_{duration_minutes}min.wav"
        
        # 저장
        audio_segment.export(str(output_path), format="wav")
        logger.info(f"외부 오디오 파일 처리 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"외부 오디오 파일 로드 실패: {e}")
        return None


def _select_public_domain_audio(
    preset: dict,
    preset_name: str,
    duration_minutes: int,
) -> Optional[Path]:
    """프리셋 설정에 따라 Public Domain 음악을 선택 또는 조합"""
    public_domain_dir = project_root / "audio" / "public_domain"
    public_domain_dir.mkdir(parents=True, exist_ok=True)

    catalog = build_public_domain_catalog()
    all_tracks = catalog.get("tracks", [])

    include_categories: List[str] = []
    exclude_categories: List[str] = []
    target_subdir = preset.get("public_domain_subdir")

    category_config = preset.get("public_domain_categories")
    if isinstance(category_config, dict):
        include_categories = list(category_config.get("include") or [])
        exclude_categories.extend(category_config.get("exclude") or [])
    elif isinstance(category_config, (list, tuple, set)):
        include_categories = list(category_config)
    elif isinstance(category_config, str):
        include_categories = [category_config]

    preset_exclude = preset.get("public_domain_exclude_categories")
    if isinstance(preset_exclude, (list, tuple, set)):
        exclude_categories.extend(list(preset_exclude))
    elif isinstance(preset_exclude, str):
        exclude_categories.append(preset_exclude)

    selected_metadata = all_tracks
    if include_categories or exclude_categories:
        selected_metadata = filter_tracks_by_category(
            catalog,
            include=include_categories or None,
            exclude=exclude_categories or None,
        )
        if include_categories and not selected_metadata:
            logger.warning(
                f"필터와 일치하는 Public Domain 음악을 찾지 못했습니다 (필터: {include_categories}). 전체 라이브러리를 사용합니다."
            )
            selected_metadata = all_tracks

    music_files: List[Path] = []
    for track in selected_metadata:
        track_path = project_root / track["path"]
        if target_subdir:
            try:
                track_path.relative_to(public_domain_dir / target_subdir)
            except ValueError:
                continue
        if track_path.exists():
            music_files.append(track_path)
        else:
            logger.debug(f"분류된 파일을 찾을 수 없습니다: {track['path']}")

    if not music_files:
        return None

    logger.info(f"Public Domain 음악 파일 {len(music_files)}개 발견")

    combine_mode = preset.get("combine_mode", "combine")
    if len(music_files) > 1 and combine_mode == "combine":
        logger.info(f"{len(music_files)}개 파일을 조합하여 {duration_minutes}분 길이로 생성합니다.")
        return combine_multiple_audio_files(music_files, duration_minutes)

    selected_file = random.choice(music_files)
    logger.info(f"Public Domain 파일 사용: {selected_file.name}")
    return load_external_audio(selected_file, duration_minutes)


def generate_bgm(preset_name: str, duration_minutes: int) -> Path:
    """
    BGM 생성 함수
    
    Args:
        preset_name: 프리셋 이름
        duration_minutes: 길이 (분)
    
    Returns:
        생성된 오디오 파일 경로
    """
    try:
        # 프리셋 로드
        presets_data = load_bgm_presets()
        presets = presets_data.get("presets", {})
        instrument_configs = presets_data.get("instruments", {})
        
        if preset_name not in presets:
            raise ValueError(f"프리셋을 찾을 수 없습니다: {preset_name}")
        
        preset = presets[preset_name]
        logger.info(f"BGM 생성 시작: {preset['name']} ({duration_minutes}분)")
        
        # Public Domain 외부 음악 파일 사용 (우선순위 1)
        use_external = preset.get("use_external_audio", False)
        external_path = preset.get("external_audio_path")
        force_public_domain_only = preset.get("public_domain_only", False)

        use_public_domain_library = (
            not use_external
            and (
                bool(preset.get("public_domain_categories"))
                or preset.get("use_public_domain_library", False)
                or "christmas" in preset_name.lower()
            )
        )

        if use_public_domain_library:
            result = _select_public_domain_audio(preset, preset_name, duration_minutes)
            if result:
                return result

            if "christmas" in preset_name.lower():
                logger.info("Public Domain 음악 파일이 없습니다. 자동 다운로드 시도 중...")
                try:
                    from scripts.download_public_domain_music import get_public_domain_christmas_music
                    downloaded_file = get_public_domain_christmas_music()
                    if downloaded_file:
                        logger.info(f"Public Domain 음악 다운로드 완료: {downloaded_file}")
                        result = load_external_audio(downloaded_file, duration_minutes)
                        if result:
                            return result
                except Exception as e:
                    logger.warning(f"자동 다운로드 실패: {e}")
                    logger.info("알고리즘 생성으로 대체합니다.")

            if force_public_domain_only:
                raise ValueError("Public Domain 음악을 찾지 못해 작업을 중단합니다.")
        
        # 명시적으로 설정된 외부 음악 파일 사용
        if use_external and external_path:
            external_audio_path = project_root / external_path
            result = load_external_audio(external_audio_path, duration_minutes)
            if result:
                return result
            else:
                logger.warning("외부 오디오 로드 실패, 알고리즘 생성으로 대체합니다.")
        
        duration_sec = duration_minutes * 60
        tempo_bpm = preset.get("tempo_bpm", 80)
        key = preset.get("key", "C_major")
        style = preset.get("style", "jazz")
        
        # 스타일 정보 로드
        styles_data = presets_data.get("styles", {})
        style_info = styles_data.get(style, {})
        chord_style = style_info.get("chord_progression", "jazz_standard")
        
        # 코드 진행 생성
        chord_progression = generate_chord_progression(chord_style, key, num_chords=4)
        logger.info(f"코드 진행 생성 완료: {len(chord_progression)}개 코드")
        
        # 각 악기 파트 생성
        sample_rate = 44100
        samples = int(duration_sec * sample_rate)
        final_output = np.zeros(samples, dtype=np.float32)
        
        instruments = preset.get("instruments", [])
        for inst_config in instruments:
            inst_type = inst_config["type"]
            inst_volume = inst_config.get("volume", 0.5)
            inst_style = inst_config.get("style", "gentle")
            
            logger.info(f"{inst_type} 파트 생성 중...")
            
            if inst_type == "piano":
                part = generate_piano_part(chord_progression, duration_sec, tempo_bpm, inst_volume, inst_style)
            elif inst_type == "strings":
                part = generate_strings_part(chord_progression, duration_sec, tempo_bpm, inst_volume, inst_style)
            elif inst_type == "bells":
                part = generate_bells_part(chord_progression, duration_sec, tempo_bpm, inst_volume, inst_style)
            else:
                logger.warning(f"지원하지 않는 악기 타입: {inst_type}, 건너뜁니다")
                continue
            
            final_output += part
        
        # 정규화
        max_val = np.max(np.abs(final_output))
        if max_val > 0:
            final_output = final_output / max_val * 0.8  # 80% 볼륨
        
        # 페이드 인/아웃
        fade_samples = int(3.0 * sample_rate)  # 3초
        if len(final_output) > fade_samples * 2:
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            final_output[:fade_samples] *= fade_in
            final_output[-fade_samples:] *= fade_out
        
        # 스테레오로 변환
        stereo_output = np.zeros((samples, 2), dtype=np.float32)
        stereo_output[:, 0] = final_output
        stereo_output[:, 1] = final_output
        
        # AudioSegment로 변환
        audio_array = (stereo_output * 32767).astype(np.int16)
        audio_segment = AudioSegment(
            audio_array.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=2
        )
        
        # 출력 디렉토리 확인
        output_dir = project_root / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{preset_name}_{duration_minutes}min.wav"
        output_path = output_dir / filename
        
        # WAV로 저장 (ffmpeg 없이도 가능)
        audio_segment.export(str(output_path), format="wav")
        
        logger.info(f"BGM 파일 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"BGM 생성 중 오류 발생: {e}", exc_info=True)
        raise


def main():
    """메인 실행 함수"""
    try:
        if len(sys.argv) < 3:
            print("사용법: python generate_bgm.py <preset_name> <duration_minutes>")
            print("예시: python generate_bgm.py christmas_cafe_3h 180")
            sys.exit(1)
        
        preset_name = sys.argv[1]
        duration_minutes = int(sys.argv[2])
        
        output_path = generate_bgm(preset_name, duration_minutes)
        logger.info(f"생성 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

