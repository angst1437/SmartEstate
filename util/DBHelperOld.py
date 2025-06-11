import psycopg2
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
from psycopg2.extras import execute_values

class DBHelper:
    def __init__(self, dbname, dbpassword, dbhost="localhost", dbport=5432, dbuser="postgres"):
        self.conn_params = {
            "host": dbhost,
            "port": dbport,
            "database": dbname,
            "user": dbuser,
            "password": dbpassword
        }

    @contextmanager
    def connect(self):
        conn = psycopg2.connect(
            host=self.conn_params["host"],
            port=self.conn_params["port"],
            database=self.conn_params["database"],
            user=self.conn_params["user"],
            password=self.conn_params["password"]
        )
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute(self, query, params=None):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)

    def fetch_one(self, query, params=None):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()

    def fetch_all(self, query, params=None):
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def insert_bulk(self, query, links, params=None):
        with self.connect() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, [(link,) for link in links], params)

    def insert_ad(self, data):
        with self.connect() as conn:
            with conn.cursor() as cur:
                city = data["address"][0] if data.get("address") else None

                cur.execute("""
                            INSERT INTO pages (link, city, address, price, photos, description, factoids, summary,
                                                  type, page)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """, (
                                data.get("link"),
                                city,
                                data.get("address"),
                                data.get("price"),
                                data.get("photos"),  # Список (массив строк)
                                data.get("description"),
                                data.get("factoids"),  # Список (массив строк)
                                data.get("summary"),  # Список (массив строк)
                                data.get("type"),
                                data.get("page")
                            ))

    def insert_ads_bulk(self, data_list: list):
        if not data_list:
            return

        values = []
        for data in data_list:
            city = data["address"][0] if data.get("address") else None
            values.append((
                data.get("link"),
                city,
                data.get("address"),
                data.get("price"),
                data.get("photos"),
                data.get("description"),
                data.get("factoids"),
                data.get("summary"),
                data.get("type"),
                data.get("page")
            ))

        query = """
                INSERT INTO pages (link, city, address, price, photos, description, factoids, summary, type, page)
                VALUES \
                %s
            ON CONFLICT \
                DO NOTHING \
                """

        with self.connect() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, values)
