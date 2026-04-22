#!/usr/bin/env python3
"""
Quick validation script to test all pipeline components
"""

import sys
import os
import torch
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all imports"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Checking Imports")
    logger.info("="*70)
    
    try:
        import config
        logger.info("✓ config")
        
        from model_crf import TransformerCRFModel, CRFLayer, FocalLoss
        logger.info("✓ model_crf")
        
        from train import NERTrainer, MultiSeedTrainer
        logger.info("✓ train")
        
        from evaluate import NEREvaluator
        logger.info("✓ evaluate")
        
        from cross_validation import CrossValidator
        logger.info("✓ cross_validation")
        
        from ensemble import (NERensemble, HardVotingEnsemble, 
                            SoftVotingEnsemble, StackingEnsemble)
        logger.info("✓ ensemble")
        
        from utils import set_seed, EarlyStopping, PercentageScheduler
        logger.info("✓ utils")
        
        from augmentation import DataAugmenter
        logger.info("✓ augmentation")
        
        from gazetteer import ArchaeologyGazetteer
        logger.info("✓ gazetteer")
        
        from src.data_utils import CoNLLDataset, NERDataset
        logger.info("✓ src.data_utils")
        
        return True
    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False


def test_model_creation():
    """Test model creation"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Model Creation")
    logger.info("="*70)
    
    try:
        from model_crf import TransformerCRFModel
        from config import MODEL_NAME, NUM_LABELS, DROPOUT
        
        model = TransformerCRFModel(
            model_name=MODEL_NAME,
            num_labels=NUM_LABELS,
            dropout=DROPOUT
        )
        
        logger.info(f"✓ Model created: {MODEL_NAME}")
        logger.info(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Model creation error: {e}")
        return False


def test_data_loading():
    """Test data loading"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Data Loading")
    logger.info("="*70)
    
    try:
        from src.data_utils import CoNLLDataset
        from config import TRAIN_FILE, DEV_FILE, TEST_FILE
        
        # Check if files exist
        if not os.path.exists(TRAIN_FILE):
            logger.warning(f"⚠ Train file not found: {TRAIN_FILE}")
            return False
        
        train_data = CoNLLDataset(TRAIN_FILE)
        logger.info(f"✓ Train data loaded: {len(train_data)} samples")
        
        dev_data = CoNLLDataset(DEV_FILE)
        logger.info(f"✓ Dev data loaded: {len(dev_data)} samples")
        
        test_data = CoNLLDataset(TEST_FILE)
        logger.info(f"✓ Test data loaded: {len(test_data)} samples")
        
        return True
    except Exception as e:
        logger.error(f"✗ Data loading error: {e}")
        return False


def test_device():
    """Test device availability"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Device Check")
    logger.info("="*70)
    
    try:
        if torch.cuda.is_available():
            logger.info(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            device = 'cuda'
        else:
            logger.info(f"✓ Using CPU")
            device = 'cpu'
        
        # Test tensor creation
        x = torch.randn(2, 3).to(device)
        logger.info(f"✓ Tensor created on {device}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Device error: {e}")
        return False


def test_utils():
    """Test utility functions"""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: Utility Functions")
    logger.info("="*70)
    
    try:
        from utils import set_seed, EarlyStopping, get_device
        
        set_seed(42)
        logger.info("✓ Seed setting works")
        
        early_stop = EarlyStopping(patience=3)
        early_stop(0.5)
        logger.info("✓ Early stopping works")
        
        device = get_device()
        logger.info(f"✓ Device detection works: {device}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Utils error: {e}")
        return False


def test_config():
    """Test configuration"""
    logger.info("\n" + "="*70)
    logger.info("TEST 6: Configuration")
    logger.info("="*70)
    
    try:
        import config
        
        required_attrs = [
            'MODEL_NAME', 'NUM_LABELS', 'BATCH_SIZE', 'LEARNING_RATE',
            'EPOCHS', 'DROPOUT', 'WEIGHT_DECAY', 'LABEL_TO_ID', 'ID_TO_LABEL'
        ]
        
        for attr in required_attrs:
            if not hasattr(config, attr):
                raise AttributeError(f"Missing config: {attr}")
            logger.info(f"✓ {attr}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Config error: {e}")
        return False


def test_output_dir():
    """Test output directory creation"""
    logger.info("\n" + "="*70)
    logger.info("TEST 7: Output Directory")
    logger.info("="*70)
    
    try:
        from utils import create_output_dir
        
        output_dir = create_output_dir('outputs/', 'test_run')
        logger.info(f"✓ Output directory created: {output_dir}")
        
        # Cleanup
        import shutil
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            logger.info(f"✓ Cleanup successful")
        
        return True
    except Exception as e:
        logger.error(f"✗ Output dir error: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "#"*70)
    logger.info("PIPELINE VALIDATION SUITE")
    logger.info("#"*70)
    
    tests = [
        ("Imports", test_imports),
        ("Model Creation", test_model_creation),
        ("Device", test_device),
        ("Utils", test_utils),
        ("Config", test_config),
        ("Data Loading", test_data_loading),
        ("Output Directory", test_output_dir),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"✗ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*70)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for test_name, passed_flag in results:
        status = "✓ PASS" if passed_flag else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All validation tests passed! Pipeline is ready to use.")
        return 0
    else:
        logger.error(f"\n⚠ {total - passed} test(s) failed. Please fix issues before running pipeline.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
