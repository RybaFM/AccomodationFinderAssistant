import psycopg
from schemas import PublicationState

class PublicationRepository:
    def __init__(self, db_url):
        self.db_url = db_url

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
                                publication.get("Date of publishing"), 
                                publication.get("Date of processing")
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
                                WHERE state = %s 
                                LIMIT %s""", (PublicationState.RAW.value, number))
                    return cursor.fetchall()
        except Exception as e:
            print(f"DB(accommodation_publication) SELECT ERROR: {e}")
            return []
                
    def update_raw_publications(self, publications, publications_extracted_info):
        if not publications or not publications_extracted_info: return
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                for publication, info in zip(publications, publications_extracted_info):
                    try:
                        with conn.transaction():
                            # NEED TO THINK ABOUT THIS PART
                            if info is None: 
                                self.set_error_state(publication[0], cursor)
                                continue

                            cursor.execute("""UPDATE accommodation_publication
                                            SET state = %s, 
                                                price = %s, 
                                                rooms = %s, 
                                                area_sqm = %s, 
                                                address = %s, 
                                                city = %s
                                            WHERE id = %s""", 
                                            (PublicationState.LLM_PROCESSED.value, 
                                            info.get('price'),
                                            info.get('rooms'),
                                            info.get('area_sqm'),
                                            info.get('address'),
                                            info.get('city'),
                                            publication[0]))
                    except Exception as e:
                        print(f"DB(accommodation_publication) UPDATE ERROR: {e}")
                        if conn.broken: break
        
    def set_error_state(self, id, cursor):
        cursor.execute("""UPDATE accommodation_publication
            SET state = %s
            WHERE id = %s""", (PublicationState.ERROR.value, id))