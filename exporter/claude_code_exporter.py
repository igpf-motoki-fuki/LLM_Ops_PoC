"""
Claude Code Admin API → Prometheus Custom Exporter

Claude Code Analytics API から日次メトリクスを取得し、
Prometheus が scrape 可能な /metrics エンドポイントとして公開する。
"""

import os
import time
import logging
import threading
from datetime import datetime, timezone, timedelta

import requests
from prometheus_client import start_http_server, Gauge, Info
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ADMIN_API_KEY = os.environ["ANTHROPIC_ADMIN_API_KEY"]  # sk-ant-admin...
EXPORTER_PORT = int(os.environ.get("EXPORTER_PORT", "9101"))
POLL_INTERVAL_SEC = int(os.environ.get("POLL_INTERVAL_SEC", "3600"))  # 1 hour
API_BASE = "https://api.anthropic.com/v1/organizations/usage_report/claude_code"
API_VERSION = "2023-06-01"
PAGE_LIMIT = 1000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus Metrics Definition
# ---------------------------------------------------------------------------
LABELS = ["user_email", "customer_type", "terminal_type"]
MODEL_LABELS = ["user_email", "model"]

# Core metrics
g_sessions = Gauge(
    "claude_code_sessions_total",
    "Number of Claude Code sessions",
    LABELS,
)
g_lines_added = Gauge(
    "claude_code_lines_added_total",
    "Lines of code added by Claude Code",
    LABELS,
)
g_lines_removed = Gauge(
    "claude_code_lines_removed_total",
    "Lines of code removed by Claude Code",
    LABELS,
)
g_commits = Gauge(
    "claude_code_commits_total",
    "Commits created by Claude Code",
    LABELS,
)
g_pull_requests = Gauge(
    "claude_code_pull_requests_total",
    "Pull requests created by Claude Code",
    LABELS,
)

# Tool action metrics
TOOL_LABELS = ["user_email", "tool_name"]
g_tool_accepted = Gauge(
    "claude_code_tool_accepted_total",
    "Tool proposals accepted",
    TOOL_LABELS,
)
g_tool_rejected = Gauge(
    "claude_code_tool_rejected_total",
    "Tool proposals rejected",
    TOOL_LABELS,
)

# Model-level token & cost metrics
g_tokens_input = Gauge(
    "claude_code_tokens_input_total",
    "Input tokens by model",
    MODEL_LABELS,
)
g_tokens_output = Gauge(
    "claude_code_tokens_output_total",
    "Output tokens by model",
    MODEL_LABELS,
)
g_tokens_cache_read = Gauge(
    "claude_code_tokens_cache_read_total",
    "Cache read tokens by model",
    MODEL_LABELS,
)
g_tokens_cache_creation = Gauge(
    "claude_code_tokens_cache_creation_total",
    "Cache creation tokens by model",
    MODEL_LABELS,
)
g_estimated_cost_cents = Gauge(
    "claude_code_estimated_cost_cents",
    "Estimated cost in USD cents by model",
    MODEL_LABELS,
)

# Exporter health
g_last_poll_timestamp = Gauge(
    "claude_code_exporter_last_poll_timestamp",
    "Unix timestamp of the last successful API poll",
)
g_last_poll_records = Gauge(
    "claude_code_exporter_last_poll_records",
    "Number of records fetched in last poll",
)

# ---------------------------------------------------------------------------
# API Fetching (with pagination)
# ---------------------------------------------------------------------------
def fetch_analytics(target_date: str) -> list[dict]:
    """Fetch all pages of Claude Code analytics for a given date."""
    headers = {
        "anthropic-version": API_VERSION,
        "x-api-key": ADMIN_API_KEY,
        "User-Agent": "ClaudeCodeExporter/1.0.0",
    }
    all_records = []
    page = None

    while True:
        params = {"starting_at": target_date, "limit": PAGE_LIMIT}
        if page:
            params["page"] = page

        try:
            resp = requests.get(API_BASE, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("API request failed: %s", exc)
            break

        body = resp.json()
        records = body.get("data", [])
        all_records.extend(records)
        logger.info(
            "Fetched %d records for %s (page=%s)", len(records), target_date, page or "first"
        )

        if body.get("has_more") and body.get("next_page"):
            page = body["next_page"]
        else:
            break

    return all_records


# ---------------------------------------------------------------------------
# Metrics Update
# ---------------------------------------------------------------------------
def get_actor_email(record: dict) -> str:
    """Extract user email from actor field."""
    actor = record.get("actor", {})
    if actor.get("type") == "user_actor":
        return actor.get("email_address", "unknown")
    elif actor.get("type") == "api_actor":
        return actor.get("api_key_name", "api_key_unknown")
    return "unknown"


def update_metrics(records: list[dict]):
    """Update all Prometheus gauges from API records."""
    for record in records:
        email = get_actor_email(record)
        ctype = record.get("customer_type", "unknown")
        ttype = record.get("terminal_type", "unknown")
        labels = [email, ctype, ttype]

        # Core metrics
        core = record.get("core_metrics", {})
        g_sessions.labels(*labels).set(core.get("num_sessions", 0))

        loc = core.get("lines_of_code", {})
        g_lines_added.labels(*labels).set(loc.get("added", 0))
        g_lines_removed.labels(*labels).set(loc.get("removed", 0))

        g_commits.labels(*labels).set(core.get("commits_by_claude_code", 0))
        g_pull_requests.labels(*labels).set(core.get("pull_requests_by_claude_code", 0))

        # Tool actions
        tool_actions = record.get("tool_actions", {})
        for tool_name, actions in tool_actions.items():
            g_tool_accepted.labels(email, tool_name).set(actions.get("accepted", 0))
            g_tool_rejected.labels(email, tool_name).set(actions.get("rejected", 0))

        # Model breakdown
        for mb in record.get("model_breakdown", []):
            model = mb.get("model", "unknown")
            tokens = mb.get("tokens", {})
            g_tokens_input.labels(email, model).set(tokens.get("input", 0))
            g_tokens_output.labels(email, model).set(tokens.get("output", 0))
            g_tokens_cache_read.labels(email, model).set(tokens.get("cache_read", 0))
            g_tokens_cache_creation.labels(email, model).set(tokens.get("cache_creation", 0))

            cost = mb.get("estimated_cost", {})
            g_estimated_cost_cents.labels(email, model).set(cost.get("amount", 0))


# ---------------------------------------------------------------------------
# Polling Loop
# ---------------------------------------------------------------------------
def poll_loop():
    """Periodically fetch today's analytics and update metrics."""
    while True:
        # 当日の日付 (UTC) を取得
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        logger.info("Polling Claude Code Analytics API for date=%s ...", today)

        records = fetch_analytics(today)
        if records:
            update_metrics(records)
            g_last_poll_records.set(len(records))
        else:
            # データがまだない場合は前日も試す
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            logger.info("No data for today, trying yesterday=%s ...", yesterday)
            records = fetch_analytics(yesterday)
            if records:
                update_metrics(records)
                g_last_poll_records.set(len(records))
            else:
                logger.warning("No data available for today or yesterday.")
                g_last_poll_records.set(0)

        g_last_poll_timestamp.set(time.time())
        logger.info("Next poll in %d seconds.", POLL_INTERVAL_SEC)
        time.sleep(POLL_INTERVAL_SEC)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    logger.info("Starting Claude Code Exporter on port %d", EXPORTER_PORT)
    start_http_server(EXPORTER_PORT)
    logger.info("Prometheus metrics available at http://0.0.0.0:%d/metrics", EXPORTER_PORT)
    poll_loop()


if __name__ == "__main__":
    main()
