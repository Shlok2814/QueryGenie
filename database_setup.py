import sqlite3
import random
import datetime

conn = sqlite3.connect("sales.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales(
    id INTEGER PRIMARY KEY,
    product TEXT,
    amount INTEGER,
    date TEXT
)
""")

products = ["Laptop", "Phone", "Tablet"]

for i in range(200):
    cursor.execute(
        "INSERT INTO sales(product, amount, date) VALUES (?, ?, ?)",
        (
            random.choice(products),
            random.randint(100, 2000),
            datetime.date(2024, random.randint(1,12), random.randint(1,28))
        )
    )

conn.commit()
conn.close()

print("Database ready!")
