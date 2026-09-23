# Building a RAG Pipeline for Playbooks

End-to-end guide to building a retrieval-augmented generation pipeline that serves domain knowledge to agents at the right harness phase.

## Pipeline Overview

```
Documents → Load → Chunk → Embed → Store → [At runtime] Query → Retrieve → Inject into agent context
```

Five decisions to make:
1. Document loading (formats, metadata)
2. Chunking strategy (size, overlap, splitter)
3. Embedding model (quality vs cost vs speed)
4. Vector store (scale, features, hosting)
5. Retrieval method (similarity, hybrid, reranking)

## 1. Document Loading

Use LangChain document loaders to ingest documents from various formats.

```python
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
    TextLoader,
)

# Load all PDFs from a directory
pdf_loader = DirectoryLoader(
    "./playbooks/legal/",
    glob="**/*.pdf",
    loader_cls=PyPDFLoader,
)

# Load Word documents
docx_loader = DirectoryLoader(
    "./playbooks/sops/",
    glob="**/*.docx",
    loader_cls=Docx2txtLoader,
)

# Load and combine all documents
all_docs = pdf_loader.load() + docx_loader.load()
```

### Adding Metadata

Metadata enables filtered retrieval — retrieve only documents relevant to the current task.

```python
for doc in all_docs:
    # Add metadata based on file path or content
    if "legal" in doc.metadata.get("source", ""):
        doc.metadata["department"] = "legal"
        doc.metadata["doc_type"] = "policy"
    elif "sop" in doc.metadata.get("source", ""):
        doc.metadata["department"] = "operations"
        doc.metadata["doc_type"] = "sop"
    
    # Add version/date metadata for freshness filtering
    doc.metadata["indexed_at"] = datetime.now().isoformat()
```

## 2. Chunking Strategy

How you split documents into retrievable units has a massive impact on retrieval quality. This is the single most important decision in the pipeline.

### Chunking Parameters

| Parameter | Range | Impact |
|---|---|---|
| **Chunk size** | 256–2048 tokens | Smaller = more precise retrieval, larger = more context per chunk |
| **Chunk overlap** | 50–200 tokens | More overlap = less chance of splitting relevant content across chunks |
| **Splitter type** | Recursive, Semantic, Markdown | Recursive respects document structure; Semantic groups by meaning |

### Recommended: RecursiveCharacterTextSplitter

The default choice. Splits on natural boundaries (paragraphs, sentences, words) in order of preference.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # ~250 tokens — good starting point
    chunk_overlap=200,     # 20% overlap to preserve context at boundaries
    separators=["\n\n", "\n", ". ", " ", ""],  # Split hierarchy
    length_function=len,
)

chunks = splitter.split_documents(all_docs)
```

### Alternative: MarkdownHeaderTextSplitter

For structured documents (SOPs, policies with clear headings), split by headers to preserve logical sections.

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "section"),
    ("##", "subsection"),
    ("###", "topic"),
]

md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
)
```

### Alternative: Semantic Chunking

Groups text by semantic similarity rather than fixed size. Better for documents with varying density.

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

semantic_splitter = SemanticChunker(
    OpenAIEmbeddings(model="text-embedding-3-large"),
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=90,
)
```

### Choosing the Right Strategy

| Document type | Recommended splitter | Chunk size | Overlap |
|---|---|---|---|
| Policies / SOPs (structured) | MarkdownHeaderTextSplitter | By section | N/A |
| Legal contracts (dense prose) | RecursiveCharacterTextSplitter | 500-800 | 150-200 |
| FAQ / Knowledge base | RecursiveCharacterTextSplitter | 300-500 | 100 |
| Technical documentation | MarkdownHeaderTextSplitter | By section | N/A |
| Mixed / Unknown | RecursiveCharacterTextSplitter | 1000 | 200 |

**Always measure with RAGAS after changing chunking parameters.** Small changes in chunk size can dramatically affect context precision and recall.

## 3. Embedding Model Selection

The embedding model converts text chunks into vectors for similarity search.

| Model | Dimensions | Quality | Speed | Cost |
|---|---|---|---|---|
| `text-embedding-3-large` (OpenAI) | 3072 | Excellent | Fast | $0.13/M tokens |
| `text-embedding-3-small` (OpenAI) | 1536 | Good | Very fast | $0.02/M tokens |
| `embed-v3` (Cohere) | 1024 | Excellent | Fast | $0.10/M tokens |
| `all-MiniLM-L6-v2` (open-source) | 384 | Decent | Very fast | Free |
| `bge-large-en-v1.5` (open-source) | 1024 | Good | Fast | Free |

**Recommendation:** Start with `text-embedding-3-large` for best quality. Drop to `text-embedding-3-small` if cost is a concern. Use open-source models for on-premise deployments.

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
```

