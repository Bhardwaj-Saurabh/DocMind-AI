# Coding Instructions for GenAI/ML Projects

> Universal coding philosophy and patterns for building production-ready AI systems.
> Technology-agnostic principles applicable to any ML/GenAI project.

---

## Core Philosophy

### 1. Clean Architecture
- **Domain logic** is independent of frameworks, databases, and external systems
- **Application layer** orchestrates use cases, never contains business rules
- **Infrastructure layer** implements technical details (DB, APIs, cloud services)
- **Dependencies point inward**: Infrastructure → Application → Domain

### 2. Type Safety as Documentation
- Types are contracts, not hints
- Invalid states should be unrepresentable
- Compile-time errors are better than runtime crashes

### 3. Explicit Over Implicit
- No magic configurations, global state, or hidden dependencies
- Constructor injection makes dependencies obvious
- Configuration is code, validated and versioned

### 4. Fail Gracefully, Log Extensively
- Return `None`/empty collections instead of crashing on expected failures
- Log with structured context (key-value pairs), not strings
- Distinguish recoverable errors from fatal errors

### 5. Test-Driven Design
- Design for testability from the start (mock modes, dependency injection)
- Every external dependency must be mockable
- Tests define the contract

---

## 1. How to Write Python Classes

### Use Generic Base Classes with TypeVars

```python
from typing import TypeVar, Generic, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel

T = TypeVar("T", bound="BaseDocument")

class BaseDocument(BaseModel, Generic[T], ABC):
    id: UUID4 = Field(default_factory=uuid.uuid4)

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        """Type-safe factory method"""
        return cls(**data)

    @abstractmethod
    def save(self: T) -> T:
        """Subclasses implement persistence"""
        pass
```

**Why**: Enables type-safe inheritance chains and reusable generic methods.

### Pydantic for Data Models

```python
from pydantic import BaseModel, Field
from typing import Optional

class Article(BaseModel):
    title: str
    content: str
    link: str
    author: Optional[str] = None

    class Config:
        # Metadata (not data fields)
        category = DataCategory.ARTICLES
```

**Rules**:
- All data objects inherit from `BaseModel`
- Use `Config` inner class for metadata only
- Use `Field()` for defaults and validation

