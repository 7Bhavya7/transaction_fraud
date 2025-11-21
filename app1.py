import json
import streamlit as st
import google.generativeai as genai

# -----------------------------
#  HARDCODE YOUR GEMINI API KEY
# -----------------------------
GEMINI_API_KEY = "AIzaSyDI6mmaaD4Y_v_lo_zJMWLH_XS37bbn3T8"   # ← Replace this with your real key

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash"

st.set_page_config(page_title="Fraud Detection", page_icon="🕵️")


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
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(build_fraud_prompt(transaction))

        raw = (response.text or "").strip()

        try:
            return json.loads(raw)
        except:
            return {
                "fraud_label": "UNKNOWN",
                "fraud_score": None,
                "reason": f"Could not parse JSON. Raw output: {raw}",
            }

    except Exception as e:
        return {
            "fraud_label": "ERROR",
            "fraud_score": None,
            "reason": f"Gemini API error: {str(e)}",
        }


# --------------------- UI ----------------------

st.title("🕵️ Real-Time Fraud Detection (Gemini API)")
st.write("Fill in transaction details and click Predict Fraud.")

col1, col2 = st.columns(2)

with col1:
    amount = st.number_input("Amount", min_value=0.0, step=1.0, value=100.0)
    currency = st.text_input("Currency", value="USD")
    merchant = st.text_input("Merchant", value="Example Store")
    country = st.text_input("Country", value="US")

with col2:
    user_id = st.text_input("User ID", value="U001")
    card_present = st.checkbox("Card Present")
    prev_fraud = st.number_input("Previous Fraud Count", min_value=0, step=1, value=0)
    timestamp = st.text_input("Timestamp", value="2025-11-21T10:30:00Z")

extra = st.text_area("Additional JSON Fields", value="{}")

st.markdown("---")

if st.button("🔍 Predict Fraud"):
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
            st.warning("Extra fields must be JSON object.")
    except:
        st.warning("Invalid JSON in Additional Fields.")

    with st.spinner("Analyzing transaction using Gemini…"):
        result = predict_fraud(tx)

    st.subheader("Prediction Result")

    label = result.get("fraud_label")
    score = result.get("fraud_score")
    reason = result.get("reason")

    if label == "FRAUD":
        st.error(f"🚨 FRAUD DETECTED")
    elif label == "NOT_FRAUD":
        st.success("✅ Transaction is NOT FRAUD")
    else:
        st.warning(f"⚠️ {label}")

    if score is not None:
        st.write(f"Fraud Score: `{score}`")

    st.write("**Reason:**")
    st.write(reason)

    st.expander("Transaction JSON").json(tx)
    st.expander("Raw Model Output").json(result)

else:
    st.info("Provide details and click **Predict Fraud**.")
