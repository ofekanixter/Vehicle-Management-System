import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

def create_test_db_if_not_exists():
    db_url = settings.DATABASE_URL
    # Find the database name at the end of the URL
    base_url, db_name = db_url.rsplit("/", 1)
    # Check if there is query parameters
    if "?" in db_name:
        db_name = db_name.split("?", 1)[0]
    
    test_db_name = f"{db_name}_test"
    postgres_url = f"{base_url}/postgres"
    
    # Connect to 'postgres' database to create the new database
    temp_engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    with temp_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{test_db_name}'"))
        if not result.scalar():
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
    temp_engine.dispose()
    
    # Return the test database URL
    if "?" in db_url.rsplit("/", 1)[1]:
        parts = db_url.rsplit("/", 1)
        db_part = parts[1].split("?", 1)
        new_db_part = f"{test_db_name}?{db_part[1]}"
        test_url = f"{parts[0]}/{new_db_part}"
    else:
        test_url = f"{base_url}/{test_db_name}"
    return test_url

@pytest.fixture(scope="session")
def test_engine():
    test_url = create_test_db_if_not_exists()
    engine = create_engine(test_url)
    
    # Create all tables in the test database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = _get_db_override
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
