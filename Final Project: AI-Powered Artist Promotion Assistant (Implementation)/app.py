import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# -------------------------------
# Paths & Config
# -------------------------------
DATA_DIR = "data"
LOG_DIR = "logs"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

INSTA_PATH = os.path.join(DATA_DIR, "instagram_sample.csv")
TWITTER_PATH = os.path.join(DATA_DIR, "twitter_sample.json")
LOG_PATH = os.path.join(LOG_DIR, "actions_log.csv")

HIGH_VALUE_KEYWORDS = [
    "commission", "buy", "price", "prints", "print",
    "gallery", "curator", "collector", "feature", "represent"
]


# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="ArtConnect AI - Opportunity Dashboard",
    layout="wide"
)

st.title("🎨 ArtConnect AI – Artist Promotion Assistant (POC)")
st.write(
    "This Streamlit app loads simulated Instagram and Twitter interactions, "
    "scores them with a rule-based Opportunity Scoring Engine, and suggests "
    "brand-aligned replies for the artist to Approve, Edit, or Reject."
)


# -------------------------------
# Data Loading
# -------------------------------
@st.cache_data
def load_data():
    # Load Instagram CSV
    insta_df = pd.read_csv(INSTA_PATH)

    # Load Twitter JSON
    with open(TWITTER_PATH, "r", encoding="utf-8") as f:
        twitter_data = json.load(f)
    twitter_df = pd.DataFrame(twitter_data)

    # Combine both platforms into one DataFrame
    raw_df = pd.concat([insta_df, twitter_df], ignore_index=True)

    return insta_df, twitter_df, raw_df


