import streamlit as st
import pandas as pd
import plotly.express as px
import os
import google.generativeai as genai

# --- Load CSV data ---
data_file = os.path.join("data", "UPi_dataframe.csv")
df = pd.read_csv(data_file)

# --- Convert numeric columns ---
numeric_cols = ["amount (INR)", "hour_of_day", "is_weekend", "fraud_flag"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df.columns = df.columns.str.strip()

# --- Streamlit App ---
st.title("UPI Customer Transaction Dashboard")

# --- Predefined Questions ---
predefined_questions = {
    "Total Transaction Amount": lambda df: df["amount (INR)"].sum(),
    "Average Transaction Amount": lambda df: df["amount (INR)"].mean(),
    "Maximum Transaction Amount": lambda df: df["amount (INR)"].max(),
    "Minimum Transaction Amount": lambda df: df["amount (INR)"].min(),
    "Transactions by Type": lambda df: df.groupby("transaction type")["transaction id"].count().reset_index(name="count"),
    "Transactions by Merchant Category": lambda df: df.groupby("merchant_category")["transaction id"].count().reset_index(name="count"),
    "Top 5 Merchants by Transaction Amount": lambda df: df.groupby("merchant_category")["amount (INR)"].sum().reset_index().sort_values("amount (INR)", ascending=False).head(5),
    "Fraudulent Transactions Count": lambda df: df["fraud_flag"].sum(),
    "Transactions by Sender Age Group": lambda df: df.groupby("sender_age_group")["transaction id"].count().reset_index(name="count"),
    "Transactions by Receiver Age Group": lambda df: df.groupby("receiver_age_group")["transaction id"].count().reset_index(name="count"),
    "Transactions by Day of Week": lambda df: df.groupby("day_of_week")["transaction id"].count().reset_index(name="count"),
    "Transactions by Hour of Day": lambda df: df.groupby("hour_of_day")["transaction id"].count().reset_index(name="count"),
    "Weekend vs Weekday Transactions": lambda df: df.groupby("is_weekend")["transaction id"].count().reset_index(name="count"),
    "Transactions by Sender State": lambda df: df.groupby("sender_state")["transaction id"].count().reset_index(name="count"),
    "Transactions by Receiver Bank": lambda df: df.groupby("receiver_bank")["transaction id"].count().reset_index(name="count"),
    "Amount Distribution Histogram": lambda df: df["amount (INR)"],
    "Transactions by Device Type": lambda df: df.groupby("device_type")["transaction id"].count().reset_index(name="count"),
    "Transactions by Network Type": lambda df: df.groupby("network_type")["transaction id"].count().reset_index(name="count"),
}

# --- Sidebar ---
st.sidebar.header("Select a Predefined Question")
selected_question = st.sidebar.selectbox("Choose a question", ["None"] + list(predefined_questions.keys()))

st.sidebar.header("Ask a Question (NLP Chatbot)")
user_query = st.sidebar.text_input("Type your question (e.g., total transactions for Delhi):")

# --- Display Charts & KPIs ---
def display_charts(result, question_name):
    if isinstance(result, pd.DataFrame) and not result.empty:
        st.dataframe(result)
        if "count" in result.columns:
            x_col = [c for c in result.columns if c != "count"][0]
            st.plotly_chart(px.bar(result, x=x_col, y="count", title=f"{question_name} (Bar Chart)"))
            st.plotly_chart(px.pie(result, names=x_col, values="count", title=f"{question_name} (Pie Chart)"))
        elif "amount (INR)" in result.columns:
            x_col = "merchant_category" if "merchant_category" in result.columns else result.columns[0]
            st.plotly_chart(px.bar(result, x=x_col, y="amount (INR)", title=f"{question_name} (Bar Chart)"))
            st.plotly_chart(px.line(result, x=x_col, y="amount (INR)", title=f"{question_name} (Line Chart)"))
    elif isinstance(result, pd.Series) and numeric_cols[0] in result.name:
        st.plotly_chart(px.histogram(result, x=result.name, nbins=30, title=f"{question_name} (Histogram)"))
    else:
        st.metric(question_name, round(result, 2))

# --- Compute Predefined Question ---
if selected_question != "None":
    result = predefined_questions[selected_question](df)
    st.subheader(f"Results for: {selected_question}")
    display_charts(result, selected_question)

# --- NLP + Gemini Integration for Data Analysis ---
def analyze_query_with_gemini(query):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
    You are a data analysis assistant. The user asked: "{query}".
    Return ONE Python pandas command to execute on the dataframe 'df' to answer it.
    Example: df.shape[0] for total rows, df['amount (INR)'].sum() for total amount.
    Only give code, no explanation.
    """

    response = model.generate_content(prompt)
    return response.text.strip()

# --- Execute User Query ---
if user_query:
    st.subheader("Chatbot Answer")
    try:
        code_to_run = analyze_query_with_gemini(user_query)
        st.write(f"Generated Code: `{code_to_run}`")

        try:
            answer = eval(code_to_run)  # Run the code on dataframe
            st.success(f"Answer: {answer}")
        except:
            st.warning("Couldn't run the generated code. Showing AI answer only.")
            st.write(code_to_run)

    except Exception as e:
        st.error(f"Error with Chatbot: {e}")
