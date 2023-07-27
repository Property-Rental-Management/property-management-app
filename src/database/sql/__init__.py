from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import config_instance

settings = config_instance().MYSQL_SETTINGS
# Replace 'your_username', 'your_password', 'your_host', and 'your_database' with your MySQL database credentials
engine = create_engine(settings.DEVELOPMENT_DB)
Session = sessionmaker(bind=engine)
session = Session()


Base = declarative_base()
