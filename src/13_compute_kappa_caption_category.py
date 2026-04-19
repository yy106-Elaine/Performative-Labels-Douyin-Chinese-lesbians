import pandas as pd
import re


FULL_DATASET_CSV = "video_categorization_with_stats_relevant.csv"
OLD_EVAL_CSV = "Evaluation/test_together.csv"

ADDITION_TEMPLATE_CSV = "Evaluation/addition_video_categorization_template.csv"
ADDITION_ORIGINAL_CSV = "Evaluation/addition_video_categorization_original_labels.csv"

ADDITION_TEST_YY_CSV = "Evaluation/addition_test_yy.csv"
ADDITION_TEST_ZX_CSV = "Evaluation/addition_test_zx.csv"
ADDITION_TEST_TOGETHER_CSV = "Evaluation/addition_test_together.csv"

OLD_YY_CSV = "Evaluation/test_yy.csv"
OLD_ZX_CSV = "Evaluation/test_zx.csv"
OLD_TOGETHER_CSV = "Evaluation/test_together.csv"
OLD_ORIGINAL_CSV = "Evaluation/video_categorization_original_labels.csv"


def normalize_video_id(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()

    m = re.search(r"/video/(\d+)", s)
    if m:
        return m.group(1)

    nums = re.findall(r"\d+", s)
    if nums:
        return max(nums, key=len)

    return s


def clean_int_or_na(x):
    if pd.isna(x):
        return "N/A"
    x = str(x).strip()

    if x in {"", "nan", "NaN", "None", "N/A", "n/a", "NA", "na", "N-A", "n-a", "-"}:
        return "N/A"
    if x in {"0", "0.0"}:
        return 0
    if x in {"1", "1.0"}:
        return 1
    if x in {"2", "2.0"}:
        return 2
    if x in {"3", "3.0"}:
        return 3

    try:
        return int(float(x))
    except Exception:
        return "N/A"


def format_for_csv(x):
    if pd.isna(x):
        return "N/A"
    if x == "N/A":
        return "N/A"
    try:
        return str(int(x))
    except Exception:
        return str(x)


def cohens_kappa_manual(df, col1, col2):
    sub = df[[col1, col2]].copy()
    N = len(sub)

    if N == 0:
        return {"N": 0, "agreement_rate": None, "p_e": None, "kappa": None, "categories": []}

    p_o = (sub[col1] == sub[col2]).mean()
    categories = sorted(set(sub[col1]).union(set(sub[col2])))

    p_e = 0
    for k in categories:
        n_k1 = (sub[col1] == k).sum()
        n_k2 = (sub[col2] == k).sum()
        p_e += (n_k1 * n_k2) / (N ** 2)

    kappa = (p_o - p_e) / (1 - p_e) if p_e != 1 else 1.0

    return {
        "N": N,
        "agreement_rate": p_o,
        "p_e": p_e,
        "kappa": kappa,
        "categories": categories,
    }


def build_additional_sample():
    full = pd.read_csv(FULL_DATASET_CSV, encoding="utf-8-sig")
    old_eval = pd.read_csv(OLD_EVAL_CSV, encoding="utf-8-sig")

    full.columns = full.columns.str.strip()
    old_eval.columns = old_eval.columns.str.strip()

    full["video_id_norm"] = full["video_id"].apply(normalize_video_id)
    full["url"] = "https://www.douyin.com/video/" + full["video_id_norm"]

    for col in [
        "video_identity_present_visual",
        "caption_identity_involved",
        "caption_identity_category",
    ]:
        full[col] = full[col].apply(clean_int_or_na)

    old_eval["url"] = old_eval["url"].astype(str).str.strip()
    old_urls = set(old_eval["url"])

    pool = full[
        (full["caption_identity_involved"] == 1) &
        (~full["url"].isin(old_urls))
    ].copy()

    pool = pool.drop_duplicates(subset=["url"])

    n_sample = 30
    if len(pool) < n_sample:
        raise ValueError(f"Only {len(pool)} eligible videos left, fewer than {n_sample}.")

    sampled = pool.sample(n=n_sample, random_state=42).copy()

    original_labels = sampled[
        [
            "url",
            "video_identity_present_visual",
            "caption_identity_involved",
            "caption_identity_category",
        ]
    ].copy()

    template = sampled[["url"]].copy()
    template["video_identity_present_visual"] = ""
    template["caption_identity_involved"] = ""
    template["caption_identity_category"] = ""

    template.to_csv(ADDITION_TEMPLATE_CSV, index=False, encoding="utf-8-sig")
    original_labels.to_csv(ADDITION_ORIGINAL_CSV, index=False, encoding="utf-8-sig")

    print("Saved additional sample files:")
    print(" -", ADDITION_TEMPLATE_CSV)
    print(" -", ADDITION_ORIGINAL_CSV)


def append_valid_category_rows(old_file, addition_file):
    old_df = pd.read_csv(old_file, encoding="utf-8-sig")
    add_df = pd.read_csv(addition_file, encoding="utf-8-sig")

    old_df.columns = old_df.columns.str.strip()
    add_df.columns = add_df.columns.str.strip()

    cols = [
        "url",
        "video_identity_present_visual",
        "caption_identity_involved",
        "caption_identity_category",
    ]

    old_df = old_df[cols].copy()
    add_df = add_df[cols].copy()

    for c in [
        "video_identity_present_visual",
        "caption_identity_involved",
        "caption_identity_category",
    ]:
        old_df[c] = old_df[c].apply(clean_int_or_na)
        add_df[c] = add_df[c].apply(clean_int_or_na)

    old_valid = old_df[old_df["caption_identity_category"] != "N/A"].copy()

    combined = pd.concat([add_df, old_valid], ignore_index=True)
    combined = combined.drop_duplicates(subset=["url"], keep="first").copy()

    for c in [
        "video_identity_present_visual",
        "caption_identity_involved",
        "caption_identity_category",
    ]:
        combined[c] = combined[c].apply(format_for_csv)

    combined.to_csv(addition_file, index=False, encoding="utf-8-sig")

    print(f"Updated: {addition_file}")
    print(f"Old valid rows added: {len(old_valid)}")
    print(f"Final valid category rows: {(combined['caption_identity_category'] != 'N/A').sum()}")


def append_old_valid_rows():
    append_valid_category_rows(OLD_YY_CSV, ADDITION_TEST_YY_CSV)
    append_valid_category_rows(OLD_ZX_CSV, ADDITION_TEST_ZX_CSV)
    append_valid_category_rows(OLD_TOGETHER_CSV, ADDITION_TEST_TOGETHER_CSV)
    append_valid_category_rows(OLD_ORIGINAL_CSV, ADDITION_ORIGINAL_CSV)


def compute_category_kappa():
    zx = pd.read_csv(ADDITION_TEST_ZX_CSV)
    yy = pd.read_csv(ADDITION_TEST_YY_CSV)

    zx.columns = zx.columns.str.strip()
    yy.columns = yy.columns.str.strip()

    zx["caption_identity_category"] = zx["caption_identity_category"].apply(clean_int_or_na)
    yy["caption_identity_category"] = yy["caption_identity_category"].apply(clean_int_or_na)

    merged_inter = pd.merge(
        zx,
        yy,
        on="url",
        suffixes=("_zx", "_yy"),
        how="inner",
    )

    subset_inter = merged_inter[
        (merged_inter["caption_identity_category_zx"] != "N/A") &
        (merged_inter["caption_identity_category_yy"] != "N/A")
    ].copy()

    print("\n========== INTER-CODER (CATEGORY) ==========")
    print("Total matched:", len(merged_inter))
    print("Valid category rows:", len(subset_inter))
    print(cohens_kappa_manual(
        subset_inter,
        "caption_identity_category_zx",
        "caption_identity_category_yy",
    ))

    human = pd.read_csv(ADDITION_TEST_TOGETHER_CSV)
    ai = pd.read_csv(ADDITION_ORIGINAL_CSV)

    human.columns = human.columns.str.strip()
    ai.columns = ai.columns.str.strip()

    human["caption_identity_category"] = human["caption_identity_category"].apply(clean_int_or_na)
    ai["caption_identity_category"] = ai["caption_identity_category"].apply(clean_int_or_na)

    merged_ai = pd.merge(
        human,
        ai,
        on="url",
        suffixes=("_human", "_ai"),
        how="inner",
    )

    subset_ai = merged_ai[
        (merged_ai["caption_identity_category_human"] != "N/A") &
        (merged_ai["caption_identity_category_ai"] != "N/A")
    ].copy()

    print("\n========== HUMAN vs AI (CATEGORY) ==========")
    print("Total matched:", len(merged_ai))
    print("Valid category rows:", len(subset_ai))
    print(cohens_kappa_manual(
        subset_ai,
        "caption_identity_category_human",
        "caption_identity_category_ai",
    ))


def main():
    build_additional_sample()
    append_old_valid_rows()
    compute_category_kappa()


if __name__ == "__main__":
    main()
