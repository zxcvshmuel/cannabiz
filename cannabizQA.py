import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import os
import re

# Set up Google Gemini AI
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
genai.configure("env:GOOGLE_API_KEY")
model = genai.GenerativeModel('gemini-pro')

# Function to get column names from the database
def get_column_names():
    conn = sqlite3.connect('cannabizData.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns

# Function to generate SQL query using AI
def generate_sql_query(question, columns):
    prompt = f"""
    Given the following columns in a 'products' table: {', '.join(columns)}

    **Prompt:**

    Generate a SQLite query to answer this question: "{question}".

    **Instructions:**

    - **Use for the name "heb_name" or "eng_name" for the product name column.
    - **Return a valid SQL query:** Ensure the query is syntactically correct and adheres to SQLite's syntax rules.
    - **Omit explanations or extraneous information:** Provide only the SQL query itself.
    - **Show all the data in human lnguage in addition to the boolet points.

    **Example:**

    If the columns are "product_id", "product_name", and "price", and the question is "What is the average price of products?", the expected output would be:

    ```sql
    SELECT AVG(price) FROM products;
    ```
    """
    response = model.generate_content(prompt)
    

    # Remove "```sql" and "```"
    filtered_query = re.sub(r'```sql|```|sql', '', response.text)
    
    select_index = filtered_query.find("SELECT")

    # Find the index of the first occurrence of ";"
    semicolon_index = filtered_query.find(";")

    # Extract the SQL query from "SELECT" to the first semicolon
    sql_query = filtered_query[select_index:semicolon_index + 1]

    return sql_query.strip()

# Function to execute SQL query and return results
def execute_query(query):
    conn = sqlite3.connect('cannabizData.db')
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Function to get AI response based on data and question
def get_ai_response(question, df):
    context = f"Here's the data retrieved from the database:\n{df.to_string()}\n\nQuestion: {question}\n\nAnswer:"
    response = model.generate_content(context)
    return response.text

# Streamlit app
st.title('Cannabis Product Data Q&A')

# Get column names
columns = get_column_names()

# User input
user_question = st.text_input('Ask a question about the cannabis product data:')

if user_question:
    # Step 1: Generate SQL query
    with st.spinner('Generating SQL query...'):
        sql_query = generate_sql_query(user_question, columns)
    st.subheader('Generated SQL Query:')
    st.code(sql_query, language='sql')

    # Step 2: Execute SQL query
    with st.spinner('Executing query...'):
        try:
            result_df = execute_query(sql_query)
            st.subheader('Query Results:')
            st.dataframe(result_df)
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")
            st.stop()

    # Step 3 & 4: Get AI response and present to user
    with st.spinner('Generating answer...'):
        ai_response = get_ai_response(user_question, result_df)
    st.subheader('AI Response:')
    st.write(ai_response)

# Option to show all column names
if st.checkbox('Show all column names'):
    st.write(columns)
