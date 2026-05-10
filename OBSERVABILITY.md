# Observability Stack - Complete Guide

This document provides detailed instructions for using the production-grade monitoring and alerting system integrated into the Market Research API.

## 📊 Overview

The observability stack provides:
- **Real-time metrics** collection with Prometheus
- **Beautiful dashboards** with Grafana
- **Centralized logs** with Loki
- **Automated alerts** with Alertmanager
- **Slack notifications** for critical issues

## 🚀 Quick Start

### 1. Start the Stack

```bash
# Start all services including monitoring
docker-compose up -d --build

# Verify everything is running
docker-compose ps
```

### 2. Access Dashboards

```
Prometheus: http://localhost:9090
Grafana: http://localhost:3000 (admin/admin)
Loki: http://localhost:3100
Alertmanager: http://localhost:9093
API: http://localhost:8000/docs
```

### 3. Make Some Queries

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest AI trends?"}'
```

### 4. View Metrics

```bash
# Prometheus format (scraped by Prometheus)
curl http://localhost:8000/api/v1/metrics | head -20

# JSON summary
curl http://localhost:8000/api/v1/metrics | jq .
```

## 📈 Key Metrics

### Performance Metrics

```
agent_execution_duration_seconds{agent_role="researcher"}
agent_execution_duration_seconds{agent_role="evaluator"}
api_request_duration_seconds{endpoint="/api/v1/ask"}
llm_call_duration_seconds{model="gpt-4o-mini"}
```

**Interpretation:**
- Higher values = slower responses
- Use Prometheus quantile function: `histogram_quantile(0.99, ...)`
- Alert if p99 > 30 seconds

### Quality Metrics

```
response_quality_score{agent_role="evaluator"}
response_quality_samples_total{quality_level="excellent|good|fair|poor"}
```

**Interpretation:**
- Score 0-100 (higher is better)
- Quality evaluated on ~10% of requests (configurable)
- Alert if >5% poor quality responses

### Cost Metrics

```
api_cost_total_usd              # Cumulative cost
api_cost_per_hour_usd           # Estimated hourly cost
api_cost_by_model_usd{model="gpt-4o"}
tokens_used_total{model="gpt-4o", token_type="input|output"}
```

**Interpretation:**
- Monitor hourly cost trends
- Alert if hourly estimate > $2 USD
- Track cost by model to optimize

### Cache Metrics

```
cache_hit_ratio                 # 0-1 (0 = all misses, 1 = all hits)
cache_hits_total
cache_misses_total
```

**Interpretation:**
- Healthy ratio: > 0.8 (80% hits)
- Alert if < 0.4 (40%) for 15+ minutes
- Indicates Redis stability

### Business Metrics

```
queries_by_type_total{query_type="rag|web_search|hybrid"}
api_requests_total{status="200|4xx|5xx"}
errors_total{error_type="..."}
```

**Interpretation:**
- Track query distribution (RAG vs web search)
- Monitor error rates
- Alert if > 10% error rate

## 🔔 Understanding Alerts

### Quality Alerts

**`ResponseQualityDegraded`**
- Triggers: >5% low-quality responses (score < 60) for 5 minutes
- Severity: WARNING
- Actions:
  1. Check OpenAI API status
  2. Review recent code changes
  3. Verify RAG document quality
  4. Check if using wrong model

**`PanicButtonQualityAlert`**
- Triggers: >10% poor quality responses (score < 40) for 5 minutes
- Severity: CRITICAL (pages on-call engineer)
- Actions:
  1. STOP - something is seriously wrong
  2. Check OpenAI API issues
  3. Review deployment changes
  4. Consider rollback

### Cost Alerts

**`HourlyApiCostBudgetExceeded`**
- Triggers: Hourly cost > $2 USD for 10 minutes
- Severity: WARNING
- Actions:
  1. Analyze query patterns
  2. Check if queries are unusually long
  3. Verify model selection (might be using gpt-4o when unnecessary)
  4. Consider rate limiting

**`DailyCostProjectionExceeded`**
- Triggers: Daily projection > $50 for 30 minutes
- Severity: CRITICAL
- Actions:
  1. Immediate investigation required
  2. Review traffic patterns
  3. Implement rate limiting
  4. Switch to RAG-only mode
  5. Contact OpenAI support

### Cache Alerts

**`CacheDegradation`**
- Triggers: Hit ratio < 40% for 15 minutes
- Severity: WARNING
- Actions:
  1. Check Redis memory: `redis-cli INFO memory`
  2. Monitor Redis CPU
  3. Restart Redis if needed
  4. Check if queries changed (less cacheable)

**`CacheDown`**
- Triggers: Hit ratio == 0 for 5 minutes
- Severity: CRITICAL
- Actions:
  1. Restart Redis: `docker-compose restart redis`
  2. Check Redis logs: `docker-compose logs redis -f`
  3. Verify Redis container exists: `docker ps | grep redis`
  4. Check disk space

### Performance Alerts

**`AgentP99LatencyHigh`**
- Triggers: p99 latency > 30 seconds for 5 minutes
- Severity: WARNING
- Actions:
  1. Check LLM API latency
  2. Monitor network connectivity
  3. Review database query performance
  4. Consider caching common queries

## 📊 Dashboards

### 1. Agent Flight Deck

**What it shows:**
- Real-time agent execution latency (p50, p99)
- Query type distribution (pie chart)
- Response quality score gauge
- Cache hit ratio gauge
- Error rate gauge

**How to use:**
- Monitor agent performance during deployments
- Identify performance regressions
- Track quality trends

**Key queries:**
```promql
# Agent latency p99
histogram_quantile(0.99, rate(agent_execution_duration_seconds_bucket[5m])) * 1000

