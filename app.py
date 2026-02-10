import streamlit as st
import pandas as pd
import sqlite3
import re

from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate



st.set_page_config(
    page_title="Universal Text → SQL",
    layout="wide",
    page_icon=""
)

st.markdown("""
#  Universal Text → SQL Generator
### Upload ANY dataset → Ask questions → Get SQL + Results + Charts
""")

st.divider()



with st.sidebar:
    st.header("⚙ Controls")
    st.write("1. Upload file")
    st.write("2. Ask question")
    st.write("3. View SQL + output")

    st.info("Works with ANY CSV / Excel file")



file = st.file_uploader(
    "📂 Upload CSV or Excel",
    type=["csv", "xlsx"]
)

if file is None:
    st.warning("⬆ Please upload a dataset to start")
    st.stop()



if file.name.endswith(".csv"):
    df = pd.read_csv(file)
else:
    df = pd.read_excel(file)


# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Rows", df.shape[0])
c2.metric("Columns", df.shape[1])
c3.metric("File", file.name)


# Preview
with st.expander("📄 Preview Data"):
    st.dataframe(df.head(20), use_container_width=True)



conn = sqlite3.connect("temp.db")

df.to_sql(
    name="data",
    con=conn,
    if_exists="replace",
    index=False
)



llm = OllamaLLM(
    model="phi3",
    temperature=0,
    num_ctx=2048
)

db = SQLDatabase.from_uri("sqlite:///temp.db")


prompt = PromptTemplate.from_template("""
You are a professional SQLite SQL generator.

Rules:
- Only output ONE valid SQL SELECT query
- No explanation
- No markdown
- Must start with SELECT
- Must end with semicolon
- Use only the provided table

Schema:
{schema}

Question:
{question}

SQL:
""")

chain = prompt | llm



def clean_sql(text):
    text = text.replace("```sql", "").replace("```", "")
    match = re.search(r"SELECT[\s\S]*?;", text, re.IGNORECASE)
    return match.group(0).strip() if match else text.strip()



st.divider()
st.subheader("💬Ask your question")

question = st.text_input(
    "Example: total revenue, top products, average price, count rows, etc"
)


if st.button(" Generate SQL & Result") and question:

    try:
        schema = db.get_table_info()[:3000]

        raw_sql = chain.invoke({
            "schema": schema,
            "question": question
        })

        sql = clean_sql(raw_sql)

       
        st.subheader("🧾 Generated SQL")
        editable_sql = st.text_area(
            "Edit if needed:",
            value=sql,
            height=100
        )


       
        result = pd.read_sql_query(editable_sql, conn)


       
        st.subheader("📊 Result Table")
        st.dataframe(result, use_container_width=True)


     
        st.subheader("📈 Visualization")

        numeric_cols = result.select_dtypes(include="number").columns

        if len(numeric_cols) > 0 and len(result) > 0:
            chart_type = st.selectbox(
                "Choose chart type",
                ["Bar Chart", "Line Chart"]
            )

            if chart_type == "Bar Chart":
                st.bar_chart(result[numeric_cols])

            else:
                st.line_chart(result[numeric_cols])
        else:
            st.info("No numeric columns available for chart")


      
        csv = result.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download Result CSV",
            csv,
            "result.csv",
            "text/csv"
        )


       
        with st.expander("🗂 View Table Schema"):
            st.code(schema)


    except Exception as e:
        st.error(f"❌ Error: {e}")
