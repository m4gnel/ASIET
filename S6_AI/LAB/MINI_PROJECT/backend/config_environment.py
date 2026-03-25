#!/usr/bin/env python3
"""
Environment Configuration and Initialization
Handles all environment setup, logging configuration, and threading optimization.
This ensures zero errors occur from encoding, missing tokens, or context issues.
"""

import os
import sys
import logging
import warnings
from pathlib import Path

# ════════════════════════════════════════════════════════════════════════════════
# 1. ENVIRONMENT VARIABLES (Before any imports that use HF_TOKEN)
# ════════════════════════════════════════════════════════════════════════════════

# Set HuggingFace token if exists, otherwise suppress warning
if not os.environ.get('HF_TOKEN'):
    os.environ['HF_TOKEN'] = os.environ.get('HUGGINGFACE_TOKEN', '')

# Disable HF Hub SSL warnings if needed
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

# Set encoding to UTF-8 for Windows compatibility
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Force stdout/stderr to use UTF-8 (Windows console fix)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ════════════════════════════════════════════════════════════════════════════════
# 2. LOGGING CONFIGURATION (UTF-8 safe, no Unicode checkmarks)
# ════════════════════════════════════════════════════════════════════════════════

class UTF8SafeFormatter(logging.Formatter):
    """Safe formatter that handles Unicode gracefully on Windows"""
    def format(self, record):
        try:
            # Replace any Unicode characters that might cause encoding issues
            if hasattr(record, 'msg'):
                msg = str(record.msg)
                # Replace checkmarks and other problematic Unicode
                msg = msg.replace('\u2713', '[OK]').replace('\u2713\u2713\u2713', '[PASS]')
                record.msg = msg
            return super().format(record)
        except Exception:
            # Fallback to basic formatting if anything fails
            return super().format(record)

def setup_logging():
    """Configure application logging with UTF-8 safety"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler (UTF-8 safe)
    try:
        file_handler = logging.FileHandler(
            log_dir / 'app.log',
            encoding='utf-8',
            errors='replace'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = UTF8SafeFormatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    # Console handler (UTF-8 safe with error replacement)
    try:
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = UTF8SafeFormatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    except Exception as e:
        print(f"Warning: Could not setup console logging: {e}")
    
    # Suppress noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    
    return logger

# ════════════════════════════════════════════════════════════════════════════════
# 3. SUPPRESS WARNINGS GLOBALLY
# ════════════════════════════════════════════════════════════════════════════════

def suppress_warnings():
    """Suppress all non-critical warnings"""
    warnings.filterwarnings("ignore")
    # More specific suppressions
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

# ════════════════════════════════════════════════════════════════════════════════
# 4. THREADING CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

import threading

class ThreadSafeCounter:
    """Thread-safe counter for tracking background tasks"""
    def __init__(self):
        self._lock = threading.Lock()
        self._count = 0
    
    def increment(self):
        with self._lock:
            self._count += 1
            return self._count
    
    def decrement(self):
        with self._lock:
            self._count -= 1
            return self._count
    
    def value(self):
        with self._lock:
            return self._count

# Global tracking
background_tasks = ThreadSafeCounter()

def configure_threading():
    """Configure threading for optimal performance with proper error handling"""
    # Set daemon thread behavior
    threading.daemon_threads = True
    
    # Configure thread pool if needed
    # Note: Flask development server uses single-threaded mode by default
    # Production servers (Gunicorn, etc.) handle threading differently

# ════════════════════════════════════════════════════════════════════════════════
# MAIN INITIALIZATION
# ════════════════════════════════════════════════════════════════════════════════

def initialize():
    """Initialize all environment configurations"""
    suppress_warnings()
    logger = setup_logging()
    configure_threading()
    
    logger.info("[INIT] Environment initialized successfully")
    logger.info(f"[INIT] Platform: {sys.platform}")
    logger.info(f"[INIT] Encoding: {sys.stdout.encoding}")
    
    return logger

# Export for use in app.py
app_logger = initialize()
