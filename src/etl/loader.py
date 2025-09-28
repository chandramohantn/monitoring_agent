"""
InfluxDB Loader for ETL Pipeline

This module provides basic InfluxDB data loading capabilities for the ETL pipeline MVP.
"""

import logging
from typing import List, Dict, Any, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError


class InfluxDBLoader:
    """
    InfluxDB loader for basic data loading operations.
    
    This class provides basic functionality to load transformed data into InfluxDB
    with connection management and error handling.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the InfluxDB loader.
        
        Args:
            config: Configuration dictionary containing load settings
        """
        load_config = config.get('load', {}).get('influxdb', {})
        
        self.url = load_config.get('url', 'http://localhost:8086').rstrip('/')
        self.token = load_config.get('token', '')
        self.org = load_config.get('org', 'monitoring')
        self.bucket = load_config.get('bucket', 'health_metrics')
        self.timeout = load_config.get('timeout', 30)
        self.batch_size = load_config.get('batch_size', 1000)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize InfluxDB client
        self.client = None
        self.write_api = None
        self.query_api = None
        
    def _initialize_client(self) -> bool:
        """
        Initialize InfluxDB client and APIs.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=self.timeout
            )
            
            # Initialize write and query APIs
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            self.logger.info("InfluxDB client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize InfluxDB client: {e}")
            return False
    
    def load_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Load transformed data into InfluxDB with batch processing.
        
        Args:
            data: Transformed data in InfluxDB format
            
        Returns:
            True if loading successful, False otherwise
        """
        if not data:
            self.logger.warning("No data to load")
            return True
        
        # Initialize client if not already done
        if not self.client:
            if not self._initialize_client():
                return False
        
        try:
            # Process data in batches
            total_loaded = 0
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                
                # Convert batch to InfluxDB Point objects
                points = []
                for item in batch:
                    try:
                        point = Point(item['measurement'])
                        
                        # Add tags
                        for key, value in item.get('tags', {}).items():
                            point = point.tag(key, str(value))
                        
                        # Add fields
                        for key, value in item.get('fields', {}).items():
                            point = point.field(key, value)
                        
                        # Set timestamp
                        timestamp = item.get('timestamp')
                        if timestamp:
                            point = point.time(timestamp)
                        
                        points.append(point)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to create point from item: {e}")
                        continue
                
                if points:
                    # Write batch to InfluxDB
                    self.write_api.write(bucket=self.bucket, org=self.org, record=points)
                    total_loaded += len(points)
                    self.logger.debug(f"Loaded batch of {len(points)} points to InfluxDB")
            
            if total_loaded > 0:
                self.logger.info(f"Successfully loaded {total_loaded} data points to InfluxDB")
                return True
            else:
                self.logger.warning("No valid points to write")
                return False
            
        except InfluxDBError as e:
            self.logger.error(f"InfluxDB error during data loading: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading data to InfluxDB: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to InfluxDB.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize client if not already done
            if not self.client:
                if not self._initialize_client():
                    return False
            
            # Try to query a measurement
            query = f'from(bucket: "{self.bucket}") |> range(start: -1h) |> limit(n: 1)'
            result = self.query_api.query(query=query, org=self.org)
            
            # If we get here without exception, connection is working
            self.logger.info("InfluxDB connection test successful")
            return True
            
        except InfluxDBError as e:
            self.logger.error(f"InfluxDB connection test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"InfluxDB connection test failed: {e}")
            return False
    
    def validate_data_format(self, data: List[Dict[str, Any]]) -> bool:
        """
        Validate data format before loading.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data format is valid, False otherwise
        """
        if not data:
            return True
        
        required_fields = ['measurement', 'fields', 'timestamp']
        
        for i, item in enumerate(data):
            # Check required fields
            for field in required_fields:
                if field not in item:
                    self.logger.error(f"Item {i} missing required field: {field}")
                    return False
            
            # Validate measurement name
            if not isinstance(item['measurement'], str) or not item['measurement']:
                self.logger.error(f"Item {i} has invalid measurement name")
                return False
            
            # Validate fields
            if not isinstance(item['fields'], dict) or not item['fields']:
                self.logger.error(f"Item {i} has invalid fields")
                return False
            
            # Validate timestamp
            if not isinstance(item['timestamp'], (str, int, float)):
                self.logger.error(f"Item {i} has invalid timestamp")
                return False
        
        self.logger.info(f"Data format validation passed for {len(data)} items")
        return True
    
    def get_bucket_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the InfluxDB bucket.
        
        Returns:
            Bucket information or None if failed
        """
        try:
            if not self.client:
                if not self._initialize_client():
                    return None
            
            buckets_api = self.client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(self.bucket)
            
            if bucket:
                return {
                    'name': bucket.name,
                    'id': bucket.id,
                    'org_id': bucket.org_id,
                    'retention_rules': [rule.duration for rule in bucket.retention_rules]
                }
            else:
                self.logger.error(f"Bucket '{self.bucket}' not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get bucket info: {e}")
            return None
    
    def close(self) -> None:
        """Close InfluxDB client connection."""
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB client connection closed")
        
        self.client = None
        self.write_api = None
        self.query_api = None
