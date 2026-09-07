# UAMD Datasets

## Overview

This directory contains documentation for datasets used in UAMD model training and evaluation.

> **IMPORTANT**: Do not commit large dataset files to this repository. Use `.gitignore` to exclude data files.

## Datasets

### 1. URL Phishing Detection

| Property | Value |
|----------|-------|
| **Name** | URL Feature Dataset (Synthetic/Generated) |
| **Source** | Generated from feature engineering on known phishing URL patterns |
| **License** | N/A (synthetic) |
| **Samples** | Generated on-demand |
| **Classes** | `legitimate` (0), `phishing` (1) |
| **Features** | Lexical, domain, structural URL features |
| **Split** | 70% train / 15% validation / 15% test |

### 2. Text Scam Detection

| Property | Value |
|----------|-------|
| **Name** | Scam/Phishing Text Dataset (Baseline) |
| **Source** | Rule-based + pattern matching baseline |
| **License** | N/A |
| **Samples** | Pattern-based classification |
| **Classes** | `safe`, `phishing`, `scam`, `spam`, `social_engineering` |
| **Preprocessing** | Lowercasing, URL extraction, entity extraction |

## Adding New Datasets

When adding a new dataset, document:

1. **Name**: Dataset identifier
2. **Source**: Where the data came from (URL, paper, organization)
3. **License**: Usage license (MIT, CC-BY, Apache, etc.)
4. **Samples**: Total number of samples
5. **Classes**: Class labels and distribution
6. **Preprocessing**: Any transformations applied
7. **Train/Val/Test Split**: How the data was divided

## Storage

- Small reference files: `datasets/references/`
- Large data files: Download via provided scripts, stored locally in `datasets/data/` (gitignored)
