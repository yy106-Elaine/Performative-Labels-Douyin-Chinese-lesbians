# Source Code Overview

This folder contains the full data processing and analysis pipeline for the project.

The workflow follows a structured pipeline from data collection to AI-assisted coding and evaluation.

---

## Pipeline Overview

The scripts are organized sequentially:

### 01–02: Data Collection
- `01_search_scraper.py`  
  Scrapes Douyin video URLs based on keyword queries.

- `02_extract_metadata.py`  
  Extracts video metadata (captions, hashtags, etc.).

---

### 03–04: Data Filtering
- `03_filter_keyword.py`  
  Filters videos using rule-based keyword matching.

- `04_filter_multimodal.py`  
  Applies multimodal filtering (e.g., hashtag relevance and content signals).

---

### 05: Engagement Data
- `05_collect_interactions.py`  
  Collects engagement metrics (likes, comments, shares, saves).

---

### 06–07: AI & Text Coding
- `06_vertex_visual_analysis.py`  
  Performs video-level coding using Vertex AI (visual features and identity signals).

- `07_caption_textual_coding.py`  
  Applies rule-based coding to caption text (identity labeling and categorization).

---

### 08–09: Dataset Construction
- `08_merge_coding_and_interactions.py`  
  Merges coding outputs with engagement data.

- `09_build_final_dataset.py`  
  Constructs the final dataset used for analysis.

---

### 10: Visualization
- `10_visualization.py`  
  Generates figures and summary outputs for analysis.

---

### 11–13: Evaluation (Cohen’s Kappa)
- `11_prepare_evaluation_files.py`  
  Prepares datasets for human and AI evaluation.

- `12_compute_kappa_main.py`  
  Computes Cohen’s kappa for main variables.

- `13_compute_kappa_caption_category.py`  
  Computes kappa specifically for caption identity categories.

---

## Notes

- The pipeline combines rule-based methods and AI-assisted analysis (Vertex AI).
- All scripts are designed to be modular and sequential.
- Public data samples in this repository are anonymized and do not reflect the full original dataset.
