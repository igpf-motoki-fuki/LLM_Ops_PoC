# OTEL Collector + Loki 監視スタック タスクリスト

## 概要

各開発者PCからOTLPでテレメトリを収集する監視基盤を構築する。

## タスク一覧

### 新規ファイル作成

- [x] **Task 1**: `loki/loki-config.yml` - Lokiサーバー設定
- [x] **Task 2**: `promtail/promtail-config.yml` - Dockerログ収集設定
- [x] **Task 3**: `otel-collector/otel-collector-config.yml` - OTEL Collector設定（OTLP受信）
- [x] **Task 4**: `grafana/provisioning/datasources/loki.yml` - Lokiデータソース

### 既存ファイル変更

- [x] **Task 5**: `docker-compose.yml` - loki, promtail, otel-collector追加
- [x] **Task 6**: `prometheus/prometheus.yml` - remote-write有効化

### 検証

- [ ] **Task 7**: 全サービス起動確認
- [ ] **Task 8**: OTLP受信テスト
- [ ] **Task 9**: Grafanaでメトリクス・ログ表示確認

## アーキテクチャ

```
開発者PC (Claude Code)
    │
    │ OTLP (gRPC:4317 / HTTP:4318)
    ▼
OTEL Collector
    │
    ├──→ Prometheus (メトリクス)
    └──→ Loki (ログ)
           │
           ▼
        Grafana
```

## 検証コマンド

```bash
# 全サービス起動
docker compose up -d

# 各サービス確認
docker compose ps
curl http://localhost:9090/-/ready      # Prometheus
curl http://localhost:3100/ready        # Loki
curl http://localhost:8888/metrics      # OTEL Collector

# OTLP受信テスト (grpcurl必要)
grpcurl -plaintext localhost:4317 list

# Grafana: http://localhost:3000 (admin/changeme)
```

## ポート一覧

| サービス | ポート | 用途 |
|----------|--------|------|
| Prometheus | 9090 | Web UI / API |
| Grafana | 3000 | ダッシュボード |
| Loki | 3100 | ログAPI |
| OTEL Collector | 4317 | OTLP gRPC |
| OTEL Collector | 4318 | OTLP HTTP |
| OTEL Collector | 8888 | 内部メトリクス |

## クライアント設定

各開発者PCでのOTLP設定例:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://<監視サーバーIP>:4317
```