### Abstract Base Classes Define Contracts

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class DataHandler(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    def process(self, data: InputT) -> OutputT:
        """Subclasses implement transformation logic"""
        pass

    @property
    @abstractmethod
    def metadata(self) -> dict:
        """Configuration for this handler"""
        pass
```

**Pattern**: Define abstract methods + properties for required implementations.

### Class Method Constructors

```python
class Query(BaseModel):
    content: str

    @classmethod
    def from_str(cls, text: str) -> "Query":
        """Alternative constructor"""
        return cls(content=text.strip())

    @classmethod
    def from_mongo(cls, data: dict) -> "Query":
        """Database deserialization"""
        data["id"] = data.pop("_id")
        return cls(**data)
```

### Cached Properties for Expensive Computations

```python
from functools import cached_property

class EmbeddingModel:
    @cached_property
    def embedding_size(self) -> int:
        """Computed once, cached forever"""
        dummy = self._model.encode("")
        return dummy.shape[0]
```

### Thread-Safe Singletons

```python
from threading import Lock
from typing import ClassVar

class SingletonMeta(type):
    _instances: ClassVar = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    """Single instance across application"""
    pass
```

---

## 2. Data Object Management in Pipelines

### Layered Architecture

```
domain/          → Pure data models & business logic
application/     → Use cases & orchestration
infrastructure/  → External systems (DB, APIs)
model/          → ML model operations
```

**Rules**:
- Domain layer has NO external dependencies
- Application layer orchestrates domain objects
- Infrastructure layer implements persistence

### Type-Safe Data Transformations

```python
# Pipeline stages maintain type safety
RawDocument → CleanedDocument → Chunk → EmbeddedChunk

class CleaningHandler(ABC, Generic[DocumentT, CleanedDocumentT]):
    @abstractmethod
    def clean(self, raw: DocumentT) -> CleanedDocumentT:
        pass

class ChunkingHandler(ABC, Generic[CleanedDocumentT, ChunkT]):
    @abstractmethod
    def chunk(self, cleaned: CleanedDocumentT) -> list[ChunkT]:
        pass
```

### Factory + Dispatcher Pattern

```python
class HandlerFactory:
    @staticmethod
    def create(data_category: DataCategory) -> DataHandler:
        if data_category == DataCategory.POSTS:
            return PostHandler()
        elif data_category == DataCategory.ARTICLES:
            return ArticleHandler()
        raise ValueError(f"Unsupported: {data_category}")

class Dispatcher:
    factory = HandlerFactory()

    @classmethod
    def dispatch(cls, data: BaseDocument) -> ProcessedDocument:
        category = data.get_category()
        handler = cls.factory.create(category)
        return handler.process(data)
```

### Database Abstraction Methods

```python
class NoSQLDocument(BaseModel):
    def to_mongo(self) -> dict:
        """Serialize for MongoDB (_id instead of id)"""
        data = self.model_dump()
        data["_id"] = str(data.pop("id"))
        return data

    @classmethod
    def from_mongo(cls, data: dict):
        """Deserialize from MongoDB"""
        data["id"] = data.pop("_id")
        return cls(**data)

class VectorDocument(BaseModel):
    embedding: list[float]

    def to_point(self) -> PointStruct:
        """Serialize for Qdrant vector DB"""
        payload = self.model_dump(exclude={"embedding"})
        return PointStruct(
            id=str(self.id),
            vector=self.embedding,
            payload=payload
        )
```

### Batch Processing Pattern

```python
class EmbeddingHandler:
    def embed(self, chunk: Chunk) -> EmbeddedChunk:
        """Single item delegates to batch"""
        return self.embed_batch([chunk])[0]

    def embed_batch(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        """Vectorized batch operation"""
        texts = [c.content for c in chunks]
        embeddings = self._model.encode(texts)
        return [
            EmbeddedChunk(**chunk.model_dump(), embedding=emb)
            for chunk, emb in zip(chunks, embeddings)
        ]
```

### Metadata Tracking

```python
class ProcessedData(BaseModel):
    content: str
    metadata: dict

    @property
    def processing_metadata(self) -> dict:
        """Auto-generated processing info"""
        return {
            "model_id": self.model_id,
            "chunk_size": self.chunk_size,
            "processed_at": datetime.utcnow().isoformat(),
        }
```

---

## 3. Coding Best Practices

### Type Hints Everywhere

```python
# Use modern Python 3.10+ union syntax
def process(data: str | None) -> list[dict]:
    pass

# Generic callables
def group_by(
    items: list[T],
    selector: Callable[[T], Any]
) -> dict[Any, list[T]]:
    pass
```

### Enums for Categories

```python
from enum import Enum

class DataCategory(str, Enum):
    POSTS = "posts"
    ARTICLES = "articles"
    REPOSITORIES = "repositories"

# Type-safe usage
if category == DataCategory.POSTS:
    # ...
```

### Structured Logging

```python
from loguru import logger

logger.info(
    "Document processed successfully",
    category=data_category,
    content_length=len(content),
    processing_time_ms=elapsed
)

logger.error(
    "Failed to insert documents",
    doc_type=cls.__name__,
    error=str(e)
)
```

### Custom Exceptions

```python
class LLMEngineeringException(Exception):
    """Base exception for all custom errors"""
    pass

class ImproperlyConfigured(LLMEngineeringException):
    """Configuration error"""
    pass

# Usage
if not hasattr(cls, "Config"):
    raise ImproperlyConfigured(f"{cls.__name__} missing Config class")
```

### Configuration Management

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_HOST: str = "mongodb://localhost:27017"
    EMBEDDING_MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"

    @classmethod
    def load(cls) -> "Settings":
        """Try secret store, fallback to .env"""
        try:
            return cls(**get_secrets())
        except Exception:
            return cls()

settings = Settings.load()
```

### Fluent Interface for Builders

```python
class PipelineBuilder:
    def __init__(self):
        self._steps = []

    def add_cleaning(self):
        self._steps.append(CleaningStep())
        return self

    def add_chunking(self):
        self._steps.append(ChunkingStep())
        return self

    def build(self) -> Pipeline:
        return Pipeline(self._steps)

# Usage
pipeline = PipelineBuilder()\
    .add_cleaning()\
    .add_chunking()\
    .build()
```

### Properties for Computed Values

```python
class User:
    first_name: str
    last_name: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

### Avoid Over-Engineering

**DON'T**:
- Add error handling for impossible scenarios
- Create abstractions for single-use code
- Add comments to self-evident code
- Refactor unrelated code when fixing bugs

**DO**:
- Keep solutions simple and focused
- Only add what's explicitly needed
- Trust internal code and framework guarantees
- Validate only at system boundaries (user input, external APIs)

### Modern Python Features

```python
# Structural pattern matching (3.10+)
match data_type:
    case DataCategory.POSTS:
        return PostHandler()
    case DataCategory.ARTICLES:
        return ArticleHandler()
    case _:
        raise ValueError(f"Unknown: {data_type}")

# Dictionary merge operator
base_config = {"a": 1}
user_config = {"b": 2}
config = base_config | user_config
```

---

## Summary

### Class Design
- Use Pydantic `BaseModel` for all data objects
- Add `Generic[T]` + `ABC` for reusable base classes
- Define clear contracts with `@abstractmethod`
- Use `@classmethod` for alternative constructors
- Implement `@cached_property` for expensive computations

### Data Pipelines
- Maintain type safety with generics across transformations
- Use Factory + Dispatcher for routing by data type
- Implement `to_mongo()` / `from_mongo()` / `to_point()` for DB abstraction
- Prefer batch operations over single-item processing
- Track metadata for observability

### Best Practices
- Type hints on all functions and methods
- Enums for fixed categories
- Structured logging with context
- Centralized configuration with fallbacks
- Thread-safe singletons for shared resources
- Keep it simple - avoid premature optimization
