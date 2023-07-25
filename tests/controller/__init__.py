from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+pymysql://root:11111111@localhost:3306/rental_manager')
Session = sessionmaker(bind=engine)
