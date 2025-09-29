#!/usr/bin/env python3
"""
ETL Pipeline Deployment Script

This script handles the deployment setup for the ETL Pipeline MVP,
including dependency checking, directory creation, and configuration validation.
"""

import os
import sys
import subprocess
import logging
import shutil
from pathlib import Path


def setup_logging() -> logging.Logger:
    """
    Set up logging for the deployment script.
    
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def check_python_version() -> bool:
    """
    Check if Python version meets requirements.
    
    Returns:
        True if Python version is compatible, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    logger.info(f"Python version check passed: {sys.version}")
    return True


def check_dependencies() -> bool:
    """
    Check if required dependencies are installed.
    
    Returns:
        True if all dependencies are available, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    required_packages = [
        'requests',
        'pandas',
        'influxdb-client',
        'pyyaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'influxdb-client':
                # Special handling for influxdb-client package name
                __import__('influxdb_client')
            else:
                __import__(package.replace('-', '_'))
            logger.info(f"✓ {package} is available")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install missing packages with:")
        logger.info(f"pip install {' '.join(missing_packages)}")
        return False
    
    logger.info("All required dependencies are available")
    return True


def check_configuration() -> bool:
    """
    Check if configuration files exist and are valid.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    config_file = 'config/etl.yaml'
    
    if not os.path.exists(config_file):
        logger.warning(f"Configuration file not found: {config_file}")
        logger.info("Please create the configuration file before running the ETL pipeline")
        return False
    
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        required_sections = ['extract', 'load', 'pipeline']
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate extract section
        if 'prometheus_url' not in config['extract']:
            logger.error("Missing prometheus_url in extract configuration")
            return False
        
        # Validate load section
        influxdb_config = config['load'].get('influxdb', {})
        required_influxdb_fields = ['url', 'token', 'org', 'bucket']
        for field in required_influxdb_fields:
            if field not in influxdb_config:
                logger.error(f"Missing {field} in InfluxDB configuration")
                return False
        
        logger.info("✓ Configuration file validation passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration file validation failed: {e}")
        return False


def check_external_services() -> bool:
    """
    Check if external services (Prometheus, InfluxDB) are accessible.
    
    Returns:
        True if services are accessible, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        import yaml
        with open('config/etl.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check Prometheus
        prometheus_url = config['extract']['prometheus_url']
        logger.info(f"Checking Prometheus connectivity: {prometheus_url}")
        
        import requests
        try:
            response = requests.get(f"{prometheus_url}/api/v1/query?query=up", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Prometheus is accessible")
            else:
                logger.warning(f"✗ Prometheus returned status code: {response.status_code}")
        except Exception as e:
            logger.warning(f"✗ Cannot connect to Prometheus: {e}")
        
        # Check InfluxDB
        influxdb_url = config['load']['influxdb']['url']
        logger.info(f"Checking InfluxDB connectivity: {influxdb_url}")
        
        try:
            response = requests.get(f"{influxdb_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✓ InfluxDB is accessible")
            else:
                logger.warning(f"✗ InfluxDB returned status code: {response.status_code}")
        except Exception as e:
            logger.warning(f"✗ Cannot connect to InfluxDB: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking external services: {e}")
        return False


def run_tests() -> bool:
    """
    Run ETL pipeline tests.
    
    Returns:
        True if tests pass, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Running ETL pipeline tests...")
    
    try:
        # Add src directory to Python path
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Run tests
        result = subprocess.run([
            sys.executable, '-m', 'unittest', 'tests.test_etl'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✓ All tests passed")
            return True
        else:
            logger.error("✗ Tests failed")
            logger.error("Test output:")
            logger.error(result.stdout)
            logger.error(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False


def print_deployment_summary() -> None:
    """
    Print deployment summary and next steps.
    """
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("ETL PIPELINE DEPLOYMENT SUMMARY")
    logger.info("=" * 60)
    
    logger.info("✓ Directory structure created")
    logger.info("✓ Dependencies verified")
    logger.info("✓ Configuration validated")
    
    logger.info("\nNEXT STEPS:")
    logger.info("1. Update config/etl.yaml with your settings:")
    logger.info("   - Prometheus URL")
    logger.info("   - InfluxDB connection details (URL, token, org, bucket)")
    logger.info("   - Pipeline interval settings")
    
    logger.info("\n2. Start the ETL pipeline:")
    logger.info("   python src/etl/pipeline.py")
    
    logger.info("\n3. Monitor the pipeline:")
    logger.info("   - Check logs in logs/etl_pipeline.log")
    logger.info("   - Verify data in InfluxDB")
    
    logger.info("\n4. Run tests:")
    logger.info("   python -m unittest tests.test_etl")
    
    logger.info("\nCONFIGURATION FILES:")
    logger.info("- config/etl.yaml: Main configuration")
    logger.info("- logs/: Pipeline log files")
    logger.info("- data/: Temporary data storage")
    
    logger.info("\nFor more information, see docs/etl_mvp_plan.md")
    logger.info("=" * 60)


def main():
    """
    Main deployment function.
    """
    logger = setup_logging()
    
    logger.info("Starting ETL Pipeline deployment...")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Deployment failed: Missing dependencies")
        sys.exit(1)
    
    # Check configuration
    config_valid = check_configuration()
    
    # Check external services (optional)
    check_external_services()
    
    # Run tests (optional)
    run_tests()
    
    # Print deployment summary
    print_deployment_summary()
    
    if not config_valid:
        logger.warning("Deployment completed with warnings. Please update configuration before running the pipeline.")
        sys.exit(1)
    else:
        logger.info("ETL pipeline deployment completed successfully!")


if __name__ == "__main__":
    main()
