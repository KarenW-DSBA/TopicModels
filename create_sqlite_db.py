import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        conn.text_factory = str #necessary to prevent UTF-8 encoding errors
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn

def get_unscraped_urls(c):
    c.execute("SELECT * FROM urls where scraped=0;")
    return c.fetchall()

if __name__=='__main__':
    conn = create_connection("C:/sqlite/db/pythonsqlite.db")
    c = conn.cursor()
    unscraped_urls = get_unscraped_urls(c)
    print(unscraped_urls)