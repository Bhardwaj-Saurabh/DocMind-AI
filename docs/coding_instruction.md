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

## 4. Architecture & Organization Patterns

### Layered Architecture (Hexagonal/Clean)

```
project/
├── domain/              # Pure business logic
│   ├── base/           # Abstract contracts
│   ├── entities.py     # Business objects
│   ├── exceptions.py   # Domain exceptions
│   └── types.py        # Enums, value objects
├── application/        # Use cases & orchestration
│   ├── pipelines/     # Data processing workflows
│   ├── services/      # Business operations
│   └── handlers/      # Command/query handlers
├── infrastructure/     # External integrations
│   ├── db/           # Database adapters
│   ├── cloud/        # Cloud services (AWS, GCP)
│   └── api/          # External API clients
└── model/             # ML-specific lifecycle
    ├── training/
    ├── inference/
    └── evaluation/
```

**Rules**:
- Domain layer has ZERO external dependencies
- Application imports from domain only
- Infrastructure implements domain contracts (interfaces)
- Model layer is isolated (training ≠ inference ≠ evaluation)

### Feature-First Organization

**DON'T** organize by technical layer:
```
models/
views/
controllers/
```

**DO** organize by business capability:
```
crawlers/       # Data ingestion feature
preprocessing/  # ETL pipeline feature
rag/           # RAG feature
dataset/       # Dataset generation feature
```

**Why**: You change features, not layers. Co-locate related code.

### Repository Pattern for Persistence

```python
# Abstract repository in domain layer
class Repository(ABC, Generic[T]):
    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def find(self, id: UUID) -> T | None:
        pass

    @abstractmethod
    def bulk_insert(self, entities: list[T]) -> bool:
        pass

# Concrete implementation in infrastructure
class MongoRepository(Repository[T]):
    def save(self, entity: T) -> T:
        # MongoDB-specific logic
        pass

class VectorRepository(Repository[T]):
    def save(self, entity: T) -> T:
        # Qdrant-specific logic
        pass
```

**Philosophy**: Business logic never knows about MongoDB or Qdrant. Swap databases without changing domain code.

---

## 5. Error Handling & Resilience

### Return Sentinels, Not Exceptions (for Expected Failures)

```python
# BAD: Exceptions for control flow
def find_user(id: UUID) -> User:
    user = db.query(id)
    if not user:
        raise UserNotFoundError()
    return user

# GOOD: Return None for missing data
def find_user(id: UUID) -> User | None:
    try:
        user = db.query(id)
        return user if user else None
    except DatabaseError:
        logger.error("Database connection failed", user_id=id)
        return None
```

**Rule**: Use exceptions for unexpected errors (network failure, DB down). Use `None`/`Result` types for expected absence.

### Graceful Degradation with Retries

```python
def save_with_retry(self, entity: T) -> T | None:
    try:
        return self._save(entity)
    except CollectionNotFoundError:
        logger.info("Collection missing, creating and retrying")
        self._create_collection()
        return self._save(entity)  # Second attempt
    except DatabaseError as e:
        logger.exception("Failed to save entity", entity_id=entity.id)
        return None
```

**Pattern**: Auto-recover from setup issues (missing tables, first-time init). Log extensively. Return `None` to let caller decide next step.

### Custom Exception Hierarchy

```python
class ProjectException(Exception):
    """Base exception for all project errors"""
    pass

class ConfigurationError(ProjectException):
    """Raised when configuration is invalid"""
    pass

class DataValidationError(ProjectException):
    """Raised when data fails validation"""
    pass

class ExternalServiceError(ProjectException):
    """Raised when external API fails"""
    pass
```

**Usage**:
```python
# Catch specific errors
try:
    result = process_data(input)
except DataValidationError:
    # Handle validation differently than service errors
    logger.warning("Invalid input data", input=input)
    return default_result
except ExternalServiceError:
    # Retry external service calls
    logger.error("API unavailable, retrying")
    return retry_with_backoff(process_data, input)
```

### Optional Dependency Handling

```python
# Top of module
try:
    import boto3
    from sagemaker import Session
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger.warning("AWS SDK not installed. Run 'pip install boto3 sagemaker'")

# Usage
def deploy_to_sagemaker(model):
    if not AWS_AVAILABLE:
        raise ConfigurationError("AWS deployment requires boto3. Install with 'pip install boto3'")
    # Deployment logic
```

