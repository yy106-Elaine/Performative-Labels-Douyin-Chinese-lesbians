import os
import re
import pandas as pd

BASE_CSV = "video_categorization_with_stats.csv"
METADATA_CSV = "metadata_keep_coded.csv"

OUTPUT_FULL_CSV = "video_categorization_with_stats_relevant.csv"
OUTPUT_CLEAN_CSV = "video_categorization_with_stats_relevant_clean.csv"


def normalize_id(x: object) -> str:
    """
    Extract the longest digit sequence as a normalized video ID.
    """
    if pd.isna(x):
        return ""

    s = str(x).strip()
    s = os.path.basename(s)
    s = os.path.splitext(s)[0]

    digits = re.findall(r"\d+", s)
    if not digits:
        return ""

    return max(digits, key=len)


def normalize_category_value(x: object) -> str:
    if pd.isna(x):
        return "N/A"

    s = str(x).strip()
    if s in ["", "nan", "None", "<NA>", "-", "N/A", "NA", "n/a", "na"]:
        return "N/A"

    try:
        return str(int(float(s)))
    except Exception:
        return s


def main():
    base_df = pd.read_csv(BASE_CSV)
    metadata_df = pd.read_csv(METADATA_CSV)

    print("Loaded base rows:", len(base_df))
    print("Loaded metadata rows:", len(metadata_df))

    if "video_id" not in base_df.columns:
        raise ValueError(f"{BASE_CSV} must contain a 'video_id' column.")

    if "video_id" not in metadata_df.columns:
        raise ValueError(f"{METADATA_CSV} must contain a 'video_id' column.")

    if "relevant_wlw" not in metadata_df.columns:
        raise ValueError(f"{METADATA_CSV} must contain a 'relevant_wlw' column.")

    # ----------------------------
    # Normalize IDs
    # ----------------------------
    base_df["video_id"] = base_df["video_id"].apply(normalize_id)
    metadata_df["video_id"] = metadata_df["video_id"].apply(normalize_id)

    # ----------------------------
    # Merge relevance flag
    # ----------------------------
    metadata_small = metadata_df[["video_id", "relevant_wlw"]].copy()
    metadata_small = metadata_small.drop_duplicates(subset=["video_id"])

    merged_df = base_df.merge(metadata_small, on="video_id", how="left")

    print(
        "Matched relevant_wlw:",
        merged_df["relevant_wlw"].notna().sum(),
        "/",
        len(merged_df),
    )

    # Fill unmatched as irrelevant
    merged_df["relevant_wlw"] = (
        pd.to_numeric(merged_df["relevant_wlw"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # ----------------------------
    # Set analysis columns to N/A if irrelevant
    # ----------------------------
    analysis_cols = [
        "video_style",
        "video_identity_present_visual",
        "video_identity_visual_type",
        "caption_identity_involved",
        "caption_identity_category",
    ]

    for col in analysis_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].astype("object")

    mask_irrelevant = merged_df["relevant_wlw"] == 0
    for col in analysis_cols:
        if col in merged_df.columns:
            merged_df.loc[mask_irrelevant, col] = "N/A"

    # Normalize category-looking columns
    for col in analysis_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].apply(normalize_category_value)

    # ----------------------------
    # Reorder columns
    # ----------------------------
    preferred_order = [
        "video_id",
        "relevant_wlw",
        "video_style",
        "video_identity_present_visual",
        "video_identity_visual_type",
        "caption_identity_involved",
        "caption_identity_category",
        "digg_count",
        "comment_count",
    ]

    merged_df = merged_df[[c for c in preferred_order if c in merged_df.columns]]

    # ----------------------------
    # Save full dataset
    # ----------------------------
    merged_df.to_csv(OUTPUT_FULL_CSV, index=False, encoding="utf-8-sig")
    print(f"[SUCCESS] Saved full dataset: {OUTPUT_FULL_CSV}")

    # ----------------------------
    # Save clean relevant-only dataset
    # ----------------------------
    clean_df = merged_df[merged_df["relevant_wlw"] == 1].copy()
    clean_df.to_csv(OUTPUT_CLEAN_CSV, index=False, encoding="utf-8-sig")
    print(f"[SUCCESS] Saved clean dataset: {OUTPUT_CLEAN_CSV}")

    # ----------------------------
    # Summary
    # ----------------------------
    print("\n===== DATASET SUMMARY =====")
    print("Total rows:", len(merged_df))
    print("Relevant rows:", (merged_df["relevant_wlw"] == 1).sum())
    print("Irrelevant rows:", (merged_df["relevant_wlw"] == 0).sum())
    print("Clean dataset rows:", len(clean_df))
    print("Final columns:", list(merged_df.columns))


if __name__ == "__main__":
    main()
