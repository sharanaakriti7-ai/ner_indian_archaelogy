#!/usr/bin/env python3
"""Project information and statistics"""

import os
from pathlib import Path
from collections import Counter

print("="*70)
print("INDIAN ARCHAEOLOGY NER - PROJECT INFORMATION")
print("="*70)

# Dataset Statistics
print("\n" + "="*70)
print("DATASET STATISTICS")
print("="*70)

data_files = {
    'train.conll': 'data/train.conll',
    'dev.conll': 'data/dev.conll',
    'test.conll': 'data/test.conll',
    'pretrain_corpus.txt': 'data/pretrain_corpus.txt'
}

for name, path in data_files.items():
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\n{name}:")
        print(f"  Total lines: {len(lines)}")
        print(f"  File size: {os.path.getsize(path) / 1024:.2f} KB")

# Parse training data for label distribution
print("\n" + "="*70)
print("TRAINING DATA ANALYSIS")
print("="*70)

sentences = []
all_labels = []

with open('data/train.conll', 'r', encoding='utf-8') as f:
    sentence_tokens = []
    sentence_labels = []
    
    for line in f:
        line = line.strip()
        
        if not line or line.startswith('#'):
            if sentence_tokens:
                sentences.append((sentence_tokens, sentence_labels))
                all_labels.extend(sentence_labels)
                sentence_tokens = []
                sentence_labels = []
            continue
        
        if '\t' in line:
            parts = line.split('\t')
        elif ' ' in line:
            parts = line.rsplit(' ', 1)
        else:
            parts = []
        
        if len(parts) >= 2:
            token = parts[0].strip()
            label = parts[1].strip()
            
            if token and label:
                sentence_tokens.append(token)
                sentence_labels.append(label)

if sentence_tokens:
    sentences.append((sentence_tokens, sentence_labels))
    all_labels.extend(sentence_labels)

print(f"\nTotal sentences: {len(sentences)}")
print(f"Total tokens: {sum(len(s[0]) for s in sentences)}")
print(f"Average tokens per sentence: {sum(len(s[0]) for s in sentences) / len(sentences):.1f}")

label_dist = Counter(all_labels)
print(f"\nLabel Distribution (total: {len(all_labels)} tokens):")
print(f"{'Label':<12} {'Count':<8} {'Percentage':<12}")
print("-" * 32)
for label, count in sorted(label_dist.items()):
    pct = (count / len(all_labels)) * 100
    print(f"{label:<12} {count:<8} {pct:>6.2f}%")

entity_types = {}
for label, count in label_dist.items():
    if label != 'O':
        entity = label.split('-')[1]
        entity_types[entity] = entity_types.get(entity, 0) + count

print(f"\nEntity Type Distribution:")
print(f"{'Type':<12} {'Count':<8}")
print("-" * 20)
for entity, count in sorted(entity_types.items()):
    print(f"{entity:<12} {count:<8}")

# Project structure
print("\n" + "="*70)
print("PROJECT FILES")
print("="*70)

src_files = {
    'config.py': 'Configuration and hyperparameters',
    'data_utils.py': 'Data loading, preprocessing, dataset classes',
    'pretrain.py': 'Domain-adaptive pretraining (MLM)',
    'finetune.py': 'NER fine-tuning with cross-validation',
    'evaluation.py': 'Metrics calculation and error analysis',
    'pipeline.py': 'Main training orchestration pipeline',
}

print("\nCore Modules (src/):")
for filename, desc in src_files.items():
    path = f'src/{filename}'
    if os.path.exists(path):
        size = os.path.getsize(path)
        with open(path, 'r') as f:
            lines = len(f.readlines())
        print(f"  {filename:<20} ({lines:>4} lines, {size/1024:>6.1f} KB) - {desc}")

scripts = {
    'run_training.py': 'Quick training and evaluation script',
    'inference.py': 'Inference interface for predictions',
    'quick_test.py': 'Quick CoNLL parser test',
    'quick_eval.py': 'Quick evaluation diagnostics',
    'eval_test.py': 'Test set evaluation with metrics',
}

print("\nUtility Scripts:")
for filename, desc in scripts.items():
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        with open(filename, 'r') as f:
            lines = len(f.readlines())
        print(f"  {filename:<20} ({lines:>4} lines, {size/1024:>6.1f} KB) - {desc}")

# Model info
print("\n" + "="*70)
print("MODEL CONFIGURATION")
print("="*70)

config = {
    'Base Model': 'bert-base-multilingual-cased (mBERT)',
    'Model Parameters': '177.3M',
    'Input Max Length': '512 tokens',
    'Entity Labels': '11 (O + 5 entity types × 2 for BIO)',
    'Entity Types': '5 (ART, PER, LOC, MAT, CON)',
    'Languages': 'Multilingual (Hindi-English code-mixed)',
}

for key, val in config.items():
    print(f"  {key:<25} {val}")

# Training configuration
print("\n" + "="*70)
print("TRAINING CONFIGURATION")
print("="*70)

training_config = {
    'Batch Size': '16',
    'Learning Rate': '2e-5',
    'Epochs (Quick Test)': '1',
    'Epochs (Full)': '20',
    'Optimizer': 'AdamW',
    'Weight Decay': '0.01',
    'Max Gradient Norm': '1.0',
    'Warmup Steps': '500',
    'MLM Probability': '0.15',
    'Class Weights': 'Yes (imbalanced dataset)',
}

for key, val in training_config.items():
    print(f"  {key:<25} {val}")

# Results
print("\n" + "="*70)
print("EVALUATION RESULTS (Test Set)")
print("="*70)

results = {
    'F1 Score (weighted)': '0.2927',
    'Precision (weighted)': '0.2141',
    'Recall (weighted)': '0.4627',
    'Average Loss': '1.8396',
    'Epochs Trained': '1 (quick-test)',
    'Best Model': 'outputs/quick_eval/best_model',
}

for key, val in results.items():
    print(f"  {key:<25} {val}")

# Dependencies
print("\n" + "="*70)
print("DEPENDENCIES")
print("="*70)

deps = {
    'PyTorch': '2.0.1',
    'Transformers': '4.33.2',
    'NumPy': '1.24.3',
    'Scikit-learn': '1.3.1',
    'Matplotlib': '3.7.2',
    'Seaborn': '0.12.2',
    'tqdm': '4.65.0',
    'Pandas': '2.0.3',
    'Tokenizers': '0.13.3',
}

for lib, version in deps.items():
    print(f"  {lib:<20} {version}")

print("\n" + "="*70)
print("✓ PROJECT INFORMATION COMPLETE")
print("="*70)
