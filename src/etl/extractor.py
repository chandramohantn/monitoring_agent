"""
Prometheus Extractor for ETL Pipeline

This module provides a Prometheus data extraction capability
for the ETL pipeline MVP implementation.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin


class PrometheusExtractor:
    """
    Prometheus data extractor for basic metrics collection.
    
    This class provides basic functionality to extract metrics from Prometheus
    using the HTTP API with error handling and data parsing.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the Prometheus extractor.
        
        Args:
            config: Configuration dictionary containing extract settings
        """
        extract_config = config.get('extract', {})
        self.prometheus_url = extract_config.get('prometheus_url', 'http://localhost:9090').rstrip('/')
        self.timeout = extract_config.get('timeout', 30)
        self.retry_attempts = extract_config.get('retry_attempts', 3)
        
        self.session = requests.Session()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    def extract_metrics(self, query: str, start_time: str, end_time: str, step: str = "15s") -> List[Dict[str, Any]]:
        """
        Extract metrics using Prometheus range query API with retry logic.
        
        Args:
            query: Prometheus query expression
            start_time: Start time in RFC3339 format or Unix timestamp
            end_time: End time in RFC3339 format or Unix timestamp
            step: Query resolution step width
            
        Returns:
            List of parsed metric data points
        """
        url = urljoin(self.prometheus_url, "/api/v1/query_range")
        params = {
            'query': query,
            'start': start_time,
            'end': end_time,
            'step': step
        }
        
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(f"Extracting metrics with query: {query} (attempt {attempt + 1}/{self.retry_attempts})")
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'success':
                    result = self._parse_response(data.get('data', {}))
                    self.logger.info(f"Successfully extracted {len(result)} data points")
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.logger.error(f"Prometheus query failed: {error_msg}")
                    if attempt == self.retry_attempts - 1:
                        raise Exception(f"Prometheus query failed after {self.retry_attempts} attempts: {error_msg}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"HTTP request failed (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt == self.retry_attempts - 1:
                    return []
            except Exception as e:
                self.logger.error(f"Error extracting metrics (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt == self.retry_attempts - 1:
                    return []
        
        return []
    
    def get_basic_metrics(self) -> List[Dict[str, Any]]:
        """
        Extract basic application metrics for the MVP.
        
        Returns:
            List of parsed metric data points
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        # Define basic metrics queries
        queries = [
            'up{job="test-app"}',  # Service availability
            'rate(http_requests_total[5m])',  # Request rate
            'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',  # 95th percentile latency
            'rate(http_requests_total{status=~"5.."}[5m])',  # Error rate
        ]
        
        all_metrics = []
        for query in queries:
            try:
                metrics = self.extract_metrics(
                    query=query,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )
                all_metrics.extend(metrics)
            except Exception as e:
                self.logger.warning(f"Failed to extract metrics for query '{query}': {e}")
                continue
        
        self.logger.info(f"Extracted total of {len(all_metrics)} basic metrics")
        return all_metrics
    
    def _parse_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Prometheus API response into structured format.
        
        Args:
            data: Raw Prometheus API response data
            
        Returns:
            List of parsed metric data points
        """
        results = []
        
        for result in data.get('result', []):
            metric = result.get('metric', {})
            values = result.get('values', [])
            
            for timestamp, value in values:
                try:
                    # Parse timestamp and value
                    parsed_timestamp = datetime.fromtimestamp(float(timestamp))
                    parsed_value = float(value) if value != 'NaN' else None
                    
                    if parsed_value is not None:
                        results.append({
                            'timestamp': parsed_timestamp,
                            'metric_name': metric.get('__name__', 'unknown'),
                            'labels': {k: v for k, v in metric.items() if k != '__name__'},
                            'value': parsed_value
                        })
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Failed to parse metric value: {e}")
                    continue
        
        return results
    
    def test_connection(self) -> bool:
        """
        Test connection to Prometheus instance.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = urljoin(self.prometheus_url, "/api/v1/query")
            params = {'query': 'up'}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                self.logger.info("Prometheus connection test successful")
                return True
            else:
                self.logger.error("Prometheus connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Prometheus connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
        self.logger.info("Prometheus extractor session closed")
