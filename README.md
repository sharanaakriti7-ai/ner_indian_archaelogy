# Domain-Specific BERT NER for Indian Archaeology 🏛️

A comprehensive implementation of domain-adaptive BERT-based Named Entity Recognition (NER) system for Indian archaeological text, inspired by the paper "Can BERT Dig It?".

## 📋 Overview

This system implements:
- **Domain-Adaptive Pretraining** using Masked Language Modeling (MLM) on Indian archaeology corpus
- **Fine-tuning** for NER task with BIO tagging format
- **Low-resource handling** via data augmentation and cross-validation
- **Multilingual support** for Hindi-English code-mixed text
- **Comprehensive evaluation** with token-level and entity-level metrics

## 🎯 Entity Types

- **ART (Artifact)**: Archaeological artifacts, pottery, sculptures, etc.
- **PER (Period)**: Historical periods (Vedic, Mauryan, Gupta, etc.)
- **LOC (Location)**: Geographical locations and sites
- **MAT (Material)**: Materials used (stone, clay, gold, etc.)
- **CON (Context)**: Archaeological context and methods

## 📁 Project Structure

```
model1/
├── config.py                 # Configuration and hyperparameters
├── requirements.txt          # Python dependencies
├── data/
│   ├── train.conll          # Training dataset (60+ sentences)
│   ├── dev.conll            # Development dataset
│   ├── test.conll           # Test dataset
│   └── pretrain_corpus.txt  # Raw text for domain-adaptive pretraining
├── src/
│   ├── __init__.py
│   ├── data_utils.py        # Data loading and preprocessing
│   ├── pretrain.py          # Domain-adaptive pretraining (MLM)
│   ├── finetune.py          # NER fine-tuning pipeline
│   ├── evaluation.py        # Evaluation and error analysis
│   └── pipeline.py          # Main training orchestration
├── models/                   # Trained model checkpoints
├── outputs/                  # Training logs and results
└── README.md
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Run Complete Pipeline

```bash
# Full pipeline: pretraining + fine-tuning + evaluation
python -m src.pipeline

# Quick test mode (small epochs)
python -m src.pipeline --quick-test

# With cross-validation
python -m src.pipeline --cross-val

# Skip specific steps
python -m src.pipeline --no-pretrain --no-eval
```

### 3. Run Individual Components

```bash
# Domain-adaptive pretraining only
python -m src.pretrain

# Fine-tuning only
python -m src.finetune

# Evaluation and error analysis
python -m src.evaluation
```

## 📊 Configuration

Edit `config.py` to customize:

- **Model**: Base model, max sequence length, number of labels
- **Training**: Batch size, learning rate, epochs, warmup steps
- **Pretraining**: MLM probability, pretraining epochs
- **Evaluation**: Metrics calculation, cross-validation folds
- **Data**: File paths, augmentation settings

Key parameters:

```python
MODEL_NAME = "bert-base-multilingual-cased"  # mBERT
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
EPOCHS = 20
PRETRAIN_EPOCHS = 5
MLM_PROBABILITY = 0.15
NUM_FOLDS = 5  # For cross-validation
```

## 📚 Data Format

CoNLL format (word\ttag):

```
Harappa B-LOC
की O
खुदाई B-CON
में O
कई O
मिट्टी B-MAT
```

BIO tags:
- `O`: Outside any entity
- `B-{TYPE}`: Beginning of entity
- `I-{TYPE}`: Inside entity

## 🔬 Key Features

### 1. Domain-Adaptive Pretraining
- Starts from multilingual BERT (mBERT)
- Further pre-trains using Masked Language Modeling on archaeology corpus
- Learns domain-specific vocabulary and context
- Outputs: `indian-archaeology-bert`

### 2. Subword Token Handling
- Properly aligns BIO tags with subword tokens from transformer tokenizer
- First subword inherits entity label
- Subsequent subwords marked as continuation or ignored
- Handles Hindi-English code-mixing

### 3. Data Augmentation
- Back-translation augmentation
- Entity swapping between sentences
- Class weight adjustment for imbalanced labels

### 4. Evaluation Metrics

**Token-Level:**
- Precision, Recall, F1 (weighted & macro)
- Per-class metrics

**Entity-Level:**
- Exact entity matching
- Entity-level precision, recall, F1
- Type-specific performance

**Error Analysis:**
- B vs I confusion detection
- Entity type confusion matrix
- False positives and false negatives breakdown

## 📈 Training Output

The system generates:

```
outputs/
├── experiment_YYYYMMDD_HHMMSS/
│   ├── indian-archaeology-bert/        # Pretrained model
│   ├── ner_models/
│   │   ├── best_model/                 # Best fine-tuned model
│   │   └── final_model/
│   ├── cross_validation/               # CV results (if enabled)
│   ├── evaluation_report.txt           # Detailed metrics
│   ├── confusion_matrix.png            # Visualization
│   └── training.log                    # Training logs
```

## 🎓 Training Pipeline Steps

### Step 1: Domain-Adaptive Pretraining
```
Input: pretrain_corpus.txt (raw archaeology text)
Process: MLM on 15% masked tokens
Output: Domain-adapted BERT weights
```

### Step 2: NER Fine-tuning
```
Input: train.conll (labeled NER data)
Process: Token classification on domain-adapted BERT
Validation: dev.conll
Output: Fine-tuned NER model
```

### Step 3: Evaluation
```
Input: test.conll (held-out test set)
Compute: Token-level & entity-level metrics
Generate: Error analysis, confusion matrix
Output: evaluation_report.txt, visualizations
```

## 💡 Advanced Usage

### Cross-Validation
```bash
python -m src.pipeline --cross-val
```
Runs 5-fold cross-validation for more robust evaluation.

### Making Predictions
```python
from src.pipeline import TrainingPipeline

