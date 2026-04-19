import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import re
import pandas as pd

INPUT_METADATA_CSV = "metadata_keep.csv"
OUTPUT_METADATA_CSV = "metadata_keep_coded.csv"

CAPTION_COL = "hashtags"

CAPTION_IDENTITY_INVOLVED_COL = "caption_identity_involved"
CAPTION_IDENTITY_CATEGORY_COL = "caption_identity_category"
CAPTION_RULE_HIT_COL = "caption_rule_hit"

print("Loading metadata...")
metadata_df = pd.read_csv(INPUT_METADATA_CSV)
print("Loaded rows:", len(metadata_df))
print("Columns:", list(metadata_df.columns))

if CAPTION_COL not in metadata_df.columns:
    raise ValueError(f"{INPUT_METADATA_CSV} must contain a '{CAPTION_COL}' column.")


# ----------------------------
# Rule-based caption coding
# ----------------------------

ALT_TAGS = [
    "姐姐", "小狗", "体育生", "老公", "老婆", "s", "m", "SM", "sm", "dom", "sub"
]

VARIANT_PREFIXES = ["铁", "长发", "短发", "娘", "甜妹", "姐", "姐系", "御姐"]
variant_pattern = re.compile(rf"({'|'.join(VARIANT_PREFIXES)})\s*([tTpPhH])")

# Original T/P/H tags as standalone tokens
original_tph_pattern = re.compile(r"(?<![A-Za-z0-9])([tTpPhH])(?![A-Za-z0-9])")

# Standalone 1/0 markers
onezero_pattern = re.compile(r"(?<!\d)([01])(?!\d)")


def code_caption(text: str):
    """
    Returns:
        involved (str): "0" or "1"
        category (str): "1", "2", "3", or "N/A"
        hit_str (str): matched rule hits for audit
    """
    if pd.isna(text) or str(text).strip() == "":
        return "0", "N/A", ""

    s = str(text)
    hits = []

    # Category 2: TPH variants
    has_variant = False

    match = variant_pattern.search(s)
    if match:
        has_variant = True
        hits.append(match.group(0))

    if "姐1" in s or "甜妹1" in s:
        has_variant = True
        if "姐1" in s:
            hits.append("姐1")
        if "甜妹1" in s:
            hits.append("甜妹1")

    has_onezero = bool(onezero_pattern.search(s))
    if has_onezero:
        # Only count 1/0 as label-like if lesbian-related context is present
        if (
            "wlw" in s.lower()
            or "la" in s.lower()
            or "喜欢女" in s
            or "女同" in s
            or "姬" in s
        ):
            has_variant = True
            hits.append("1/0")

    # Category 1: original T/P/H
    has_original = bool(original_tph_pattern.search(s))
    if has_original:
        hits.append("t/p/h")

    # Category 3: alternative tags
    has_alternative = False
    for tag in ALT_TAGS:
        if tag.lower() in ["s", "m", "sm"]:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(tag)}(?![A-Za-z0-9])", s, flags=re.IGNORECASE):
                has_alternative = True
                hits.append(tag)
        else:
            if tag in s:
                has_alternative = True
                hits.append(tag)

    involved = "1" if (has_variant or has_original or has_alternative) else "0"

    if involved == "0":
        return "0", "N/A", ""

    # Priority: variants > original > alternative
    if has_variant:
        category = "2"
    elif has_original:
        category = "1"
    else:
        category = "3"

    return involved, category, ",".join(dict.fromkeys(hits))


# ----------------------------
# Ensure output columns exist
# ----------------------------
for col in [
    CAPTION_IDENTITY_INVOLVED_COL,
    CAPTION_IDENTITY_CATEGORY_COL,
    CAPTION_RULE_HIT_COL,
]:
    if col not in metadata_df.columns:
        metadata_df[col] = ""


# ----------------------------
# Run coding with resume support
# ----------------------------
for idx, row in metadata_df.iterrows():
    if (
        str(row.get(CAPTION_IDENTITY_INVOLVED_COL, "")).strip() != ""
        and str(row.get(CAPTION_IDENTITY_CATEGORY_COL, "")).strip() != ""
    ):
        continue

    involved, category, hit = code_caption(row.get(CAPTION_COL, ""))

    metadata_df.at[idx, CAPTION_IDENTITY_INVOLVED_COL] = involved
    metadata_df.at[idx, CAPTION_IDENTITY_CATEGORY_COL] = category
    metadata_df.at[idx, CAPTION_RULE_HIT_COL] = hit

    if (idx + 1) % 50 == 0:
        metadata_df.to_csv(OUTPUT_METADATA_CSV, index=False, encoding="utf-8")
        print(f"Saved progress: {idx + 1}/{len(metadata_df)}")


metadata_df.to_csv(OUTPUT_METADATA_CSV, index=False, encoding="utf-8")
print(f"Done. Saved coded metadata to {OUTPUT_METADATA_CSV}")