**Philosophy**: Fail at usage time, not import time. Provide clear installation instructions.

---

## 6. Testing & Mockability

### Mock Mode as Constructor Parameter

```python
class RAGPipeline:
    def __init__(self, mock: bool = False):
        self._mock = mock
        self._retriever = Retriever(mock=mock)
        self._reranker = Reranker(mock=mock)
        self._llm = LLM(mock=mock)

    def search(self, query: str) -> str:
        if self._mock:
            return "Mock response for testing"
        # Real implementation
        docs = self._retriever.search(query)
        ranked = self._reranker.rank(docs)
        return self._llm.generate(query, ranked)
```

**Test code**:
```python
def test_rag_pipeline():
    pipeline = RAGPipeline(mock=True)
    result = pipeline.search("What is GenAI?")
    assert result == "Mock response for testing"
```

**Philosophy**: No environment variables, no monkey patching. Mock mode is explicit and testable.

### Dependency Injection for Swappable Components

```python
# Abstract interface
class EmbeddingModel(ABC):
    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]:
        pass

# Production implementation
class SentenceTransformerModel(EmbeddingModel):
    def __init__(self, model_id: str):
        self._model = SentenceTransformer(model_id)

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts)

# Test implementation
class MockEmbeddingModel(EmbeddingModel):
    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

# Service uses abstraction
class VectorStore:
    def __init__(self, embedding_model: EmbeddingModel):
        self._embedding_model = embedding_model

    def add_documents(self, docs: list[str]):
        embeddings = self._embedding_model.encode(docs)
        # Store embeddings

# Test with mock
def test_vector_store():
    mock_embedder = MockEmbeddingModel()
    store = VectorStore(embedding_model=mock_embedder)
    store.add_documents(["test doc"])
```

**Rule**: Accept interfaces in constructors, not concrete classes.

---

## 7. Configuration Management

### Single Source of Truth with Type Safety

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Required settings (no defaults)
    OPENAI_API_KEY: str
    DATABASE_URL: str

    # Optional with safe defaults
    MODEL_ID: str = "gpt-4o-mini"
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 30

    # Computed properties
    @property
    def MAX_TOKEN_WINDOW(self) -> int:
        model_limits = {
            "gpt-4o-mini": 128000,
            "gpt-4": 8192,
        }
        # 90% of max to leave room for system prompts
        return int(model_limits.get(self.MODEL_ID, 128000) * 0.90)

    @classmethod
    def load(cls) -> "Settings":
        """Multi-source loading with fallbacks"""
        try:
            # Try secret manager first (production)
            secrets = load_from_secret_manager("app-settings")
            return cls(**secrets)
        except Exception:
            # Fallback to .env file (local development)
            logger.warning("Loading settings from .env file")
            return cls()

# Global singleton
settings = Settings.load()
```

**Usage**:
```python
# Type-safe access
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
max_tokens = settings.MAX_TOKEN_WINDOW
```

**Rules**:
1. All config in one class, typed with Pydantic
2. Multi-source loading: Secrets → Environment → Defaults
3. Computed properties for derived values
4. Fail fast on missing required settings

---

## 8. Resource Management

### Thread-Safe Singletons for Heavy Resources

```python
from threading import Lock
from typing import ClassVar

class SingletonMeta(type):
    _instances: ClassVar[dict] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class EmbeddingModel(metaclass=SingletonMeta):
    """Load model once, share across requests"""
    def __init__(self, model_id: str):
        logger.info(f"Loading embedding model: {model_id}")
        self._model = load_heavy_model(model_id)
        self._model.eval()

# Usage: Always returns same instance
model1 = EmbeddingModel("all-MiniLM-L6-v2")
model2 = EmbeddingModel("all-MiniLM-L6-v2")
assert model1 is model2  # True
```

**When to use singletons**:
- ML models (heavy, slow to load)
- Database connection pools
- HTTP session objects
- File system watchers

**When NOT to use singletons**:
- Business logic objects
- Request-scoped data
- Stateful services

### Connection Pooling

```python
class DatabaseConnector:
    _instance: ClientType | None = None

    def __new__(cls) -> ClientType:
        if cls._instance is None:
            cls._instance = MongoClient(
                settings.DATABASE_URL,
                maxPoolSize=50,
                minPoolSize=10
            )
            logger.info("Database connection pool created")
        return cls._instance

