# Market Research Assistant API

A production-ready Market Research Assistant API built with FastAPI, LangChain, and LangGraph.

## Architecture & Design Patterns

This project demonstrates advanced LLM system capabilities through the following features:

- **Multi-Agent System (A2A)**: Utilizes LangGraph to orchestrate a workflow between a "Researcher" agent (which gathers data) and an "Evaluator" agent (which refines and formats the final answer).
- **Tool Use & RAG**: The Researcher agent decides whether to use a local Vector Database (pgvector via LangChain) for RAG or search the web (via Tavily/SerpAPI) dynamically.
- **Dynamic Model Selection (Strategy Pattern)**: The `LLMFactory` dynamically selects the model (e.g., `gpt-3.5-turbo` / `gpt-4o-mini` vs `gpt-4o`) based on the query complexity and the agent's role (Researcher vs Evaluator), optimizing costs.
- **Cost & Token Tracking**: Custom LangChain `BaseCallbackHandler` (`TokenCostCallbackHandler`) captures token usage in real-time, estimating cost per request, accessible via a `/metrics` endpoint.
- **Caching**: Implements Redis caching for identical queries with a configurable TTL (e.g., 1 hour), significantly reducing LLM inference costs and latency.
- **Production-Ready**: Configured with Docker Compose, structured settings via Pydantic, proper logging, and automated testing.

## Prerequisites

- Docker and Docker Compose
- OpenAI API Key
- (Optional) Tavily API Key for live web search

## Installation and Setup

1. **Clone the repository** (if not already done).

2. **Configure Environment Variables**:
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your `OPENAI_API_KEY` and `TAVILY_API_KEY`. If you don't add them, the system will use mocked tools.

3. **Start the Services**:
   Run the full stack using Docker Compose:
   ```bash
   docker-compose up -d --build
   ```
   This will start the FastAPI application (`http://localhost:8000`), the PostgreSQL database with `pgvector`, and the Redis cache.

4. **Seed the Vector Database**:
   Populate the pgvector database with sample market research documents:
   ```bash
   docker-compose exec api python scripts/seed_db.py
   ```

## API Usage Examples

### 1. Ask a Question
Submit a market research query.
```bash
curl -X POST http://localhost:8000/api/v1/ask \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the Generative AI adoption trends for startups in 2024?"}'
```
*Note: If you run this exact command again within 1 hour, it will return the cached response.*

### 2. Check Metrics and Costs
View the total token usage, estimated costs, and number of requests.
```bash
curl http://localhost:8000/api/v1/metrics
```

### 3. Provide Feedback
Submit feedback for fine-tuning loops.
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
     -H "Content-Type: application/json" \
     -d '{"query": "AI adoption trends", "rating": 5, "comments": "Excellent summary"}'
```

## Running Tests

To run the unit and integration tests locally (requires `pytest`):
```bash
docker-compose exec api pytest
```

## Possible Improvements / Next Steps

- **Advanced Rate Limiting**: Integrate `slowapi` or custom Redis-based rate limiting per user/API key to prevent abuse and control costs.
- **Asynchronous Agents**: Currently, the workflow runs synchronously over `invoke`. Moving to `ainvoke` for the graph and tools would increase throughput under heavy load.
- **Authentication**: Add JWT-based authentication using OAuth2 or API keys for securing the endpoints.
- **Streaming Responses**: Implement Server-Sent Events (SSE) using FastAPI's `StreamingResponse` to stream the output of the evaluator agent back to the client in real-time.
- **Hybrid Search**: Enhance pgvector with Full-Text Search (FTS) combining sparse and dense retrieval (e.g., BM25 + Embeddings).
