import pandas as pd
from pathlib import Path
import shutil
import re

# =========================
# Configuration
# =========================
BASE_DIR = Path("Douyin_Data")
DOWNLOAD_DIR = BASE_DIR / "Download"
RAW_CSV = Path("existing_videos_metadata.csv")

OUT_KEEP_DIR = Path("filtered_data")
OUT_EXCLUDE_DIR = Path("excluded_data")

(OUT_KEEP_DIR / "videos").mkdir(parents=True, exist_ok=True)
(OUT_EXCLUDE_DIR / "videos").mkdir(parents=True, exist_ok=True)

# =========================
# Core vs. Noise Patterns
# Logic:
# relevant_wlw = 1 only if:
#   (matches at least one core pattern)
#   AND
#   (does not match any noise pattern)
# =========================

# Symbol / whitespace boundaries for short identity labels
# This helps match forms such as #le#, (wlw), or standalone "la"
SYM_BOUND = r"(?:^|[\s#@,，。.!！？\-\(\)\[\]{}<>《》“”\"'/:;|\\])"
SYM_END = r"(?:$|[\s#@,，。.!！？\-\(\)\[\]{}<>《》“”\"'/:;|\\])"

CORE_PATTERNS = [
    # Community / identity / stylistic labels
    r"铁[ＴTt]",
    r"[tT][pP][hH]?\s*圈",      # t圈 / tp圈 / tph圈
    r"姬圈",
    r"女同",
    r"拉拉",
    r"女女",
    r"彩虹旗",
    r"🌈",
    r"纯拉",
    r"爷[ＴTt]",
    r"娘[pP]",
    r"奶[ＴTt]",
    r"长发[ＴTt]",
    r"短发[pP]",
    r"甜妹",
    r"姐姐|姐",
    r"小狗型?",

    # Abbreviations and shorthand labels
    rf"{SYM_BOUND}wlw{SYM_END}",
    rf"{SYM_BOUND}les{SYM_END}",
    rf"{SYM_BOUND}gl{SYM_END}",
    rf"{SYM_BOUND}le{SYM_END}",
    rf"{SYM_BOUND}la{SYM_END}",

    # Short-form "t" only in identity-like contexts
    rf"{SYM_BOUND}t{SYM_END}",
    r"铁t",
    r"姛",
    r"女姛",
    r"双女主",

    # Include 百合 but exclude floral usage separately
    r"百合(?!花)",
]

NOISE_PATTERNS = [
    # Gardening / flower / cooking related noise
    r"养护技巧",
    r"盆栽",
    r"种植",
    r"百合花",
    r"园艺",
    r"泰国百合",
    r"百合炒肉",
    r"插花",
    r"花束",
    r"花店",
    r"食谱",
    r"做法",
]

CORE_REGEX = re.compile("|".join(f"(?:{p})" for p in CORE_PATTERNS), flags=re.I)
NOISE_REGEX = re.compile("|".join(f"(?:{p})" for p in NOISE_PATTERNS), flags=re.I)

# =========================
# Load Metadata
# Expected columns from 02_extract_metadata.py:
# video_id, url, full_caption, extracted_hashtags
# =========================
df = pd.read_csv(
    RAW_CSV,
    dtype={"video_id": "string"},
)

# Combine hashtag and caption text for rule-based filtering
text = (
    df["extracted_hashtags"].fillna("").astype(str)
    + " "
    + df["full_caption"].fillna("").astype(str)
)

is_core = text.str.contains(CORE_REGEX, na=False)
is_noise = text.str.contains(NOISE_REGEX, na=False)

df["relevant_wlw"] = (is_core & ~is_noise).astype(int)

keep_df = df[df["relevant_wlw"] == 1].copy()
exclude_df = df[df["relevant_wlw"] == 0].copy()

# =========================
# Copy Filtered Video Files
# =========================
def copy_videos(sub_df: pd.DataFrame, destination_dir: Path) -> int:
    """
    Copy matching video files into a destination folder
    based on video_id.
    """
    copied = 0
    for video_id in sub_df["video_id"].astype(str):
        src = DOWNLOAD_DIR / f"{video_id}.mp4"
        if src.exists():
            shutil.copy2(src, destination_dir / f"{video_id}.mp4")
            copied += 1
    return copied


copied_keep = copy_videos(keep_df, OUT_KEEP_DIR / "videos")
copied_exclude = copy_videos(exclude_df, OUT_EXCLUDE_DIR / "videos")

# =========================
# Save Filtered Metadata
# =========================
keep_df.to_csv(OUT_KEEP_DIR / "metadata_keep.csv", index=False)
exclude_df.to_csv(OUT_EXCLUDE_DIR / "metadata_exclude.csv", index=False)

print(
    f"Filtering complete.\n"
    f"- Kept (relevant_wlw = 1): {len(keep_df)} rows "
    f"(videos copied: {copied_keep})\n"
    f"- Excluded (relevant_wlw = 0): {len(exclude_df)} rows "
    f"(videos copied: {copied_exclude})\n"
    f"- Output files:\n"
    f"  {OUT_KEEP_DIR / 'metadata_keep.csv'}\n"
    f"  {OUT_EXCLUDE_DIR / 'metadata_exclude.csv'}"
)
