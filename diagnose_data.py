"""
Simple diagnostic script to verify data loading and show metrics
"""
import os
import sys
sys.path.insert(0, 'c:\\Users\\shara\\OneDrive\\Desktop\\pro\\model1')

import config
from src.data_utils import CoNLLDataset
from collections import Counter

print("="*80)
print("DIAGNOSTIC: CONLL DATA LOADING")
print("="*80)

# Load raw CoNLL data
print("\nReading train.conll file directly...")
with open(config.TRAIN_FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f"Total lines: {len(lines)}")
    print("\nFirst 30 lines:")
    for i, line in enumerate(lines[:30]):
        print(f"  {i+1:2d}: {repr(line)}")

# Parse using CoNLLDataset
print("\n" + "="*80)
print("Loading with CoNLLDataset class...")
train_data = CoNLLDataset(config.TRAIN_FILE)

print(f"\nLoaded {len(train_data)} sentences")
print(f"Total tokens: {sum(len(s) for s in train_data.sentences)}")

# Show first few sentences with labels
print("\n" + "="*80)
print("PARSED SENTENCES")
print("="*80)

for idx in range(min(5, len(train_data))):
    sent, labels = train_data[idx]
    print(f"\nSentence {idx+1}:")
    print(f"  Tokens ({len(sent)}): {' '.join(sent)}")
    print(f"  Labels ({len(labels)}): {' '.join(labels)}")
    
    # Show paired view
    print(f"  Paired:")
    for token, label in zip(sent, labels):
        print(f"    {token:20s} -> {label}")

# Label statistics
print("\n" + "="*80)
print("LABEL DISTRIBUTION")
print("="*80)

all_labels = []
all_sentences = []
entity_types = Counter()

for sent, labels in zip(train_data.sentences, train_data.labels):
    all_sentences.extend(sent)
    all_labels.extend(labels)
    for label in labels:
        if label != 'O':
            entity_type = label.split('-')[1]
            entity_types[entity_type] += 1

label_counts = Counter(all_labels)
total = len(all_labels)

print(f"\nTotal tokens: {total}")
print(f"{'Label':<15} {'Count':<10} {'%':<10}")
print("-"*35)
for label in sorted(label_counts.keys()):
    count = label_counts[label]
    pct = (count / total) * 100
    print(f"{label:<15} {count:<10} {pct:>6.2f}%")

if entity_types:
    print(f"\nEntity Types:")
    print(f"{'Type':<10} {'Count':<10}")
    print("-"*20)
    for etype in sorted(entity_types.keys()):
        count = entity_types[etype]
        print(f"{etype:<10} {count:<10}")
else:
    print("\n⚠ No entity types found!")

# Check alignment
print("\n" + "="*80)
print("ALIGNMENT CHECK")
print("="*80)

misaligned = 0
for idx, (sent, labels) in enumerate(zip(train_data.sentences, train_data.labels)):
    if len(sent) != len(labels):
        print(f"  Sentence {idx}: Length mismatch! Tokens={len(sent)}, Labels={len(labels)}")
        misaligned += 1

if misaligned == 0:
    print("✓ All sentences properly aligned")
else:
    print(f"⚠ {misaligned} sentences have misalignment")

# Configuration summary
print("\n" + "="*80)
print("CONFIGURATION SUMMARY")
print("="*80)
print(f"Model: {config.MODEL_NAME}")
print(f"Batch size: {config.BATCH_SIZE}")
print(f"Max length: {config.MAX_LENGTH}")
print(f"Number of labels: {config.NUM_LABELS}")
print(f"Label mapping: {config.LABEL_TO_ID}")

print("\n" + "="*80)
print("✓ Diagnostic complete")
print("="*80)
