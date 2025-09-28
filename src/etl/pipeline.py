"""
ETL Pipeline Orchestrator

This module provides the main ETL pipeline orchestrator that coordinates
the extract, transform, and load operations for the MVP implementation.
"""

import logging
import time
import signal
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import yaml

from .extractor import PrometheusExtractor
from .transformer import DataTransformer
from .loader import InfluxDBLoader


class ETLPipeline:
    """
    ETL pipeline orchestrator for MVP implementation.
    
    This class coordinates the extract, transform, and load operations
    with basic error handling and continuous operation capabilities.
    """
    
    def __init__(self, config_path: str) -> None:
        """
        Initialize the ETL pipeline.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = {}
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize components (will be set up in initialize method)
        self.extractor = None
        self.transformer = None
        self.loader = None
        
        # Pipeline state
        self.running = False
        self.stats = {
            'cycles_completed': 0,
            'cycles_failed': 0,
            'total_data_points': 0,
            'last_run_time': None,
            'start_time': None
        }
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If configuration file not found
            yaml.YAMLError: If configuration file is invalid YAML
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in configuration file: {e}")
            raise
    
    def initialize(self) -> bool:
        """
        Initialize ETL pipeline components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load configuration
            self.config = self._load_config(self.config_path)
            
            # Set up logging from configuration
            self._setup_logging()
            
            # Initialize Prometheus extractor
            extract_config = self.config.get('extract', {})
            if not extract_config.get('prometheus_url'):
                raise ValueError("prometheus_url not found in extract configuration")
            
            self.extractor = PrometheusExtractor(self.config)
            
            # Initialize data transformer
            self.transformer = DataTransformer(self.config)
            
            # Initialize InfluxDB loader
            load_config = self.config.get('load', {}).get('influxdb', {})
            required_fields = ['url', 'token', 'org', 'bucket']
            
            for field in required_fields:
                if field not in load_config:
                    raise ValueError(f"InfluxDB {field} not found in load configuration")
            
            self.loader = InfluxDBLoader(self.config)
            
            # Test connections
            self.logger.info("Testing Prometheus connection...")
            if not self.extractor.test_connection():
                self.logger.error("Prometheus connection test failed")
                return False
            
            self.logger.info("Testing InfluxDB connection...")
            if not self.loader.test_connection():
                self.logger.error("InfluxDB connection test failed")
                return False
            
            self.logger.info("ETL pipeline initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ETL pipeline: {e}")
            return False
    
    def _setup_logging(self) -> None:
        """
        Set up logging configuration from config file.
        """
        logging_config = self.config.get('logging', {})
        
        # Set log level
        log_level = getattr(logging, logging_config.get('level', 'INFO').upper())
        
        # Set log format
        log_format = logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        log_file = logging_config.get('file')
        if log_file:
            try:
                from logging.handlers import RotatingFileHandler
                max_size = self._parse_size(logging_config.get('max_size', '10MB'))
                backup_count = logging_config.get('backup_count', 5)
                
                file_handler = RotatingFileHandler(
                    log_file, 
                    maxBytes=max_size, 
                    backupCount=backup_count
                )
                file_handler.setLevel(log_level)
                file_formatter = logging.Formatter(log_format)
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
                
                self.logger.info(f"Logging to file: {log_file}")
                
            except Exception as e:
                self.logger.warning(f"Failed to set up file logging: {e}")
        
        self.logger.info(f"Logging configured with level: {logging_config.get('level', 'INFO')}")
    
    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string like '10MB' to bytes.
        
        Args:
            size_str: Size string (e.g., '10MB', '1GB')
            
        Returns:
            Size in bytes
        """
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def run_single_cycle(self) -> bool:
        """
        Run a single ETL cycle (extract → transform → load).
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        cycle_start_time = datetime.now()
        
        try:
            self.logger.info("Starting ETL cycle")
            
            # Extract data
            self.logger.info("Extracting data from Prometheus...")
            raw_data = self.extractor.get_basic_metrics()
            self.logger.info(f"Extracted {len(raw_data)} data points")
            
            if not raw_data:
                self.logger.warning("No data extracted from Prometheus")
                self.stats['cycles_completed'] += 1
                self.stats['last_run_time'] = cycle_start_time
                return True
            
            # Transform data
            self.logger.info("Transforming data...")
            transformed_data = self.transformer.transform(raw_data)
            self.logger.info(f"Transformed {len(transformed_data)} data points")
            
            if not transformed_data:
                self.logger.warning("No data remaining after transformation")
                self.stats['cycles_completed'] += 1
                self.stats['last_run_time'] = cycle_start_time
                return True
            
            # Load data
            self.logger.info("Loading data to InfluxDB...")
            success = self.loader.load_data(transformed_data)
            
            if success:
                self.logger.info("ETL cycle completed successfully")
                
                # Update statistics
                self.stats['cycles_completed'] += 1
                self.stats['total_data_points'] += len(transformed_data)
                self.stats['last_run_time'] = cycle_start_time
                
                return True
            else:
                self.logger.error("ETL cycle failed during data loading")
                self.stats['cycles_failed'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"ETL cycle failed: {e}")
            self.stats['cycles_failed'] += 1
            return False
    
    def run_continuous(self, interval_seconds: Optional[int] = None) -> None:
        """
        Run ETL pipeline continuously with configurable intervals.
        
        Args:
            interval_seconds: Interval between cycles in seconds.
                            If None, uses value from configuration.
        """
        pipeline_config = self.config.get('pipeline', {})
        
        if interval_seconds is None:
            interval_seconds = pipeline_config.get('interval_seconds', 300)
        
        max_retries = pipeline_config.get('max_retries', 3)
        retry_delay = pipeline_config.get('retry_delay', 60)
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        self.logger.info(f"Starting continuous ETL pipeline (interval: {interval_seconds}s)")
        
        while self.running:
            try:
                success = self.run_single_cycle()
                
                if not success:
                    self.logger.warning("ETL cycle failed, continuing...")
                
                # Log statistics
                self._log_statistics()
                
                # Wait for next cycle
                self.logger.info(f"Waiting {interval_seconds} seconds until next cycle...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, stopping pipeline...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in continuous run: {e}")
                self.logger.info(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
        
        self.running = False
        self.logger.info("ETL pipeline stopped")
    
    def stop(self) -> None:
        """
        Stop the ETL pipeline gracefully.
        """
        self.running = False
        
        # Close connections
        if self.extractor:
            self.extractor.close()
        
        if self.loader:
            self.loader.close()
        
        self.logger.info("ETL pipeline shutdown complete")
    
    def _signal_handler(self, signum, frame) -> None:
        """
        Handle shutdown signals.
        """
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)
    
    def _log_statistics(self) -> None:
        """
        Log pipeline statistics.
        """
        total_cycles = self.stats['cycles_completed'] + self.stats['cycles_failed']
        success_rate = (self.stats['cycles_completed'] / total_cycles * 100) if total_cycles > 0 else 0
        
        self.logger.info(
            f"Pipeline Statistics - "
            f"Cycles: {total_cycles} total, {self.stats['cycles_completed']} successful, "
            f"{self.stats['cycles_failed']} failed, "
            f"Success Rate: {success_rate:.1f}%, "
            f"Total Data Points: {self.stats['total_data_points']}"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current pipeline statistics.
        
        Returns:
            Dictionary containing pipeline statistics
        """
        total_cycles = self.stats['cycles_completed'] + self.stats['cycles_failed']
        success_rate = (self.stats['cycles_completed'] / total_cycles * 100) if total_cycles > 0 else 0
        
        return {
            'total_cycles': total_cycles,
            'successful_cycles': self.stats['cycles_completed'],
            'failed_cycles': self.stats['cycles_failed'],
            'success_rate': success_rate,
            'total_data_points': self.stats['total_data_points'],
            'last_run_time': self.stats['last_run_time'],
            'start_time': self.stats['start_time'],
            'is_running': self.running
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get pipeline health status based on monitoring configuration.
        
        Returns:
            Dictionary containing health status information
        """
        monitoring_config = self.config.get('monitoring', {})
        
        if not monitoring_config.get('enable_metrics', True):
            return {'status': 'monitoring_disabled'}
        
        stats = self.get_statistics()
        
        # Determine health status based on success rate
        health_status = 'healthy'
        if stats['total_cycles'] > 0:
            if stats['success_rate'] < 50:
                health_status = 'critical'
            elif stats['success_rate'] < 80:
                health_status = 'warning'
        
        return {
            'status': health_status,
            'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0,
            'statistics': stats,
            'monitoring_enabled': monitoring_config.get('enable_metrics', True),
            'health_check_interval': monitoring_config.get('health_check_interval', 60)
        }


def main():
    """Main entry point for the ETL pipeline."""
    # Basic logging setup (will be reconfigured in initialize)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize and run pipeline
        pipeline = ETLPipeline('config/etl.yaml')
        
        if pipeline.initialize():
            logger.info("Starting ETL pipeline...")
            pipeline.run_continuous()
        else:
            logger.error("Failed to initialize ETL pipeline")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in ETL pipeline: {e}")
        sys.exit(1)
    finally:
        logger.info("ETL pipeline execution ended")


if __name__ == "__main__":
    main()