# Global singleton
db = DatabaseConnector()
```

### Lazy Initialization with Cached Properties

```python
from functools import cached_property

class ModelWrapper:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self._model = None  # Not loaded yet

    @cached_property
    def embedding_size(self) -> int:
        """Computed once, cached forever"""
        # Load model only when first needed
        if self._model is None:
            self._model = load_model(self.model_id)
        dummy = self._model.encode("")
        return len(dummy)
```

### Explicit Cleanup for GPU Resources

```python
import gc
import torch

def train_model(dataset):
    model = load_large_model()
    model.train()
    # Training logic

    # Explicit cleanup
    del model
    gc.collect()
    torch.cuda.empty_cache()
    logger.info("GPU memory released")
```

---

## 9. Observability & Monitoring

### Structured Logging with Context

```python
from loguru import logger

# BAD: String logging
logger.info("User processed 15 documents successfully")

# GOOD: Structured logging
logger.info(
    "Documents processed successfully",
    user_id=user.id,
    num_documents=15,
    processing_time_ms=elapsed,
    model_id=settings.MODEL_ID
)
```

**Why**: Structured logs can be queried, filtered, and aggregated. "Show all logs where `processing_time_ms > 1000`" is easy.

### Trace Critical Paths

```python
import opik  # or OpenTelemetry

@opik.track(name="RAG.search")
def search(query: str, k: int = 5) -> list[Document]:
    # Automatic span creation
    documents = vector_db.search(query, k=k)

    # Enrich trace with metadata
    opik.update_current_trace(
        metadata={
            "query_tokens": count_tokens(query),
            "results_found": len(documents),
            "search_latency_ms": elapsed
        }
    )
    return documents
```

**Pattern**: Add `@track` to:
- API endpoints
- Model inference calls
- Database queries
- External API calls

### Cost Tracking for LLM Calls

```python
def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model=settings.MODEL_ID,
        messages=[{"role": "user", "content": prompt}]
    )

    # Log token usage
    logger.info(
        "LLM call completed",
        model=settings.MODEL_ID,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_cost_usd=calculate_cost(response.usage)
    )

    return response.choices[0].message.content
```

---

## 10. Concurrency Patterns

### Thread Pools for I/O-Bound Tasks

```python
import concurrent.futures
from tqdm import tqdm

def process_batch(items: list[Item], max_workers: int = 10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(process_item, item) for item in items]

        # Collect results with progress bar
        results = []
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(items)):
            try:
                result = future.result(timeout=30)
                results.append(result)
            except Exception as e:
                logger.exception("Task failed", error=str(e))

        return results
```

**When to use threads**:
- API calls (OpenAI, HuggingFace, AWS)
- Database queries
- File I/O
- Network requests

**When to use processes**:
- CPU-intensive tasks (data preprocessing, tokenization)
- Avoid GIL limitations

### Batching for Efficiency

```python
def embed_documents(docs: list[str], batch_size: int = 32) -> list[Embedding]:
    embeddings = []

    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        # Vectorized operation
        batch_embeddings = model.encode(batch)
        embeddings.extend(batch_embeddings)

        logger.debug(f"Embedded batch {i//batch_size + 1}/{len(docs)//batch_size + 1}")

    return embeddings
```

**Rule**: Batch size depends on:
- Model memory requirements
- API rate limits
- System RAM

---

## 11. Prompt Engineering Patterns

### Prompts as Domain Objects

```python
class PromptTemplate(BaseModel):
    name: str
    template: str
    variables: list[str]
    separator: str | None = None

    def render(self, **kwargs) -> str:
        """Render template with variables"""
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing variables: {missing}")
        return self.template.format(**kwargs)

class QueryExpansionPrompt(PromptTemplate):
    name: str = "query_expansion"
    template: str = """Generate {n} different versions of this question:

    Original: {question}

    Separate each version with '{separator}'"""
    variables: list[str] = ["question", "n"]
    separator: str = "#NEXT#"

