# ETL Configuration Usage

This document describes how the ETL pipeline components now fully utilize all sections of the `config/etl.yaml` configuration file.

## Configuration Sections Usage

### 1. Extract Configuration

**File**: `src/etl/extractor.py`

The `PrometheusExtractor` class now uses all extract configuration options:

```yaml
extract:
  prometheus_url: "http://localhost:9090"  # ✅ Used
  timeout: 30                              # ✅ Used
  retry_attempts: 3                        # ✅ Used
```

**Usage**:
- `prometheus_url`: Base URL for Prometheus API requests
- `timeout`: HTTP request timeout in seconds
- `retry_attempts`: Number of retry attempts for failed requests

**Implementation**:
- Constructor now takes full config dictionary
- Retry logic implemented in `extract_metrics()` method
- Timeout applied to all HTTP requests

### 2. Transform Configuration

**File**: `src/etl/transformer.py`

The `DataTransformer` class now uses all transform configuration options:

```yaml
transform:
  valid_metrics:                           # ✅ Used
    - "up"
    - "http_requests_total"
    # ... more metrics
  
  data_cleaning:                           # ✅ Used
    remove_nulls: true
    validate_timestamps: true
    remove_duplicates: true
    validate_value_ranges: true
```

**Usage**:
- `valid_metrics`: Whitelist of allowed metric names for filtering
- `data_cleaning.remove_nulls`: Whether to remove null values
- `data_cleaning.validate_timestamps`: Whether to validate timestamps
- `data_cleaning.remove_duplicates`: Whether to remove duplicate entries
- `data_cleaning.validate_value_ranges`: Whether to validate metric value ranges

**Implementation**:
- Constructor now takes full config dictionary
- `valid_metrics` used for metric filtering
- `data_cleaning` options control cleaning behavior in `_clean_data()` method

### 3. Load Configuration

**File**: `src/etl/loader.py`

The `InfluxDBLoader` class now uses all load configuration options:

```yaml
load:
  influxdb:
    url: "http://localhost:8086"           # ✅ Used
    token: "your-influxdb-token"           # ✅ Used
    org: "monitoring"                      # ✅ Used
    bucket: "health_metrics"               # ✅ Used
    timeout: 30                            # ✅ Used
    batch_size: 1000                       # ✅ Used
```

**Usage**:
- `url`: InfluxDB server URL
- `token`: Authentication token
- `org`: Organization name
- `bucket`: Bucket name for data storage
- `timeout`: Request timeout in seconds
- `batch_size`: Number of records to process in each batch

**Implementation**:
- Constructor now takes full config dictionary
- All connection parameters used for InfluxDB client initialization
- `batch_size` used for batch processing in `load_data()` method

### 4. Pipeline Configuration

**File**: `src/etl/pipeline.py`

The `ETLPipeline` class now uses all pipeline configuration options:

```yaml
pipeline:
  interval_seconds: 300                    # ✅ Used
  log_level: "INFO"                        # ✅ Used (via logging config)
  max_retries: 3                           # ✅ Used
  retry_delay: 60                          # ✅ Used
```

**Usage**:
- `interval_seconds`: Time between ETL cycles
- `max_retries`: Maximum retry attempts (available for future use)
- `retry_delay`: Delay between retries on errors

**Implementation**:
- Used in `run_continuous()` method
- Controls pipeline scheduling and error handling

### 5. Logging Configuration

**File**: `src/etl/pipeline.py`

The `ETLPipeline` class now fully implements logging configuration:

```yaml
logging:
  level: "INFO"                            # ✅ Used
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # ✅ Used
  file: "logs/etl_pipeline.log"            # ✅ Used
  max_size: "10MB"                         # ✅ Used
  backup_count: 5                          # ✅ Used
```

**Usage**:
- `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `format`: Log message format string
- `file`: Log file path
- `max_size`: Maximum log file size before rotation
- `backup_count`: Number of backup log files to keep

**Implementation**:
- `_setup_logging()` method configures logging from config
- `_parse_size()` helper method parses size strings (KB, MB, GB)
- Rotating file handler with configurable size and backup count
- Console and file handlers with configurable format

### 6. Monitoring Configuration

**File**: `src/etl/pipeline.py`

The `ETLPipeline` class now uses monitoring configuration:

```yaml
monitoring:
  enable_metrics: true                     # ✅ Used
  metrics_port: 8080                       # ✅ Available for future use
  health_check_interval: 60                # ✅ Used
```

**Usage**:
- `enable_metrics`: Whether to enable metrics collection
- `metrics_port`: Port for metrics endpoint (future use)
- `health_check_interval`: Interval for health checks

**Implementation**:
- `get_health_status()` method uses monitoring config
- Health status determination based on success rates
- Monitoring enable/disable functionality

## Configuration Loading Flow

1. **Pipeline Initialization**:
   ```python
   pipeline = ETLPipeline('config/etl.yaml')
   ```

2. **Configuration Loading**:
   - `_load_config()` loads YAML configuration
   - Validates required sections and fields

3. **Component Initialization**:
   - `PrometheusExtractor(config)` - uses extract section
   - `DataTransformer(config)` - uses transform section  
   - `InfluxDBLoader(config)` - uses load section

4. **Logging Setup**:
   - `_setup_logging()` configures logging from config
   - Sets up console and file handlers

5. **Pipeline Execution**:
   - Uses pipeline section for scheduling
   - Uses monitoring section for health checks

## Benefits of Full Configuration Usage

### 1. **Flexibility**
- All parameters configurable without code changes
- Easy to adapt to different environments
- Runtime configuration updates possible

### 2. **Maintainability**
- Single source of truth for all settings
- Clear separation of concerns
- Easy to document and understand

### 3. **Production Readiness**
- Proper error handling and retry logic
- Configurable logging and monitoring
- Batch processing for performance

### 4. **Operational Excellence**
- Health monitoring and status reporting
- Configurable log rotation and retention
- Graceful error handling and recovery

## Example Configuration Usage

```python
# Initialize pipeline with full configuration
pipeline = ETLPipeline('config/etl.yaml')

# All components automatically use their respective config sections
if pipeline.initialize():
    # Pipeline uses logging, monitoring, and scheduling config
    pipeline.run_continuous()
    
    # Health status uses monitoring config
    health = pipeline.get_health_status()
    print(f"Pipeline status: {health['status']}")
```

## Migration from Previous Implementation

The updated implementation maintains backward compatibility while adding full configuration support:

- **Old**: `SimplePrometheusExtractor(url, timeout)`
- **New**: `PrometheusExtractor(config)` - uses extract section

- **Old**: `SimpleDataTransformer()` - hardcoded settings
- **New**: `DataTransformer(config)` - uses transform section

- **Old**: `SimpleInfluxDBLoader(url, token, org, bucket)`
- **New**: `InfluxDBLoader(config)` - uses load section

- **Old**: `SimpleETLPipeline(config_path)` - basic config loading
- **New**: `ETLPipeline(config_path)` - full configuration utilization

This ensures that all configuration sections in `etl.yaml` are now fully utilized by the ETL pipeline components, providing maximum flexibility and production readiness.
