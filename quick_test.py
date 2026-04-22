#!/usr/bin/env python3
"""Quick test of CoNLL parser fix"""

# Read and parse directly without importing full package
sentence_tokens = []
sentence_labels = []
sentences = []
labels_list = []

with open('data/train.conll', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        
        # Empty line or comment indicates end of sentence
        if not line or line.startswith('#'):
            if sentence_tokens:
                sentences.append(sentence_tokens)
                labels_list.append(sentence_labels)
                sentence_tokens = []
                sentence_labels = []
            continue
        
        # Parse token and label (handle both tab and space separation)
        if '\t' in line:
            parts = line.split('\t')
        elif ' ' in line:
            parts = line.rsplit(' ', 1)  # Split from right
        else:
            parts = []
        
        if len(parts) >= 2:
            token = parts[0].strip()
            label = parts[1].strip()
            
            if token and label:
                sentence_tokens.append(token)
                sentence_labels.append(label)

# Add last sentence if exists
if sentence_tokens:
    sentences.append(sentence_tokens)
    labels_list.append(sentence_labels)

print(f"✓ Loaded {len(sentences)} sentences")
print(f"✓ Total tokens: {sum(len(s) for s in sentences)}")

# Check label distribution
from collections import Counter
all_labels = [l for sent_labels in labels_list for l in sent_labels]
label_counts = Counter(all_labels)

print("\nLabel Distribution:")
for label, count in sorted(label_counts.items()):
    pct = (count / len(all_labels)) * 100
    print(f"  {label:12} {count:4}  ({pct:6.2f}%)")

print("\nFirst 3 sentences:")
for i in range(min(3, len(sentences))):
    print(f"\nSentence {i+1}:")
    for token, label in zip(sentences[i], labels_list[i]):
        print(f"  {token:20} -> {label}")
