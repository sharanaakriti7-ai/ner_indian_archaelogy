#!/usr/bin/env python3
"""
Data Augmentation Module for Indian Archaeology NER
Implements multiple augmentation techniques for low-resource scenario
"""

import random
from typing import List, Tuple, Dict
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAugmenter:
    """Augment NER data with multiple techniques"""
    
    # Domain-specific synonym mappings
    SYNONYMS = {
        "pottery": ["vessel", "ceramic", "pot", "urn"],
        "artifact": ["object", "item", "relic"],
        "excavation": ["dig", "digging", "unearthing"],
        "bronze": ["copper-tin alloy", "bronze material"],
        "clay": ["mud", "soil"],
        "sculpture": ["statue", "carving"],
        "stone": ["rock", "limestone"],
        "site": ["location", "place"],
        "building": ["structure", "dwelling"],
    }
    
    # Entity type swaps for augmentation
    ENTITY_SWAPS = {
        "B-LOC": ["Harappa", "Mohenjo-daro", "Dholavira", "Lothal", "Kalibangan"],
        "B-PER": ["Mauryan", "Gupta", "Vedic", "Ancient Indian", "Paleolithic"],
        "B-ART": ["pottery", "sculpture", "seal", "figurine", "idol"],
        "B-MAT": ["stone", "clay", "bronze", "copper", "gold"],
    }
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.seed = seed
    
    def synonym_replacement(self, sentence: List[Tuple[str, str]], 
                           num_replacements: int = 2) -> List[Tuple[str, str]]:
        """Replace common words with synonyms"""
        augmented = sentence.copy()
        
        for _ in range(num_replacements):
            idx = random.randint(0, len(augmented) - 1)
            word, tag = augmented[idx]
            
            if tag == 'O' and word.lower() in self.SYNONYMS:
                synonym = random.choice(self.SYNONYMS[word.lower()])
                augmented[idx] = (synonym, tag)
        
        return augmented
    
    def entity_swap(self, sentence: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Swap entity mentions with similar entity types"""
        augmented = sentence.copy()
        
        # Find all entities
        entity_positions = defaultdict(list)
        i = 0
        while i < len(augmented):
            word, tag = augmented[i]
            if tag.startswith('B-'):
                entity_type = tag
                start = i
                i += 1
                # Collect continuation tags
                while i < len(augmented) and augmented[i][1].startswith('I-'):
                    i += 1
                entity_positions[entity_type].append((start, i))
            else:
                i += 1
        
        # Swap entities of same type
        for entity_type, positions in entity_positions.items():
            if len(positions) >= 2:
                idx1, idx2 = random.sample(positions, 2)
                start1, end1 = idx1
                start2, end2 = idx2
                
                # Extract entity values
                entity1 = [w for w, t in augmented[start1:end1]]
                entity2 = [w for w, t in augmented[start2:end2]]
                
                # Create tags
                if len(entity1) > 0 and len(entity2) > 0:
                    tags1 = [entity_type] + [entity_type.replace('B-', 'I-')] * (len(entity1) - 1)
                    tags2 = [entity_type] + [entity_type.replace('B-', 'I-')] * (len(entity2) - 1)
                    
                    # Swap
                    for i, (word, _) in enumerate(zip(entity1, tags2)):
                        augmented[start2 + i] = (word, tags2[i])
                    
                    for i, (word, _) in enumerate(zip(entity2, tags1)):
                        augmented[start1 + i] = (word, tags1[i])
        
        return augmented
    
    def random_insertion(self, sentence: List[Tuple[str, str]], 
                        num_insertions: int = 1) -> List[Tuple[str, str]]:
        """Insert random neutral tokens"""
        augmented = sentence.copy()
        neutral_words = ["है", "में", "के", "की", "का", "एक", "यह", "वह"]
        
        for _ in range(num_insertions):
            idx = random.randint(0, len(augmented))
            word = random.choice(neutral_words)
            augmented.insert(idx, (word, 'O'))
        
        return augmented
    
    def random_deletion(self, sentence: List[Tuple[str, str]], 
                       p: float = 0.1) -> List[Tuple[str, str]]:
        """Randomly delete neutral tokens"""
        if len(sentence) == 1:
            return sentence
        
        augmented = []
        for word, tag in sentence:
            if tag == 'O' and random.random() > (1 - p):
                continue  # Delete
            augmented.append((word, tag))
        
        return augmented if augmented else sentence
    
    def back_translation_simulation(self, sentence: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Simulate back-translation by modifying word order slightly"""
        augmented = sentence.copy()
        
        # Only swap adjacent neutral tokens
        for i in range(len(augmented) - 1):
            if augmented[i][1] == 'O' and augmented[i + 1][1] == 'O':
                if random.random() < 0.3:  # 30% chance
                    augmented[i], augmented[i + 1] = augmented[i + 1], augmented[i]
        
        return augmented
    
    def context_injection(self, sentence: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Add contextual information from archaeology domain"""
        augmented = sentence.copy()
        
        context_phrases = [
            [("की", "O"), ("खोज", "B-CON")],
            [("में", "O"), ("मिली", "O")],
            [("से", "O"), ("बना", "O"), ("है", "O")],
            [("का", "O"), ("उपयोग", "O")],
        ]
        
        # Add context at random position
        if len(augmented) > 2 and random.random() < 0.5:
            idx = random.randint(1, len(augmented) - 1)
            context = random.choice(context_phrases)
            augmented = augmented[:idx] + context + augmented[idx:]
        
        return augmented
    
    def mixup_augmentation(self, sentence1: List[Tuple[str, str]], 
                          sentence2: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Mix two sentences to create new training example"""
        if len(sentence1) < 3 or len(sentence2) < 3:
            return sentence1
        
        # Take first half of sentence1, second half of sentence2
        split1 = len(sentence1) // 2
        split2 = len(sentence2) // 2
        
        augmented = sentence1[:split1] + sentence2[split2:]
        return augmented
    
    def apply_augmentation(self, sentences: List[List[Tuple[str, str]]], 
                          augmentation_factor: int = 3) -> List[List[Tuple[str, str]]]:
        """Apply multiple augmentations to dataset"""
        augmented_dataset = sentences.copy()
        
        for sentence in sentences:
            for _ in range(augmentation_factor):
                # Choose random augmentation
                aug_type = random.choice([
                    'synonym',
                    'entity_swap',
                    'insertion',
                    'deletion',
                    'back_trans',
                    'context'
                ])
                
                if aug_type == 'synonym':
                    aug_sent = self.synonym_replacement(sentence)
                elif aug_type == 'entity_swap':
                    aug_sent = self.entity_swap(sentence)
                elif aug_type == 'insertion':
                    aug_sent = self.random_insertion(sentence)
                elif aug_type == 'deletion':
                    aug_sent = self.random_deletion(sentence)
                elif aug_type == 'back_trans':
                    aug_sent = self.back_translation_simulation(sentence)
                else:  # context
                    aug_sent = self.context_injection(sentence)
                
                augmented_dataset.append(aug_sent)
        
        logger.info(f"✓ Augmented {len(sentences)} → {len(augmented_dataset)} sentences")
        return augmented_dataset
    
    def oversample_minority_classes(self, sentences: List[List[Tuple[str, str]]], 
                                    target_per_class: int = 100) -> List[List[Tuple[str, str]]]:
        """Oversample sentences containing minority entity types"""
        
        # Count entity types per sentence
        entity_counts = defaultdict(list)
        
        for idx, sentence in enumerate(sentences):
            for word, tag in sentence:
                if tag.startswith('B-'):
                    entity_type = tag.split('-')[1]
                    entity_counts[entity_type].append(idx)
        
        augmented_sentences = sentences.copy()
        
        # Oversample minority classes
        for entity_type, indices in entity_counts.items():
            if len(indices) < target_per_class:
                needed = target_per_class - len(indices)
                for _ in range(needed):
                    idx = random.choice(indices)
                    aug_sent = self.apply_random_augmentation(sentences[idx])
                    augmented_sentences.append(aug_sent)
        
        logger.info(f"✓ Oversampled dataset: {len(sentences)} → {len(augmented_sentences)}")
        return augmented_sentences
    
    def apply_random_augmentation(self, sentence: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Apply single random augmentation"""
        aug_type = random.choice(['synonym', 'insertion', 'deletion', 'back_trans'])
        
        if aug_type == 'synonym':
            return self.synonym_replacement(sentence)
        elif aug_type == 'insertion':
            return self.random_insertion(sentence)
        elif aug_type == 'deletion':
            return self.random_deletion(sentence)
        else:
            return self.back_translation_simulation(sentence)


def parse_conll_file(filepath: str) -> List[List[Tuple[str, str]]]:
    """Parse CoNLL format file"""
    sentences = []
    current_sentence = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if not line or line.startswith('#'):
                if current_sentence:
                    sentences.append(current_sentence)
                    current_sentence = []
            else:
                if '\t' in line:
                    parts = line.split('\t')
                elif ' ' in line:
                    parts = line.rsplit(' ', 1)
                else:
                    continue
                
                if len(parts) >= 2:
                    word = parts[0].strip()
                    tag = parts[1].strip()
                    if word and tag:
                        current_sentence.append((word, tag))
    
    if current_sentence:
        sentences.append(current_sentence)
    
    return sentences


def save_augmented_data(sentences: List[List[Tuple[str, str]]], output_file: str) -> None:
    """Save augmented data in CoNLL format"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Augmented Indian Archaeology Dataset\n")
        f.write("# Hindi-English Code-Mixed with BIO Tags\n\n")
        
        for idx, sentence in enumerate(sentences, 1):
            f.write(f"# Sentence {idx}\n")
            for word, tag in sentence:
                f.write(f"{word}\t{tag}\n")
            f.write("\n")


if __name__ == "__main__":
    # Example usage
    logger.info("Loading original data...")
    sentences = parse_conll_file('data/train.conll')
    logger.info(f"✓ Loaded {len(sentences)} sentences")
    
    # Initialize augmenter
    augmenter = DataAugmenter(seed=42)
    
    # Apply augmentation
    logger.info("\nApplying augmentation (3x per sentence)...")
    augmented = augmenter.apply_augmentation(sentences, augmentation_factor=3)
    
    # Oversample minority classes
    logger.info("\nOversampling minority classes...")
    final_data = augmenter.oversample_minority_classes(augmented, target_per_class=50)
    
    # Save
    logger.info(f"\nSaving {len(final_data)} augmented sentences...")
    save_augmented_data(final_data, 'data/train_augmented.conll')
    
    logger.info("✓ Augmentation complete!")
