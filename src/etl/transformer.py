"""
Data Transformer for ETL Pipeline

This module provides basic data transformation capabilities for the ETL pipeline MVP,
including data cleaning and InfluxDB format conversion.
"""

import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional


class DataTransformer:
    """
    Data transformer for basic data cleaning and InfluxDB format conversion.
    
    This class provides basic transformation capabilities including data cleaning,
    validation, and conversion to InfluxDB line protocol format.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the data transformer.
        
        Args:
            config: Configuration dictionary containing transform settings
        """
        self.logger = logging.getLogger(__name__)
        
        # Load transform configuration
        transform_config = config.get('transform', {})
        
        # Set valid metrics from configuration
        self.valid_metrics = set(transform_config.get('valid_metrics', [
            'up',
            'http_requests_total', 
            'http_request_duration_seconds_bucket',
            'rate(http_requests_total[5m])',
            'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',
            'rate(http_requests_total{status=~"5.."}[5m])'
        ]))
        
        # Load data cleaning configuration
        self.cleaning_config = transform_config.get('data_cleaning', {
            'remove_nulls': True,
            'validate_timestamps': True,
            'remove_duplicates': True,
            'validate_value_ranges': True
        })
        
    def transform(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main transformation pipeline from raw Prometheus data to InfluxDB format.
        
        Args:
            raw_data: Raw data from Prometheus extractor
            
        Returns:
            Transformed data in InfluxDB format
        """
        if not raw_data:
            self.logger.warning("No data to transform")
            return []
        
        self.logger.info(f"Starting transformation of {len(raw_data)} data points")
        
        try:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(raw_data)
            
            # Basic data cleaning
            df = self._clean_data(df)
            
            if df.empty:
                self.logger.warning("No data remaining after cleaning")
                return []
            
            # Transform to InfluxDB format
            transformed_data = self._to_influxdb_format(df)
            
            self.logger.info(f"Successfully transformed {len(transformed_data)} data points")
            return transformed_data
            
        except Exception as e:
            self.logger.error(f"Error during transformation: {e}")
            return []
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Data cleaning operations based on configuration.
        
        Args:
            df: Raw data DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        original_count = len(df)
        
        # Remove rows with null values in 'value' field
        if self.cleaning_config.get('remove_nulls', True):
            df = df.dropna(subset=['value'])
        
        # Remove invalid timestamps
        if self.cleaning_config.get('validate_timestamps', True):
            df = df[df['timestamp'].notna()]
        
        # Filter out invalid metrics (if metric_name exists)
        if 'metric_name' in df.columns:
            df = df[df['metric_name'].isin(self.valid_metrics)]
        
        # Remove duplicate entries based on timestamp, metric_name, and labels
        if self.cleaning_config.get('remove_duplicates', True):
            if 'metric_name' in df.columns:
                df = df.drop_duplicates(subset=['timestamp', 'metric_name', 'labels'])
            else:
                df = df.drop_duplicates(subset=['timestamp'])
        
        # Validate value ranges for common metrics
        if self.cleaning_config.get('validate_value_ranges', True):
            df = self._validate_value_ranges(df)
        
        cleaned_count = len(df)
        removed_count = original_count - cleaned_count
        
        if removed_count > 0:
            self.logger.info(f"Cleaned data: removed {removed_count} rows, kept {cleaned_count} rows")
        
        return df
    
    def _validate_value_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate value ranges for common metrics.
        
        Args:
            df: Data DataFrame
            
        Returns:
            DataFrame with valid value ranges
        """
        if 'metric_name' not in df.columns or 'value' not in df.columns:
            return df
        
        original_count = len(df)
        
        # Define validation rules for common metrics
        validation_rules = {
            'up': lambda x: x in [0, 1],
            'rate(http_requests_total[5m])': lambda x: x >= 0,
            'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))': lambda x: x >= 0,
            'rate(http_requests_total{status=~"5.."}[5m])': lambda x: x >= 0,
        }
        
        # Apply validation rules
        for metric_name, validator in validation_rules.items():
            mask = df['metric_name'] == metric_name
            if mask.any():
                valid_mask = df[mask]['value'].apply(validator)
                df = df[~(mask & ~valid_mask)]
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} rows with invalid value ranges")
        
        return df
    
    def _to_influxdb_format(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert DataFrame to InfluxDB line protocol format.
        
        Args:
            df: Cleaned DataFrame
            
        Returns:
            List of InfluxDB data points
        """
        influxdb_data = []
        
        for _, row in df.iterrows():
            try:
                # Extract service information from labels
                labels = row.get('labels', {}) or {}
                service = labels.get('job', 'unknown')
                instance = labels.get('instance', 'unknown')
                metric_name = row.get('metric_name', 'unknown')
                
                # Create InfluxDB point
                point = {
                    'measurement': 'health_metrics',
                    'tags': {
                        'service': service,
                        'instance': instance,
                        'metric_type': metric_name
                    },
                    'fields': {
                        'value': row['value']
                    },
                    'timestamp': row['timestamp']
                }
                
                # Add additional labels as tags (limit length to avoid cardinality issues)
                for key, value in labels.items():
                    if key not in ['job', 'instance'] and len(str(value)) < 100:
                        point['tags'][key] = str(value)
                
                influxdb_data.append(point)
                
            except Exception as e:
                self.logger.warning(f"Failed to convert row to InfluxDB format: {e}")
                continue
        
        return influxdb_data
    
    def get_transformation_stats(self, original_count: int, transformed_count: int) -> Dict[str, Any]:
        """
        Get transformation statistics.
        
        Args:
            original_count: Original data count
            transformed_count: Transformed data count
            
        Returns:
            Transformation statistics
        """
        return {
            'original_count': original_count,
            'transformed_count': transformed_count,
            'removed_count': original_count - transformed_count,
            'success_rate': (transformed_count / original_count * 100) if original_count > 0 else 0
        }
