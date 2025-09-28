"""
Unit tests for ETL Pipeline components.

This module contains comprehensive unit tests for all ETL pipeline components
including extractor, transformer, loader, and pipeline orchestrator.
"""

import unittest
import tempfile
import yaml
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from etl.extractor import PrometheusExtractor
from etl.transformer import DataTransformer
from etl.loader import InfluxDBLoader
from etl.pipeline import ETLPipeline


class TestPrometheusExtractor(unittest.TestCase):
    """
    Test cases for PrometheusExtractor.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = PrometheusExtractor("http://localhost:9090")
        
    def test_initialization(self):
        """Test extractor initialization."""
        self.assertEqual(self.extractor.prometheus_url, "http://localhost:9090")
        self.assertEqual(self.extractor.timeout, 30)
        self.assertIsNotNone(self.extractor.session)
    
    @patch('requests.Session.get')
    def test_extract_metrics_success(self, mock_get):
        """
        Test successful metrics extraction.
        """
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'result': [{
                    'metric': {'__name__': 'up', 'job': 'test-app'},
                    'values': [[1640995200.0, '1']]
                }]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.extractor.extract_metrics(
            query="up{job='test-app'}",
            start_time="2022-01-01T00:00:00Z",
            end_time="2022-01-01T01:00:00Z"
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['metric_name'], 'up')
        self.assertEqual(result[0]['value'], 1.0)
    
    @patch('requests.Session.get')
    def test_extract_metrics_failure(self, mock_get):
        """
        Test metrics extraction failure.
        """
        # Mock failed response
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'error',
            'error': 'Query failed'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.extractor.extract_metrics(
            query="invalid_query",
            start_time="2022-01-01T00:00:00Z",
            end_time="2022-01-01T01:00:00Z"
        )
        
        self.assertEqual(len(result), 0)
    
    def test_parse_response(self):
        """
        Test response parsing.
        """
        data = {
            'result': [{
                'metric': {'__name__': 'up', 'job': 'test-app'},
                'values': [[1640995200.0, '1'], [1640995260.0, '1']]
            }]
        }
        
        result = self.extractor._parse_response(data)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['metric_name'], 'up')
        self.assertEqual(result[0]['value'], 1.0)
        self.assertIsInstance(result[0]['timestamp'], datetime)


class TestDataTransformer(unittest.TestCase):
    """
    Test cases for DataTransformer.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.transformer = DataTransformer()
        
        # Sample raw data
        self.sample_data = [
            {
                'timestamp': datetime.now(),
                'metric_name': 'up',
                'labels': {'job': 'test-app', 'instance': 'localhost:8080'},
                'value': 1.0
            },
            {
                'timestamp': datetime.now(),
                'metric_name': 'up',
                'labels': {'job': 'test-app', 'instance': 'localhost:8080'},
                'value': None  # This should be filtered out
            }
        ]
    
    def test_initialization(self):
        """
        Test transformer initialization.
        """
        self.assertIsInstance(self.transformer.valid_metrics, set)
        self.assertIn('up', self.transformer.valid_metrics)
    
    def test_transform_success(self):
        """
        Test successful data transformation.
        """
        result = self.transformer.transform(self.sample_data)
        
        self.assertEqual(len(result), 1)  # One valid data point
        self.assertEqual(result[0]['measurement'], 'health_metrics')
        self.assertEqual(result[0]['fields']['value'], 1.0)
        self.assertEqual(result[0]['tags']['service'], 'test-app')
    
    def test_transform_empty_data(self):
        """
        Test transformation with empty data.
        """
        result = self.transformer.transform([])
        self.assertEqual(len(result), 0)
    
    def test_clean_data(self):
        """
        Test data cleaning functionality.
        """
        df = pd.DataFrame(self.sample_data)
        cleaned_df = self.transformer._clean_data(df)
        
        # Should remove null values
        self.assertEqual(len(cleaned_df), 1)
        self.assertFalse(cleaned_df['value'].isnull().any())
    
    def test_to_influxdb_format(self):
        """
        Test InfluxDB format conversion.
        """
        df = pd.DataFrame(self.sample_data[:1])  # Only valid data
        result = self.transformer._to_influxdb_format(df)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['measurement'], 'health_metrics')
        self.assertIn('tags', result[0])
        self.assertIn('fields', result[0])
        self.assertIn('timestamp', result[0])


