#!/usr/bin/env python3
"""
Script to simulate low-quality responses and trigger quality alerts.
This helps test the alerting system without actually degrading the API.

Usage:
    python scripts/simulate_quality_alert.py --severity low|high
"""

import asyncio
import httpx
import argparse
from datetime import datetime
from app.services.prometheus_metrics import metrics_tracker

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(msg: str, color: str = Colors.BLUE):
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {msg}{Colors.END}")

async def simulate_quality_degradation(severity: str = "low"):
    """
    Simulate quality score degradation by recording low scores to Prometheus.
    This doesn't actually call the API, just populates metrics.
    
    Args:
        severity: "low" (40-60), "medium" (20-40), "high" (0-20)
    """
    log(f"Simulating {severity} quality degradation...", Colors.YELLOW)
    
    # Determine score range based on severity
    if severity == "low":
        score_range = (40, 60)
        count = 5
    elif severity == "medium":
        score_range = (20, 40)
        count = 10
    else:  # high
        score_range = (0, 20)
        count = 15
    
    log(f"Recording {count} low-quality samples (range: {score_range[0]}-{score_range[1]})", Colors.YELLOW)
    
    import random
    for i in range(count):
        score = random.uniform(score_range[0], score_range[1])
        metrics_tracker.record_response_quality(score, "evaluator")
        log(f"  [{i+1}/{count}] Recorded quality score: {score:.1f}", Colors.BLUE)
        await asyncio.sleep(0.1)  # Small delay between recordings
    
    log(f"✓ Simulation complete - check Grafana for quality alerts", Colors.GREEN)


async def simulate_cost_spike():
    """
    Simulate a cost spike by recording high LLM call costs.
    """
    log("Simulating API cost spike...", Colors.YELLOW)
    
    # Record 10 expensive calls
    expensive_call_cost = 0.25  # $0.25 per call
    for i in range(10):
        metrics_tracker.record_llm_call(
            model="gpt-4o",
            agent_role="researcher",
            duration=5.0,
            input_tokens=2000,
            output_tokens=1000,
            cost=expensive_call_cost
        )
        log(f"  [{i+1}/10] Recorded expensive call: ${expensive_call_cost}", Colors.BLUE)
        await asyncio.sleep(0.5)
    
    log(f"✓ Cost spike recorded - check Cost Dashboard for alerts", Colors.GREEN)


async def simulate_cache_failure():
    """
    Simulate Redis cache failures by recording cache misses.
    """
    log("Simulating cache degradation...", Colors.YELLOW)
    
    # Record more misses than hits
    for i in range(20):
        metrics_tracker.record_cache_miss()
        log(f"  [{i+1}/20] Recorded cache miss", Colors.BLUE)
        if i % 5 == 0:
            await asyncio.sleep(0.2)
    
    # Few hits to keep it below 40%
    for i in range(5):
        metrics_tracker.record_cache_hit()
        log(f"  [+{i+1}/5] Recorded cache hit", Colors.BLUE)
    
    log(f"✓ Cache degradation recorded - check Cache Dashboard for alerts", Colors.GREEN)


async def main():
    parser = argparse.ArgumentParser(
        description="Simulate alerts for the Market Research API"
    )
    parser.add_argument(
        "--severity",
        choices=["low", "medium", "high"],
        default="low",
        help="Severity level for quality simulation"
    )
    parser.add_argument(
        "--scenario",
        choices=["quality", "cost", "cache", "all"],
        default="quality",
        help="Which scenario to simulate"
    )
    
    args = parser.parse_args()
    
    print()
    print(f"{Colors.BLUE}{'='*60}")
    print(f"Alert Simulation Tool")
    print(f"{'='*60}{Colors.END}\n")
    
    try:
        if args.scenario in ["quality", "all"]:
            await simulate_quality_degradation(args.severity)
            print()
        
        if args.scenario in ["cost", "all"]:
            await simulate_cost_spike()
            print()
        
        if args.scenario in ["cache", "all"]:
            await simulate_cache_failure()
            print()
        
        log("=== What to check next ===", Colors.YELLOW)
        log("1. Grafana: http://localhost:3000 (admin/admin)", Colors.BLUE)
        log("2. Prometheus: http://localhost:9090", Colors.BLUE)
        log("3. Check dashboards for updated metrics", Colors.BLUE)
        log("4. Monitor Slack for alert notifications", Colors.BLUE)
        print()
        
    except Exception as e:
        log(f"✗ Error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
