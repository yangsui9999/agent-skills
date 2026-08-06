---
name: api-design-fastapi
description: Use when implementing REST APIs with FastAPI. Triggers on FastAPI project setup, route handlers, Pydantic models, dependency injection, authentication, testing, Docker deployment. Covers uv package management, TOML config, async patterns, SQLAlchemy 2.0, Alembic migrations, pytest-asyncio, GitHub Actions CI.
---

# FastAPI API 实现规范

> **强制依赖：本规范必须遵循 `api-design-principles`（API 设计总纲）。** URL 设计、HTTP 方法/状态码、错误响应格式、分页约定等以总纲为准，本文档仅提供 FastAPI 框架的具体实现模式。若发现本文档与总纲冲突，以总纲为准。

**技术栈**: FastAPI 0.128+, Pydantic 2.x, SQLAlchemy 2.0, Python 3.12+, uv, pytest-asyncio

## 项目结构

按层划分，职责清晰：

```
project-root/
├── app/
│   ├── main.py                  # 应用入口
│   ├── api/                     # API 路由层
│   │   ├── deps.py              # 共享依赖（认证、DB会话）
│   │   └── v1/
│   │       ├── __init__.py      # 注册路由
│   │       ├── auth.py
│   │       ├── classes.py
│   │       ├── tasks.py
│   │       └── hsk.py
│   ├── core/                    # 基础设施
│   │   ├── config.py            # TOML 配置加载
│   │   ├── database.py          # 数据库连接
│   │   ├── security.py          # JWT 验证
│   │   └── logging.py           # 结构化日志
│   ├── models/                  # SQLAlchemy ORM
│   │   ├── __init__.py          # 导出所有模型
│   │   ├── base.py              # Base 类
│   │   ├── user.py
│   │   ├── class_.py            # class 是关键字
│   │   ├── task.py
│   │   └── hsk.py
│   ├── schemas/                 # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── common.py            # 分页、错误响应
│   │   ├── auth.py
│   │   ├── class_.py
│   │   ├── task.py
│   │   └── hsk.py
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── class_service.py
│   │   ├── task_service.py
│   │   └── hsk_service.py
│   ├── repositories/            # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py              # BaseRepository
│   │   ├── user_repository.py
│   │   ├── class_repository.py
│   │   ├── task_repository.py
│   │   └── hsk_repository.py
│   ├── exceptions/
│   │   └── business.py          # 业务异常
│   └── middleware/
│       └── error_handler.py     # 全局异常处理
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── configs/
│   ├── config.example.toml
│   ├── config.local.toml        # .gitignore
│   ├── config.dev.toml
│   └── config.prod.toml         # .gitignore
├── tests/
│   ├── conftest.py
│   ├── test_api/
│   └── test_services/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── scripts/
│   └── seed_hsk.py
├── alembic.ini
├── pyproject.toml
├── Makefile
└── README.md
```

## 分层架构

```
┌─────────────────────────────────────────────────────────┐
│  API Layer (api/v1/*.py)                                │
│  - 路由定义、参数校验、响应序列化                          │
│  - 调用 Service，不包含业务逻辑                           │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Service Layer (services/*.py)                          │
│  - 业务逻辑、权限校验、跨表操作                           │
│  - 调用 Repository，可调用其他 Service                   │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Repository Layer (repositories/*.py)                   │
│  - 数据访问、CRUD 操作                                   │
│  - 只操作自己负责的表，不跨表                             │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Database (SQLAlchemy ORM)                              │
└─────────────────────────────────────────────────────────┘
```

**跨域调用规则：**
- Repository：只操作自己的表，不跨域
- Service：可调用其他 Service（注意避免循环依赖）
- 复杂聚合查询：API 层组装或专用 Query 类

## uv 包管理

```toml
# pyproject.toml
[project]
name = "zidome-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.128.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.11.0",
    "pydantic-settings>=2.0.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "PyJWT[crypto]>=2.9.0",
    "httpx>=0.27.0",
    "tomli>=2.0.0",
    "structlog>=24.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.11.0",
    "ruff>=0.6.0",
    "aiosqlite>=0.20.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
```

## TOML 多环境配置

