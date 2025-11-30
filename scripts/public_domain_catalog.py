"""
Public Domain 음악 라이브러리 분류 도구

- audio/public_domain/ 폴더의 음악 파일을 스캔하여 키워드 기반으로 분류
- 카테고리/무드/소스 태그를 자동으로 부여
- generate_bgm 등에서 원하는 카테고리만 선택할 수 있도록 지원
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set, Iterable, Optional


project_root = Path(__file__).parent.parent
PUBLIC_DOMAIN_DIR = project_root / "audio" / "public_domain"
CATALOG_PATH = PUBLIC_DOMAIN_DIR / "catalog.json"

# 키워드 맵핑
CATEGORY_KEYWORDS: Dict[str, Iterable[str]] = {
    "lofi": ["lofi", "chillhop", "chill", "study", "beats"],
    "piano": ["piano", "keys", "grand", "solo"],
    "bells": ["bell", "bells", "chimes", "glockenspiel"],
    "strings": ["strings", "orchestral", "symphony", "violin", "cello"],
    "choir": ["choir", "vocal", "voices", "sing"],
    "jazz": ["jazz", "swing", "blues"],
    "rock": ["rock", "guitar"],
    "electronic": ["electronic", "edm", "synth", "future"],
    "kids": ["kids", "children", "cartoon"],
    "ambient": ["ambient", "relax", "calm", "soft", "serene", "meditation"],
    "upbeat": ["upbeat", "happy", "fun", "cheerful", "bright", "energetic", "festive"],
    "traditional": ["traditional", "carol", "hymn", "classic"],
    "commercial": ["advertising", "commercial", "promo", "corporate", "branding"],
    "lofi_jazz": ["lofi", "jazz"],
    "celtic": ["celtic", "fiddle", "irish", "scottish", "scotland", "ireland", "cape breton", "newfoundland", "quebecois", "ottawa valley", "acadian", "maritime"],
    "folk": ["folk", "acoustic", "traditional"],
}

MOOD_KEYWORDS: Dict[str, Iterable[str]] = {
    "calm": ["calm", "relax", "soft", "gentle", "peaceful", "cozy", "chill"],
    "bright": ["bright", "happy", "cheerful", "uplifting", "positive"],
    "festive": ["christmas", "holiday", "xmas", "winter", "snow", "santa"],
    "dramatic": ["epic", "dramatic", "majestic"],
    "emotional": ["emotional", "touching", "romantic"],
}

SOURCE_HINTS: Dict[str, Iterable[str]] = {
    "pixabay": ["pixabay", "free for use"],
    "freepd": ["freepd"],
    "musopen": ["musopen"],
}


@dataclass
class TrackMetadata:
    filename: str
    path: str  # project root 상대 경로
    categories: List[str]
    moods: List[str]
    keywords: List[str]
    source: str = "unknown"


def _tokenize(text: str) -> List[str]:
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    return [token for token in tokens if token]


def _extract_keywords(filename: Path) -> List[str]:
    name = filename.stem.replace("Free for use", "")
    parts = re.split(r"[,_\-\(\)\[\]]+", name)
    keywords: Set[str] = set()
    for part in parts:
        keywords.update(_tokenize(part))
    return sorted(keywords)


def _detect_source(keywords: Iterable[str]) -> str:
    keywords_set = set(keywords)
    for source, hints in SOURCE_HINTS.items():
        for hint in hints:
            if " " in hint:
                hint_tokens = [token.strip() for token in hint.split() if token.strip()]
                if hint_tokens and all(token in keywords_set for token in hint_tokens):
                    return source
            elif hint in keywords_set:
                return source
    return "pixabay" if "pixabay" in keywords_set else "unknown"


def _classify(keywords: List[str]) -> tuple[Set[str], Set[str]]:
    keyword_set = set(keywords)
    categories: Set[str] = set()
    moods: Set[str] = set()

    for category, hints in CATEGORY_KEYWORDS.items():
        if any(hint in keyword_set for hint in hints):
            categories.add(category)

    for mood, hints in MOOD_KEYWORDS.items():
        if any(hint in keyword_set for hint in hints):
            moods.add(mood)

    if any(word in keyword_set for word in ["christmas", "xmas", "holiday", "winter", "noel"]):
        categories.add("christmas")
        moods.add("festive")

    if not categories:
        categories.add("general")

    return categories, moods


def analyze_track(file_path: Path) -> Optional[TrackMetadata]:
    if not file_path.is_file():
        return None

    keywords = _extract_keywords(file_path)
    categories, moods = _classify(keywords)
    source = _detect_source(keywords)

    relative_path = file_path.relative_to(project_root)
    return TrackMetadata(
        filename=file_path.name,
        path=str(relative_path),
        categories=sorted(categories),
        moods=sorted(moods),
        keywords=keywords,
        source=source,
    )


def build_public_domain_catalog() -> Dict[str, List[Dict]]:
    PUBLIC_DOMAIN_DIR.mkdir(parents=True, exist_ok=True)
    tracks: List[TrackMetadata] = []

    # 하위 폴더 포함하여 모든 음악 파일 스캔
    for extension in ("*.mp3", "*.wav", "*.flac"):
        for file_path in sorted(PUBLIC_DOMAIN_DIR.rglob(extension)):
            # catalog.json은 제외
            if file_path.name == "catalog.json":
                continue
            metadata = analyze_track(file_path)
            if metadata:
                tracks.append(metadata)

    catalog = {
        "tracks": [asdict(track) for track in tracks],
        "categories": {},
    }

    for track in catalog["tracks"]:
        for category in track["categories"]:
            catalog["categories"].setdefault(category, []).append(track)

    # catalog.json 저장 (선택 사항)
    try:
        with open(CATALOG_PATH, "w", encoding="utf-8") as fp:
            json.dump(catalog, fp, ensure_ascii=False, indent=2)
    except Exception:
        # 저장 실패는 치명적이지 않으므로 무시
        pass

    return catalog


def load_cached_catalog() -> Optional[Dict]:
    if not CATALOG_PATH.exists():
        return None
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return None


def filter_tracks_by_category(
    catalog: Dict,
    include: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
) -> List[Dict]:
    tracks = catalog.get("tracks", [])
    if include:
        include_set = {cat.lower() for cat in include}
        tracks = [
            track for track in tracks
            if any(cat.lower() in include_set for cat in track["categories"])
        ]
    if exclude:
        exclude_set = {cat.lower() for cat in exclude}
        tracks = [
            track for track in tracks
            if not any(cat.lower() in exclude_set for cat in track["categories"])
        ]
    return tracks


def print_summary(catalog: Dict) -> str:
    lines = []
    total = len(catalog.get("tracks", []))
    lines.append(f"총 {total}개 트랙 분류됨")
    for category, tracks in sorted(catalog.get("categories", {}).items()):
        lines.append(f"- {category}: {len(tracks)}곡")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Public Domain 음악 라이브러리 분류")
    parser.add_argument("--refresh", action="store_true", help="catalog.json을 무시하고 다시 스캔")
    parser.add_argument("--summary", action="store_true", help="카테고리별 요약 출력")
    args = parser.parse_args()

    catalog = None
    if not args.refresh:
        catalog = load_cached_catalog()
    if not catalog:
        catalog = build_public_domain_catalog()

    if args.summary:
        print(print_summary(catalog))
    else:
        print(json.dumps(catalog, ensure_ascii=False, indent=2))

