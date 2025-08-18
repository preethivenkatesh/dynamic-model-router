import os, json, requests, streamlit as st

BASE_URL = os.getenv("LITELLM_URL", "http://localhost:4000/v1")  # e.g. http://litellm.NAMESPACE.svc.cluster.local:4000/v1
DEFAULT_MODEL = os.getenv("MODEL_NAME", "auto")

st.set_page_config(page_title="LiteLLM UI", layout="centered")
st.title("RedHat Openshift AI on Intel® Xeon and Intel® Gaudi")
st.markdown("<span style='font-size:16px;'>This demo showcases how Red Hat OpenShift AI can deploy and run LLM inference on both Intel Xeon and Intel Gaudi hardware. Using a routing technique, it demonstrates how hardware choices are made based on prompt complexity.</span>", unsafe_allow_html=True)

# 👇 USER TYPES PROMPT HERE
prompt = st.text_area("Your Prompt", "What is artificial intelligence?")

model = st.text_input("Model", value=DEFAULT_MODEL)
max_tokens = st.number_input("Max tokens", min_value=1, max_value=8192, value=100)
temperature = st.number_input("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)

if st.button("Send"):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],   # 👈 prompt comes from UI
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "stream": False
    }
    try:
        r = requests.post(f"{BASE_URL.rstrip('/')}/chat/completions",
                          headers={"Content-Type":"application/json"},
                          data=json.dumps(body), timeout=60)
        data = r.json()
        used_model = data.get("model", "unknown")
        final_hw= "Intel® Xeon®" if "simple-xeon" in used_model.lower() else "Intel® Gaudi™"
        selected_model = data.get("extra_body", {}).get("selected_model")    
        if data.get("choices"):
            content = data["choices"][0]["message"].get("content", "")
        st.markdown(f"**Hardware Choice** `{final_hw}`")
        st.markdown("**Output:**")
        st.write(content)
    except Exception as e:
        st.error(f"Error: {e}")

