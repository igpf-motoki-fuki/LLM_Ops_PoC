# OTEL Collector + Loki 追加実装タスクリスト

## 概要

Claude Code監視スタックにOTEL Collector、Loki、Promtailを追加し、フル機能の監視基盤を構築する。

## タスク一覧

### 新規ファイル作成

- [x] **Task 1**: `exporter/Dockerfile` - Exporterコンテナ化
- [x] **Task 2**: `loki/loki-config.yml` - Lokiサーバー設定
- [x] **Task 3**: `promtail/promtail-config.yml` - ログ収集設定
- [x] **Task 4**: `otel-collector/otel-collector-config.yml` - OTEL Collector設定
- [x] **Task 5**: `grafana/provisioning/datasources/loki.yml` - Lokiデータソース

### 既存ファイル変更

- [x] **Task 6**: `docker-compose.yml` - 4サービス追加（exporter, loki, promtail, otel-collector）
- [x] **Task 7**: `prometheus/prometheus.yml` - OTEL Collector scrape設定追加

### 検証

- [ ] **Task 8**: 全サービス起動確認
- [ ] **Task 9**: Grafanaでメトリクス・ログ表示確認

## 依存関係

```
Task 1 (Dockerfile)
    ↓
Task 6 (docker-compose.yml) ← Task 2, 3, 4, 5
    ↓
Task 7 (prometheus.yml)
    ↓
Task 8, 9 (検証)
```

## 検証コマンド

```bash
# 環境変数設定
export ANTHROPIC_ADMIN_API_KEY=sk-ant-admin-xxx

# 全サービス起動
docker compose up -d --build

# 各サービス確認
curl http://localhost:9101/metrics      # Exporter
curl http://localhost:9090/-/ready      # Prometheus
curl http://localhost:3100/ready        # Loki
curl http://localhost:8888/metrics      # OTEL Collector

# Grafana: http://localhost:3000 (admin/changeme)
```

## ポート一覧

| サービス | ポート | 用途 |
|----------|--------|------|
| Exporter | 9101 | Prometheusメトリクス |
| Prometheus | 9090 | Web UI / API |
| Grafana | 3000 | ダッシュボード |
| Loki | 3100 | ログAPI |
| OTEL Collector | 4317 | OTLP gRPC |
| OTEL Collector | 4318 | OTLP HTTP |
| OTEL Collector | 8888 | 内部メトリクス |
