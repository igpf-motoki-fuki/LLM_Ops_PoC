# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code usage monitoring stack with full observability. Collects telemetry from developer PCs via OTLP protocol.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           各開発者PC (Claude Code)                   │
│     OTLP Exporter → metrics/logs/traces            │
└─────────────────────┬───────────────────────────────┘
                      │ OTLP (gRPC:4317 / HTTP:4318)
                      ▼
┌─────────────────────────────────────────────────────┐
│              監視サーバー                            │
│  ┌─────────────────────┐                           │
│  │   OTEL Collector    │                           │
│  │  (port 4317/4318)   │                           │
│  └──────────┬──────────┘                           │
│             │                                       │
│    ┌────────┴────────┐                             │
│    ▼                 ▼                             │
│ ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│ │Prometheus│   │   Loki   │   │ Promtail │        │
│ │  :9090   │   │  :3100   │   │(Docker)  │        │
│ └────┬─────┘   └────┬─────┘   └────┬─────┘        │
│      │              │              │               │
│      └──────────────┼──────────────┘               │
│                     ▼                              │
│              ┌─────────────┐                       │
│              │   Grafana   │                       │
│              │   :3000     │                       │
│              └─────────────┘                       │
└─────────────────────────────────────────────────────┘
```

## Directory Structure

- **prometheus/**: Prometheus configuration
- **grafana/**: Grafana provisioning (datasources: Prometheus, Loki)
- **loki/**: Loki server configuration
- **promtail/**: Docker container log collection
- **otel-collector/**: OTEL Collector configuration (OTLP receiver)
- **docs/**: Task lists and documentation

## Commands

### Start monitoring stack
```bash
docker compose up -d
```

### Check service status
```bash
docker compose ps
curl http://localhost:9090/-/ready      # Prometheus
curl http://localhost:3100/ready        # Loki
curl http://localhost:8888/metrics      # OTEL Collector
```

### Access UIs
- Grafana: http://localhost:3000 (admin/changeme)
- Prometheus: http://localhost:9090

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Web UI / API |
| Grafana | 3000 | Dashboard |
| Loki | 3100 | Log API |
| OTEL Collector | 4317 | OTLP gRPC (開発者PC接続用) |
| OTEL Collector | 4318 | OTLP HTTP (開発者PC接続用) |
| OTEL Collector | 8888 | Internal metrics |

## Client Configuration

各開発者PCでClaude CodeのOTLP出力を設定:

```bash
# OTEL Collector endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT=http://<監視サーバーIP>:4317
```
