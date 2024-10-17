import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

import config

engine = db.create_engine(config.DB_URL, connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Генератор подключений к бд
def get_connection():
    connection = Session()
    try:
        yield connection
    except Exception as e:
        print(e)
        raise
    finally:
        connection.close()


class Base(DeclarativeBase):
    ...