# Query distribution
sum(rate(queries_by_type_total[5m])) by (query_type)

# Quality score
response_quality_score{agent_role="evaluator"}
```

### 2. Cost Dashboard

**What it shows:**
- Hourly cost (with budget line at $2)
- Total cost accumulated
- Projected daily cost
- Cost by model (hourly breakdown)
- Hourly cost trend

**How to use:**
- Daily budget monitoring
- Model cost comparison
- Identify cost spikes
- Forecast monthly spend

**Key queries:**
```promql
# Hourly cost
api_cost_per_hour_usd

# Total cost
api_cost_total_usd

# Cost by model
increase(api_cost_by_model_usd[1h])

# Projected daily
api_cost_total_usd * 24
```

### 3. Semantic Drift Monitor

**What it shows:**
- Quality score timeline (7 days)
- Quality distribution pie chart (last hour)
- Quality tier stacked bar chart
- Trend analysis

**How to use:**
- Detect gradual quality degradation
- Identify when quality threshold is crossed
- Verify improvements after fixes
- Long-term trend analysis

**Key queries:**
```promql
# Quality over time
response_quality_score{agent_role="evaluator"}

# Quality distribution
sum(rate(response_quality_samples_total{quality_level="excellent"}[1h]))
```

### 4. Cache & Request Status

**What it shows:**
- Current cache hit ratio (gauge)
- Cache hits in last hour (stat)
- Cache misses in last hour (stat)
- Cache ratio trend
- Request status distribution (2xx/4xx/5xx)
- Requests by endpoint

**How to use:**
- Monitor cache efficiency
- Track request success rates
- Identify problematic endpoints
- Detect request pattern changes

## 🧪 Testing Alerts

### Simulate Quality Degradation

```bash
# Low quality alert (triggers at 5% low quality)
docker-compose exec api python scripts/simulate_alerts.py \
  --scenario quality \
  --severity low

# Medium quality alert
docker-compose exec api python scripts/simulate_alerts.py \
  --scenario quality \
  --severity medium

# High quality alert (triggers panic at 10% poor quality)
docker-compose exec api python scripts/simulate_alerts.py \
  --scenario quality \
  --severity high
```

### Simulate Cost Spike

```bash
# Record expensive API calls
docker-compose exec api python scripts/simulate_alerts.py \
  --scenario cost
```

**Verification:**
- Wait ~5 minutes for alert to trigger
- Check Prometheus: http://localhost:9090/alerts
- Check Alertmanager: http://localhost:9093

### Simulate Cache Failure

```bash
# Record cache misses
docker-compose exec api python scripts/simulate_alerts.py \
  --scenario cache
```

## 🔧 Configuration

### Adjusting Alert Thresholds

Edit `config/alerts.yml`:

```yaml
- alert: HourlyApiCostBudgetExceeded
  expr: api_cost_per_hour_usd > 2.0  # ← Change threshold
  for: 10m  # ← Change duration
```

Then reload:
```bash
curl -X POST http://localhost:9090/-/reload
```

### Changing Quality Sample Rate

In `app/services/quality_evaluator.py`:

```python
quality_evaluator = QualityEvaluator(sample_rate=0.1)  # ← Change from 0.1 (10%)
```

### Slack Webhook Setup

1. Create incoming webhook: https://api.slack.com/apps
2. Add to `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   ```
3. Restart Alertmanager:
   ```bash
   docker-compose restart alertmanager
   ```

## 📝 Log Queries (Loki)

Access Grafana → Explore → Select "Loki"

### Common queries

```
# All logs from API service
{service="api"}

# Error logs only
{service="api"} | json | level="ERROR"

# Slow queries (> 5 seconds)
{service="api"} | json | duration_ms > 5000

# Specific agent execution
{service="api"} | json | agent_role="researcher"

# Cost tracking logs
{service="api"} | json | cost_usd > 0
```

## 🐛 Common Issues

### "Prometheus targets show 'DOWN'"

**Solution:**
```bash
# Verify API is running
curl http://localhost:8000/api/v1/metrics

# Check network
docker-compose ps

# Restart Prometheus
docker-compose restart prometheus
```

### "Grafana shows 'No Data'"

**Solution:**
```bash
# Wait for Prometheus to scrape
# First scrape happens after scrape_interval (15s)
# Then dashboards query recent data (last 6 hours default)

# Make some queries first
curl -X POST http://localhost:8000/api/v1/ask \
  -d '{"query": "test"}' \
  -H "Content-Type: application/json"

# Wait 30 seconds for metrics to appear
sleep 30

# Refresh Grafana dashboard
```

### "Alerts not sending to Slack"

**Solution:**
1. Verify webhook URL in `.env`
2. Test webhook manually:
   ```bash
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text": "Test message"}'
   ```
3. Check Alertmanager logs:
   ```bash
   docker-compose logs alertmanager | tail -20
   ```

## 📚 Resources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [Loki Docs](https://grafana.com/docs/loki/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Alert Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
