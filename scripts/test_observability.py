#!/usr/bin/env python3
"""
Test script for the observability and monitoring stack.
Simulates different scenarios to trigger alerts and verify the system is working.

Usage:
    python scripts/test_observability.py
"""

import asyncio
import httpx
import random
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
PROMETHEUS_URL = "http://localhost:9090"
GRAFANA_URL = "http://localhost:3000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(msg: str, color: str = Colors.BLUE):
    """Print colored message"""
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Colors.END}")

async def test_basic_query():
    """Test basic query processing"""
    log("Testing basic query processing...", Colors.BLUE)
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/ask",
                json={"query": "What are the latest trends in AI?"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log(f"✓ Query processed successfully", Colors.GREEN)
                log(f"  - Cached: {data.get('cached', False)}", Colors.GREEN)
                if quality_score := data.get('quality_score'):
                    log(f"  - Quality Score: {quality_score}", Colors.GREEN)
                return True
            else:
                log(f"✗ Failed with status {response.status_code}", Colors.RED)
                return False
    except Exception as e:
        log(f"✗ Error: {e}", Colors.RED)
        return False

async def test_cache_hit():
    """Test cache hit by querying the same question"""
    log("Testing cache performance...", Colors.BLUE)
    
    query = "What is blockchain technology?"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # First query (cache miss)
            t1 = time.time()
            response1 = await client.post(
                f"{API_BASE_URL}/api/v1/ask",
                json={"query": query}
            )
            duration1 = (time.time() - t1) * 1000
            
            if response1.status_code != 200:
                log(f"✗ First query failed", Colors.RED)
                return False
            
            # Second query (cache hit)
            await asyncio.sleep(1)  # Wait a bit
            t2 = time.time()
            response2 = await client.post(
                f"{API_BASE_URL}/api/v1/ask",
                json={"query": query}
            )
            duration2 = (time.time() - t2) * 1000
            
            if response2.status_code != 200:
                log(f"✗ Second query failed", Colors.RED)
                return False
            
            cached = response2.json().get('cached', False)
            log(f"✓ Cache test completed", Colors.GREEN)
            log(f"  - First query: {duration1:.2f}ms (cache miss)", Colors.GREEN)
            log(f"  - Second query: {duration2:.2f}ms (cached: {cached})", Colors.GREEN)
            log(f"  - Speed improvement: {duration1/duration2:.1f}x faster" if duration2 > 0 else "", Colors.GREEN)
            return cached  # Should be True
            
    except Exception as e:
        log(f"✗ Error: {e}", Colors.RED)
        return False

async def test_metrics_endpoint():
    """Test the metrics endpoint"""
    log("Testing Prometheus metrics endpoint...", Colors.BLUE)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/metrics")
            
            if response.status_code == 200:
                content = response.text
                if "cache_hit_ratio" in content and "response_quality_score" in content:
                    log(f"✓ Metrics endpoint working", Colors.GREEN)
                    log(f"  - Contains {len(content.splitlines())} metric lines", Colors.GREEN)
                    return True
                else:
                    log(f"✗ Metrics incomplete", Colors.RED)
                    return False
            else:
                log(f"✗ Failed with status {response.status_code}", Colors.RED)
                return False
    except Exception as e:
        log(f"✗ Error: {e}", Colors.RED)
        return False

async def test_load_generation():
    """Generate some load to populate metrics"""
    log("Generating load for metrics...", Colors.BLUE)
    
    queries = [
        "What are the top AI companies?",
        "How does blockchain work?",
        "What is the future of quantum computing?",
        "Explain cloud computing",
        "What are microservices?",
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = []
            for i in range(5):  # 5 concurrent queries
                query = random.choice(queries)
                tasks.append(
                    client.post(
                        f"{API_BASE_URL}/api/v1/ask",
                        json={"query": query}
                    )
                )
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 200)
            failed = len(results) - successful
            
            log(f"✓ Load test completed", Colors.GREEN)
            log(f"  - Successful: {successful}/{len(results)}", Colors.GREEN)
            if failed > 0:
                log(f"  - Failed: {failed}/{len(results)}", Colors.YELLOW)
            
            return failed == 0
    except Exception as e:
        log(f"✗ Error: {e}", Colors.RED)
        return False

def check_prometheus():
    """Verify Prometheus is accessible"""
    log("Checking Prometheus connection...", Colors.BLUE)
    
    try:
        import requests
        response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
        if response.status_code == 200:
            log(f"✓ Prometheus is accessible", Colors.GREEN)
            log(f"  - URL: {PROMETHEUS_URL}", Colors.GREEN)
            return True
        else:
            log(f"✗ Prometheus returned {response.status_code}", Colors.RED)
            return False
    except Exception as e:
        log(f"✗ Cannot reach Prometheus: {e}", Colors.RED)
        log(f"  - Make sure to run: docker-compose up -d", Colors.YELLOW)
        return False

def check_grafana():
    """Verify Grafana is accessible"""
    log("Checking Grafana connection...", Colors.BLUE)
    
    try:
        import requests
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        if response.status_code == 200:
            log(f"✓ Grafana is accessible", Colors.GREEN)
            log(f"  - URL: {GRAFANA_URL}", Colors.GREEN)
            log(f"  - Default credentials: admin / admin", Colors.YELLOW)
            return True
        else:
            log(f"✗ Grafana returned {response.status_code}", Colors.RED)
            return False
    except Exception as e:
        log(f"✗ Cannot reach Grafana: {e}", Colors.RED)
        log(f"  - Make sure to run: docker-compose up -d", Colors.YELLOW)
        return False

async def main():
    """Run all tests"""
    print()
    print(f"{Colors.BLUE}{'='*60}")
    print(f"Market Research API - Observability Stack Test")
    print(f"{'='*60}{Colors.END}\n")
    
    # Check infrastructure
    log("=== Infrastructure Checks ===", Colors.YELLOW)
    prometheus_ok = check_prometheus()
    grafana_ok = check_grafana()
    
    if not prometheus_ok or not grafana_ok:
        log("\n⚠️  Some infrastructure components are not available", Colors.YELLOW)
        log("Starting stack: docker-compose up -d", Colors.YELLOW)
        return
    
    print()
    log("=== Functional Tests ===", Colors.YELLOW)
    
    # Run tests
    tests = [
        ("Basic Query", test_basic_query),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Load Generation", test_load_generation),
        ("Cache Performance", test_cache_hit),
    ]
    
    results = {}
    for name, test_func in tests:
        print()
        try:
            result = await test_func()
            results[name] = result
        except Exception as e:
            log(f"✗ {name} - Unexpected error: {e}", Colors.RED)
            results[name] = False
    
    # Summary
    print()
    log("=== Test Summary ===", Colors.YELLOW)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {name}")
    
    print()
    if passed == total:
        log(f"All tests passed! ({passed}/{total})", Colors.GREEN)
    else:
        log(f"Some tests failed ({passed}/{total})", Colors.RED)
    
    # Show URLs
    print()
    log("=== Dashboard URLs ===", Colors.YELLOW)
    log("Prometheus: http://localhost:9090", Colors.BLUE)
    log("Grafana: http://localhost:3000", Colors.BLUE)
    log("Loki: http://localhost:3100", Colors.BLUE)
    log("API Docs: http://localhost:8000/docs", Colors.BLUE)
    print()

if __name__ == "__main__":
    asyncio.run(main())
