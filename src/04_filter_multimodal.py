import re
import pandas as pd

INPUT_METADATA_CSV = "metadata_keep_coded.csv"
OUTPUT_METADATA_CSV = "metadata_keep_coded.csv"

CAPTION_COL = "hashtags"
REL_COL = "relevant_wlw"
RULE_HIT_COL = "relevance_rule_hit"
REASON_COL = "relevance_reason"

DOWNSTREAM_COLS = [
    "caption_identity_involved",
    "caption_identity_category",
]

# Boundary patterns for short identity labels such as #le#, #wlw#, or standalone "la"
SYM_BOUND = r"(?:^|[\s#@,，。.!！？\-\(\)\[\]{}<>《》“”\"'/:;|\\])"
SYM_END = r"(?:$|[\s#@,，。.!！？\-\(\)\[\]{}<>《》“”\"'/:;|\\])"

# -------------------------
# 1) Hard negatives
# If matched, default to relevance = 0
# -------------------------
HARD_NEGATIVE_PATTERNS = [
    r"Love\s*Sick\s*Girls",
    r"lovesickgirls",
    r"#lovesickgirls",
    r"blackpink",
    r"kpop",
    r"翻跳",
    r"手势舞",
    r"手势舞教程",
    r"舞蹈教学",
    r"卡点舞",
    r"抖音舞蹈潮流",
    r"跟跳",
    r"练舞",
]

# -------------------------
# 2) Strong positives
# If matched, default to relevance = 1
# -------------------------
STRONG_POSITIVE_PATTERNS = [
    rf"{SYM_BOUND}wlw{SYM_END}",
    rf"{SYM_BOUND}les{SYM_END}",
    rf"{SYM_BOUND}gl{SYM_END}",
    rf"{SYM_BOUND}le{SYM_END}",
    rf"{SYM_BOUND}la{SYM_END}",
    r"女同",
    r"拉拉",
    r"女女",
    r"姬圈",
    r"姛",
    r"女姛",
    r"双女主",
    r"铁[ＴTt]",
    r"长发[ＴTt]",
    r"短发[pPＰ]",
    r"娘[pPＰ]",
    r"奶[ＴTt]",
    r"爷[ＴTt]",
    r"甜妹",
    r"纯拉",
    r"喜欢女的",
    r"喜欢女生",
    r"只喜欢女生",
    r"爱上女生",
    r"她和她",
    r"两个女生",
    r"陈乐",
    r"直女",
    r"crush",
    r"心选姐",
    r"玛朴缇香水",
    r"叫什么叫",
    r"百合(?!花)",
]

# -------------------------
# 3) Weak positives
# Cannot determine relevance on their own
# -------------------------
WEAK_POSITIVE_PATTERNS = [
    r"恋爱日常",
    r"穿搭",
    r"日常",
    r"猛女舞",
    r"姐姐",
    r"姐",
    r"小狗型?",
]

# -------------------------
# 4) Botanical / irrelevant "baihe"
# -------------------------
BAIHE_NOISE_PATTERNS = [
    r"百合花",
    r"香水百合",
    r"盆栽",
    r"种植",
    r"园艺",
    r"鲜花",
    r"植物",
    r"插花",
    r"花束",
    r"花店",
    r"百合炒肉",
]

HARD_NEG_RE = re.compile("|".join(f"(?:{p})" for p in HARD_NEGATIVE_PATTERNS), flags=re.I)
STRONG_POS_RE = re.compile("|".join(f"(?:{p})" for p in STRONG_POSITIVE_PATTERNS), flags=re.I)
WEAK_POS_RE = re.compile("|".join(f"(?:{p})" for p in WEAK_POSITIVE_PATTERNS), flags=re.I)
BAIHE_NOISE_RE = re.compile("|".join(f"(?:{p})" for p in BAIHE_NOISE_PATTERNS), flags=re.I)


def normalize_text(text: object) -> str:
    if pd.isna(text):
        return ""
    s = str(text).strip()
    s = s.replace("＃", "#")
    s = re.sub(r"\s+", " ", s)
    return s


def collect_hits(pattern_list: list[str], text: str) -> list[str]:
    hits = []
    for pattern in pattern_list:
        match = re.search(pattern, text, flags=re.I)
        if match:
            hits.append(match.group(0))
    return list(dict.fromkeys(hits))


def code_relevance(text: object) -> tuple[int, str, str]:
    s = normalize_text(text)

    if s == "":
        return 0, "", "empty hashtags"

    hard_neg_hits = collect_hits(HARD_NEGATIVE_PATTERNS, s)
    strong_pos_hits = collect_hits(STRONG_POSITIVE_PATTERNS, s)
    weak_pos_hits = collect_hits(WEAK_POSITIVE_PATTERNS, s)
    baihe_noise_hits = collect_hits(BAIHE_NOISE_PATTERNS, s)

    has_hard_neg = bool(HARD_NEG_RE.search(s))
    has_strong_pos = bool(STRONG_POS_RE.search(s))
    has_weak_pos = bool(WEAK_POS_RE.search(s))
    has_baihe_noise = bool(BAIHE_NOISE_RE.search(s))

    # 1. Botanical / flower-related usage of "baihe" -> 0
    if has_baihe_noise and not has_strong_pos:
        return 0, ",".join(baihe_noise_hits), "botanical/flower usage"

    # 2. Hard negatives take priority unless there is also a strong lesbian-related signal
    if has_hard_neg and not has_strong_pos:
        return 0, ",".join(hard_neg_hits), "hard negative pattern"

    # 3. Strong positives -> 1
    if has_strong_pos:
        all_hits = list(dict.fromkeys(strong_pos_hits + weak_pos_hits))
        return 1, ",".join(all_hits), "strong lesbian-related signal"

    # 4. Weak positives alone are not sufficient
    if has_weak_pos:
        return 0, ",".join(weak_pos_hits), "weak/ambiguous only"

    # 5. Default
    return 0, "", "insufficient evidence"


def main():
    metadata_df = pd.read_csv(INPUT_METADATA_CSV)

    print("Loaded metadata rows:", len(metadata_df))
    print("Metadata columns:", list(metadata_df.columns))

    for col in [REL_COL, RULE_HIT_COL, REASON_COL] + DOWNSTREAM_COLS:
        if col not in metadata_df.columns:
            metadata_df[col] = ""
        metadata_df[col] = metadata_df[col].astype("object")

    # Clear previous coding results and rerun from scratch
    metadata_df[REL_COL] = ""
    metadata_df[RULE_HIT_COL] = ""
    metadata_df[REASON_COL] = ""

    for idx, row in metadata_df.iterrows():
        hashtags = row.get(CAPTION_COL, "")
        rel, hit, reason = code_relevance(hashtags)

        metadata_df.at[idx, REL_COL] = rel
        metadata_df.at[idx, RULE_HIT_COL] = hit
        metadata_df.at[idx, REASON_COL] = reason

        if rel == 0:
            for col in DOWNSTREAM_COLS:
                metadata_df.at[idx, col] = "N/A"

        if (idx + 1) % 50 == 0:
            metadata_df.to_csv(OUTPUT_METADATA_CSV, index=False, encoding="utf-8-sig")
            print(f"Saved progress: {idx + 1}/{len(metadata_df)}")

    metadata_df.to_csv(OUTPUT_METADATA_CSV, index=False, encoding="utf-8-sig")
    print(f"Done. Saved coded metadata to {OUTPUT_METADATA_CSV}")

    print("\nRelevant_wlw value counts:")
    print(metadata_df[REL_COL].value_counts(dropna=False))


if __name__ == "__main__":
    main()
