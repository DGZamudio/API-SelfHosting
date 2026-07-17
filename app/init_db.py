from app.database import engine, Base
from app import models

def init():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init()