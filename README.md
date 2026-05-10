# Market Research Assistant API

A production-ready Multi-Agent Market Research Assistant API built with **FastAPI**, **LangChain**, and **LangGraph**.

## 📋 Overview

This project demonstrates an advanced AI system for market research with intelligent agents that gather, process, and refine information. It combines RAG (Retrieval-Augmented Generation), web search, and LLM orchestration to deliver comprehensive research responses.

**Key Highlights:**
- 🤖 Multi-Agent Architecture (Researcher + Evaluator)
- 🗂️ RAG with pgvector for document retrieval
- 💰 Dynamic model selection for cost optimization
- ⚡ Redis caching for improved performance
- 📊 Real-time token and cost tracking
- 🐳 Docker containerized for production

---

## 🏗️ Architecture & Design Patterns

### Core Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Researcher Agent** | Gathers data from RAG (pgvector) or web search | LangChain Agent + MCP Tools |
| **Evaluator Agent** | Refines and polishes researcher's draft | LangChain Chain + ChatOpenAI |
| **LangGraph Orchestrator** | Manages workflow between agents | LangGraph StateGraph |
| **Vector Database** | Stores and retrieves document embeddings | PostgreSQL + pgvector |
| **Cache Layer** | Stores responses for identical queries | Redis (TTL: 1 hour) |
| **LLM Factory** | Selects optimal models by query complexity | Strategy Pattern |
| **Token Tracker** | Monitors usage and costs in real-time | LangChain Callbacks |

### Design Patterns Used

1. **Multi-Agent Architecture (A2A)**: LangGraph orchestrates workflow between two specialized agents
2. **Strategy Pattern**: `LLMFactory` selects models based on query complexity and agent role
3. **RAG (Retrieval-Augmented Generation)**: Combines local vector search with web search
4. **Callback Handler Pattern**: Custom `TokenCostCallbackHandler` for token tracking

### Workflow

```
User Query
    ↓
Cache Check (Redis)
    ├─ [HIT] → Return cached response
    └─ [MISS] → Continue to agents
        ↓
    Researcher Agent
    ├─ Tool: vector_search (RAG) → pgvector
    ├─ Tool: web_search (Tavily) → External API
    └─ Output: draft response
        ↓
    Evaluator Agent
    └─ Refines & polishes draft
        ↓
    Cache Result (1 hour TTL)
    ↓
Return Final Response
```

---

## 📁 Project Structure

```
proyecto_LLM/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── agents/
│   │   ├── graph.py           # LangGraph workflow orchestration
│   │   ├── researcher.py      # Researcher agent + tools
│   │   ├── evaluator.py       # Evaluator agent for refinement
│   │   └── tools.py           # Tool definitions
│   ├── api/
│   │   ├── endpoints.py       # REST API routes (/ask, /evaluate, /metrics)
│   │   └── models.py          # Pydantic request/response schemas
│   ├── core/
│   │   ├── config.py          # Settings & environment variables
│   │   ├── cache.py           # Redis cache implementation
│   │   ├── logger.py          # Logging configuration
│   │   ├── dependencies.py    # Dependency injection
│   │   └── database.py        # Database connections
│   └── services/
│       ├── llm_factory.py     # Dynamic LLM model selection
│       ├── mcp_client.py      # MCP protocol client
│       ├── vector_db.py       # PGVector store management
│       ├── rag_router.py      # RAG query routing
│       ├── evaluator_judge.py # LLM-as-judge for batch evaluation
│       └── metrics.py         # Token & cost tracking
├── scripts/
│   ├── mcp_server.py          # MCP server launcher
│   └── seed_db.py             # Initialize pgvector with sample data
├── tests/
│   ├── test_agents.py         # Agent workflow tests
│   ├── test_api.py            # API endpoint tests
│   └── test_services.py       # Service unit tests
├── docker-compose.yml         # Multi-container orchestration
├── Dockerfile                 # API container configuration
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
└── README.md                 # This file
```

---

