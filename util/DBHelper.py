from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()

class DBHelper:
    @staticmethod
    def _unpack_dbconfig(db_config: dict) -> list:
        """Распаковывает db_config"""
        user = db_config.get('user', 'postgres')
        password = db_config.get('password', '')
        host = db_config.get('host', 'localhost')
        db_name = db_config['db_name']
        port = db_config.get('port', '')
        return [user, password, host, db_name, port]

    @staticmethod
    def _get_table(db_name: str):
        model_registry = {
            model.__tablename__: model
            for model in Base.__subclasses__()
        }

        return model_registry[db_name.title()]


    def __init__(self, db_config: dict):
        user, password, host, db_name, port = self._unpack_dbconfig(db_config)
        self.engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db_name}")
        self.session_factory = sessionmaker(bind=self.engine) # фабрика сессий
        self.Session = scoped_session(self.session_factory) # управление сессиями
        self.table = self._get_table(db_name)


    def get_session(self):
        """Возвращает сессию для работы с бд"""
        return self.Session()

    def close(self):
        """Закрывает соединения"""
        self.Session.remove()
        self.engine.dispose()

    def add_data(self, data_dict):
        """
        Добавляет одну запись в БД
        :param data_dict: словарь с данными
        :return: созданный объект(для отладки)
        """
        session = self.Session()

        try:

            new_item = self.table(**data_dict)

            session.add(new_item)
            session.commit()
            session.refresh(new_item)

            return new_item
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all(self):
        """
        Получает все записи из таблицы
        """
        session = self.Session()

        try:
            return session.query(self.table).all()
        finally:
            session.close()

    def get_query(self, query):
        # ПОКА НЕ РАБОТАЕТ
        pass

    def create_table_cian(self):
        """Создать таблицу Циана"""
        Cian.__table__.create(bind=self.engine)

    def create_table_avito(self):
        """Создать таблицу авито"""
        Avito.__table__.create(bind=self.engine)



class Cian(Base):
    __tablename__ = 'cian_data'

    link = Column(String, primary_key=True)
    address = Column(String)
    price =Column(String)
    photos = Column(ARRAY(String))
    description = Column(String)
    factoids = Column(ARRAY(String))
    summary = Column(ARRAY(String))
    type = Column(String)
    page = Column(Integer)
    latitude = Column(REAL)
    longitude = Column(REAL)

class Avito(Base):
    __tablename__ = 'avito_data'
    # ПОКА НЕ РАБОТАЕТ
    pass