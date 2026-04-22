#!/usr/bin/env python3
"""Verify cleaned data integrity and quality"""

import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

def read_conll(filename):
    """Read CoNLL format file"""
    sentences = []
    current = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                if current:
                    sentences.append(current)
                    current = []
            else:
                parts = line.split('\t')
                if len(parts) == 2:
                    current.append(tuple(parts))
    if current:
        sentences.append(current)
    return sentences

def validate_bio_tags(sentences):
    """Validate BIO tag sequences"""
    valid_tags = {'O', 'B-ART', 'I-ART', 'B-PER', 'I-PER', 'B-LOC', 'I-LOC', 
                  'B-MAT', 'I-MAT', 'B-CON', 'I-CON'}
    
    errors = []
    for sent_idx, sentence in enumerate(sentences):
        prev_tag = 'O'
        for token_idx, (token, label) in enumerate(sentence):
            # Check valid tag
            if label not in valid_tags:
                errors.append(f"Sent {sent_idx}: Invalid tag '{label}'")
            
            # Check BIO sequence validity
            if label.startswith('I-'):
                entity = label.split('-')[1]
                if prev_tag == 'O' or prev_tag.endswith(entity) == False:
                    errors.append(f"Sent {sent_idx}: Invalid BIO sequence at token {token_idx}")
            
            prev_tag = label
    
    return errors

def get_statistics(sentences):
    """Get detailed statistics"""
    total_tokens = sum(len(sent) for sent in sentences)
    
    label_counts = Counter()
    entity_counts = Counter()
    avg_len = total_tokens / len(sentences) if sentences else 0
    
    for sentence in sentences:
        for token, label in sentence:
            label_counts[label] += 1
            if label.startswith('B-'):
                entity = label.split('-')[1]
                entity_counts[entity] += 1
    
    return {
        'sentences': len(sentences),
        'tokens': total_tokens,
        'avg_tokens_per_sent': avg_len,
        'labels': dict(label_counts),
        'entities': dict(entity_counts),
    }

def main():
    print("="*80)
    print("DATA VERIFICATION AND QUALITY REPORT")
    print("="*80)
    
    files = {
        'Training': 'data/train.conll',
        'Development': 'data/dev.conll',
        'Test': 'data/test.conll'
    }
    
    total_train = 0
    total_dev = 0
    total_test = 0
    total_entities = Counter()
    
    for name, filepath in files.items():
        print(f"\n[{name.upper()}]")
        print("-" * 80)
        
        try:
            sentences = read_conll(filepath)
            stats = get_statistics(sentences)
            errors = validate_bio_tags(sentences)
            
            print(f"Sentences:              {stats['sentences']}")
            print(f"Total Tokens:           {stats['tokens']}")
            print(f"Avg Tokens/Sentence:    {stats['avg_tokens_per_sent']:.2f}")
            
            print(f"\nEntity Distribution:")
            for entity, count in sorted(stats['entities'].items()):
                print(f"  - {entity}: {count}")
                total_entities[entity] += count
            
            print(f"\nTag Distribution (top 5):")
            sorted_labels = sorted(stats['labels'].items(), key=lambda x: -x[1])
            for label, count in sorted_labels[:5]:
                print(f"  - {label}: {count}")
            
            if errors:
                print(f"\n[WARN] Validation Errors: {len(errors)}")
                for err in errors[:5]:
                    print(f"  - {err}")
            else:
                print(f"\n[PASS] All BIO tags valid!")
            
            if name == 'Training':
                total_train = stats['sentences']
            elif name == 'Development':
                total_dev = stats['sentences']
            else:
                total_test = stats['sentences']
                
        except Exception as e:
            print(f"[ERROR] {e}")
    
    print("\n" + "="*80)
    print("DATASET SUMMARY")
    print("="*80)
    total = total_train + total_dev + total_test
    print(f"Total Sentences:        {total}")
    print(f"  - Train: {total_train} ({100*total_train/total:.1f}%)")
    print(f"  - Dev:   {total_dev} ({100*total_dev/total:.1f}%)")
    print(f"  - Test:  {total_test} ({100*total_test/total:.1f}%)")
    
    print(f"\nTotal Entities:         {sum(total_entities.values())}")
    for entity, count in sorted(total_entities.items()):
        print(f"  - {entity}: {count}")
    
    print("\n[PASS] Data verification completed!")
    print("="*80)

if __name__ == "__main__":
    main()
