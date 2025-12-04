# ArtConnect AI – AI-Powered Artist Promotion Assistant (POC)

This repository contains the implementation of **ArtConnect AI**, a proof-of-concept (POC) assistant that helps a visual artist (client: **Joe Fleishman**) find and respond to high-value engagement opportunities across social media.

The system:

- Monitors **simulated Instagram & Twitter interactions**
- Scores each interaction with an **Opportunity Scoring Engine (0–100)**
- Generates **brand-aligned reply suggestions**
- Lets the artist **Approve, Edit & Approve, or Reject** each reply
- Logs human decisions and shows **live KPIs & analytics**


---

## 1. Features

### Live (Simulated) Multi-Platform Monitoring

- Loads interactions from:
  - `data/instagram_sample.csv`
  - `data/twitter_sample.json`
- Treats them as two distinct platforms:
  - **Instagram**
  - **Twitter**

### Opportunity Scoring Engine

For each interaction, the app computes a 0–100 opportunity score based on:

- **Keyword factor (K)** – commission/buy/gallery/etc.
- **Sentiment factor (S)** – VADER sentiment, positive only
- **User influence (U)** – normalized follower count
- **Recency factor (R)** – newer comments are prioritized

Weights (from technical documentation):

- `W_K = 0.50`
- `W_S = 0.30`
- `W_U = 0.15`
- `W_R = 0.05`

Final score is:

> Opportunity Score = (K * W_K + S * W_S + U * W_U + R * W_R) × 100

### AI Reply Suggestions (Brand Voice)

- Template-based replies in a **polite, professional, artist-centric tone**
- Different templates for:
  - commission/price/prints
  - gallery/curator/collector/feature
  - generic praise

### Human-in-the-Loop Approval Workflow

For each high-value interaction, the artist can:

- **Approve** – send the reply as-is  
- **Edit & Approve** – adjust the reply text, then approve  
- **Reject** – decide not to respond

All actions are logged in `logs/actions_log.csv`.

The **approval rate** is computed as:

> (Approved + Edited) / (Approved + Edited + Rejected)

### Analytics Dashboard (Streamlit Tabs)

Two main tabs in the app:

1. **Opportunities**
   - Platform & score summary
   - Filters by:
     - platform (All / Instagram / Twitter)
     - minimum opportunity score
   - Table of interactions
   - Review & Respond panel with AI-generated reply

2. **Analytics**
   - Overview KPIs:
     - Total interactions scanned
     - High-value opportunities (Score ≥ 50)
     - Total logged actions
     - Approval rate (Approve + Edit)
   - Engagement funnel chart:
     - Total interactions → High-value → Replied
   - Action breakdown chart:
     - Approve / Edit / Reject
   - Recent action log


---

## 2. Project Structure

```text
artconnect-ai/
│
├── app.py                      # Main Streamlit application
├── generate_fake_data.py       # Script to generate simulated Instagram/Twitter data
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── data/
│   ├── instagram_sample.csv    # Simulated Instagram interactions
│   └── twitter_sample.json     # Simulated Twitter interactions
│
├── logs/
│   └── actions_log.csv         # Human actions logged by the app (created at runtime)
│
└── docs/
    ├── Business_Performance_Report.pdf
    ├── Technical_Documentation.pdf
    └── Presentation_Manual.pdf