## 4. Vector Store Selection

Where you store and search embeddings.

| Store | Type | Best for | Notes |
|---|---|---|---|
| **Chroma** | Local / embedded | Prototyping, small corpora (< 100K docs) | Easy setup, no server needed |
| **Pinecone** | Managed cloud | Production, large scale | Fully managed, metadata filtering |
| **Weaviate** | Self-hosted / cloud | Hybrid search, multi-modal | Built-in keyword + vector search |
| **Qdrant** | Self-hosted / cloud | High performance, filtering | Strong metadata filtering |
| **FAISS** | In-memory | Fast prototyping, read-heavy | No persistence by default |
| **pgvector** | PostgreSQL extension | Existing Postgres infrastructure | Combine with relational data |

### Chroma (Prototyping)

```python
from langchain_community.vectorstores import Chroma

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="playbooks",
    persist_directory="./playbook_db",
)
```

### Pinecone (Production)

```python
from langchain_pinecone import PineconeVectorStore
import pinecone

pinecone.init(api_key="...", environment="us-east1-gcp")

vector_store = PineconeVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    index_name="playbooks",
)
```

## 5. Retrieval Methods

### Basic Similarity Search

```python
# Simple similarity search — returns top k most similar chunks
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

# Use in a chain
relevant_docs = retriever.invoke("What is our data retention policy?")
```

### Hybrid Search (Vector + Keyword)

Combines semantic similarity with BM25 keyword matching. Better for queries with specific terminology that pure vector search might miss.

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# Keyword retriever
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 5

# Vector retriever
vector_retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# Combine with reciprocal rank fusion
hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6],  # Weight vector higher for semantic queries
)
```

### Metadata Filtering

Filter retrieval by document metadata — critical for multi-domain playbooks.

```python
# Only retrieve legal department documents
retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {"department": "legal", "doc_type": "policy"},
    }
)
```

### Contextual Compression

Re-rank and compress retrieved documents to keep only the most relevant passages.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_anthropic import ChatAnthropic

compressor = LLMChainExtractor.from_llm(
    ChatAnthropic(model="claude-haiku-4-5-20251001")  # Cheap model for compression
)

compressed_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever,
)
```

## Wiring Retrieval into a Harness Phase

In a LangGraph harness, retrieval is a node that runs at a specific phase.

```python
from langgraph.graph import StateGraph, START, END

def load_playbook(state: HarnessState) -> dict:
    """Phase 4: Retrieve relevant playbook documents."""
    contract_type = state["classification"]["type"]
    
    # Build a targeted query
    query = f"SOPs and policies for {contract_type} contracts"
    
    # Retrieve with metadata filtering
    docs = retriever.invoke(
        query,
        filter={"doc_type": "policy", "contract_type": contract_type},
    )
    
    # Store retrieved context in state for downstream agents
    playbook_context = "\n---\n".join([doc.page_content for doc in docs])
    return {"playbook_context": playbook_context, "phase": "playbook_loaded"}

# Wire into graph after classification, before analysis
builder.add_edge("classify", "load_playbook")
builder.add_edge("load_playbook", "analyse")
```

## Evaluating with RAGAS

Always measure retrieval quality. Without measurement, you're guessing whether your chunking, embedding, and retrieval choices are working.

```python
from ragas import evaluate as ragas_evaluate
from ragas.metrics import (
    faithfulness,
    context_precision,
    context_recall,
    answer_relevancy,
)
from datasets import Dataset

# Build eval dataset from real harness queries
eval_data = Dataset.from_dict({
    "question": ["What is our data retention policy?"],
    "answer": ["Data must be retained for 7 years per SOX compliance."],
    "contexts": [["SOX compliance requires 7-year data retention..."]],
    "ground_truth": ["7 years under SOX."],
})

results = ragas_evaluate(
    dataset=eval_data,
    metrics=[faithfulness, context_precision, context_recall, answer_relevancy],
)
```

**Iterate on chunking and retrieval parameters until RAGAS scores meet your targets.** A typical production target is > 0.85 on context precision and > 0.80 on faithfulness.

## Playbook Maintenance

Playbooks are living documents. Plan for ongoing maintenance:

1. **Versioning** — Track which version of each document is indexed. Re-index when documents change.
2. **Freshness** — Add `indexed_at` metadata. Periodically re-index to catch updates.
3. **Coverage audits** — Periodically check if new document types need adding to the corpus.
4. **Quality monitoring** — Run RAGAS evaluations on a schedule. Quality can degrade as the corpus grows.
5. **Feedback loops** — When agents produce poor answers, check whether the retriever found the right documents. Log retrieval results alongside agent outputs in LangSmith.
