# Performative Labels Under Censorship  
### T/P/H Labeling Culture and Lesbian Identity in Digital China

This project investigates how lesbian identity labeling practices (T/P/H culture) are performed, transformed, and negotiated on Chinese short-video platforms, particularly Douyin.

It combines computational social media analysis with cultural studies approaches to examine how identity is signaled through captions, visual presentation, and platform interaction patterns.

---

## Overview

The project builds a full data pipeline to:

- Collect Douyin video URLs based on identity-related keywords  
- Extract video metadata and captions  
- Filter relevant lesbian content using rule-based and multimodal methods  
- Code identity signals in both visual and textual dimensions  
- Merge coding results with engagement data (likes, comments)  
- Construct a final analytical dataset  
- Evaluate coding reliability using human annotation and Cohen’s kappa  
The analysis focuses on how labeling practices shift from traditional T/P/H categories toward more flexible and performative identity expressions.
This project demonstrates how AI-assisted, multimodal pipelines can be used to scale qualitative cultural analysis into structured, reproducible computational research.
---

## Data Flow

The pipeline follows a multi-stage workflow:

1. **Data Collection**  
   Scrape Douyin video URLs using identity-related keywords.

2. **Metadata Extraction**  
   Extract captions and hashtag information.

3. **Filtering**  
   - Rule-based keyword filtering  
   - Multimodal refinement using AI (Gemini)

4. **Coding**  
   - Visual identity coding (Vertex AI)  
   - Caption-based identity classification

5. **Data Integration**  
   Merge coding outputs with engagement metrics (likes, comments).

6. **Dataset Construction**  
   Build final analytical dataset.

7. **Validation**  
   Conduct human annotation and compute Cohen’s kappa for reliability.

## Repository Structure

```text
src/
├── 01_search_scraper.py              # Collect video URLs from Douyin search
├── 02_extract_metadata.py           # Extract captions and hashtag metadata
├── 03_filter_keyword.py             # Rule-based keyword filtering
├── 04_filter_multimodal.py          # Multimodal refinement (video-level filtering)
├── 05_collect_interactions.py       # Collect engagement metrics (likes/comments)
├── 06_vertex_visual_analysis.py     # Visual coding via Vertex AI (video-level)
├── 07_caption_textual_coding.py     # Caption-level identity coding
├── 08_merge_coding_and_interactions.py  # Merge coding results with engagement data
├── 09_build_final_dataset.py        # Construct final dataset for analysis
├── 10_visualization.py              # Generate figures for analysis
├── 11_prepare_evaluation_files.py   # Prepare human evaluation datasets
├── 12_compute_kappa_main.py         # Cohen’s kappa for main variables
└── 13_compute_kappa_caption_category.py # Kappa for caption label categories
└── README.md                      

data/
├── sample_raw_like/                  # Simulated raw metadata
│   └── sample_existing_metadata.csv
├── sample_filtered/                  # Filtered subset (relevant_wlw = 1)
│   └── sample_metadata_keep.csv
├── sample_enriched/                  # Engagement metrics
│   └── sample_video_interaction.csv
├── sample_ai_analysis/               # AI coding outputs (Vertex AI)
│   └── sample_video_categorization.csv
├── evaluation_sample/                # Evaluation workflow samples
│   ├── sample_human_result_yy.csv
│   ├── sample_human_result_zx.csv
│   ├── sample_human_agreement_result.csv
│   └── sample_ai_result.csv
├── data_dictionary.md                # Variable definitions
└── README.md

results/
├── figures/                         # Final visualizations of key findings
│   ├── fig1_label_distribution.png
│   ├── fig2_label_diversification.png
│   ├── fig3_engagement_comparison.png
│   └── README.md                    # Figure descriptions and interpretations
│
├── tables/                          # Summary tables and evaluation results
│   ├── table1_kappa_summary.csv
│   └── README.md                    # Table descriptions and explanations
│
└── README.md                        # Overview of results outputs

archive/
└── repair_exclude_to_keep.py

**## Key Findings**

- Identity labeling appears in over 50% of videos, functioning as a routine communicative system.
- Labeling practices have diversified beyond traditional T/P/H categories.
- Videos with identity signals show higher engagement, suggesting labeling functions as algorithmic capital.
