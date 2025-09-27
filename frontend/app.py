import streamlit as st
import requests

st.set_page_config(page_title="MongoDB NLP Chatbot", layout="wide")
st.title("MongoDB NLP Chatbot")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_input("Ask me anything about your data:")

if st.button("Send") and user_input:
    response = requests.post(
        "http://127.0.0.1:8080/chat",
        json={"question": user_input}
    )
    answer = response.json()["answer"]
    
    # Save chat history
    st.session_state.history.append({"user": user_input, "bot": answer})

# Display chat history
for chat in st.session_state.history:
    st.markdown(f"**You:** {chat['user']}")
    st.markdown(f"**Bot:** {chat['bot']}")
