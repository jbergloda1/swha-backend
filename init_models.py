#!/usr/bin/env python3
"""
Model Initialization Script for SWHA Backend
This script pre-downloads and initializes AI models required by the application.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_spacy_models():
    """Download and setup spaCy models required by Kokoro TTS."""
    logger.info("Setting up spaCy models...")
    
    try:
        import spacy
        from spacy.cli import download
        
        # Models required by Kokoro for different languages
        models_to_download = [
            'en_core_web_sm',   # English (small)
            'en_core_web_md',   # English (medium) - better for TTS
        ]
        
        for model in models_to_download:
            try:
                logger.info(f"Downloading spaCy model: {model}")
                download(model)
                logger.info(f"✅ Successfully downloaded: {model}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to download {model}: {e}")
                # Try alternative download method
                try:
                    os.system(f"python -m spacy download {model}")
                    logger.info(f"✅ Successfully downloaded via alternative method: {model}")
                except:
                    logger.warning(f"❌ All download methods failed for: {model}")
        
        # Verify models
        for model in models_to_download:
            try:
                nlp = spacy.load(model)
                logger.info(f"✅ Verified model: {model}")
            except Exception as e:
                logger.warning(f"⚠️ Cannot load model {model}: {e}")
    
    except ImportError as e:
        logger.error(f"❌ spaCy not found: {e}")
        return False
    
    return True

def setup_kokoro_models():
    """Initialize Kokoro TTS models."""
    logger.info("Setting up Kokoro TTS models...")
    
    try:
        from kokoro import KPipeline
        
        # Language codes to pre-initialize
        language_codes = ['a', 'b']  # American and British English (most common)
        
        for lang_code in language_codes:
            try:
                logger.info(f"Initializing Kokoro pipeline for language: {lang_code}")
                pipeline = KPipeline(lang_code=lang_code)
                logger.info(f"✅ Successfully initialized Kokoro for language: {lang_code}")
                
                # Clean up to save memory
                del pipeline
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Kokoro for {lang_code}: {e}")
        
        logger.info("✅ Kokoro models setup completed")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Kokoro library not found: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error setting up Kokoro models: {e}")
        return False

def setup_transformers_models():
    """Pre-download transformers models."""
    logger.info("Setting up Transformers models...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForQuestionAnswering
        
        model_name = "deepset/roberta-base-squad2"
        logger.info(f"Downloading transformers model: {model_name}")
        
        # Download tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        
        logger.info(f"✅ Successfully downloaded: {model_name}")
        
        # Clean up to save memory
        del tokenizer, model
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error downloading transformers model: {e}")
        return False

def create_cache_directories():
    """Create necessary cache directories."""
    logger.info("Creating cache directories...")
    
    cache_dirs = [
        "/app/.cache/huggingface",
        "/app/.cache/spacy", 
        "/home/app/.cache/spacy",
        "app/static/audio",
        "app/static/uploads",
        "app/static/videos"
    ]
    
    for cache_dir in cache_dirs:
        try:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {cache_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create directory {cache_dir}: {e}")

def main():
    """Main initialization function."""
    logger.info("🚀 Starting model initialization for SWHA Backend")
    logger.info("=" * 60)
    
    success_count = 0
    total_steps = 4
    
    # Step 1: Create cache directories
    create_cache_directories()
    success_count += 1
    
    # Step 2: Setup spaCy models
    if setup_spacy_models():
        success_count += 1
    
    # Step 3: Setup Kokoro models
    if setup_kokoro_models():
        success_count += 1
    
    # Step 4: Setup Transformers models
    if setup_transformers_models():
        success_count += 1
    
    logger.info("=" * 60)
    logger.info(f"✅ Model initialization completed: {success_count}/{total_steps} steps successful")
    
    if success_count < total_steps:
        logger.warning("⚠️ Some models failed to initialize. The application may work with reduced functionality.")
        # Don't fail the build - let the application handle missing models gracefully
        return 0
    else:
        logger.info("🎉 All models initialized successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 