## � Observability Stack (NEW!)

This project includes a **production-grade monitoring and alerting system** built with:

### Components

| Component | Purpose | URL |
|-----------|---------|-----|
| **Prometheus** | Metrics collection & alert rules | http://localhost:9090 |
| **Grafana** | Dashboards & visualization | http://localhost:3000 |
| **Loki** | Centralized log aggregation | http://localhost:3100 |
| **Alertmanager** | Alert routing & notifications | http://localhost:9093 |
| **Promtail** | Log shipper (Docker containers) | N/A |

### Exposed Metrics

**Performance:**
- Agent execution latency (p50, p99) by role
- LLM API call duration by model
- Request latency by endpoint

**Quality:**
- `response_quality_score`: 0-100 quality rating (LLM-as-judge)
- Quality sample distribution: excellent/good/fair/poor
- Semantic drift detection over time

**Cost:**
- `api_cost_total_usd`: Cumulative cost
- `api_cost_per_hour_usd`: Hourly cost estimate
- Cost breakdown by model

**Cache:**
- `cache_hit_ratio`: Hit/miss ratio (0-1)
- Cache hits/misses counters

**Business:**
- Query distribution: RAG vs Web Search
- Request status codes: 2xx/4xx/5xx
- Error rates by type and agent

### Automated Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| **Response Quality Degraded** | >5% low-quality (score < 60) for 5min | Warning in Slack |
| **PANIC: Critical Quality** | >10% poor quality (score < 40) for 5min | Immediate page/alert |
| **Budget Exceeded** | Cost > $2/hour for 10min | Warning in Slack |
| **Cache Degradation** | Hit ratio < 40% for 15min | Warning in Slack |
| **High Latency** | p99 > 30s | Warning in Slack |
| **API Errors** | >10% error rate | Critical alert |

### Dashboards

1. **Agent Flight Deck**: Agent latency, query distribution, quality gauge
2. **Cost Dashboard**: Hourly/daily costs, projections, model breakdown
3. **Semantic Drift Monitor**: Quality score trends over 7 days
4. **Cache & Request Status**: Cache ratio, request status distribution

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (required for full stack)
- Or: Python 3.11+, PostgreSQL, Redis, Prometheus, Grafana
- OpenAI API Key
- (Optional) Tavily API Key for web search
- (Optional) Slack webhook for alert notifications

### Installation with Docker (Recommended)

1. **Clone and configure:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```env
   OPENAI_API_KEY=sk-your-openai-key-here
   TAVILY_API_KEY=tvly-your-tavily-key-here  # Optional
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...  # Optional
   ENVIRONMENT=development
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d --build
   ```

   **Services started:**
   - 🌐 FastAPI: `http://localhost:8000`
   - 📊 Prometheus: `http://localhost:9090`
   - 📈 Grafana: `http://localhost:3000` (admin/admin)
   - 📝 Loki: `http://localhost:3100`
   - 🗂️ PostgreSQL: `localhost:5432`
   - 💾 Redis: `localhost:6379`
   - 🔔 Alertmanager: `http://localhost:9093`

4. **Seed vector database (optional):**
   ```bash
   docker-compose exec api python scripts/seed_db.py
   ```

5. **Access Dashboards:**
   - **API Docs**: http://localhost:8000/docs
   - **Prometheus**: http://localhost:9090
   - **Grafana**: http://localhost:3000 (Default: admin/admin)
   - **Loki**: http://localhost:3100

### Testing the Observability Stack

**Run tests to verify everything is working:**
```bash
docker-compose exec api python scripts/test_observability.py
```

**Expected output:**
```
✓ Basic Query
✓ Metrics Endpoint  
✓ Load Generation
✓ Cache Performance
```

**Simulate alerts (for testing):**
```bash
# Trigger quality degradation alert
docker-compose exec api python scripts/simulate_alerts.py --scenario quality --severity high

# Trigger cost spike alert
docker-compose exec api python scripts/simulate_alerts.py --scenario cost

# Trigger cache degradation alert
docker-compose exec api python scripts/simulate_alerts.py --scenario cache
```

