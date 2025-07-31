import streamlit as st
import boto3
import json

st.set_page_config(page_title="CoffeeBot ☕", layout="centered")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Branding and Reset Chat button (in main window)
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown("<h2 style='color: #BB9F78FF;'>Welcome To</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 50px; color: #BB9F78FF;'>Merry's Way Coffee Shop ☕</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 18px; color: #9F9A93FF;'>Built by Ishant</p>", unsafe_allow_html=True)
with col2:
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# Custom styling
st.markdown("""
<style>
    .stChatMessage { 
        background-color: #653E3EFF; 
        padding: 10px; 
        border-radius: 10px; 
        margin-bottom: 10px;
    }
    .stCaption {
        color: #999999;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Create Lambda client using Streamlit secrets
lambda_client = boto3.client(
    "lambda",
    aws_access_key_id=st.secrets["aws_access_key_id"],
    aws_secret_access_key=st.secrets["aws_secret_access_key"],
    region_name=st.secrets["aws_region"]
)
# Chat input
if prompt := st.chat_input("Type your coffee question here..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # chat_context = [
    #     {"role": msg["role"], "content": msg["content"]}
    #     for msg in st.session_state.chat_history
    #     if msg["role"] in ["user", "assistant"]
    # ][-4:]  # Only the last 4 messages

    # # Payload with limited memory context
    # payload = {
    #     "input": {
    #         "messages": chat_context
    #     }
    # }
    # Extract last 3 user messages (if any) + current prompt
    previous_user_prompts = [
        msg["content"] for msg in st.session_state.chat_history
        if msg["role"] == "user"
    ][-3:]  # Only last 3 previous user messages

    # Append the current prompt
    chat_context = previous_user_prompts + [prompt]

    # Prepare payload as per Lambda expectation
    payload = {
        "input": {
            "messages": chat_context  # List of strings
        }
    }

    # payload = { "input": { "messages": [prompt] } }

    try:
        response = lambda_client.invoke(
            FunctionName='coffee_chatbot_docker_function2',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload),
        )
        response_payload = response["Payload"].read().decode("utf-8")
        response_json = json.loads(response_payload)

        if response_json.get("statusCode") == 200:
            body = response_json.get("body")
            if isinstance(body, str):
                body = json.loads(body)

            bot_reply = body.get("content", "⚠️ No reply received.")
            agent_used = body.get("memory", {}).get("agent", "Unknown")

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": bot_reply,
                "agent": agent_used
            })

            with st.chat_message("assistant"):
                st.markdown(bot_reply)
                st.caption(f"🧠 Agent used: `{agent_used}`")
        else:
            error_msg = "⚠️ Something went wrong."
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "agent": "none"
            })
            with st.chat_message("assistant"):
                st.markdown(error_msg)

    except Exception as e:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"⚠️ Error: {e}",
            "agent": "none"
        })
        with st.chat_message("assistant"):
            st.markdown(f"⚠️ Error: {e}")