```toml
# configs/config.example.toml
[app]
name = "zidome-api"
version = "1.0.0"
debug = true
host = "127.0.0.1"
port = 8000

[database]
url = "postgresql+asyncpg://user:pass@localhost:5432/zidome"
pool_size = 10
max_overflow = 20
echo = false

[security]
secret_key = "change_this_secret_key_in_production"
algorithm = "HS256"
access_token_expire_minutes = 10080  # 7 days

[logging]
level = "INFO"
format = "json"  # simple / json
```

```python
# app/core/config.py
import tomli
from pydantic import BaseModel
from functools import lru_cache
from pathlib import Path
import os

class AppConfig(BaseModel):
    name: str
    version: str
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000

class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

class SecurityConfig(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"

class Settings(BaseModel):
    app: AppConfig
    database: DatabaseConfig
    security: SecurityConfig
    logging: LoggingConfig

@lru_cache
def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT", "local")
    config_path = Path(f"configs/config.{env}.toml")
    with open(config_path, "rb") as f:
        data = tomli.load(f)
    return Settings(**data)
```

## 数据库连接

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    echo=settings.database.echo,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## Repository 层

```python
# app/repositories/base.py
from datetime import UTC, datetime
from typing import TypeVar, Generic
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, db: AsyncSession, model: type[T]):
        self.db = db
        self.model = model

    async def get_by_id(self, id: UUID) -> T | None:
        return await self.db.get(self.model, id)

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> list[T]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def soft_delete(self, instance: T) -> T:
        """默认删除方式：软删除（设置 deleted_at）"""
        instance.deleted_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def hard_delete(self, instance: T) -> None:
        """物理删除：仅用于明确需要硬删除的场景（如账号删除）"""
        await self.db.delete(instance)
        await self.db.flush()
```

```python
# app/repositories/class_repository.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.class_ import Class
from app.repositories.base import BaseRepository

class ClassRepository(BaseRepository[Class]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Class)

    async def get_by_invite_code(self, code: str) -> Class | None:
        stmt = select(Class).where(
            Class.invite_code == code,
            Class.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_teacher(self, teacher_id: UUID) -> list[Class]:
        stmt = select(Class).where(
            Class.teacher_id == teacher_id,
            Class.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

## Service 层

```python
# app/services/class_service.py
from uuid import UUID
import secrets
from app.repositories.class_repository import ClassRepository
from app.repositories.user_repository import UserRepository
from app.schemas.class_ import ClassCreate, ClassResponse
from app.exceptions.business import NotFoundError, ForbiddenError

class ClassService:
    def __init__(
        self,
        class_repo: ClassRepository,
        user_repo: UserRepository,  # 可依赖其他 Repository
    ):
        self.class_repo = class_repo
        self.user_repo = user_repo

    async def create_class(self, teacher_id: UUID, data: ClassCreate) -> ClassResponse:
        # 验证教师存在
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher or teacher.role != "teacher":
            raise ForbiddenError("仅教师可创建班级")

        # 生成邀请码
        invite_code = secrets.token_hex(4).upper()

        db_class = await self.class_repo.create(
            teacher_id=teacher_id,
            name=data.name,
            invite_code=invite_code,
        )
        return ClassResponse.model_validate(db_class)

    async def get_class(self, class_id: UUID) -> ClassResponse:
        db_class = await self.class_repo.get_by_id(class_id)
        if not db_class or db_class.deleted_at:
            raise NotFoundError("班级不存在")
        return ClassResponse.model_validate(db_class)
```

## 依赖注入

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.class_repository import ClassRepository
from app.services.auth_service import AuthService
from app.services.class_service import ClassService

security = HTTPBearer()

# Repository 依赖
def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_class_repo(db: AsyncSession = Depends(get_db)) -> ClassRepository:
    return ClassRepository(db)

# Service 依赖
def get_auth_service(user_repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(user_repo)

def get_class_service(
    class_repo: ClassRepository = Depends(get_class_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> ClassService:
    return ClassService(class_repo, user_repo)

# 认证依赖
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail={"code": "unauthorized", "message": "无效的访问令牌"})
    return user

async def require_teacher(user = Depends(get_current_user)):
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "仅教师可执行此操作"})
    return user
```

## API 路由

