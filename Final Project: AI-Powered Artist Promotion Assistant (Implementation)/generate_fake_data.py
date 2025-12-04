import os
import json
import random
from datetime import datetime, timedelta

import pandas as pd


# ---------- Config ----------
TOTAL_INTERACTIONS = 240
TOTAL_HIGH_VALUE = 25

INSTAGRAM_SHARE = 0.55  # 55% of interactions from Instagram
INSTAGRAM_TOTAL = int(TOTAL_INTERACTIONS * INSTAGRAM_SHARE)
TWITTER_TOTAL = TOTAL_INTERACTIONS - INSTAGRAM_TOTAL

INSTAGRAM_HIGH = TOTAL_HIGH_VALUE // 2  # split high-value approx evenly
TWITTER_HIGH = TOTAL_HIGH_VALUE - INSTAGRAM_HIGH

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------- Helper data ----------
generic_comments = [
    "Love this!", "Amazing work!", "So cool 🔥", "Nice!", "Beautiful piece.",
    "Wow!", "Great colors!", "This is awesome.", "Nice composition.",
    "Stunning!"
]

high_value_templates = [
    "I'd love to commission a piece in this style.",
    "Do you sell prints of this artwork?",
    "What is the price for a commission?",
    "I'm a gallery curator, would love to talk.",
    "I'm a collector and really interested in this piece.",
    "We run an online art gallery, can we feature your work?",
    "I'd like to buy this painting for my collection.",
]

user_handles = [
    "ArtLover", "GalleryGazer", "CollectorJane", "CuratorMike",
    "PainterFan", "AbstractAddict", "ColorChaser", "GalleryOwnerTX",
    "DesignGeek", "ModernArtFan"
]


def random_timestamp(days_back=30):
    """Random timestamp within last `days_back` days."""
    now = datetime.now()
    delta_days = random.randint(0, days_back)
    delta_seconds = random.randint(0, 24 * 3600)
    ts = now - timedelta(days=delta_days, seconds=delta_seconds)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def make_interaction(idx, platform, high_value=False):
    handle = f"@{random.choice(user_handles)}{random.randint(1, 999)}"
    if high_value:
        text = random.choice(high_value_templates)
        followers = random.randint(1500, 15000)  # more influential
    else:
        text = random.choice(generic_comments)
        followers = random.randint(10, 1200)

    interaction_id = f"{platform[:3].upper()}-{idx:04d}"

    return {
        "interaction_id": interaction_id,
        "platform": platform.capitalize(),  # "Instagram" or "Twitter"
        "timestamp": random_timestamp(),
        "user_handle": handle,
        "user_followers": followers,
        "text_content": text,
    }


# ---------- Generate Instagram CSV ----------
insta_rows = []
for i in range(1, INSTAGRAM_TOTAL + 1):
    high = i <= INSTAGRAM_HIGH
    insta_rows.append(make_interaction(i, "instagram", high_value=high))

insta_df = pd.DataFrame(insta_rows)
insta_path = os.path.join(OUTPUT_DIR, "instagram_sample.csv")
insta_df.to_csv(insta_path, index=False)
print(f"Wrote {len(insta_df)} Instagram rows to {insta_path}")

# ---------- Generate Twitter JSON ----------
twitter_rows = []
for i in range(1, TWITTER_TOTAL + 1):
    high = i <= TWITTER_HIGH
    twitter_rows.append(make_interaction(i, "twitter", high_value=high))

twitter_path = os.path.join(OUTPUT_DIR, "twitter_sample.json")
with open(twitter_path, "w", encoding="utf-8") as f:
    json.dump(twitter_rows, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(twitter_rows)} Twitter rows to {twitter_path}")
print("Done.")
