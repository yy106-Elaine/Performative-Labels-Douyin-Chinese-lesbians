# Data Overview

This folder contains anonymized sample datasets illustrating the data processing pipeline used in this project.

Due to privacy, platform policy, and ethical considerations, raw Douyin video data (including URLs and original identifiers) are not included. All samples are anonymized and simplified for demonstration purposes.

---

## Folder Structure

### sample_raw_like/
Simulated raw metadata extracted from Douyin videos, including generalized captions and hashtags.

### sample_filtered/
Filtered dataset after applying relevance classification (`relevant_wlw = 1`).

### sample_enriched/
Engagement metrics (likes, comments, shares, saves) merged with filtered data.

### sample_ai_analysis/
Output of the AI-assisted coding pipeline (Vertex AI), including video-level and caption-level variables.

### evaluation_sample/
Anonymized samples demonstrating the evaluation workflow for Cohen’s kappa calculation, including:
- human coding (two independent coders)
- reconciled human agreement
- AI coding results

---

## Notes

- All identifiers (`sample_id`) are anonymized and do not correspond to real Douyin video IDs.
- Text fields (captions, descriptions) are rewritten or generalized to prevent reverse identification.
- This repository focuses on methodological transparency rather than data release.
