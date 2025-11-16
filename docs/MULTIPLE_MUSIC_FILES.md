# 여러 음악 파일 사용 가이드

## 현재 상태

`audio/public_domain/` 폴더에 **20개의 크리스마스 MP3 파일**이 있습니다.

## 사용 방법

### 방법 1: 여러 파일 조합 (기본값)

여러 파일을 순차적으로 조합하여 하나의 긴 음악을 만듭니다.

```bash
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

- 20개 파일이 순차적으로 조합됩니다
- 원하는 길이(예: 180분)까지 반복됩니다

### 방법 2: 하나의 파일만 사용

`config/bgm_presets.yaml`에서 설정:

```yaml
christmas_cafe_3h:
  combine_mode: "single"  # "combine" 또는 "single"
```

이렇게 하면 20개 파일 중 랜덤으로 하나를 선택하여 사용합니다.

## 파일 목록

현재 `audio/public_domain/` 폴더의 파일들:

1. beautiful-christmas-426337.mp3
2. christmas-434436.mp3
3. christmas-background-431808.mp3
4. christmas-background-music-434626.mp3
5. christmas-background-music-436117.mp3
6. christmas-cheer-262617.mp3
7. christmas-holiday-431026.mp3
8. christmas-holiday-background-431002.mp3
9. christmas-holiday-background-436118.mp3
10. christmas-holiday-festive-cheer-snow-427231.mp3
11. christmas-holidays-270797.mp3
12. christmas-jazz-christmas-holiday-347485.mp3
13. christmas-party-time-249613.mp3
14. festive-christmas-tunes-435037.mp3
15. its-christmas-261279.mp3
16. merry-christmas-261280.mp3
17. merry-christmas-christmas-dream-268557.mp3
18. ready-for-christmas-santa-workshop-happiness-435817.mp3
19. soft-christmas-piano-432383.mp3
20. winter-day-christmas-holidays-270802.mp3

## 테스트 결과

✅ **5분 테스트 성공**
- 20개 파일 중 2개 파일이 조합되어 5분 음악 생성
- 영상 생성 완료 (44.31 MB)

## 다음 단계

더 긴 영상을 만들려면:

```bash
# 3시간 영상 생성
python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
```

이렇게 하면 20개 파일이 모두 사용되어 다양한 크리스마스 음악이 조합됩니다!