# Usage
prompt = QueryExpansionPrompt()
rendered = prompt.render(question="What is RAG?", n=3)
```

**Why**: Prompts are testable, versioned, and trackable.

### Token Window Management

```python
def truncate_to_token_limit(text: str, max_tokens: int, tokenizer) -> str:
    """Safely truncate text at token boundaries"""
    tokens = tokenizer.encode(text)

    if len(tokens) <= max_tokens:
        return text

    # Truncate and decode
    truncated_tokens = tokens[:max_tokens]
    return tokenizer.decode(truncated_tokens)

# Usage
prompt = create_prompt(context, query)
prompt = truncate_to_token_limit(
    prompt,
    max_tokens=settings.MAX_TOKEN_WINDOW,
    tokenizer=tokenizer
)
```

### Structured Output Parsing

```python
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    sentiment: str
    confidence: float
    topics: list[str]

def analyze_text(text: str) -> AnalysisResult:
    prompt = f"""Analyze this text and return JSON:
    {{
        "sentiment": "positive" | "negative" | "neutral",
        "confidence": 0.0-1.0,
        "topics": ["topic1", "topic2"]
    }}

    Text: {text}
    """

    response = llm_call(prompt)

    try:
        result = AnalysisResult.model_validate_json(response)
        return result
    except ValidationError as e:
        logger.error("LLM returned invalid JSON", error=str(e), response=response)
        raise
```

**Rule**: Always validate LLM outputs with schemas. LLMs are unreliable.

---

## 12. ML Model Lifecycle

### Separation of Training and Inference

```
model/
├── training/
│   ├── train.py          # Training logic
│   ├── dataset.py        # Training datasets
│   └── requirements.txt  # Training dependencies (torch, transformers)
├── inference/
│   ├── serve.py          # Inference server
│   ├── optimize.py       # Model optimization (quantization, ONNX)
│   └── requirements.txt  # Lightweight inference deps
└── evaluation/
    ├── evaluate.py       # Evaluation metrics
    └── benchmark.py      # Performance benchmarks
```

**Rules**:
1. Training and inference have separate dependencies
2. Never import training code in production inference
3. Evaluation is independent of both

### Model Registry Pattern

```python
class ModelRegistry:
    """Track model versions and metadata"""
    def __init__(self):
        self._models = {}

    def register(
        self,
        name: str,
        version: str,
        path: str,
        metadata: dict
    ):
        key = f"{name}:{version}"
        self._models[key] = {
            "path": path,
            "metadata": metadata,
            "registered_at": datetime.utcnow()
        }
        logger.info(f"Registered model {key}", metadata=metadata)

    def load(self, name: str, version: str = "latest"):
        if version == "latest":
            # Get latest version
            versions = [k for k in self._models if k.startswith(f"{name}:")]
            version = max(versions).split(":")[1]

        key = f"{name}:{version}"
        model_info = self._models[key]
        return load_model(model_info["path"])

# Usage
registry = ModelRegistry()
registry.register("sentiment", "v1.2", "s3://models/sentiment-v1.2", {...})
model = registry.load("sentiment", "v1.2")
```

### Evaluation as First-Class Concern

```python
def evaluate_model(model, test_dataset) -> dict:
    """Automated evaluation with multiple metrics"""
    predictions = model.predict(test_dataset)

    metrics = {
        "accuracy": compute_accuracy(predictions, test_dataset.labels),
        "f1_score": compute_f1(predictions, test_dataset.labels),
        "latency_p50_ms": measure_latency_percentile(model, 0.5),
        "latency_p99_ms": measure_latency_percentile(model, 0.99),
        "memory_mb": measure_memory_usage(model),
    }

    logger.info("Model evaluation completed", **metrics)

    # Save results for comparison
    save_evaluation_results(model.version, metrics)

    return metrics
```

---

## 13. Pipeline Orchestration

### Dispatcher + Strategy Pattern

```python
class DataCategory(Enum):
    POSTS = "posts"
    ARTICLES = "articles"
    VIDEOS = "videos"

class ProcessingHandler(ABC):
    @abstractmethod
    def process(self, data: RawData) -> ProcessedData:
        pass

class PostHandler(ProcessingHandler):
    def process(self, data: RawData) -> ProcessedData:
        # Post-specific processing
        return ProcessedData(...)

class ArticleHandler(ProcessingHandler):
    def process(self, data: RawData) -> ProcessedData:
        # Article-specific processing
        return ProcessedData(...)

