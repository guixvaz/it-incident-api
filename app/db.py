from sqlmodel import Session, SQLModel, create_engine

#Define the SQLite database file name and URL
sqlite_file_name = "it_service_desk.db"
sqlite_url = f"sqlite:///./{sqlite_file_name}"

# Create the database engine
engine = create_engine(sqlite_url,echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables() -> None:
    """Create the database and tables based on the defined SQLModel models.
    """
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    """Provide a database session for interacting with the database.
    
    Yields:
        Session: A SQLModel session for database operations.
    """
    with Session(engine) as session:
        yield session