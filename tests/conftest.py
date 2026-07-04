import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from app.api.routers.rentals import get_publisher
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.repositories.car_repo import CarRepository
from app.repositories.rental_repo import RentalRepository
from app.services.car_service import CarService
from app.services.rental_service import RentalService

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

    # Application code (services) calls session.commit(). Nest everything in a
    # SAVEPOINT so a "commit" only ends the savepoint, not the outer `transaction`
    # below — otherwise the first commit in a test would end the connection's
    # transaction early and the final rollback() would be a no-op, leaking data
    # into the real drivenow_test database instead of isolating each test.
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    yield session

    event.remove(session, "after_transaction_end", _restart_savepoint)
    session.close()
    # A flush failure inside a test (e.g. the concurrent-rental IntegrityError
    # path) already tears down the outer transaction via session.rollback().
    if transaction.is_active:
        transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass
            
    # API tests must not publish real events to the shared broker —
    # swap the RabbitMQ publisher for an in-memory fake.
    fake = FakePublisher()

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_publisher] = lambda: fake
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class FakePublisher:
    """Stands in for the real RabbitMQ publisher so
    services can be tested without a broker running."""

    def __init__(self):
        self.events = []

    def publish(self, routing_key, body):
        self.events.append((routing_key, body))


@pytest.fixture
def fake_publisher():
    return FakePublisher()


@pytest.fixture
def car_repo(db_session):
    return CarRepository(db_session)


@pytest.fixture
def rental_repo(db_session):
    return RentalRepository(db_session)


@pytest.fixture
def car_service(car_repo):
    return CarService(car_repo)


@pytest.fixture
def rental_service(car_repo, rental_repo, fake_publisher):
    return RentalService(car_repo, rental_repo, publisher=fake_publisher)