class TestInfluxDBLoader(unittest.TestCase):
    """
    Test cases for InfluxDBLoader.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = InfluxDBLoader(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        # Sample data
        self.sample_data = [{
            'measurement': 'health_metrics',
            'tags': {'service': 'test-app'},
            'fields': {'value': 1.0},
            'timestamp': datetime.now()
        }]
    
    def test_initialization(self):
        """
        Test loader initialization.
        """
        self.assertEqual(self.loader.url, "http://localhost:8086")
        self.assertEqual(self.loader.token, "test-token")
        self.assertEqual(self.loader.org, "test-org")
        self.assertEqual(self.loader.bucket, "test-bucket")
    
    @patch('influxdb_client.InfluxDBClient')
    def test_load_data_success(self, mock_client_class):
        """
        Test successful data loading.
        """
        # Mock InfluxDB client and write API
        mock_client = Mock()
        mock_write_api = Mock()
        mock_client.write_api.return_value = mock_write_api
        mock_client_class.return_value = mock_client
        
        self.loader.client = mock_client
        self.loader.write_api = mock_write_api
        
        result = self.loader.load_data(self.sample_data)
        
        self.assertTrue(result)
        mock_write_api.write.assert_called_once()
    
    def test_load_data_empty(self):
        """
        Test loading empty data.
        """
        result = self.loader.load_data([])
        self.assertTrue(result)  # Should succeed with empty data
    
    def test_validate_data_format(self):
        """
        Test data format validation.
        """
        # Valid data
        self.assertTrue(self.loader.validate_data_format(self.sample_data))
        
        # Invalid data - missing required fields
        invalid_data = [{'measurement': 'test'}]  # Missing fields, timestamp
        self.assertFalse(self.loader.validate_data_format(invalid_data))


class TestETLPipeline(unittest.TestCase):
    """
    Test cases for ETLPipeline.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create temporary config file
        self.config = {
            'extract': {'prometheus_url': 'http://localhost:9090'},
            'load': {
                'influxdb': {
                    'url': 'http://localhost:8086',
                    'token': 'test-token',
                    'org': 'test-org',
                    'bucket': 'test-bucket'
                }
            }
        }
        
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config, self.config_file)
        self.config_file.close()
        
        self.pipeline = ETLPipeline(self.config_file.name)
    
    def tearDown(self):
        """
        Clean up test fixtures.
        """
        os.unlink(self.config_file.name)
    
    def test_config_loading(self):
        """
        Test configuration loading.
        """
        config = self.pipeline._load_config(self.config_file.name)
        self.assertEqual(config['extract']['prometheus_url'], 'http://localhost:9090')
    
    @patch('etl.pipeline.PrometheusExtractor')
    @patch('etl.pipeline.InfluxDBLoader')
    def test_initialization(self, mock_loader_class, mock_extractor_class):
        """
        Test pipeline initialization.
        """
        # Mock extractor and loader
        mock_extractor = Mock()
        mock_extractor.test_connection.return_value = True
        mock_extractor_class.return_value = mock_extractor
        
        mock_loader = Mock()
        mock_loader.test_connection.return_value = True
        mock_loader_class.return_value = mock_loader
        
        result = self.pipeline.initialize()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.pipeline.extractor)
        self.assertIsNotNone(self.pipeline.loader)
    
    @patch('etl.pipeline.PrometheusExtractor')
    @patch('etl.pipeline.InfluxDBLoader')
    def test_single_cycle(self, mock_loader_class, mock_extractor_class):
        """
        Test single ETL cycle execution.
        """
        # Mock components
        mock_extractor = Mock()
        mock_extractor.get_basic_metrics.return_value = [{
            'timestamp': datetime.now(),
            'metric_name': 'up',
            'labels': {'job': 'test-app'},
            'value': 1.0
        }]
        mock_extractor_class.return_value = mock_extractor
        
        mock_loader = Mock()
        mock_loader.load_data.return_value = True
        mock_loader_class.return_value = mock_loader
        
        self.pipeline.extractor = mock_extractor
        self.pipeline.loader = mock_loader
        
        result = self.pipeline.run_single_cycle()
        
        self.assertTrue(result)
        self.assertEqual(self.pipeline.stats['cycles_completed'], 1)
    
    def test_get_statistics(self):
        """
        Test statistics retrieval.
        """
        stats = self.pipeline.get_statistics()
        
        self.assertIn('total_cycles', stats)
        self.assertIn('successful_cycles', stats)
        self.assertIn('failed_cycles', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('is_running', stats)


class TestETLIntegration(unittest.TestCase):
    """
    Integration tests for ETL pipeline components.
    """
    
    def test_data_flow(self):
        """
        Test complete data flow from extract to load.
        """
        # This is a simplified integration test
        # In a real scenario, you would mock the external dependencies
        
        transformer = DataTransformer()
        
        # Sample extracted data
        extracted_data = [{
            'timestamp': datetime.now(),
            'metric_name': 'up',
            'labels': {'job': 'test-app', 'instance': 'localhost:8080'},
            'value': 1.0
        }]
        
        # Transform data
        transformed_data = transformer.transform(extracted_data)
        
        # Validate transformation
        self.assertEqual(len(transformed_data), 1)
        self.assertEqual(transformed_data[0]['measurement'], 'health_metrics')
        self.assertEqual(transformed_data[0]['fields']['value'], 1.0)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestPrometheusExtractor))
    test_suite.addTest(unittest.makeSuite(TestDataTransformer))
    test_suite.addTest(unittest.makeSuite(TestInfluxDBLoader))
    test_suite.addTest(unittest.makeSuite(TestETLPipeline))
    test_suite.addTest(unittest.makeSuite(TestETLIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