```python
# app/api/v1/classes.py
from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user, require_teacher, get_class_service
from app.schemas.class_ import ClassCreate, ClassResponse
from app.services.class_service import ClassService

router = APIRouter(prefix="/classes", tags=["classes"])

@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    data: ClassCreate,
    teacher = Depends(require_teacher),
    class_service: ClassService = Depends(get_class_service),
):
    """创建班级（仅教师）"""
    return await class_service.create_class(teacher.id, data)

@router.get("", response_model=list[ClassResponse])
async def list_my_classes(
    current_user = Depends(get_current_user),
    class_service: ClassService = Depends(get_class_service),
):
    """获取我的班级列表"""
    return await class_service.get_user_classes(current_user.id, current_user.role)
```

## 异常处理

```python
# app/exceptions/business.py
from fastapi import HTTPException, status

class AppError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})

class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__("not_found", message, status.HTTP_404_NOT_FOUND)

class ForbiddenError(AppError):
    def __init__(self, message: str = "无权限"):
        super().__init__("forbidden", message, status.HTTP_403_FORBIDDEN)

class ValidationError(AppError):
    def __init__(self, message: str, details: list = None):
        super().__init__("validation_error", message, status.HTTP_400_BAD_REQUEST)

class RoleMismatchError(AppError):
    def __init__(self, message: str):
        super().__init__("role_mismatch", message, status.HTTP_403_FORBIDDEN)

class AlreadyExistsError(AppError):
    def __init__(self, message: str = "资源已存在"):
        super().__init__("already_exists", message, status.HTTP_409_CONFLICT)
```

## Alembic 迁移

```python
# alembic/env.py（关键部分）
from app.core.config import get_settings
from app.core.database import Base
from app.models import *  # 导入所有模型

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database.url.replace("+asyncpg", ""))
target_metadata = Base.metadata
```

迁移文件命名：`{YYYY_MM_DD}_{seq}_{description}.py`

## 测试

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.api.deps import get_current_user
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def mock_teacher():
    return User(id="uuid-teacher", email="teacher@test.com", role="teacher", name="测试老师")

@pytest.fixture
async def auth_client(client, mock_teacher):
    app.dependency_overrides[get_current_user] = lambda: mock_teacher
    yield client
    app.dependency_overrides.clear()
```

```python
# tests/test_api/test_classes.py
import pytest

class TestCreateClass:
    async def test_success(self, auth_client):
        response = await auth_client.post("/api/v1/classes", json={"name": "HSK1"})
        assert response.status_code == 201
        assert response.json()["name"] == "HSK1"
        assert len(response.json()["invite_code"]) == 8

    async def test_unauthorized(self, client):
        response = await client.post("/api/v1/classes", json={"name": "Test"})
        assert response.status_code == 401
```

## Docker

```dockerfile
# docker/Dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./configs ./configs
COPY ./alembic.ini ./
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker/docker-compose.yml
services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=dev
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: zidome
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --dev

      - name: Lint
        run: |
          uv run ruff check app tests
          uv run mypy app

      - name: Test
        run: uv run pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

## Makefile

```makefile
.PHONY: dev test lint db-migrate

# 开发
dev:
	uv run fastapi dev app/main.py

# 测试
test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=html

# 代码检查
lint:
	uv run ruff check app tests
	uv run mypy app

format:
	uv run ruff format app tests

# 数据库
db-migrate:
	uv run alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	uv run alembic upgrade head

db-downgrade:
	uv run alembic downgrade -1

# Docker
docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

# 安装依赖
install:
	uv sync --dev
```

## Git 规范

**分支模型：**
- `main`: 稳定分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复
- `release/*`: 发布分支

**提交信息（Conventional Commits）：**
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档修改
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建或辅助工具

## 已知问题防护

| 问题 | 解决方案 |
|------|----------|
| Form + Pydantic metadata 丢失 | 用 JSON body |
| BackgroundTasks 覆盖 | 只用一种机制 |
| ValueError 返回 500 | 用 ValidationError |
| 阻塞调用 | 全部用 async |

## 生产就绪检查清单

- [ ] `uv run pytest --cov` 覆盖率 ≥ 80%
- [ ] `uv run mypy app` 无错误
- [ ] `uv run ruff check app` 无警告
- [ ] 敏感配置通过 TOML 文件注入（不提交 Git）
- [ ] JWT 过期时间合理
- [ ] CORS 配置白名单
- [ ] 健康检查端点 `/health`
- [ ] 结构化日志已配置
