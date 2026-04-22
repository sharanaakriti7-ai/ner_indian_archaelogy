#!/usr/bin/env python3
"""
Comprehensive Evaluation Module for NER
- seqeval metrics (entity-level)
- Error analysis
- Confusion matrix
- Per-entity performance
"""

import torch
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
import json
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from seqeval.metrics import precision_recall_fscore_support, f1_score as seqeval_f1
    from seqeval.scheme import IOB2
    SEQEVAL_AVAILABLE = True
except ImportError:
    SEQEVAL_AVAILABLE = False
    logger.warning("⚠ seqeval not available. Install with: pip install seqeval")


class NEREvaluator:
    """Comprehensive NER Evaluation"""
    
    def __init__(self, id_to_label: Dict[int, str]):
        self.id_to_label = id_to_label
        self.misclassified = []
        self.confusion_matrix = None
    
    def evaluate_predictions(self, predictions: List[List[int]], 
                             labels: List[List[int]],
                             id_to_label: Dict[int, str] = None) -> Dict:
        """
        Evaluate predictions at token level
        
        Args:
            predictions: (batch_size, seq_len) - predicted label ids
            labels: (batch_size, seq_len) - true label ids
            id_to_label: mapping from label id to label string
        """
        if id_to_label is None:
            id_to_label = self.id_to_label
        
        # Convert to sequences of tags
        true_tags = self._convert_ids_to_tags(labels, id_to_label)
        pred_tags = self._convert_ids_to_tags(predictions, id_to_label)
        
        # Entity-level evaluation
        if SEQEVAL_AVAILABLE:
            return self._evaluate_entity_level(true_tags, pred_tags, id_to_label)
        else:
            return self._evaluate_token_level(true_tags, pred_tags)
    
    def _convert_ids_to_tags(self, label_ids: List[List[int]], 
                            id_to_label: Dict[int, str]) -> List[List[str]]:
        """Convert label ids to tag strings"""
        tag_sequences = []
        
        for seq in label_ids:
            tags = []
            for label_id in seq:
                if label_id == -100:
                    continue  # Skip padding
                tag = id_to_label.get(label_id, 'O')
                tags.append(tag)
            tag_sequences.append(tags)
        
        return tag_sequences
    
    def _evaluate_entity_level(self, true_tags: List[List[str]], 
                              pred_tags: List[List[str]],
                              id_to_label: Dict[int, str]) -> Dict:
        """Entity-level evaluation using seqeval"""
        
        # Compute metrics
        precision, recall, f1, support = precision_recall_fscore_support(
            true_tags, pred_tags, scheme=IOB2, average='weighted', zero_division=0
        )
        
        # Per-entity metrics
        per_entity = self._compute_per_entity_metrics(true_tags, pred_tags)
        
        # Compute confusion matrix
        self.confusion_matrix = self._compute_confusion_matrix(true_tags, pred_tags)
        
        # Find misclassifications
        self.misclassified = self._find_misclassifications(true_tags, pred_tags)
        
        return {
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'support': int(support),
            'per_entity': per_entity,
            'confusion_matrix': self.confusion_matrix
        }
    
    def _evaluate_token_level(self, true_tags: List[List[str]], 
                             pred_tags: List[List[str]]) -> Dict:
        """Token-level evaluation (fallback without seqeval)"""
        
        correct = 0
        total = 0
        
        for true_seq, pred_seq in zip(true_tags, pred_tags):
            for true_tag, pred_tag in zip(true_seq, pred_seq):
                if true_tag == pred_tag:
                    correct += 1
                total += 1
        
        accuracy = correct / total if total > 0 else 0
        
        return {
            'accuracy': float(accuracy),
            'correct': correct,
            'total': total
        }
    
    def _compute_per_entity_metrics(self, true_tags: List[List[str]], 
                                   pred_tags: List[List[str]]) -> Dict:
        """Compute metrics for each entity type"""
        
        # Extract entities from sequences
        true_entities = self._extract_entities(true_tags)
        pred_entities = self._extract_entities(pred_tags)
        
        per_entity = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
        
        # Count true positives, false positives, false negatives
        pred_set = set(pred_entities)
        true_set = set(true_entities)
        
        for entity in true_set:
            entity_type = entity[1]
            if entity in pred_set:
                per_entity[entity_type]['tp'] += 1
            else:
                per_entity[entity_type]['fn'] += 1
        
        for entity in pred_set:
            entity_type = entity[1]
            if entity not in true_set:
                per_entity[entity_type]['fp'] += 1
        
        # Calculate metrics
        results = {}
        for entity_type, counts in per_entity.items():
            tp, fp, fn = counts['tp'], counts['fp'], counts['fn']
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            results[entity_type] = {
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'support': tp + fn
            }
        
        return results
    
    def _extract_entities(self, tag_sequences: List[List[str]]) -> List[Tuple]:
        """Extract entities from BIO tag sequences"""
        entities = []
        
        for seq_idx, tags in enumerate(tag_sequences):
            current_entity = None
            current_type = None
            
            for token_idx, tag in enumerate(tags):
                if tag == 'O':
                    if current_entity is not None:
                        entities.append((seq_idx, current_type, current_entity))
                        current_entity = None
                        current_type = None
                elif tag.startswith('B-'):
                    if current_entity is not None:
                        entities.append((seq_idx, current_type, current_entity))
                    current_type = tag[2:]
                    current_entity = [(token_idx, tag)]
                elif tag.startswith('I-'):
                    entity_type = tag[2:]
                    if current_type == entity_type:
                        current_entity.append((token_idx, tag))
                    else:
                        if current_entity is not None:
                            entities.append((seq_idx, current_type, current_entity))
                        current_type = entity_type
                        current_entity = [(token_idx, tag)]
            
            if current_entity is not None:
                entities.append((seq_idx, current_type, current_entity))
        
        return entities
    
    def _compute_confusion_matrix(self, true_tags: List[List[str]], 
                                 pred_tags: List[List[str]]) -> np.ndarray:
        """Compute confusion matrix"""
        
        # Get unique labels
        all_labels = set()
        for seq in true_tags + pred_tags:
            all_labels.update(seq)
        all_labels = sorted(list(all_labels))
        label_to_idx = {label: idx for idx, label in enumerate(all_labels)}
        
        # Initialize confusion matrix
        n_labels = len(all_labels)
        conf_matrix = np.zeros((n_labels, n_labels), dtype=np.int64)
        
        # Fill matrix
        for true_seq, pred_seq in zip(true_tags, pred_tags):
            for true_tag, pred_tag in zip(true_seq, pred_seq):
                true_idx = label_to_idx[true_tag]
                pred_idx = label_to_idx[pred_tag]
                conf_matrix[true_idx, pred_idx] += 1
        
        return conf_matrix.tolist()
    
    def _find_misclassifications(self, true_tags: List[List[str]], 
                                pred_tags: List[List[str]],
                                max_samples: int = 50) -> List[Dict]:
        """Find and collect misclassified examples"""
        
        misclassified = []
        
        for seq_idx, (true_seq, pred_seq) in enumerate(zip(true_tags, pred_tags)):
            for token_idx, (true_tag, pred_tag) in enumerate(zip(true_seq, pred_seq)):
                if true_tag != pred_tag:
                    misclassified.append({
                        'sentence_id': seq_idx,
                        'token_id': token_idx,
                        'true_tag': true_tag,
                        'pred_tag': pred_tag
                    })
                    
                    if len(misclassified) >= max_samples:
                        break
            
            if len(misclassified) >= max_samples:
                break
        
        return misclassified
    
    def print_error_analysis(self, max_samples: int = 20) -> None:
        """Print error analysis"""
        
        if not self.misclassified:
            logger.info("✓ No misclassifications found!")
            return
        
        logger.info("\n" + "="*80)
        logger.info("ERROR ANALYSIS - Common Confusions")
        logger.info("="*80)
        
        # Group by confusion type
        confusions = defaultdict(int)
        for item in self.misclassified:
            confusion = f"{item['true_tag']} → {item['pred_tag']}"
            confusions[confusion] += 1
        
        # Sort by frequency
        sorted_confusions = sorted(confusions.items(), key=lambda x: x[1], reverse=True)
        
        logger.info("\nTop Confusions:")
        for confusion, count in sorted_confusions[:10]:
            logger.info(f"  {confusion}: {count} times")
        
        # Entity-level confusion analysis
        logger.info("\nEntity-Level Confusions:")
        entity_confusions = defaultdict(lambda: defaultdict(int))
        
        for item in self.misclassified:
            true_entity = item['true_tag'].split('-')[1] if '-' in item['true_tag'] else 'O'
            pred_entity = item['pred_tag'].split('-')[1] if '-' in item['pred_tag'] else 'O'
            
            if true_entity != pred_entity:
                entity_confusions[true_entity][pred_entity] += 1
        
        for true_entity in sorted(entity_confusions.keys()):
            confusions_dict = entity_confusions[true_entity]
            total = sum(confusions_dict.values())
            logger.info(f"  {true_entity}:")
            for pred_entity in sorted(confusions_dict.keys(), 
                                     key=lambda x: confusions_dict[x], 
                                     reverse=True):
                count = confusions_dict[pred_entity]
                pct = 100 * count / total
                logger.info(f"    → {pred_entity}: {count} ({pct:.1f}%)")
    
    def print_summary(self, metrics: Dict) -> None:
        """Print evaluation summary"""
        
        logger.info("\n" + "="*80)
        logger.info("EVALUATION SUMMARY")
        logger.info("="*80)
        
        logger.info(f"\nOverall Metrics:")
        logger.info(f"  Precision: {metrics.get('precision', 0):.4f}")
        logger.info(f"  Recall:    {metrics.get('recall', 0):.4f}")
        logger.info(f"  F1 Score:  {metrics.get('f1', 0):.4f}")
        
        if 'per_entity' in metrics:
            logger.info(f"\nPer-Entity Metrics:")
            for entity_type in sorted(metrics['per_entity'].keys()):
                entity_metrics = metrics['per_entity'][entity_type]
                logger.info(f"  {entity_type}:")
                logger.info(f"    Precision: {entity_metrics['precision']:.4f}")
                logger.info(f"    Recall:    {entity_metrics['recall']:.4f}")
                logger.info(f"    F1:        {entity_metrics['f1']:.4f}")
                logger.info(f"    Support:   {entity_metrics['support']}")


def print_predictions_sample(predictions: List[Tuple[str, str, str]], 
                            max_samples: int = 10) -> None:
    """Print sample predictions"""
    
    logger.info("\n" + "="*80)
    logger.info("SAMPLE PREDICTIONS")
    logger.info("="*80)
    
    for idx, (token, true_tag, pred_tag) in enumerate(predictions[:max_samples]):
        status = "✓" if true_tag == pred_tag else "✗"
        logger.info(f"\n{status} Token: {token}")
        logger.info(f"  True: {true_tag}")
        logger.info(f"  Pred: {pred_tag}")