**View metrics in action:**
```bash
# Watch metrics being exposed
watch -n 1 'curl -s http://localhost:8000/api/v1/metrics | head -20'
```

### Local Installation (Without Docker)


1. **Create virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start services independently:**
   ```bash
   # Terminal 1: PostgreSQL (with pgvector)
   # Start PostgreSQL server with pgvector extension
   
   # Terminal 2: Redis
   redis-server
   
   # Terminal 3: FastAPI
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 📚 API Usage Examples

### 1. Ask a Question
Submit a market research query to the multi-agent system:

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key challenges for GenAI adoption in enterprise in 2024?"
  }'
```

**Response:**
```json
{
  "query": "What are the key challenges for GenAI adoption in enterprise in 2024?",
  "response": "Enterprise adoption of GenAI faces several challenges...",
  "cached": false
}
```

**Response time:** ~10-20s (first query) | <100ms (cached)

### 2. Batch Evaluation
Evaluate system performance on multiple test cases using LLM-as-judge:

```bash
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "cases": [
      {
        "query": "What is blockchain?",
        "expected": "Distributed ledger technology..."
      },
      {
        "query": "Top AI trends 2024?",
        "expected": "GenAI adoption, multimodal models..."
      }
    ]
  }'
```

**Response:**
```json
{
  "average_score": 8.5,
  "total_cases": 2,
  "scores": [8.0, 9.0]
}
```

### 3. View Metrics & Costs
Monitor token usage and estimated costs:

```bash
curl http://localhost:8000/api/v1/metrics
```

**Response:**
```json
{
  "total_tokens": 15420,
  "total_cost": "$0.18",
  "total_requests": 12,
  "cached_hits": 3,
  "cache_hit_ratio": 0.25
}
```

### 4. Provide Feedback
Submit feedback for system improvement:

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query": "GenAI adoption trends",
    "rating": 5,
    "comments": "Excellent research and well-structured response"
  }'
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# API Configuration
PORT=8000
ENVIRONMENT=development  # or 'production'

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/market_research

# Cache
REDIS_URL=redis://localhost:6379/0

# LLM Provider
OPENAI_API_KEY=sk-your-key-here

# External APIs
TAVILY_API_KEY=tvly-your-key-here
```

### Dynamic Model Selection

The `LLMFactory` automatically selects models based on:

| Scenario | Model | Reasoning |
|----------|-------|-----------|
| Researcher, short query (<500 chars) | gpt-4o-mini | Cost-effective |
| Researcher, long query (>500 chars) | gpt-4o | More capable |
| Evaluator (any query) | gpt-4o | Higher quality refinement |

---

## 🧪 Testing

Run the full test suite:

```bash
# With Docker
docker-compose exec api pytest -v

