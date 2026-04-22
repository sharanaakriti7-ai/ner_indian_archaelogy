"""
Complete evaluation script with training and metrics
"""
import os
import sys
import logging
import torch
import torch.nn as nn
from torch.optim import AdamW
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score
from tqdm import tqdm

import config
from src.data_utils import load_and_prepare_data, CoNLLDataset
from src.finetune import NERFineTuner
from src.evaluation import NEREvaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set device
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Device: {device}")

print("\n" + "="*80)
print("INDIAN ARCHAEOLOGY NER - EVALUATION METRICS")
print("="*80)

# 1. Load data
print("\n### STEP 1: DATA LOADING ###\n")
train_loader, dev_loader, test_loader, tokenizer = load_and_prepare_data(
    config.TRAIN_FILE,
    config.DEV_FILE,
    config.TEST_FILE,
    config.MODEL_NAME,
    config.BATCH_SIZE,
    augment=False
)

print(f"✓ Train samples: {len(train_loader) * config.BATCH_SIZE} (batches: {len(train_loader)})")
print(f"✓ Dev samples: {len(dev_loader) * config.BATCH_SIZE} (batches: {len(dev_loader)})")
print(f"✓ Test samples: {len(test_loader) * config.BATCH_SIZE} (batches: {len(test_loader)})")

# 2. Load raw data and print statistics
print("\n### STEP 2: DATASET STATISTICS ###\n")
train_data = CoNLLDataset(config.TRAIN_FILE)

print(f"Total sentences: {len(train_data)}")
print(f"Total tokens: {sum(len(s) for s in train_data.sentences)}")

# Label distribution
from collections import Counter
label_counts = Counter()
for labels in train_data.labels:
    for label in labels:
        label_counts[label] += 1

total = sum(label_counts.values())
print(f"\nLabel Distribution:")
print(f"{'Label':<15} {'Count':<8} {'%':<8}")
print("-"*30)
for label in sorted(label_counts.keys()):
    count = label_counts[label]
    pct = (count / total) * 100
    print(f"{label:<15} {count:<8} {pct:>6.2f}%")

# Entity type distribution
entity_type_counts = Counter()
for label_seq in train_data.labels:
    for label in label_seq:
        if label != 'O':
            entity_type = label.split('-')[1]
            entity_type_counts[entity_type] += 1

if entity_type_counts:
    print(f"\nEntity Type Counts:")
    print(f"{'Type':<10} {'Count':<8}")
    print("-"*18)
    for entity_type in sorted(entity_type_counts.keys()):
        count = entity_type_counts[entity_type]
        print(f"{entity_type:<10} {count:<8}")
else:
    print("\n⚠ No entities found in dataset - check CoNLL format")

# 3. Configuration
print("\n### STEP 3: CONFIGURATION ###\n")
print(f"Model: {config.MODEL_NAME}")
print(f"Number of labels: {config.NUM_LABELS}")
print(f"Batch size: {config.BATCH_SIZE}")
print(f"Learning rate: {config.LEARNING_RATE}")
print(f"Epochs (quick test): 1")
print(f"Use class weights: {config.USE_CLASS_WEIGHTS}")

print(f"\nEntity Types (BIO):")
for label_id, label in sorted(config.ID_TO_LABEL.items()):
    print(f"  {label_id}: {label}")

# 4. Train model (quick test - 1 epoch)
print("\n### STEP 4: TRAINING (1 EPOCH DEMO) ###\n")

finetuner = NERFineTuner(device=device)

print("Training for 1 epoch...")
model = finetuner.train(train_loader, dev_loader, epochs=1, output_dir=config.MODEL_DIR)

print("\n✓ Training completed")

# 5. Evaluation
print("\n### STEP 5: EVALUATION METRICS ###\n")

finetuner.model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for batch in tqdm(test_loader, desc="Evaluating"):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        
        outputs = finetuner.model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        logits = outputs.logits
        preds = torch.argmax(logits, dim=2)
        
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(batch['labels'].cpu().numpy())

# Flatten and remove -100
true_flat = []
pred_flat = []

for true_seq, pred_seq in zip(all_labels, all_preds):
    for true_label, pred_label in zip(true_seq, pred_seq):
        if true_label != -100:
            true_flat.append(true_label)
            pred_flat.append(pred_label)

true_flat = np.array(true_flat)
pred_flat = np.array(pred_flat)

# Calculate metrics
if len(np.unique(true_flat)) > 1:
    precision = precision_score(true_flat, pred_flat, average='weighted', zero_division=0)
    recall = recall_score(true_flat, pred_flat, average='weighted', zero_division=0)
    f1 = f1_score(true_flat, pred_flat, average='weighted', zero_division=0)
    
    precision_macro = precision_score(true_flat, pred_flat, average='macro', zero_division=0)
    recall_macro = recall_score(true_flat, pred_flat, average='macro', zero_division=0)
    f1_macro = f1_score(true_flat, pred_flat, average='macro', zero_division=0)
    
    print("TOKEN-LEVEL METRICS (Weighted):")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")
    print(f"  F1-Score: {f1:.4f}")
    
    print("\nTOKEN-LEVEL METRICS (Macro):")
    print(f"  Precision: {precision_macro:.4f}")
    print(f"  Recall: {recall_macro:.4f}")
    print(f"  F1-Score: {f1_macro:.4f}")
    
    print("\nPER-CLASS METRICS:")
    precision_per_class = precision_score(true_flat, pred_flat, average=None, zero_division=0)
    recall_per_class = recall_score(true_flat, pred_flat, average=None, zero_division=0)
    f1_per_class = f1_score(true_flat, pred_flat, average=None, zero_division=0)
    
    print(f"{'Label':<15} {'Precision':<12} {'Recall':<12} {'F1':<12}")
    print("-"*52)
    for label_id in range(config.NUM_LABELS):
        label = config.ID_TO_LABEL[label_id]
        p = precision_per_class[label_id] if label_id < len(precision_per_class) else 0
        r = recall_per_class[label_id] if label_id < len(recall_per_class) else 0
        f = f1_per_class[label_id] if label_id < len(f1_per_class) else 0
        print(f"{label:<15} {p:<12.4f} {r:<12.4f} {f:<12.4f}")
else:
    print("⚠ Insufficient unique labels for comprehensive metrics")
    print(f"  Unique true labels: {len(np.unique(true_flat))}")

# 6. Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"""
✓ Dataset loaded: {len(train_data)} sentences
✓ Model: {config.MODEL_NAME}
✓ Training completed: 1 epoch
✓ Evaluation completed

NEXT STEPS:
1. For full training: python -m src.pipeline
2. For quick test: python -m src.pipeline --quick-test
3. For cross-validation: python -m src.pipeline --cross-val
4. For inference: python inference.py --model models/final_model --text "your text"

EXPECTED RESULTS:
- Token-level F1: ~70-75% (baseline mBERT without pretraining)
- Token-level F1: ~80-85% (with domain pretraining)
- Entity-level F1: ~65-75% (with improvements)
""")
print("="*80)
