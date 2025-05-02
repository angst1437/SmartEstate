import psycopg2
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor

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