class HandlerFactory:
    @staticmethod
    def create(category: DataCategory) -> ProcessingHandler:
        handlers = {
            DataCategory.POSTS: PostHandler(),
            DataCategory.ARTICLES: ArticleHandler(),
        }
        return handlers[category]

class ProcessingDispatcher:
    factory = HandlerFactory()

    @classmethod
    def dispatch(cls, data: RawData) -> ProcessedData:
        category = data.get_category()
        handler = cls.factory.create(category)
        result = handler.process(data)

        logger.info(
            "Data processed",
            category=category,
            input_size=len(data),
            output_size=len(result)
        )

        return result
```

**Benefits**:
- Add new data types without modifying dispatcher
- Each handler is independently testable
- Type-safe routing

### Chain of Responsibility for Multi-Stage Pipelines

```python
RawData → Clean → Chunk → Embed → Store

class Pipeline:
    def __init__(self):
        self._stages = []

    def add_stage(self, stage: Callable):
        self._stages.append(stage)
        return self

    def execute(self, data):
        result = data
        for stage in self._stages:
            result = stage(result)
            logger.debug(f"Stage {stage.__name__} completed")
        return result

# Build pipeline
pipeline = Pipeline()\
    .add_stage(CleaningDispatcher.dispatch)\
    .add_stage(ChunkingDispatcher.dispatch)\
    .add_stage(EmbeddingDispatcher.dispatch)\
    .add_stage(save_to_vector_db)

# Execute
final_result = pipeline.execute(raw_data)
```

---

## 14. Dataset Management

### Datasets as Typed Artifacts

```python
class DatasetSample(BaseModel):
    instruction: str
    output: str
    metadata: dict

class Dataset(BaseModel):
    name: str
    version: str
    category: DataCategory
    samples: list[DatasetSample]

    @property
    def num_samples(self) -> int:
        return len(self.samples)

    def train_test_split(self, test_size: float = 0.2):
        split_idx = int(len(self.samples) * (1 - test_size))
        return (
            Dataset(samples=self.samples[:split_idx]),
            Dataset(samples=self.samples[split_idx:])
        )

    def to_huggingface(self):
        """Convert to HuggingFace Dataset"""
        return HFDataset.from_dict({
            "instruction": [s.instruction for s in self.samples],
            "output": [s.output for s in self.samples]
        })

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.model_dump(), f)
```

### Quality Filtering

```python
def filter_dataset(dataset: Dataset) -> Dataset:
    """Remove low-quality samples"""
    filtered_samples = []

    for sample in dataset.samples:
        # Filter short answers
        if len(sample.output.split()) < 10:
            continue

        # Filter invalid format
        if not is_valid_format(sample.output):
            continue

        # Filter toxic content
        if is_toxic(sample.output):
            continue

        filtered_samples.append(sample)

    logger.info(
        "Dataset filtered",
        original_size=len(dataset.samples),
        filtered_size=len(filtered_samples),
        removal_rate=1 - len(filtered_samples)/len(dataset.samples)
    )

    return Dataset(samples=filtered_samples)
```

---

## Summary: Universal Principles

### Architecture
1. **Clean Architecture**: Domain → Application → Infrastructure
2. **Feature-First**: Organize by capability, not technical layer
3. **Repository Pattern**: Abstract persistence behind interfaces

### Code Quality
4. **Type Safety**: Use Pydantic/TypedDict/dataclasses for all data
5. **Explicit Dependencies**: Constructor injection, no globals
6. **Testability**: Mock modes, dependency injection

### Error Handling
7. **Graceful Degradation**: Return `None`/empty on expected failures
8. **Structured Logging**: Key-value pairs, not strings
9. **Custom Exceptions**: Hierarchy for error categorization

### Configuration
10. **Single Source**: One config class, typed and validated
11. **Multi-Source Loading**: Secrets → Environment → Defaults
12. **Computed Properties**: Derive complex values

### Resources
13. **Singletons**: For heavy resources (models, connections)
14. **Connection Pooling**: Reuse database/HTTP connections
15. **Explicit Cleanup**: GPU memory, file handles

### Observability
16. **Structured Logs**: Always include context
17. **Distributed Tracing**: Track critical paths
18. **Cost Tracking**: Log tokens, API calls

### Concurrency
19. **Thread Pools**: For I/O-bound tasks (APIs, DB)
20. **Batching**: Group operations for efficiency
21. **Progress Tracking**: Use tqdm for long operations

### ML Lifecycle
22. **Separate Training/Inference**: Different deps, never mix
23. **Model Registry**: Version and track models
24. **Evaluation First**: Automated metrics for all models

### Pipelines
25. **Dispatcher + Strategy**: Route by data type
26. **Chain of Responsibility**: Multi-stage processing
27. **Type-Safe Transformations**: Generics across stages

### Prompts & LLMs
28. **Prompts as Objects**: Versioned, testable templates
29. **Token Management**: Truncate safely at boundaries
30. **Schema Validation**: Validate all LLM outputs

---

## Quick Reference: Python-Specific

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

---

## Anti-Patterns to Avoid

### 1. God Objects
**DON'T**: One class doing everything
```python
class AISystem:
    def crawl_data(self): ...
    def clean_data(self): ...
    def train_model(self): ...
    def deploy_model(self): ...
    def generate_answer(self): ...