# -------------------------------
# Scoring & Preprocessing
# -------------------------------
@st.cache_data
def preprocess_and_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add features and compute a 0–100 Opportunity Score for each interaction.
    Rule-based, aligned with the technical documentation.
    """
    df = df.copy()
    analyzer = SentimentIntensityAnalyzer()

    # Keyword factor K: 1 if any high-value keyword appears in the text, else 0
    def keyword_factor(text: str) -> int:
        t = str(text).lower()
        return int(any(kw in t for kw in HIGH_VALUE_KEYWORDS))

    df["keyword_factor"] = df["text_content"].apply(keyword_factor)

    # Sentiment factor S: map VADER compound [-1,1] to [0,1], only positive contributes
    def sentiment_factor(text: str) -> float:
        scores = analyzer.polarity_scores(str(text))
        compound = scores["compound"]
        if compound <= 0:
            return 0.0
        return (compound + 1.0) / 2.0  # 0 to 1

    df["sentiment_factor"] = df["text_content"].apply(sentiment_factor)

    # User influence U: normalize follower count to [0,1]
    max_followers = df["user_followers"].max() if df["user_followers"].max() > 0 else 1
    df["user_influence"] = df["user_followers"] / max_followers

    # Recency factor R: newer = closer to 1, older within ~30 days decays toward 0
    def recency_factor(ts_str: str, days_window: int = 30) -> float:
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return 0.5  # fallback
        now = datetime.now()
        days_diff = (now - ts).days
        if days_diff <= 0:
            return 1.0
        if days_diff >= days_window:
            return 0.0
        return 1.0 - (days_diff / days_window)

    df["recency_factor"] = df["timestamp"].apply(recency_factor)

    # Weights from your technical documentation
    W_K = 0.50  # Keyword presence
    W_S = 0.30  # Sentiment
    W_U = 0.15  # User influence
    W_R = 0.05  # Recency

    # Apply scoring formula
    raw_score = (
        df["keyword_factor"] * W_K
        + df["sentiment_factor"] * W_S
        + df["user_influence"] * W_U
        + df["recency_factor"] * W_R
    )

    df["opportunity_score"] = (raw_score * 100).clip(0, 100).round(1)

    # Sort by score descending
    df = df.sort_values(by="opportunity_score", ascending=False).reset_index(drop=True)

    return df


# -------------------------------
# Reply Generator (Brand Voice)
# -------------------------------
def generate_reply(row: pd.Series) -> str:
    """
    Very simple, template-based reply generator aligned with your 'brand voice':
    professional, appreciative, and focused on opportunities.
    """
    user = row.get("user_handle", "@collector")
    text = str(row.get("text_content", "")).lower()

    # Decide type based on keywords
    if any(kw in text for kw in ["commission", "buy", "price", "prints", "print"]):
        return (
            f"Thank you so much for your interest, {user}! "
            "I’d be happy to talk more about a commission or print options. "
            "Could you please send me a message or email with a bit more detail about what you have in mind?"
        )

    if any(kw in text for kw in ["gallery", "curator", "collector", "represent", "feature"]):
        return (
            f"Hi {user}, I really appreciate you reaching out. "
            "I’d love to learn more about your gallery/collection and see if my work could be a good fit. "
            "Feel free to contact me so we can talk more about it."
        )

    # Default: simple praise / general positive comment
    return (
        f"Thank you so much, {user}! "
        "I really appreciate your kind words and support. "
        "This piece was inspired by my love for color and texture, "
        "so it means a lot that it resonated with you."
    )


# -------------------------------
# Logging Human Decisions
# -------------------------------
def init_log_file():
    if not os.path.exists(LOG_PATH):
        df = pd.DataFrame(
            columns=[
                "timestamp",
                "interaction_id",
                "platform",
                "user_handle",
                "action",          # APPROVE / EDIT / REJECT
                "original_reply",
                "final_reply",
            ]
        )
        df.to_csv(LOG_PATH, index=False)


def log_action(row: pd.Series, action: str, original_reply: str, final_reply: str):
    init_log_file()
    log_df = pd.read_csv(LOG_PATH)

    new_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "interaction_id": row["interaction_id"],
        "platform": row["platform"],
        "user_handle": row["user_handle"],
        "action": action,
        "original_reply": original_reply,
        "final_reply": final_reply,
    }

    log_df = pd.concat([log_df, pd.DataFrame([new_row])], ignore_index=True)
    log_df.to_csv(LOG_PATH, index=False)


def load_logs() -> pd.DataFrame:
    if not os.path.exists(LOG_PATH):
        init_log_file()
    return pd.read_csv(LOG_PATH)


# -------------------------------
# Main App Logic
# -------------------------------
try:
    insta_df, twitter_df, raw_df = load_data()
    scored_df = preprocess_and_score(raw_df)
    logs_df = load_logs()
    data_loaded = True
except Exception as e:
    st.error("❌ Failed to load or process data. Make sure you ran generate_fake_data.py.")
    st.exception(e)
    data_loaded = False


if data_loaded:
    # Precompute some shared metrics
    total_count = len(scored_df)
    insta_count = (scored_df["platform"] == "Instagram").sum()
    twitter_count = (scored_df["platform"] == "Twitter").sum()
    high_value_count = (scored_df["opportunity_score"] >= 50).sum()

    approve_count = (logs_df["action"] == "APPROVE").sum()
    edit_count = (logs_df["action"] == "EDIT").sum()
    reject_count = (logs_df["action"] == "REJECT").sum()
    acted_on_count = approve_count + edit_count + reject_count

    if acted_on_count > 0:
        approval_rate = (approve_count + edit_count) / acted_on_count * 100
    else:
        approval_rate = 0.0

    # -------------------------------
    # Tabs: Opportunities & Analytics
    # -------------------------------
    tab_ops, tab_analytics = st.tabs(["🎯 Opportunities", "📊 Analytics"])

    # ===============================
    # 🎯 OPPORTUNITIES TAB
    # ===============================
    with tab_ops:
        st.subheader("📊 Platform & Score Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Interactions", total_count)
        col2.metric("Instagram Interactions", insta_count)
        col3.metric("Twitter Interactions", twitter_count)
        col4.metric("High-Value (Score ≥ 50)", high_value_count)

        st.divider()

        # Filters
        st.subheader("🔎 Filter Opportunities")

        col_f1, col_f2 = st.columns([1, 1])

        with col_f1:
            selected_platform = st.selectbox(
                "Platform",
                options=["All", "Instagram", "Twitter"],
            )

        with col_f2:
            min_score = st.slider(
                "Minimum Opportunity Score",
                min_value=0,
                max_value=100,
                value=50,
                step=5,
                help="Focus on higher-value leads by increasing the minimum score.",
            )

        filtered = scored_df.copy()
        if selected_platform != "All":
            filtered = filtered[filtered["platform"] == selected_platform]
        filtered = filtered[filtered["opportunity_score"] >= min_score]

        st.write(f"Showing {len(filtered)} interactions with score ≥ {min_score}:")

        display_cols = [
            "interaction_id",
            "platform",
            "timestamp",
            "user_handle",
            "user_followers",
            "text_content",
            "keyword_factor",
            "sentiment_factor",
            "user_influence",
            "recency_factor",
            "opportunity_score",
        ]
        st.dataframe(filtered[display_cols].head(50))

        st.divider()

        # Human-in-the-loop review panel
        st.subheader("🧑‍🎨 Review & Respond (Human-in-the-Loop)")

        if filtered.empty:
            st.info("No interactions match the current filters. Try lowering the minimum score.")
        else:
            # Let user pick one interaction to review
            def row_label(idx):
                row = filtered.loc[idx]
                preview = row["text_content"]
                if len(preview) > 60:
                    preview = preview[:60] + "..."
                return f"{row['interaction_id']} | {row['platform']} | {row['user_handle']} | {preview}"

            selected_index = st.selectbox(
                "Select an interaction to review:",
                options=filtered.index.tolist(),
                format_func=row_label,
            )

            row = filtered.loc[selected_index]

            # Show details
            st.markdown("**Interaction Details:**")
            st.write(f"**Platform:** {row['platform']}")
            st.write(f"**User:** {row['user_handle']}  |  Followers: {row['user_followers']}")
            st.write(f"**Timestamp:** {row['timestamp']}")
            st.write(f"**Text:** {row['text_content']}")
            st.write(f"**Opportunity Score:** {row['opportunity_score']}")

            # Draft reply
            st.markdown("**AI-Suggested Reply (Brand Voice):**")
            default_reply = generate_reply(row)

            edited_reply = st.text_area(
                "You can edit the reply before approving:",
                value=default_reply,
                height=150,
            )

            col_a, col_b, col_c = st.columns(3)

            if col_a.button("✅ Approve", key=f"approve_{row['interaction_id']}"):
                log_action(row, "APPROVE", default_reply, edited_reply)
                st.success("Approved and logged. Go to the Analytics tab to see updated metrics.")

            if col_b.button("✏️ Edit & Approve", key=f"edit_{row['interaction_id']}"):
                log_action(row, "EDIT", default_reply, edited_reply)
                st.success("Edited, approved, and logged. Go to the Analytics tab to see updated metrics.")

            if col_c.button("❌ Reject", key=f"reject_{row['interaction_id']}"):
                log_action(row, "REJECT", default_reply, edited_reply)
                st.warning("Rejected and logged. Go to the Analytics tab to see updated metrics.")

        st.caption(
            "Opportunities Tab – Prioritize and respond to high-value interactions."
        )

    # ===============================
    # 📊 ANALYTICS TAB
    # ===============================
    with tab_analytics:
        st.subheader("📈 Overview KPIs")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Interactions Scanned", total_count)
        c2.metric("High-Value Opportunities (Score ≥ 50)", high_value_count)
        c3.metric("Total Logged Actions", acted_on_count)
        c4.metric("Approval Rate (Approve + Edit)", f"{approval_rate:.1f}%")

        st.markdown(
            "_These KPIs connect directly to the Business & Performance Analysis report (e.g., ~25 opportunities out of 240 and ~85% approval rate)._"  # for your instructor
        )

        st.divider()

        # Engagement Funnel (bar chart)
        st.subheader("🔻 Engagement Funnel (POC)")

        replied_count = approve_count + edit_count

        funnel_df = pd.DataFrame({
            "Stage": [
                "Total Interactions",
                "High-Value (Score ≥ 50)",
                "Replied (Approved or Edited)",
            ],
            "Count": [total_count, high_value_count, replied_count],
        }).set_index("Stage")

        st.bar_chart(funnel_df)

        st.caption(
            "Funnel: From all scanned interactions → AI-flagged high-value opportunities → "
            "human-approved or edited replies."
        )

        st.divider()

        # Action breakdown chart
        st.subheader("✅ / ✏️ / ❌ Action Breakdown")

        if acted_on_count == 0:
            st.info("No logged actions yet. Use the Opportunities tab to review and approve/edit/reject replies.")
        else:
            action_counts = pd.Series(
                {
                    "APPROVE": approve_count,
                    "EDIT": edit_count,
                    "REJECT": reject_count,
                }
            )
            st.bar_chart(action_counts)

            st.caption("This shows how often the AI suggestions are accepted as-is, edited, or rejected.")

        st.divider()

        # Recent log table
        st.subheader("📜 Recent Logged Decisions")

        if logs_df.empty:
            st.info("No actions logged yet.")
        else:
            st.write("Most recent actions:")
            st.dataframe(logs_df.tail(15))

        st.caption(
            "Analytics Tab – Demonstrates system performance and human-in-the-loop oversight "
            "for your final presentation."
        )

    # -------------------------------
    # Global Footer
    # -------------------------------
    st.caption(
        "ArtConnect AI – Proof of Concept | Simulated Instagram & Twitter Data | "
        "Creative Intelligence Co. (CIC) | Client: Joe Fleishman"
    )
