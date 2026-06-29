import psycopg2
from dotenv import load_dotenv
import os

class PublicationRepository:
    def __init__(self):
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cursor = self.conn.cursor()
    def add_publication(self,publication):
        self.cursor.execute("""
                INSERT INTO accommodation_publication (link, source, description, state, date_posted, date_crawler)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (link) DO NOTHING
            """, (
            publication["Link"],
            publication["Source"],
            publication["Description"],
            publication["State"],
            publication["Date of processing"],
            publication["Date of publishing"],
        ))
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()
