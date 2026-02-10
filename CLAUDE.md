# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code usage monitoring stack with full observability: metrics (Prometheus), logs (Loki), and telemetry pipeline (OTEL Collector).

## Architecture

```
Anthropic Admin API
       ↓
┌─────────────────────┐
│ claude-code-exporter│ (port 9101)
└─────────┬───────────┘
          │ scrape
          ↓
┌─────────────────────┐     ┌─────────────────┐
│   OTEL Collector    │────→│   Prometheus    │
│  (port 4317/4318)   │     │   (port 9090)   │
└─────────────────────┘     └────────┬────────┘
                                     │
┌─────────────────────┐              │
│     Promtail        │              │
│ (Docker logs収集)   │              │
└─────────┬───────────┘              │
          ↓                          │
┌─────────────────────┐              │
│       Loki          │              │
│    (port 3100)      │              │
└─────────┬───────────┘              │
          └──────────┬───────────────┘
                     ↓
              ┌─────────────┐
              │   Grafana   │
              │ (port 3000) │
              └─────────────┘
```

## Directory Structure

- **exporter/**: Python exporter + Dockerfile
- **prometheus/**: Prometheus configuration
- **grafana/**: Grafana provisioning (datasources: Prometheus, Loki)
- **loki/**: Loki server configuration
- **promtail/**: Log collection agent configuration
- **otel-collector/**: OTEL Collector configuration
- **docs/**: Task lists and documentation

## Commands

### Start monitoring stack
```bash
export ANTHROPIC_ADMIN_API_KEY=sk-ant-admin-xxx
docker compose up -d --build
```

### Check service status
```bash
docker compose ps
curl http://localhost:9101/metrics      # Exporter
curl http://localhost:9090/-/ready      # Prometheus
curl http://localhost:3100/ready        # Loki
curl http://localhost:8888/metrics      # OTEL Collector
```

### Access UIs
- Grafana: http://localhost:3000 (admin/changeme)
- Prometheus: http://localhost:9090
- Exporter metrics: http://localhost:9101/metrics

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_ADMIN_API_KEY` | Yes | - | Admin API key (sk-ant-admin-...) |
| `EXPORTER_PORT` | No | 9101 | Exporter HTTP port |
| `POLL_INTERVAL_SEC` | No | 3600 | API polling interval in seconds |

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Exporter | 9101 | Prometheus metrics |
| Prometheus | 9090 | Web UI / API |
| Grafana | 3000 | Dashboard |
| Loki | 3100 | Log API |
| OTEL Collector | 4317 | OTLP gRPC |
| OTEL Collector | 4318 | OTLP HTTP |
| OTEL Collector | 8888 | Internal metrics |

## Exposed Metrics

Core metrics (labels: `user_email`, `customer_type`, `terminal_type`):
- `claude_code_sessions_total`, `claude_code_lines_added_total`, `claude_code_lines_removed_total`
- `claude_code_commits_total`, `claude_code_pull_requests_total`

Tool metrics (labels: `user_email`, `tool_name`):
- `claude_code_tool_accepted_total`, `claude_code_tool_rejected_total`

Model metrics (labels: `user_email`, `model`):
- `claude_code_tokens_input_total`, `claude_code_tokens_output_total`
- `claude_code_tokens_cache_read_total`, `claude_code_tokens_cache_creation_total`
- `claude_code_estimated_cost_cents`

Exporter health:
- `claude_code_exporter_last_poll_timestamp`, `claude_code_exporter_last_poll_records`
