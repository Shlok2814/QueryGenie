import sqlite3
import re
from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate


# Load model
llm = OllamaLLM(model="phi3")

# Connect DB
db = SQLDatabase.from_uri("sqlite:///sales.db")

# Strict prompt
prompt = PromptTemplate.from_template("""
You are a SQLite SQL generator.

ONLY output ONE valid SQL SELECT query.

Rules:
- Only SQL
- No explanation
- No comments
- No markdown
- Must start with SELECT
- Must end with semicolon

Schema:
{schema}

Question:
{question}

SQL:
""")

chain = prompt | llm


# Clean SQL
def clean_sql(text):
    text = text.replace("```sql", "").replace("```", "")
    match = re.search(r"SELECT[\\s\\S]*?;", text, re.IGNORECASE)
    return match.group(0).strip() if match else text.strip()


# Execute SQL
def execute_sql(query):
    conn = sqlite3.connect("sales.db")
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return rows


# Main loop
print("\n🚀 Text-to-SQL Ready")
print("Type 'exit' to quit\n")

while True:
    question = input("Ask question (or type exit): ")

    if question.lower() == "exit":
        break

    raw_sql = chain.invoke({
        "schema": db.get_table_info(),
        "question": question
    })

    sql = clean_sql(raw_sql)

    print("\nGenerated SQL:")
    print(sql)

    try:
        result = execute_sql(sql)
        print("\nResult:")
        print(result)

    except Exception as e:
        print("\n❌ SQL Error:", e)
