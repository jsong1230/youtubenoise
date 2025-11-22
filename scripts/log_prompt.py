"""
프롬프트 로깅 유틸리티
사용자가 Cursor에서 입력한 프롬프트를 머신/IDE 정보와 함께 로깅
"""
import os
import sys
import json
import platform
import socket
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_machine_info() -> Dict[str, str]:
    """머신 정보 수집"""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def get_ide_info() -> Dict[str, str]:
    """IDE 정보 수집"""
    # Cursor 관련 환경변수 확인
    cursor_info = {
        "ide": "Cursor",
        "cursor_version": os.environ.get("CURSOR_VERSION", "unknown"),
    }
    
    # 추가 IDE 정보가 있다면 수집
    if "VSCODE_INJECTION" in os.environ:
        cursor_info["vscode_injection"] = os.environ.get("VSCODE_INJECTION")
    
    return cursor_info


def log_prompt(
    prompt: str,
    context: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Path:
    """
    프롬프트를 로그 파일에 기록
    
    Args:
        prompt: 사용자가 입력한 프롬프트
        context: 추가 컨텍스트 정보 (선택사항)
        metadata: 추가 메타데이터 (선택사항)
    
    Returns:
        로그 파일 경로
    """
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로그 파일 경로 (날짜별로 분리)
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"prompts_{date_str}.jsonl"
    
    # 로그 엔트리 생성
    entry = {
        "timestamp": datetime.now().isoformat(),
        "machine": get_machine_info(),
        "ide": get_ide_info(),
        "prompt": prompt,
    }
    
    if context:
        entry["context"] = context
    
    if metadata:
        entry["metadata"] = metadata
    
    # JSONL 형식으로 추가 (한 줄에 하나의 JSON 객체)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return log_file


def read_prompt_logs(date_str: Optional[str] = None) -> list:
    """
    프롬프트 로그 읽기
    
    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD), None이면 오늘 날짜
    
    Returns:
        로그 엔트리 리스트
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    log_file = project_root / "logs" / f"prompts_{date_str}.jsonl"
    
    if not log_file.exists():
        return []
    
    entries = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return entries


if __name__ == "__main__":
    # 테스트 실행
    import argparse
    
    parser = argparse.ArgumentParser(description="프롬프트 로깅 유틸리티")
    parser.add_argument("--prompt", type=str, help="로깅할 프롬프트")
    parser.add_argument("--read", action="store_true", help="오늘 날짜의 로그 읽기")
    parser.add_argument("--date", type=str, help="읽을 로그의 날짜 (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    if args.prompt:
        log_file = log_prompt(args.prompt)
        print(f"프롬프트가 로그에 기록되었습니다: {log_file}")
    elif args.read:
        entries = read_prompt_logs(args.date)
        print(f"\n총 {len(entries)}개의 로그 엔트리를 찾았습니다:\n")
        for i, entry in enumerate(entries, 1):
            print(f"[{i}] {entry['timestamp']}")
            print(f"    머신: {entry['machine']['hostname']} ({entry['machine']['system']})")
            print(f"    IDE: {entry['ide']['ide']}")
            print(f"    프롬프트: {entry['prompt'][:100]}...")
            print()
    else:
        # 머신 정보 출력
        print("머신 정보:")
        print(json.dumps(get_machine_info(), indent=2, ensure_ascii=False))
        print("\nIDE 정보:")
        print(json.dumps(get_ide_info(), indent=2, ensure_ascii=False))

