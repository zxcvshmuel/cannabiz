import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import os
import re

# Set up Google Gemini AI
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
genai.configure(api_key=st.secrets["google"])
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

    - **Focus on the 'description' column:** This column contains a mix of general information, user reviews, and disclaimers about the product's effects.
    - **Use for the name "heb_name" or "eng_name" for the product name column.**
    - **Return a valid SQL query:** Ensure the query is syntactically correct and adheres to SQLite's syntax rules.
    - **Omit explanations or extraneous information:** Provide only the SQL query itself.
    - **Show all the data in human lnguage in addition to the boolet points.
    - **Examples of potential questions:**
        - What are the common effects of Sativa strains according to user reviews?
        - Which products are mentioned as being suitable for beginners?
        
    - ** Example of data inside the description: שימו לב: אתר קנאביז לא מכיל תיאורים שיווקיים לזנים כדוגמת השפעות בריאותיות ואחרות משום שאלו לעיתים קרובות מטעים, בלתי מבוססים ולמעשה – אסורים. במקום זה, אתם מוזמנים ללמוד על השפעות הזן דרך הביקורות שהשאירו מטופלים אחרים, וגם להוסיף ביקורת משלכם אם ניסיתם אותו.
איך הזן משפיע?השפעות הזן משתנות ותלויות הרבה בצרכן ובמגוון פרמטרים. לפי משרד הבריאות, מוצרי קנאביס מסוג סאטיבה הינם בעלי אופי של מתן הרגשה אנרגטית, מספקים תחושה "קלילה", משפרים את מצב הרוח ומגבירים את יכולת הריכוז והיצירתיות, ועל כן מתאימים יותר לשימוש בשעות היום. יש לציין שהסיווג של זני קנאביס לקטגוריות אינדיקה, סאטיבה והיבריד שנוי במחלוקת (פרטים נוספים כאן).מוצרי קנאביס בעלי ריכוז THC של מעל 14% נחשבים כבעלי השפעה פסיכואקטיבית חזקה, ומתאימים יותר למטופלי קנאביס מנוסים. השפעת הקנאביס עשויה להשתנות גם בהתאם לריכוז החומרים הפעילים האחרים בו, כמו טרפנים.על חברת פארמוקן (Pharmocann)פארמוקן (Pharmocann), מחברות הקנאביס הותיקות בישראל, הוקמה ב-2008 והחלה להיסחר בבורסה הישראלית בשנת 2019.פארמוקן מתנהלת החל משנת 2023 באמצעות חברת "פארמוקן שיווק בע"מ", שמחזיקה ברישיון עיסוק בקנאביס ללא מגע (רישיון "אחר" / קונסטרוקטיבי).בעבר ולאורך כעשור היא החזיקה בחוות גידול קנאביס בישוב ציפורי שבצפון הארץ, ומאז שנת 2021 גם מפעילה בית מרקחת לקנאביס בעפולה בשם קליניקאן.בנובמבר 2021 התפטר מתפקידו יו"ר החברה דני גילרמן שעמד בראש החברה מאז נובמבר 2019. במקומו מונה לתפקיד פרופ' זאב רוטשטיין, מנכ"ל לשעבר של בית החולים הדסה בירושלים.בשנת 2021 הפסידה פארמוקן 9 מיליון שקל, בשנת 2022 חתמה על שת"פ עם חברת פלאנטיס של יעקב שחר במסגרתו חוות פלאנטיס תגדל קנאביס עבור פארמוקן. במקביל חתמה על שת"פ גם עם חוות עין חצבה.פרופ' זאב רוטשטיין ומנכ"ל החברה גיל חובש הודחו מתפקידם בהמשך, ובמסגרת הנפקת מניות השתלט על הדירקטוריון המשקיע יריב לרנר שהפך לבעל השליטה בפועל בחברה.בחודש ינואר 2023 נסגרה סופית חוות הגידול של פארמוקן והיא איבדה את רישיונות הריבוי והגידול שלה. במקום זאת היא קיבלה רישיון קונסטרוקטיבי למסחר ותיווך קנאביס בעיסוק ללא מגע ומפיצה זני קנאביס הגדלים בחוות פלאנטיס שבמושב קשת ועין חצבה.מוצרים נוספים של פארמוקן (Pharmocann)

    **Example:**

    If the columns are "product_id", "product_name", "description", and "price", and the question is "What are the common effects of Sativa strains according to user reviews?", the expected output might be:

    ```sql
    SELECT description FROM products WHERE description LIKE '%Sativa%' AND description LIKE '%effects%';

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
