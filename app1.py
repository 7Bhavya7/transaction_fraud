import json
import streamlit as st
import google.generativeai as genai
import pandas as pd

# -----------------------------
#  HARDCODE YOUR MODEL API KEY
# -----------------------------
# ⚠️ Apna real key yahan daalo, is file ko public repo me mat daalna
MODEL_API_KEY = "AIzaSyDI6mmaaD4Y_v_lo_zJMWLH_XS37bbn3T8"

# Configure model client
genai.configure(api_key=MODEL_API_KEY)

MODEL_NAME = "gemini-1.5-flash"

st.set_page_config(page_title="Fraud Detection System", page_icon="🕵️")


def build_fraud_prompt(transaction: dict) -> str:
    return f"""
You are a fraud detection assistant.

Given this transaction, classify it as FRAUD or NOT_FRAUD.

Return JSON with:
- "fraud_label": "FRAUD" or "NOT_FRAUD"
- "fraud_score": float 0-1
- "reason": short explanation

Transaction:
{json.dumps(transaction, indent=2)}
"""


def predict_fraud(transaction: dict) -> dict:
    """
    Backend model call – UI me kahin bhi model ka naam nahi dikhaya jaata.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(build_fraud_prompt(transaction))

        raw = (response.text or "").strip()

        try:
            return json.loads(raw)
        except Exception:
            return {
                "fraud_label": "UNKNOWN",
                "fraud_score": None,
                "reason": f"Could not parse JSON from model output. Raw output: {raw}",
            }

    except Exception as e:
        # Generic error – koi model / API ka naam UI me nahi aayega
        return {
            "fraud_label": "ERROR",
            "fraud_score": None,
            "reason": f"Internal model error: {str(e)}",
        }


# --------------------- UI ----------------------

st.title("🕵️ Real-Time Fraud Detection System")
st.write("Fill in transaction details or upload a CSV file to check for potential fraud.")


# --------- Single Transaction Form ----------

st.subheader("Single Transaction Check")

col1, col2 = st.columns(2)

with col1:
    amount = st.number_input("Amount", min_value=0.0, step=1.0, value=100.0)
    currency = st.text_input("Currency", value="USD")
    merchant = st.text_input("Merchant", value="Example Store")
    country = st.text_input("Country", value="US")

with col2:
    user_id = st.text_input("User ID", value="U001")
    card_present = st.checkbox("Card Present (in-person transaction)", value=False)
    prev_fraud = st.number_input("Previous Fraud Count", min_value=0, step=1, value=0)
    timestamp = st.text_input("Timestamp (ISO 8601)", value="2025-11-21T10:30:00Z")

extra = st.text_area(
    "Additional JSON Fields (optional)",
    value="{}",
    help='Example: {"ip_address": "1.2.3.4", "device_id": "abc123"}',
)

st.markdown("---")

if st.button("🔍 Predict Fraud for This Transaction"):
    tx = {
        "amount": amount,
        "currency": currency,
        "merchant": merchant,
        "country": country,
        "user_id": user_id,
        "card_present": card_present,
        "previous_fraud_history": prev_fraud,
        "timestamp": timestamp,
    }

    # Merge extra JSON
    try:
        extra_json = json.loads(extra)
        if isinstance(extra_json, dict):
            tx.update(extra_json)
        else:
            st.warning("Additional fields must be a valid JSON object.")
    except Exception:
        st.warning("Invalid JSON in Additional Fields. Ignoring these fields.")

    with st.spinner("Analyzing transaction..."):
        result = predict_fraud(tx)

    st.subheader("Prediction Result")

    label = result.get("fraud_label")
    score = result.get("fraud_score")
    reason = result.get("reason")

    if label == "FRAUD":
        st.error("🚨 FRAUD DETECTED")
    elif label == "NOT_FRAUD":
        st.success("✅ Transaction is NOT FRAUD")
    elif label == "ERROR":
        st.error(f"❌ {reason}")
    else:
        st.warning(f"⚠️ {label}")

    if score is not None:
        st.write(f"**Fraud Score:** `{score}` (0 = safe, 1 = very likely fraud)")

    st.markdown("**Reason:**")
    st.write(reason)

    with st.expander("View transaction JSON"):
        st.json(tx)

    with st.expander("View model response JSON"):
        st.json(result)
else:
    st.info("Fill the details above and click **Predict Fraud for This Transaction**.")


# --------- Bulk CSV Upload Section ----------

st.markdown("---")
st.subheader("📂 Bulk Fraud Check via CSV Upload")

uploaded_file = st.file_uploader("Upload CSV file with transactions", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of Uploaded Data")
    st.dataframe(df.head())

    if st.button("🚀 Predict Fraud for All Rows in CSV"):
        results = []

        with st.spinner("Analyzing all transactions..."):
            for _, row in df.iterrows():
                transaction = row.to_dict()
                result = predict_fraud(transaction)

                results.append({
                    **transaction,
                    "fraud_label": result.get("fraud_label"),
                    "fraud_score": result.get("fraud_score"),
                    "reason": result.get("reason"),
                })

        result_df = pd.DataFrame(results)

        st.success("✅ Predictions completed for all rows!")
        st.write("### Results")
        st.dataframe(result_df)

        # Optionally allow download as CSV
        csv_data = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Results as CSV",
            data=csv_data,
            file_name="fraud_predictions.csv",
            mime="text/csv",
        )
else:
    st.info("Upload a CSV file to run bulk fraud predictions.")