pipeline = TrainingPipeline()
sentences = [
    ["Harappa", "की", "खुदाई", "में", "pottery", "मिली"],
    ["Vedic", "period", "में", "copper", "tools", "use", "होते", "थे"]
]
predictions = pipeline.predict_on_new_text(sentences)
```

### Custom Model Path
```python
from src.evaluation import NEREvaluator

evaluator = NEREvaluator("path/to/custom/model")
results = evaluator.print_evaluation_report("data/test.conll")
```

## 🔧 Hyperparameter Tuning

Experiment with these key parameters in `config.py`:

```python
# Learning rate schedule
LEARNING_RATE = 2e-5           # Try: 1e-5, 3e-5, 5e-5
PRETRAIN_LEARNING_RATE = 1e-4

# Batch size
BATCH_SIZE = 16                # Try: 8, 32, 64
PRETRAIN_BATCH_SIZE = 32

# Epochs
EPOCHS = 20
PRETRAIN_EPOCHS = 5

# Regularization
WEIGHT_DECAY = 0.01            # Try: 0.005, 0.02
MAX_GRAD_NORM = 1.0

# Class weights for imbalance
USE_CLASS_WEIGHTS = True
CLASS_WEIGHTS = {...}          # Adjust per entity type
```

## 📊 Expected Results

### Baseline (mBERT without pretraining)
- Token-level F1: ~65-70%
- Entity-level F1: ~55-60%

### With Domain-Adaptive Pretraining
- Token-level F1: ~75-80% (expected improvement)
- Entity-level F1: ~70-75% (expected improvement)

### Common Improvements
- Better artifact vs material distinction
- Reduced B vs I confusion
- Improved period and location recognition

## 🐛 Troubleshooting

### Out of Memory
```python
# Reduce batch size in config.py
BATCH_SIZE = 8
```

### Slow Training
```python
# Reduce epochs for quick testing
EPOCHS = 5
PRETRAIN_EPOCHS = 1
python -m src.pipeline --quick-test
```

### Poor Entity Recognition
```python
# Increase pretraining epochs
PRETRAIN_EPOCHS = 10

# Increase class weights for rare entities
CLASS_WEIGHTS['B-ART'] = 3.0
```

## 📚 Dataset Format Requirements

**CoNLL Format:**
- One token per line with tab-separated labels
- Empty lines separate sentences
- Comments start with `#`

**Pretraining Corpus:**
- One sentence per line (raw text)
- No labels needed
- Can mix Hindi and English

## 🔍 Evaluation Metrics Explanation

**Precision**: Of predicted entities, how many are correct?
**Recall**: Of true entities, how many did we find?
**F1**: Harmonic mean of precision and recall

**Weighted vs Macro:**
- **Weighted**: Accounts for class imbalance (more common classes weighted higher)
- **Macro**: Equal weight to all classes

## 🌟 Tips for Best Results

1. **Data Quality**: Ensure consistent annotation in CoNLL format
2. **Domain Corpus**: Add more archaeology text to `pretrain_corpus.txt`
3. **Pretraining**: More epochs on corpus improves performance
4. **Class Weights**: Adjust based on entity frequency in your data
5. **Cross-Validation**: Use for small datasets to reduce variance
6. **Error Analysis**: Review confusion matrix to identify systematic errors

## 📖 References

- "Can BERT Dig It?" - Domain-specific BERT for archaeology (ArcheoBERTje)
- BERT: Pre-training of Deep Bidirectional Transformers
- Multilingual BERT (mBERT) for code-mixed NER
- BIO tagging scheme for token classification

## 📝 License

MIT License - Feel free to use and modify for your research.

## 👤 Author

NLP Research Team - Indian Archaeology Project

## 📧 Questions & Issues

For bugs, feature requests, or questions, please open an issue or contact the team.

---

**Happy NER Research! 🎯**
