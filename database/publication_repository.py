import psycopg
from dotenv import load_dotenv
import os

class PublicationRepository:
    def __init__(self):
        load_dotenv()
        self.db_url = os.getenv("DATABASE_URL")

    def insert_raw_publications(self, publications):
        if not publications:return
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                for publication in publications:
                    try:
                        with conn.transaction(): 
                            cursor.execute("""
                                INSERT INTO accommodation_publication 
                                    (link, 
                                    source, 
                                    description, 
                                    state, 
                                    date_posted, 
                                    date_crawler)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (link) DO NOTHING
                            """, 
                            (
                                publication.get("Link"), 
                                publication.get("Source"), 
                                publication.get("Description"),
                                publication.get("State"), 
                                publication.get("Date of processing"), 
                                publication.get("Date of publishing")
                            ))
                    except Exception as e:
                        print(f"DB(accommodation_publication) INSERT ERROR: {e}")
                        if conn.broken: break

    def select_raw_publications(self, number):
        try:
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""SELECT id, description 
                                FROM accommodation_publication 
                                WHERE state = 'raw' 
                                LIMIT %s""", (number,))
                    return cursor.fetchall()
        except Exception as e:
            print(f"DB(accommodation_publication) SELECT ERROR: {e}")
            return []
                
    def update_raw_publications(self, postings, postings_extracted_info):
        if not postings or not postings_extracted_info: return
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                for posting, info in zip(postings, postings_extracted_info):
                    if info is None: 
                        try:
                            with conn.transaction():
                                cursor.execute("""UPDATE accommodation_publication
                                               SET state = 'error'
                                               WHERE id = %s""", (posting[0],))
                        except Exception as e:
                            print(f"DB(accommodation_publication) ERROR while setting 'error' state: {e}")
                            if conn.broken: break
                        continue
                    try:
                        with conn.transaction():
                            cursor.execute("""UPDATE accommodation_publication
                                            SET state = 'processed', 
                                                price = %s, 
                                                rooms = %s, 
                                                area_sqm = %s, 
                                                address = %s, 
                                                city = %s
                                            WHERE id = %s""", 
                                            (info.get('price'),
                                            info.get('rooms'),
                                            info.get('area_sqm'),
                                            info.get('address'),
                                            info.get('city'),
                                            posting[0]))
                    except Exception as e:
                        print(f"DB(accommodation_publication) UPDATE ERROR: {e}")
                        if conn.broken: break