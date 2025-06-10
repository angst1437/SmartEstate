import sqlite3
import os
print("Current working directory:", os.getcwd())

conn = sqlite3.connect("links.db")
cur = conn.cursor()
cur.execute("SELECT buy_link from links LIMIT 1;")
print(cur.fetchone())