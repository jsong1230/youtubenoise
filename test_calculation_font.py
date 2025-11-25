#!/usr/bin/env python3
"""
더하기 문제 폰트 크기 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.make_brain_training_video import create_calculation_display_image

# 테스트용 색상 스킴
color_scheme = {
    'background': [245, 240, 235],
    'text': [40, 40, 40],
    'highlight': [100, 150, 200]
}

# 출력 디렉토리
output_dir = project_root / "output" / "test_calculation"
output_dir.mkdir(parents=True, exist_ok=True)

# 여러 개의 계산 문제 생성 (다양한 숫자 조합)
test_cases = [
    (5, 3, '+'),
    (12, 8, '+'),
    (25, 17, '+'),
    (100, 50, '+'),
    (7, 4, '-'),
    (20, 11, '-'),
]

print("더하기 문제 샘플 생성 중...")
for i, (num1, num2, op) in enumerate(test_cases, 1):
    output_path = output_dir / f"calc_test_{i}_{num1}_{op}_{num2}.png"
    print(f"생성 중: {output_path.name}")
    
    # font_size를 다르게 설정해도 폰트 크기가 일정해야 함
    test_font_size = 80 + (i * 5)  # 80, 85, 90, 95, 100, 105
    
    create_calculation_display_image(
        num1=num1,
        num2=num2,
        operation=op,
        color_scheme=color_scheme,
        font_size=test_font_size,  # 이 값이 달라도 폰트 크기는 일정해야 함
        output_path=output_path
    )
    
    print(f"  ✓ 완료 (font_size={test_font_size}, 실제 폰트 크기: 300px 고정)")

print(f"\n모든 샘플 생성 완료!")
print(f"출력 디렉토리: {output_dir}")
print(f"\n생성된 파일들:")
for file in sorted(output_dir.glob("calc_test_*.png")):
    print(f"  - {file.name}")

