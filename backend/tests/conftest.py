import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)

    # 创建默认测试用户并设置请求头
    db: Session = TestingSessionLocal()
    test_user = User(name="测试用户", is_active=True, is_demo=False)
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    db.close()

    with TestClient(app) as c:
        c.headers.update({"X-User-Id": str(test_user.id)})
        yield c

    Base.metadata.drop_all(bind=engine)
