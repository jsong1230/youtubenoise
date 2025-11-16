"""
메인 CLI 인터페이스
롱폼 BGM 자동 생성 파이프라인 실행
"""
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
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


def run_longform_bgm(preset_name: str, duration_minutes: int, upload: bool = False):
    """
    롱폼 BGM 모드 실행
    
    Args:
        preset_name: BGM 프리셋 이름
        duration_minutes: 길이 (분)
        upload: YouTube 업로드 여부
    """
    try:
        logger.info("=" * 60)
        logger.info("롱폼 BGM 생성 파이프라인 시작")
        logger.info(f"프리셋: {preset_name}, 길이: {duration_minutes}분")
        logger.info("=" * 60)
        
        # 1. BGM 오디오 생성
        logger.info("\n[1/5] BGM 오디오 생성 중...")
        from scripts.generate_bgm import generate_bgm
        audio_path = generate_bgm(preset_name, duration_minutes)
        logger.info(f"오디오 생성 완료: {audio_path}")
        
        # 2. 배경 이미지 생성
        logger.info("\n[2/5] 배경 이미지 생성 중...")
        from scripts.generate_image import generate_background_image_for_bgm
        image_path = generate_background_image_for_bgm(preset_name)
        logger.info(f"이미지 생성 완료: {image_path}")
        
        # 3. 메타데이터 생성
        logger.info("\n[3/5] 메타데이터 생성 중...")
        from scripts.generate_title_description import generate_metadata_for_bgm
        metadata = generate_metadata_for_bgm(preset_name, duration_minutes)
        logger.info(f"메타데이터 생성 완료")
        logger.info(f"제목: {metadata['title']}")
        
        # 4. 영상 생성
        logger.info("\n[4/5] 영상 생성 중...")
        from scripts.make_video import make_video
        video_path = make_video(image_path, audio_path)
        logger.info(f"영상 생성 완료: {video_path}")
        
        # 5. YouTube 업로드 (선택사항)
        video_id = None
        if upload:
            logger.info("\n[5/5] 유튜브 업로드 중...")
            from scripts.upload_youtube import upload_video
            video_id = upload_video(
                video_path=video_path,
                title=metadata["title"],
                description=metadata["description"],
                tags=metadata["tags"],
                thumbnail_path=image_path
            )
            logger.info(f"유튜브 업로드 완료! Video ID: {video_id}")
            logger.info(f"영상 URL: https://www.youtube.com/watch?v={video_id}")
            
            # 히스토리 저장
            try:
                from scripts.scheduler import save_history
                history_data = {
                    "start_time": datetime.now().isoformat(),
                    "preset_name": preset_name,
                    "duration_minutes": duration_minutes,
                    "status": "completed",
                    "files": {
                        "audio": str(audio_path),
                        "image": str(image_path),
                        "video": str(video_path)
                    },
                    "video_id": video_id,
                    "metadata": metadata,
                    "end_time": datetime.now().isoformat()
                }
                save_history(history_data)
                logger.info("히스토리 저장 완료")
            except Exception as e:
                logger.warning(f"히스토리 저장 실패: {e}")
        else:
            logger.info("\n[5/5] 업로드 건너뜀 (--upload 플래그 없음)")
        
        logger.info("\n" + "=" * 60)
        logger.info("파이프라인 완료!")
        logger.info("=" * 60)
        
        return {
            "audio": str(audio_path),
            "image": str(image_path),
            "video": str(video_path),
            "metadata": metadata,
            "video_id": video_id
        }
        
    except Exception as e:
        logger.error(f"파이프라인 실행 중 오류 발생: {e}", exc_info=True)
        raise


def list_presets():
    """사용 가능한 프리셋 목록 출력"""
    try:
        import yaml
        presets_path = project_root / "config" / "bgm_presets.yaml"
        with open(presets_path, 'r', encoding='utf-8') as f:
            presets_data = yaml.safe_load(f)
            presets = presets_data.get("presets", {})
            
            print("\n사용 가능한 BGM 프리셋:")
            print("=" * 60)
            for preset_name, preset_info in presets.items():
                name = preset_info.get("name", preset_name)
                description = preset_info.get("description", "")
                duration = preset_info.get("duration_minutes", "N/A")
                print(f"\n  {preset_name}")
                print(f"    이름: {name}")
                print(f"    설명: {description}")
                print(f"    기본 길이: {duration}분")
            print("\n" + "=" * 60)
            
    except Exception as e:
        logger.error(f"프리셋 목록 로드 실패: {e}")
        print("프리셋 목록을 불러올 수 없습니다.")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="롱폼 BGM 자동 생성 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 프리셋 목록 보기
  python main.py --list-presets
  
  # 크리스마스 카페 BGM 생성 (3시간, 업로드 없음)
  python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180
  
  # 크리스마스 카페 BGM 생성 및 YouTube 업로드
  python main.py --mode longform_bgm --preset christmas_cafe_3h --duration-minutes 180 --upload
  
  # YouTube 채널에서 영상 목록 동기화
  python main.py --sync-youtube
  
  # 모든 영상 통계 업데이트
  python main.py --update-stats
  
  # 영상 통계 리포트 출력
  python main.py --report
        """
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["longform_bgm"],
        default="longform_bgm",
        help="실행 모드 (기본값: longform_bgm)"
    )
    
    parser.add_argument(
        "--preset",
        type=str,
        help="BGM 프리셋 이름"
    )
    
    parser.add_argument(
        "--duration-minutes",
        type=int,
        help="BGM 길이 (분)"
    )
    
    parser.add_argument(
        "--upload",
        action="store_true",
        help="YouTube에 자동 업로드"
    )
    
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="사용 가능한 프리셋 목록 출력"
    )
    
    parser.add_argument(
        "--update-stats",
        action="store_true",
        help="모든 영상의 통계 업데이트"
    )
    
    parser.add_argument(
        "--sync-youtube",
        action="store_true",
        help="YouTube 채널에서 영상 목록 동기화"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="영상 통계 리포트 출력"
    )
    
    args = parser.parse_args()
    
    # 프리셋 목록 출력
    if args.list_presets:
        list_presets()
        return
    
    # YouTube 채널 동기화
    if args.sync_youtube:
        from scripts.update_statistics import sync_from_youtube
        sync_from_youtube()
        return
    
    # 통계 업데이트
    if args.update_stats:
        from scripts.update_statistics import update_all_statistics
        update_all_statistics()
        return
    
    # 리포트 출력
    if args.report:
        from scripts.update_statistics import generate_report
        report = generate_report()
        print(report)
        return
    
    # 필수 인자 확인
    if args.mode == "longform_bgm":
        if not args.preset:
            parser.error("--preset이 필요합니다. --list-presets로 사용 가능한 프리셋을 확인하세요.")
        if not args.duration_minutes:
            parser.error("--duration-minutes가 필요합니다.")
        
        # 파이프라인 실행
        run_longform_bgm(args.preset, args.duration_minutes, args.upload)
    else:
        parser.error(f"지원하지 않는 모드: {args.mode}")


if __name__ == "__main__":
    main()

