"""
Comprehensive Configuration for Research-Grade NER Pipeline
Indian Archaeology Domain
"""

import os

# ====================================
# MODEL CONFIGURATION
# ====================================
MODEL_NAME = "models/indian-archaeology-bert"  # Primary model
SECONDARY_MODEL_NAME = "xlm-roberta-base"    # For ensemble
DOMAIN_MODEL_NAME = "indian-archaeology-bert"
MAX_LENGTH = 128
NUM_LABELS = 11  # BIO tags
USE_SELF_ATTENTION = True

# Entity Labels and BIO Tags
ENTITY_TYPES = {
    "O": 0,      # Outside
    "B-ART": 1,  # Beginning of Artifact
    "I-ART": 2,  # Inside Artifact
    "B-PER": 3,  # Beginning of Period
    "I-PER": 4,  # Inside Period
    "B-LOC": 5,  # Beginning of Location
    "I-LOC": 6,  # Inside Location
    "B-MAT": 7,  # Beginning of Material
    "I-MAT": 8,  # Inside Material
    "B-CON": 9,  # Beginning of Context
    "I-CON": 10, # Inside Context
}

LABEL_TO_ID = ENTITY_TYPES
ID_TO_LABEL = {v: k for k, v in ENTITY_TYPES.items()}

# ====================================
# TRAINING CONFIGURATION
# ====================================
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
EPOCHS = 1
WARMUP_STEPS = 10
WEIGHT_DECAY = 0.01
MAX_GRAD_NORM = 1.0
DROPOUT = 0.1

# Overfitting Control
USE_GRADIENT_CLIPPING = True
USE_WEIGHT_DECAY = True
EARLY_STOPPING_PATIENCE = 3
EARLY_STOPPING_MIN_DELTA = 0.0

# Loss Configuration
USE_FOCAL_LOSS = True  # Focal loss for class imbalance
FOCAL_ALPHA = 1.0
FOCAL_GAMMA = 2.0

# ====================================
# DATA AUGMENTATION
# ====================================
USE_DATA_AUGMENTATION = True
AUGMENTATION_FACTOR = 2
USE_BACK_TRANSLATION = False
USE_ENTITY_SWAP = True
USE_SYNONYM_REPLACEMENT = True

# ====================================
# WEAK SUPERVISION & GAZETTEERS
# ====================================
USE_GAZETTEER = True
USE_WEAK_LABELING = True
GAZETTEER_CONFIDENCE_THRESHOLD = 0.7

# ====================================
# CROSS-VALIDATION
# ====================================
USE_CROSS_VALIDATION = False
NUM_FOLDS = 2
CROSS_VALIDATION_RANDOM_STATE = 42

# ====================================
# MULTI-RUN STABILITY
# ====================================
USE_MULTI_SEED_TRAINING = False
NUM_SEEDS = 1
SEED_START = 42

# ====================================
# ENSEMBLE CONFIGURATION
# ====================================
USE_ENSEMBLE = True
ENSEMBLE_METHOD = "majority_vote"  # majority_vote, weighted, stacking
ENSEMBLE_WEIGHTS = None  # None for equal weights

# ====================================
# EVALUATION
# ====================================
USE_SEQEVAL = True
EVAL_METRICS = ['precision', 'recall', 'f1', 'support']
COMPUTE_PER_ENTITY_METRICS = True
COMPUTE_CONFUSION_MATRIX = True
PRINT_ERROR_ANALYSIS = True

# ====================================
# PRETRAINING CONFIGURATION (MLM)
# ====================================
USE_DOMAIN_PRETRAINING = False  # Set to True for domain adaptation
MLM_PROBABILITY = 0.15
PRETRAIN_EPOCHS = 5
PRETRAIN_BATCH_SIZE = 32
PRETRAIN_LEARNING_RATE = 1e-4
PRETRAIN_CORPUS_FILE = "data/pretrain_corpus.txt"

# ====================================
# CLASS WEIGHTS (for handling imbalance)
# ====================================
USE_CLASS_WEIGHTS = True
CLASS_WEIGHTS = {
    0: 0.1,   # O (most common)
    1: 2.0,   # B-ART
    2: 1.8,   # I-ART
    3: 2.0,   # B-PER
    4: 1.8,   # I-PER
    5: 1.5,   # B-LOC
    6: 1.3,   # I-LOC
    7: 2.2,   # B-MAT
    8: 2.0,   # I-MAT
    9: 1.8,   # B-CON
    10: 1.6,  # I-CON
}

# ====================================
# PATHS
# ====================================
DATA_DIR = "data/"
MODEL_DIR = "models/"
OUTPUT_DIR = "outputs/"
CHECKPOINTS_DIR = os.path.join(OUTPUT_DIR, "checkpoints/")

TRAIN_FILE = os.path.join(DATA_DIR, "train.conll")
TEST_FILE = os.path.join(DATA_DIR, "test.conll")
DEV_FILE = os.path.join(DATA_DIR, "dev.conll")

# ====================================
# LOGGING & OUTPUT
# ====================================
LOG_FILE = os.path.join(OUTPUT_DIR, "training.log")
SAVE_BEST_MODEL = True
SAVE_CHECKPOINT_EVERY = 100
PLOT_TRAINING_CURVES = True
SAVE_PREDICTIONS = True
SAVE_ERROR_ANALYSIS = True

# ====================================
# DEVICE & OPTIMIZATION
# ====================================
USE_CUDA = True
NUM_WORKERS = 4
PIN_MEMORY = True

# ====================================
# HYPERPARAMETER SEARCH
# ====================================
SEARCH_BATCH_SIZES = [8, 16, 32]
SEARCH_LEARNING_RATES = [1e-5, 2e-5, 3e-5]
SEARCH_DROPOUT_RATES = [0.1, 0.2, 0.3]

# ====================================
# RANDOM SEEDS
# ====================================
RANDOM_SEED = 42
NUMPY_SEED = 42
TORCH_SEED = 42
CUDA_SEED = 42

# ====================================
# PERFORMANCE TARGETS
# ====================================
TARGET_F1_SCORE = 0.60
TARGET_PRECISION = 0.55
TARGET_RECALL = 0.65
