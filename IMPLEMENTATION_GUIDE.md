# Complete NER Pipeline - Implementation Guide

## 📋 Overview

This is a **research-grade, production-ready NER (Named Entity Recognition) system** for Indian Archaeology domain. The pipeline addresses:

- **Overfitting control** (dropout, early stopping, gradient clipping, weight decay)
- **Data scarcity** (augmentation, weak labeling, cross-validation)
- **Class imbalance** (focal loss, class weights)
- **Stability** (multi-seed training, ensemble methods)
- **Comprehensive evaluation** (seqeval, error analysis, per-entity metrics)

## 🏗️ Architecture

### Core Components

```
model_crf.py          → TransformerCRFModel (BERT + BiLSTM + CRF)
utils.py              → Utilities (seeding, plotting, early stopping)
train.py              → Training framework with overfitting control
evaluate.py           → Comprehensive evaluation with seqeval
cross_validation.py   → K-fold cross-validation
ensemble.py           → Ensemble methods (voting, stacking)
pipeline_main.py      → Main orchestration script
config.py             → Centralized configuration
```

### Model Architecture

```
Input Text
    ↓
Tokenization (BERT tokenizer with subword alignment)
    ↓
Transformer Encoder (BERT/mBERT)
    ↓
Dropout (0.1-0.3 tunable)
    ↓
BiLSTM (bidirectional)
    ↓
Linear Layer (to num_labels)
    ↓
CRF Layer (Viterbi decoding)
    ↓
BIO Tag Predictions
```

## 🚀 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Prepare Data

Data should be in CoNLL format (one token per line, blank line between sentences):

```
Token1  B-LOC
Token2  I-LOC
Token3  O

Token4  B-ART
...
```

Place files in `data/`:
- `train.conll` - Training data
- `dev.conll` - Validation data  
- `test.conll` - Test data

### 3. Run Complete Pipeline

```python
from pipeline_main import NERPipeline

# Create pipeline
pipeline = NERPipeline()

# Run full pipeline with all stages
results = pipeline.run_full_pipeline()
```

Or run from command line:

```bash
python pipeline_main.py
```

## 📚 Module Details

### 1. Model (model_crf.py)

#### Key Classes

**TransformerCRFModel**
```python
model = TransformerCRFModel(
    model_name='bert-base-multilingual-cased',
    num_labels=11,
    dropout=0.1
)

# Forward pass
embeddings, loss = model(input_ids, attention_mask, labels)

# Inference
embeddings, predictions = model(input_ids, attention_mask)
```

**CRFLayer**
- Implements full CRF with Viterbi decoding
- Forward algorithm for loss computation
- Proper handling of variable-length sequences

**FocalLoss**
- Addresses class imbalance
- Focuses training on hard examples
- Parameters: alpha=1.0, gamma=2.0

### 2. Training (train.py)

#### Features

- **EarlyStopping**: Stops training when validation metric plateaus
- **GradientClipping**: Prevents exploding gradients (max_norm=1.0)
- **WeightDecay**: L2 regularization (weight_decay=0.01)
- **LR Scheduler**: Linear warmup + decay schedule
- **Loss Tracking**: Plots train vs validation curves

#### Usage

```python
from train import NERTrainer

trainer = NERTrainer(
    model=model,
    train_dataset=train_data,
    dev_dataset=dev_data,
    batch_size=16,
    learning_rate=2e-5,
    weight_decay=0.01,
    gradient_clip=1.0,
    dropout=0.1,
    use_focal_loss=True
)

history = trainer.train(
    epochs=30,
    early_stopping_patience=3,
    warmup_steps=500
)
```

#### Multi-Seed Training

```python
from train import MultiSeedTrainer

multi_trainer = MultiSeedTrainer(
    model_name='bert-base-multilingual-cased',
    num_labels=11,
    num_seeds=5,
    output_dir='outputs/'
)

results = multi_trainer.train_all_seeds(
    train_dataset=train_data,
    dev_dataset=dev_data,
    test_dataset=test_data,
    epochs=30
)

# Results include: mean F1, std F1 across seeds
```

### 3. Evaluation (evaluate.py)

#### Features

- **Entity-level metrics** using seqeval (Precision, Recall, F1)
- **Per-entity performance** breakdown
- **Confusion matrix** analysis
- **Error analysis** showing common confusions
- **Sample predictions** display

#### Usage

```python
from evaluate import NEREvaluator

evaluator = NEREvaluator(id_to_label)

metrics = evaluator.evaluate_predictions(
    predictions=pred_labels,
    labels=true_labels
)

# Returns: precision, recall, f1, per_entity metrics
evaluator.print_summary(metrics)
evaluator.print_error_analysis()
```

### 4. Data Pipeline (src/data_utils.py, augmentation.py)

#### CoNLL Loading

```python
from src.data_utils import CoNLLDataset, NERDataset

# Load CoNLL
train_conll = CoNLLDataset('data/train.conll')

# Convert to NER dataset with tokenization
tokenizer = AutoTokenizer.from_pretrained(model_name)
train_dataset = NERDataset(
    train_conll.sentences,
    train_conll.labels,
    tokenizer,
    label_to_id,
    max_length=512
)
```

#### Data Augmentation

