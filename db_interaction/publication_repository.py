import psycopg
from schemas.schemas import PublicationState, ApartmentRawFeatures, ApartmentLLMFeatures, ApartmentGeoFeatures
import logging
logger = logging.getLogger(__name__)

class PublicationRepository:
    def __init__(self, db_url):
        self.db_url = db_url

    def insert_raw_publications(self, publications: list[ApartmentRawFeatures]):
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
                                publication.link, 
                                publication.source.value, 
                                publication.description,
                                publication.state.value, 
                                publication.scraping_date, 
                                publication.posted_date
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
        
    def select_llm_processed_publications(self, number=20):
        try:
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""SELECT id, building, street, district, city, country
                                   FROM accomodation_publication
                                   WHERE state = %s
                                   LIMIT %s""", 
                                   (PublicationState.LLM_PROCESSED.value, number))
                    return cursor.fetchall()
        except Exception:
            logger.exception("DB(accommodation_publication) SELECT ERROR")
            return []
        
    def set_error_state(self, cursor, id):
        cursor.execute("""UPDATE accommodation_publication
            SET state = %s
            WHERE id = %s""", (PublicationState.ERROR.value, id))
        
    def set_fully_processed_state(self, cursor, id):
        cursor.execute("""UPDATE accommodation_publication
            SET state = %s
            WHERE id = %s""", (PublicationState.FULLY_PROCESSED.value, id))
                
    def update_raw_publications(self, publications_extracted_info: list[tuple[int, ApartmentLLMFeatures | None]]):
        if not publications_extracted_info: return
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                for (publication_id, info) in publications_extracted_info:
                    try:
                        if info is None: 
                            with conn.transaction():    
                                self.set_error_state(cursor, publication_id)
                            continue

                        with conn.transaction():
                            cursor.execute("""UPDATE accommodation_publication
                                            SET state = %s, 
                                                price = %s, 
                                                rooms = %s, 
                                                area_sqm = %s, 
                                                building = %s,
                                                street = %s,
                                                district = %s, 
                                                city = %s,
                                                country = %s
                                            WHERE id = %s""", 
                                            (PublicationState.LLM_PROCESSED.value, 
                                            info.price,
                                            info.rooms,
                                            info.area_sqm,
                                            info.building,
                                            info.street,
                                            info.district,
                                            info.city,
                                            info.country,
                                            publication_id))
                    except Exception:
                        logger.exception("DB(accommodation_publication) UPDATE ERROR")
                        if conn.broken: break

    def update_llm_processed_publications(self, publications_extracted_info: list[tuple[int, ApartmentGeoFeatures | None]]): 
        if not publications_extracted_info: return
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                for (publication_id, info) in publications_extracted_info:
                    try:
                        if info is None: 
                            with conn.transaction():    
                                self.set_fully_processed_state(cursor, publication_id)
                            continue

                        with conn.transaction():
                            cursor.execute("""UPDATE accommodation_publication
                                            SET state = %s, 
                                                distance_to_center = %s, 
                                                distance_to_shopping_mall = %s, 
                                                nearest_shopping_mall_name = %s, 
                                                distance_to_supermarket = %s,
                                                nearest_supermarket_name = %s,
                                                distance_to_transport_stop = %s, 
                                                nearest_transport_stop_name = %s
                                            WHERE id = %s""", 
                                            (PublicationState.FULLY_PROCESSED.value, 
                                            info.distance_to_center,
                                            info.distance_to_shopping_mall,
                                            info.nearest_shopping_mall_name,
                                            info.distance_to_supermarket,
                                            info.nearest_supermarket_name,
                                            info.distance_to_transport_stop,
                                            info.nearest_transport_stop_name,
                                            publication_id))
                    except Exception:
                        logger.exception("DB(accommodation_publication) UPDATE ERROR")
                        if conn.broken: break