```

**DO**: Single Responsibility Principle
```python
class DataCrawler: ...
class DataCleaner: ...
class ModelTrainer: ...
class ModelDeployer: ...
class InferenceService: ...
```

### 2. Magic Strings/Numbers
**DON'T**:
```python
if user_type == "premium":
    max_tokens = 4096
```

**DO**:
```python
class UserType(Enum):
    PREMIUM = "premium"
    FREE = "free"

MAX_TOKENS = {
    UserType.PREMIUM: 4096,
    UserType.FREE: 1024,
}

if user.type == UserType.PREMIUM:
    max_tokens = MAX_TOKENS[user.type]
```

### 3. Global Mutable State
**DON'T**:
```python
_cached_embeddings = {}

def get_embedding(text):
    if text not in _cached_embeddings:
        _cached_embeddings[text] = model.encode(text)
    return _cached_embeddings[text]
```

**DO**:
```python
class EmbeddingCache:
    def __init__(self):
        self._cache = {}

    def get(self, text: str) -> list[float]:
        if text not in self._cache:
            self._cache[text] = self._model.encode(text)
        return self._cache[text]
```

### 4. Tight Coupling to External Services
**DON'T**:
```python
def process_user(user_id):
    user = requests.get(f"https://api.example.com/users/{user_id}").json()
    # Process user
```

**DO**:
```python
class UserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> User:
        pass

class APIUserRepository(UserRepository):
    def get_user(self, user_id: str) -> User:
        response = requests.get(f"{self.base_url}/users/{user_id}")
        return User(**response.json())

def process_user(user_id: str, repo: UserRepository):
    user = repo.get_user(user_id)
    # Process user
```

### 5. Premature Optimization
**DON'T**: Over-engineer before knowing bottlenecks
```python
# Complex caching, sharding, async before measuring
class HyperOptimizedCache:
    def __init__(self):
        self._shards = [LRUCache() for _ in range(16)]
        self._lock_pool = [Lock() for _ in range(16)]
    # 200 lines of optimization
```

**DO**: Simple first, optimize with data
```python
class SimpleCache:
    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self._max_size = max_size

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value):
        if len(self._cache) >= self._max_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = value
```

---

## Technology Transfer Guide

This codebase uses Python, but these principles apply to any language:

| Python | Go | Rust | TypeScript |
|--------|-----|------|------------|
| `Pydantic BaseModel` | `struct` with tags | `struct` with `serde` | `interface` or `class` |
| `TypeVar` + `Generic` | Generics (`[T any]`) | Generics (`<T>`) | Generics (`<T>`) |
| `ABC` + `@abstractmethod` | `interface` | `trait` | `abstract class` |
| `@cached_property` | `sync.Once` | `once_cell::sync::Lazy` | Getters with cache |
| `ThreadPoolExecutor` | `sync.WaitGroup` + goroutines | `tokio` runtime | `Promise.all()` |
| `Settings` (Pydantic) | `viper` or `envconfig` | `config` crate | `dotenv` + validation |
| `loguru` | `zap` or `zerolog` | `tracing` | `winston` or `pino` |

The **patterns remain identical**, only syntax changes.