```python
from augmentation import DataAugmenter

augmenter = DataAugmenter(seed=42)

# Available techniques:
augmented = augmenter.synonym_replacement(sentence)
augmented = augmenter.entity_swap(sentence)
augmented = augmenter.back_translation_simulation(sentence)
```

### 5. Weak Labeling (gazetteer.py)

```python
from gazetteer import ArchaeologyGazetteer, WeakSupervisionGenerator

gazetteer = ArchaeologyGazetteer()
weak_gen = WeakSupervisionGenerator(gazetteer)

# Generate weak labels
weak_labels = weak_gen.generate_weak_labels(text)
```

### 6. Cross-Validation (cross_validation.py)

```python
from cross_validation import CrossValidator

cv = CrossValidator(n_splits=5, random_state=42)

cv_results = cv.cross_validate(
    dataset=combined_dataset,
    train_config=config_dict,
    device='cuda',
    output_dir='outputs/cv'
)

# Reports mean and std of metrics across folds
```

### 7. Ensemble Methods (ensemble.py)

#### Hard Voting (Majority Vote)

```python
from ensemble import HardVotingEnsemble

ensemble = HardVotingEnsemble(
    models=[model1, model2, model3],
    device='cuda'
)

predictions = ensemble.predict(input_ids, attention_mask)
```

#### Soft Voting (Average Probabilities)

```python
from ensemble import SoftVotingEnsemble

ensemble = SoftVotingEnsemble(
    models=[model1, model2, model3],
    device='cuda'
)

predictions = ensemble.predict(input_ids, attention_mask)
```

#### Weighted Ensemble

```python
from ensemble import NERensemble

ensemble = NERensemble(
    models=[model1, model2],
    weights=[0.6, 0.4],  # Custom weights
    device='cuda'
)

predictions = ensemble.predict_ensemble(input_ids, attention_mask)
```

## ⚙️ Configuration (config.py)

### Key Hyperparameters

```python
# Model
MODEL_NAME = "bert-base-multilingual-cased"
MAX_LENGTH = 512
NUM_LABELS = 11
DROPOUT = 0.1

# Training
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
EPOCHS = 30
WEIGHT_DECAY = 0.01
MAX_GRAD_NORM = 1.0

# Overfitting Control
EARLY_STOPPING_PATIENCE = 3
USE_FOCAL_LOSS = True
USE_GRADIENT_CLIPPING = True

# Data Augmentation
USE_DATA_AUGMENTATION = True
AUGMENTATION_FACTOR = 2

# Cross-Validation
NUM_FOLDS = 5

# Multi-Seed
NUM_SEEDS = 5

# Ensemble
USE_ENSEMBLE = True
ENSEMBLE_METHOD = "majority_vote"
```

### Hyperparameter Search

Grid search over:
- Batch sizes: [8, 16, 32]
- Learning rates: [1e-5, 2e-5, 3e-5]
- Dropout rates: [0.1, 0.2, 0.3]

```python
config.SEARCH_BATCH_SIZES
config.SEARCH_LEARNING_RATES
config.SEARCH_DROPOUT_RATES
```

## 📊 Training Pipeline

### Stage-by-Stage Execution

1. **Data Loading**: Load CoNLL files
2. **Data Augmentation**: Apply augmentation techniques
3. **Single Model Training**: Train primary model with early stopping
4. **Multi-Seed Training**: Train with 5 different seeds for stability
5. **Cross-Validation**: 5-fold CV on combined train+dev
6. **Evaluation**: Comprehensive evaluation on test set
7. **Ensemble**: Combine models for better predictions

### Outputs

```
outputs/
├── experiment_YYYYMMDD_HHMMSS/
│   ├── pipeline.log              # Main log
│   ├── config.json               # Configuration
│   ├── pipeline_results.json     # All results
│   ├── single_model/
│   │   ├── best_model/           # Best checkpoint
│   │   ├── final_model/          # Final model
│   │   └── config.json
│   ├── multi_seed/
│   │   ├── seed_42/
│   │   ├── seed_43/
│   │   └── ...
│   └── cross_validation/
│       ├── fold_1/
│       ├── fold_2/
│       └── ...
```

## 🎯 Performance Targets

- **F1 Score**: ≥ 0.60 (from 0.29)
- **Precision**: ≥ 0.55
- **Recall**: ≥ 0.65
- **Overfitting Gap**: Minimize train-val loss gap

## 🔍 Troubleshooting

### CUDA Out of Memory
```python
config.BATCH_SIZE = 8  # Reduce batch size
config.MAX_LENGTH = 256  # Reduce sequence length
```

### Poor Convergence
```python
config.LEARNING_RATE = 3e-5  # Try higher LR
config.WARMUP_STEPS = 1000   # More warmup
```

### High Overfitting
```python
config.DROPOUT = 0.3         # Increase dropout
config.WEIGHT_DECAY = 0.05   # Increase weight decay
```

## 📖 References

- [seqeval Documentation](https://github.com/chakki-works/seqeval)
- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [PyTorch CRF](https://pytorch-crf.readthedocs.io/)
- [BERT Paper](https://arxiv.org/abs/1810.04805)

## 📝 Citation

This pipeline was designed for research in low-resource NER systems. If used in publications, please cite:

```
@misc{ner_pipeline_2024,
  title={Research-Grade NER Pipeline for Indian Archaeology},
  author={Your Name},
  year={2024}
}
```

## 📧 Support

For issues or questions, please create an issue in the repository.
