# create_tables.py
from utils.database_sqlalchemy import create_tables
from utils.database_sqlalchemy import engine

def main():
    create_tables()
    print("Tables created in DB:", engine.url)

if __name__ == "__main__":
    main()
