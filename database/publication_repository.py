import psycopg
from schemas import PublicationState, ApartmentLLMFeatures
import logging
logger = logging.getLogger(__name__)

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
                    except Exception:
                        logger.exception("DB(accommodation_publication) INSERT ERROR")
                        if conn.broken: break

    def select_raw_publications(self, number=20):
        try:
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""SELECT id, description 
                                FROM accommodation_publication 
                                WHERE state = %s 
                                LIMIT %s""", (PublicationState.RAW.value, number))
                    return cursor.fetchall()
        except Exception:
            logger.exception("DB(accommodation_publication) SELECT ERROR")
            return []
                
    def update_raw_publications(self, publications_extracted_info: list[tuple[int, ApartmentLLMFeatures | None]]):
        if not publications_extracted_info: return
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                for (publication_id, info) in publications_extracted_info:
                    try:
                        if info is None: 
                            with conn.transaction():    
                                self.set_error_state(publication_id, cursor)
                            continue

                        with conn.transaction():
                            cursor.execute("""UPDATE accommodation_publication
                                            SET state = %s, 
                                                price = %s, 
                                                rooms = %s, 
                                                area_sqm = %s, 
                                                address = %s, 
                                                city = %s
                                            WHERE id = %s""", 
                                            (PublicationState.LLM_PROCESSED.value, 
                                            info.price,
                                            info.rooms,
                                            info.area_sqm,
                                            info.address,
                                            info.city,
                                            publication_id))
                    except Exception:
                        logger.exception("DB(accommodation_publication) UPDATE ERROR")
                        if conn.broken: break
        
    def set_error_state(self, cursor, id):
        cursor.execute("""UPDATE accommodation_publication
            SET state = %s
            WHERE id = %s""", (PublicationState.ERROR.value, id))