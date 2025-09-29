# ETL Pipeline

This directory contains the ETL Pipeline MVP implementation for extracting health metrics data from Prometheus and loading it into InfluxDB.

## Overview

The ETL pipeline consists of four main components:

1. **PrometheusExtractor** - Extracts metrics from Prometheus
2. **DataTransformer** - Cleans and transforms data
3. **InfluxDBLoader** - Loads data into InfluxDB
4. **ETLPipeline** - Orchestrates the entire process

## Quick Start

### 1. Deploy the ETL Pipeline

```bash
# Run the deployment script
python scripts/deploy_etl.py
```

### 2. Configure the Pipeline

Edit `config/etl.yaml` with your settings:

```yaml
extract:
  prometheus_url: "http://your-prometheus:9090"

load:
  influxdb:
    url: "http://your-influxdb:8086"
    token: "your-influxdb-token"
    org: "your-org"
    bucket: "your-bucket"
```

### 3. Run the Pipeline

```bash
# Start the ETL pipeline
python src/etl/pipeline.py
```

### 4. Monitor the Pipeline

- Check logs: `tail -f logs/etl_pipeline.log`
- Verify data in InfluxDB dashboard
- Run tests: `python -m unittest tests.test_etl`

## Architecture

```
Prometheus → Extract → Transform → Load → InfluxDB
    ↓           ↓         ↓         ↓        ↓
  Metrics    Raw Data  Cleaned   Processed  Storage
            Collection  Data     Data      (Hot/Warm/Cold)
```

## Components

### PrometheusExtractor

Extracts basic application metrics from Prometheus:
- Service availability (`up{job="test-app"}`)
- Request rate (`rate(http_requests_total[5m])`)
- 95th percentile latency
- Error rate

### DataTransformer

Performs basic data cleaning and transformation:
- Removes null values and invalid timestamps
- Validates metric names against whitelist
- Removes duplicate entries
- Converts to InfluxDB line protocol format

### InfluxDBLoader

Loads transformed data into InfluxDB:
- Converts data to InfluxDB Point objects
- Handles batch writes with error handling
- Tests connectivity before operations
- Manages connection lifecycle

### ETLPipeline

Orchestrates the entire ETL process:
- Loads configuration from YAML
- Initializes all components
- Runs continuous ETL cycles
- Handles errors and logging
- Provides statistics and monitoring

## Configuration

The pipeline is configured via `config/etl.yaml`:

```yaml
# Extract configuration
extract:
  prometheus_url: "http://localhost:9090"
  timeout: 30

# Transform configuration
transform:
  valid_metrics:
    - "up"
    - "http_requests_total"
    # ... more metrics

# Load configuration
load:
  influxdb:
    url: "http://localhost:8086"
    token: "your-token"
    org: "monitoring"
    bucket: "health_metrics"

# Pipeline configuration
pipeline:
  interval_seconds: 300  # 5 minutes
  log_level: "INFO"
```

## Testing

Run the test suite:

```bash
python -m unittest tests.test_etl
```

The tests cover:
- Component initialization
- Data extraction and transformation
- Data loading operations
- Pipeline orchestration
- Error handling scenarios

## Monitoring

The pipeline provides:
- Detailed logging to `logs/etl_pipeline.log`
- Pipeline statistics (success rate, data points processed)
- Health checks for external services
- Error tracking and reporting

## Dependencies

Required Python packages:
- `requests` - HTTP client for Prometheus API
- `pandas` - Data manipulation and analysis
- `influxdb-client` - InfluxDB Python client
- `pyyaml` - YAML configuration file parsing

## Limitations (MVP)

This MVP implementation has the following limitations:
- Basic error handling only
- No retry logic or circuit breakers
- Synchronous operations only
- Limited data validation
- No advanced monitoring or alerting

For production use, see the production ETL plan in `docs/etl_production_plan.md`.

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify Prometheus/InfluxDB URLs are accessible
   - Check network connectivity
   - Validate authentication tokens

2. **Configuration Errors**
   - Ensure YAML syntax is correct
   - Verify all required fields are present
   - Check file permissions

3. **Data Issues**
   - Verify Prometheus has data for the configured metrics
   - Check InfluxDB bucket exists and is writable
   - Review logs for transformation errors

### Debug Mode

Enable debug logging by setting log level to DEBUG in configuration:

```yaml
pipeline:
  log_level: "DEBUG"
```

## Next Steps

1. Update configuration with your environment settings
2. Test with sample data
3. Monitor pipeline performance
4. Plan migration to production ETL pipeline

For more information, see:
- `docs/etl_mvp_plan.md` - Detailed MVP implementation plan
- `docs/etl_production_plan.md` - Production-ready ETL pipeline plan