# Local environment
pytest -v
```

**Test Coverage:**
- `test_agents.py`: Agent workflow and LangGraph orchestration
- `test_api.py`: API endpoint responses and status codes
- `test_services.py`: Service utilities (cache, LLM factory, metrics)

---

## 📊 Features Explained

### 🤖 Multi-Agent System

**Researcher Agent:**
- Searches internal vector database (RAG) for market documents
- Falls back to web search (Tavily) for missing information
- Uses tool_calling to decide best information source

**Evaluator Agent:**
- Reviews researcher's draft response
- Improves tone, structure, and clarity
- Optimizes for readability and accuracy

### 💾 Caching Strategy

- **Key Generation:** SHA256 hash of query
- **TTL:** 1 hour (configurable)
- **Cache Hit Ratio:** Tracked in `/metrics`
- **Storage:** Redis with async client

### 📈 Token & Cost Tracking

Custom `TokenCostCallbackHandler` captures:
- Input/output tokens per request
- Estimated costs using OpenAI pricing
- Real-time metrics dashboard

### 🔍 RAG Implementation

- **Vector Store:** PGVector with pgvector extension
- **Embedding Models:** 
  - Fast: `text-embedding-3-small` (default)
  - Precise: `text-embedding-3-large` (optional)
- **Collections:**
  - `docs_small` (fast embeddings)
  - `docs_large` (precise embeddings)

---

## 🐛 Troubleshooting

### "Failed to connect to Redis"
- Check if Redis is running: `redis-cli ping`
- Verify `REDIS_URL` in `.env`
- Restart service: `docker-compose restart redis`

### "OPENAI_API_KEY not set"
- Copy `.env.example`: `cp .env.example .env`
- Add your actual API key to `.env`
- Restart API: `docker-compose restart api`

### "PGVector connection failed"
- Ensure pgvector extension is installed
- Check PostgreSQL is running: `docker-compose logs postgres`
- Verify `DATABASE_URL` in `.env`

### Cache not working
- Check Redis logs: `docker-compose logs redis`
- Clear cache: `redis-cli FLUSHDB`
- Verify query is identical (case-sensitive)

### Slow response times
- Check if using gpt-4o or gpt-4o-mini (logs show model used)
- Verify internet connection for web search
- Check PostgreSQL performance: `docker-compose logs postgres`

### Observability Stack Issues

**Prometheus not scraping metrics:**
- Verify API metrics endpoint: `curl http://localhost:8000/api/v1/metrics`
- Check Prometheus targets: http://localhost:9090/targets
- Verify network connection: `docker network ls`
- Restart Prometheus: `docker-compose restart prometheus`

**Grafana dashboards not showing data:**
- Wait 30-60 seconds for Prometheus to populate data
- Verify data source: http://localhost:3000/datasources
- Check dashboard timezone settings
- Manually refresh Prometheus: http://localhost:9090/graph

**Loki not receiving logs:**
- Check Promtail status: `docker-compose logs promtail`
- Verify Promtail config: `config/promtail-config.yml`
- Test Loki directly: http://localhost:3100/ready
- Restart Loki: `docker-compose restart loki`

**Alerts not triggering:**
- Verify alertmanager is running: `docker ps | grep alertmanager`
- Check alert rules: http://localhost:9090/alerts
- Verify Slack webhook in `.env`: `SLACK_WEBHOOK_URL=...`
- Test webhook: `curl -X POST $SLACK_WEBHOOK_URL`

**Metrics not appearing:**
- Check application logs: `docker-compose logs api | grep metric`
- Verify middleware is added in `app/main.py`
- Wait for first query to generate metrics
- Run test script: `docker-compose exec api python scripts/test_observability.py`

---

## 🔮 Future Enhancements

- ✅ **Async Agents**: Switch from `invoke` to `ainvoke` for better concurrency
- ✅ **Streaming Responses**: SSE support for real-time agent output
- ✅ **Authentication**: JWT/OAuth2 with API key management
- ✅ **Rate Limiting**: Per-user/per-API-key limits using slowapi
- ✅ **Hybrid Search**: BM25 + vector search for improved retrieval
- ✅ **Advanced RAG**: Multi-hop retrieval, query reformulation
- ✅ **Analytics Dashboard**: Web UI for metrics and system health
- ✅ **Custom Fine-tuning**: User feedback loops for model adaptation

---

## 📦 Dependencies

Key Python packages:
- **FastAPI** - Web framework
- **LangChain** - LLM orchestration
- **LangGraph** - Agent workflow
- **Pydantic** - Data validation
- **Redis** - Caching
- **PostgreSQL/pgvector** - Vector storage
- **OpenAI API** - LLM provider
- **Tavily** - Web search
- **pytest** - Testing

See `requirements.txt` for complete list and versions.

---

## 📝 License

This project is provided as-is for educational and demonstration purposes.

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Create a feature branch
2. Test thoroughly (run pytest)
3. Submit a pull request

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API documentation at `http://localhost:8000/docs`
3. Check application logs: `docker-compose logs api`
