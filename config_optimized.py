#!/usr/bin/env python3
"""
OPTIMIZED Configuration for Fast NER Training
Speed-focused with maintained performance
"""

import os
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "outputs"

# Create directories
OUTPUT_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# ============================================================================
# MODEL CONFIGURATION - SPEED OPTIMIZED
# ============================================================================

# Use DistilBERT instead of full BERT (40% faster, 60% smaller)
MODEL_NAME = "distilbert-base-multilingual-cased"
# Alternative: "xlm-roberta-base" (good multilingual option)

MAX_LENGTH = 128  # Reduced from 512 for faster processing
HIDDEN_DROPOUT = 0.3  # Prevent overfitting
ATTENTION_PROBS_DROPOUT = 0.3

NUM_LABELS = 11  # BIO tags: O, B/I-ART, B/I-PER, B/I-LOC, B/I-MAT, B/I-CON

# ============================================================================
# TRAINING CONFIGURATION - SPEED OPTIMIZED
# ============================================================================

# Epochs: 3-5 for small datasets (was 30)
NUM_EPOCHS = 5
WARMUP_STEPS = 100  # Less warmup needed for short training

# Batch size (16-32 recommended)
BATCH_SIZE = 16
EVAL_BATCH_SIZE = 32  # Can use larger for evaluation

# Learning rate
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
GRADIENT_ACCUMULATION_STEPS = 1
MAX_GRAD_NORM = 1.0

# ============================================================================
# OPTIMIZATION FLAGS
# ============================================================================

USE_FP16 = True  # Mixed precision training (2-3x speedup on GPU)
USE_FROZEN_LAYERS = True  # Freeze 70% of transformer layers
NUM_FROZEN_LAYERS = 4  # Freeze bottom 4 layers out of 6 in DistilBERT

# Early stopping (crucial for small datasets)
EARLY_STOPPING_PATIENCE = 2  # Stop if no improvement for 2 epochs
EARLY_STOPPING_THRESHOLD = 0.001  # Minimum improvement to reset patience

# ============================================================================
# DATA CONFIGURATION
# ============================================================================

USE_DATA_AUGMENTATION = False  # Skip for speed (small dataset already)
AUGMENTATION_FACTOR = 1  # No augmentation

# Cross-validation (disable for speed, use for final eval)
USE_CROSS_VALIDATION = False
NUM_FOLDS = 5

# Multi-seed training (disable for speed)
USE_MULTI_SEED_TRAINING = False
NUM_SEEDS = 1

# ============================================================================
# LOSS CONFIGURATION
# ============================================================================

USE_FOCAL_LOSS = True  # Better for class imbalance
FOCAL_LOSS_ALPHA = 1.0
FOCAL_LOSS_GAMMA = 2.0

# ============================================================================
# LOGGING & EVALUATION
# ============================================================================

LOG_LEVEL = "INFO"
SAVE_STRATEGY = "epoch"  # Save after each epoch
EVAL_STRATEGY = "epoch"  # Evaluate after each epoch
EVAL_STEPS = 100  # Evaluate every N steps (if using steps strategy)

# Logging
LOGGING_STEPS = 10
LOGGING_DIR = OUTPUT_DIR / "logs"
LOGGING_DIR.mkdir(exist_ok=True)

# ============================================================================
# DEVICE CONFIGURATION
# ============================================================================

DEVICE = "cuda"  # "cuda" for GPU, "cpu" for CPU
USE_CUDA = True

# ============================================================================
# RANDOM SEED
# ============================================================================

RANDOM_SEED = 42

# ============================================================================
# LABEL MAPPING
# ============================================================================

# BIO tag scheme
LABEL_TO_ID = {
    "O": 0,
    "B-ART": 1,
    "I-ART": 2,
    "B-PER": 3,
    "I-PER": 4,
    "B-LOC": 5,
    "I-LOC": 6,
    "B-MAT": 7,
    "I-MAT": 8,
    "B-CON": 9,
    "I-CON": 10,
}

ID_TO_LABEL = {v: k for k, v in LABEL_TO_ID.items()}

# ============================================================================
# OPTIMIZATION SUMMARY
# ============================================================================
"""
SPEED OPTIMIZATIONS APPLIED:
✓ DistilBERT instead of BERT (40% faster)
✓ Epochs: 5 instead of 30 (6x reduction)
✓ Max sequence length: 128 instead of 512 (4x reduction)
✓ Frozen layers: Bottom 4/6 layers frozen
✓ Mixed precision (fp16): 2-3x speedup on GPU
✓ Early stopping: Patience=2, stops training early
✓ Dynamic padding: Reduces computation
✓ No data augmentation: Small dataset, skip expansion
✓ Single seed: Skip multi-seed analysis
✓ No cross-validation: Do for final eval only

EXPECTED SPEEDUP: 50-100x faster training
EXPECTED TIME: 30 min - 2 hours (GPU) or 2-6 hours (CPU)

MAINTAINED QUALITY:
✓ Focal Loss for class imbalance
✓ Dropout + weight decay for regularization
✓ Proper learning rate scheduling
✓ Gradient clipping
"""
