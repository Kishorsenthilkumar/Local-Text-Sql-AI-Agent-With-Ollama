# streamlit_app.py

import streamlit as st
import requests
import pandas as pd
import json
import os

# --- Configuration ---
# Define the URL of your FastAPI backend
# Make sure your FastAPI app.py is running on this address and port
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/query-database")

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="SQL AI Agent (Ollama Local LLM)",
    layout="wide", # Use wide layout for better dashboard experience
    initial_sidebar_state="expanded"
)

# --- Title and Introduction ---
st.title("💡 SQL AI Agent (Ollama Local LLM)")
st.markdown("""
Welcome to the **AI-powered SQL Agent**! Ask your data questions in natural language,
and I'll generate and execute the SQL query for you. All processing is done locally
using **Ollama** and **ChromaDB** for enhanced data security and privacy.
""")

st.divider()

# --- User Input Section ---
st.header("Ask Your Database a Question")
user_question = st.text_area(
    "Enter your natural language query here:",
    placeholder="e.g., Show me the names and salaries of employees in the 'Sales' department.",
    height=100,
    key="user_query_input"
)

# Button to trigger the query
if st.button("Generate & Execute SQL", key="execute_button"):
    if user_question.strip() == "":
        st.warning("Please enter a question before clicking the button.")
    else:
        # Display a spinner while processing
        with st.spinner("Processing your request... (Generating SQL & Fetching Data)"):
            try:
                # Prepare the payload for the FastAPI backend
                payload = {"natural_language_query": user_question}

                # Make the POST request to your FastAPI backend
                response = requests.post(BACKEND_URL, json=payload)
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
                
                # Parse the JSON response from the backend
                data = response.json()
                generated_sql = data.get("sql_query", "No SQL query generated.")
                query_result = data.get("query_result", [])

                st.success("Query processed successfully!")

                # --- Display Generated SQL ---
                st.subheader("Generated SQL Query:")
                st.code(generated_sql, language="sql")

                # --- Display Query Results ---
                st.subheader("Query Results:")
                if query_result:
                    # Convert list of dicts to Pandas DataFrame for nice display
                    df_results = pd.DataFrame(query_result)
                    st.dataframe(df_results, use_container_width=True)
                    
                    # Optional: Add simple visualization if data is numeric
                    if not df_results.empty and pd.api.types.is_numeric_dtype(df_results.iloc[:, -1]):
                        st.line_chart(df_results.set_index(df_results.columns[0]))
                else:
                    st.info("No results found for this query or the query returned an empty set.")

            except requests.exceptions.ConnectionError:
                st.error(f"Failed to connect to the backend server at {BACKEND_URL}. Please ensure your FastAPI app (app.py) is running.")
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred during the request to the backend: {e}")
                if response.status_code == 500:
                    st.error(f"Backend Error Details: {response.json().get('detail', 'No details provided.')}")
            except json.JSONDecodeError:
                st.error("Received an invalid JSON response from the backend. Check backend logs.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

st.divider()
st.caption("Architecture: Streamlit (Frontend) ➡️ FastAPI (Backend) ➡️ Langflow (AI Workflow) ➡️ Ollama (LLM) + ChromaDB (Vector DB) ➡️ Your Database")

