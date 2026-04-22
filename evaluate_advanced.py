#!/usr/bin/env python3
"""
Comprehensive Evaluation Module for Advanced NER
Entity-level metrics, error analysis, and visualization
"""

import numpy as np
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    precision_recall_fscore_support, 
    confusion_matrix, 
    classification_report
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NEREvaluator:
    """Comprehensive NER evaluation with entity-level metrics"""
    
    # Entity types mapping
    ID_TO_LABEL = {
        0: 'O', 1: 'B-ART', 2: 'I-ART', 3: 'B-PER', 4: 'I-PER',
        5: 'B-LOC', 6: 'I-LOC', 7: 'B-MAT', 8: 'I-MAT',
        9: 'B-CON', 10: 'I-CON'
    }
    
    ENTITY_TYPES = {'ART', 'PER', 'LOC', 'MAT', 'CON'}
    
    def __init__(self):
        pass
    
    def extract_entities(self, tags: List[str]) -> List[Tuple[str, int, int]]:
        """
        Extract entities from BIO tags
        Returns: [(entity_type, start_idx, end_idx), ...]
        """
        entities = []
        current_entity = None
        
        for idx, tag in enumerate(tags):
            if tag == 'O':
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
            elif tag.startswith('B-'):
                if current_entity:
                    entities.append(current_entity)
                entity_type = tag.split('-')[1]
                current_entity = (entity_type, idx, idx)
            elif tag.startswith('I-'):
                if current_entity:
                    entity_type = tag.split('-')[1]
                    if current_entity[0] == entity_type:
                        # Continue current entity
                        current_entity = (entity_type, current_entity[1], idx)
                    else:
                        # Different entity type - shouldn't happen with valid BIO
                        entities.append(current_entity)
                        current_entity = (entity_type, idx, idx)
        
        if current_entity:
            entities.append(current_entity)
        
        return entities
    
    def compute_token_level_metrics(self, true_labels: List[str], 
                                   pred_labels: List[str]) -> Dict[str, float]:
        """Compute token-level precision, recall, F1"""
        if len(true_labels) != len(pred_labels):
            raise ValueError("True and predicted labels must have same length")
        
        # Filter out -100 (ignored labels)
        true_filtered = []
        pred_filtered = []
        
        for t, p in zip(true_labels, pred_labels):
            if t != -100:
                true_filtered.append(t if isinstance(t, str) else self.ID_TO_LABEL.get(t, 'O'))
                pred_filtered.append(p if isinstance(p, str) else self.ID_TO_LABEL.get(p, 'O'))
        
        if not true_filtered:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'accuracy': 0.0}
        
        # Convert to integers for sklearn
        label_list = sorted(set(true_filtered + pred_filtered))
        label_to_id = {label: idx for idx, label in enumerate(label_list)}
        
        true_ids = [label_to_id[l] for l in true_filtered]
        pred_ids = [label_to_id[l] for l in pred_filtered]
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_ids, pred_ids, average='weighted', zero_division=0
        )
        
        accuracy = np.mean([t == p for t, p in zip(true_ids, pred_ids)])
        
        return {
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'accuracy': float(accuracy)
        }
    
    def compute_entity_level_metrics(self, true_labels: List[str], 
                                    pred_labels: List[str]) -> Dict[str, float]:
        """Compute entity-level precision, recall, F1"""
        true_entities = self.extract_entities(true_labels)
        pred_entities = self.extract_entities(pred_labels)
        
        # Convert to sets for comparison
        true_set = set(true_entities)
        pred_set = set(pred_entities)
        
        # Calculate metrics
        tp = len(true_set & pred_set)
        fp = len(pred_set - true_set)
        fn = len(true_set - pred_set)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'tp': tp,
            'fp': fp,
            'fn': fn
        }
    
    def compute_per_entity_metrics(self, true_labels: List[str], 
                                  pred_labels: List[str]) -> Dict[str, Dict[str, float]]:
        """Compute metrics per entity type"""
        metrics_per_entity = {}
        
        for entity_type in self.ENTITY_TYPES:
            # Extract entities of this type
            true_ents = [e for e in self.extract_entities(true_labels) if e[0] == entity_type]
            pred_ents = [e for e in self.extract_entities(pred_labels) if e[0] == entity_type]
            
            true_set = set(true_ents)
            pred_set = set(pred_ents)
            
            tp = len(true_set & pred_set)
            fp = len(pred_set - true_set)
            fn = len(true_set - pred_set)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            metrics_per_entity[entity_type] = {
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'tp': tp,
                'fp': fp,
                'fn': fn,
            }
        
        return metrics_per_entity
    
    def analyze_errors(self, true_labels: List[str], 
                      pred_labels: List[str]) -> Dict[str, any]:
        """Analyze prediction errors"""
        errors = {
            'false_positives': defaultdict(int),  # Predicted but not in true
            'false_negatives': defaultdict(int),  # In true but not predicted
            'wrong_boundaries': defaultdict(int),  # Same entity type but wrong span
            'confusion_matrix': defaultdict(lambda: defaultdict(int))
        }
        
        true_entities = self.extract_entities(true_labels)
        pred_entities = self.extract_entities(pred_labels)
        
        true_set = set(true_entities)
        pred_set = set(pred_entities)
        
        # False positives
        for entity in pred_set - true_set:
            errors['false_positives'][entity[0]] += 1
        
        # False negatives
        for entity in true_set - pred_set:
            errors['false_negatives'][entity[0]] += 1
        
        # Confusion matrix for tags
        for t, p in zip(true_labels, pred_labels):
            if t != -100:
                t_label = t if isinstance(t, str) else self.ID_TO_LABEL.get(t, 'O')
                p_label = p if isinstance(p, str) else self.ID_TO_LABEL.get(p, 'O')
                errors['confusion_matrix'][t_label][p_label] += 1
        
        return {
            'false_positives': dict(errors['false_positives']),
            'false_negatives': dict(errors['false_negatives']),
            'confusion_matrix': dict(errors['confusion_matrix'])
        }
    
    def generate_report(self, true_labels: List[str], 
                       pred_labels: List[str]) -> str:
        """Generate comprehensive evaluation report"""
        report = []
        report.append("=" * 70)
        report.append("COMPREHENSIVE NER EVALUATION REPORT")
        report.append("=" * 70)
        
        # Token-level metrics
        token_metrics = self.compute_token_level_metrics(true_labels, pred_labels)
        report.append("\nTOKEN-LEVEL METRICS:")
        report.append(f"  Precision: {token_metrics['precision']:.4f}")
        report.append(f"  Recall:    {token_metrics['recall']:.4f}")
        report.append(f"  F1 Score:  {token_metrics['f1']:.4f}")
        report.append(f"  Accuracy:  {token_metrics['accuracy']:.4f}")
        
        # Entity-level metrics
        entity_metrics = self.compute_entity_level_metrics(true_labels, pred_labels)
        report.append("\nENTITY-LEVEL METRICS:")
        report.append(f"  Precision: {entity_metrics['precision']:.4f}")
        report.append(f"  Recall:    {entity_metrics['recall']:.4f}")
        report.append(f"  F1 Score:  {entity_metrics['f1']:.4f}")
        report.append(f"  TP: {entity_metrics['tp']} | FP: {entity_metrics['fp']} | FN: {entity_metrics['fn']}")
        
        # Per-entity metrics
        per_entity = self.compute_per_entity_metrics(true_labels, pred_labels)
        report.append("\nPER-ENTITY METRICS:")
        report.append(f"{'Entity':<10} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Count':<8}")
        report.append("-" * 54)
        
        for entity_type in sorted(self.ENTITY_TYPES):
            metrics = per_entity[entity_type]
            count = metrics['tp'] + metrics['fn']
            report.append(f"{entity_type:<10} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f} {metrics['f1']:<12.4f} {count:<8}")
        
        # Error analysis
        errors = self.analyze_errors(true_labels, pred_labels)
        report.append("\nERROR ANALYSIS:")
        report.append("\nFalse Positives (by entity type):")
        for entity_type, count in sorted(errors['false_positives'].items()):
            report.append(f"  {entity_type}: {count}")
        
        report.append("\nFalse Negatives (by entity type):")
        for entity_type, count in sorted(errors['false_negatives'].items()):
            report.append(f"  {entity_type}: {count}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def plot_confusion_matrix(self, true_labels: List[str], 
                             pred_labels: List[str], 
                             output_path: str = "confusion_matrix.png") -> None:
        """Plot confusion matrix"""
        errors = self.analyze_errors(true_labels, pred_labels)
        conf_matrix = errors['confusion_matrix']
        
        # Convert to matrix
        all_labels = sorted(set(list(conf_matrix.keys()) + 
                               [k for v in conf_matrix.values() for k in v.keys()]))
        label_to_idx = {label: idx for idx, label in enumerate(all_labels)}
        
        matrix = np.zeros((len(all_labels), len(all_labels)))
        for true_label, pred_counts in conf_matrix.items():
            for pred_label, count in pred_counts.items():
                matrix[label_to_idx[true_label], label_to_idx[pred_label]] = count
        
        # Plot
        plt.figure(figsize=(12, 10))
        sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues',
                   xticklabels=all_labels, yticklabels=all_labels)
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('NER Confusion Matrix')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        logger.info(f"✓ Confusion matrix saved to {output_path}")
        plt.close()
    
    def plot_entity_metrics(self, per_entity_metrics: Dict[str, Dict[str, float]], 
                           output_path: str = "entity_metrics.png") -> None:
        """Plot per-entity metrics"""
        entities = sorted(per_entity_metrics.keys())
        precisions = [per_entity_metrics[e]['precision'] for e in entities]
        recalls = [per_entity_metrics[e]['recall'] for e in entities]
        f1s = [per_entity_metrics[e]['f1'] for e in entities]
        
        x = np.arange(len(entities))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(x - width, precisions, width, label='Precision')
        ax.bar(x, recalls, width, label='Recall')
        ax.bar(x + width, f1s, width, label='F1')
        
        ax.set_xlabel('Entity Type')
        ax.set_ylabel('Score')
        ax.set_title('Per-Entity Performance Metrics')
        ax.set_xticks(x)
        ax.set_xticklabels(entities)
        ax.legend()
        ax.set_ylim([0, 1.0])
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        logger.info(f"✓ Entity metrics plot saved to {output_path}")
        plt.close()


class CrossValidationEvaluator:
    """K-fold cross-validation evaluator"""
    
    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits
        self.evaluator = NEREvaluator()
    
    def evaluate_folds(self, all_true: List[List[str]], 
                      all_pred: List[List[str]]) -> Dict[str, float]:
        """Evaluate across folds"""
        all_results = []
        
        fold_size = len(all_true) // self.n_splits
        
        for fold in range(self.n_splits):
            start_idx = fold * fold_size
            end_idx = start_idx + fold_size if fold < self.n_splits - 1 else len(all_true)
            
            test_true = all_true[start_idx:end_idx]
            test_pred = all_pred[start_idx:end_idx]
            
            # Flatten
            test_true_flat = [label for seq in test_true for label in seq]
            test_pred_flat = [label for seq in test_pred for label in seq]
            
            entity_metrics = self.evaluator.compute_entity_level_metrics(test_true_flat, test_pred_flat)
            all_results.append(entity_metrics)
        
        # Average results
        avg_results = {
            'precision': np.mean([r['precision'] for r in all_results]),
            'recall': np.mean([r['recall'] for r in all_results]),
            'f1': np.mean([r['f1'] for r in all_results]),
            'std_f1': np.std([r['f1'] for r in all_results])
        }
        
        logger.info(f"Cross-validation results ({self.n_splits} folds):")
        logger.info(f"  F1: {avg_results['f1']:.4f} (±{avg_results['std_f1']:.4f})")
        
        return avg_results


def load_conll_data(filepath):
    """Load CoNLL format data"""
    sentences = []
    labels = []
    current_sent = []
    current_labels = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                if current_sent:
                    sentences.append(current_sent)
                    labels.append(current_labels)
                    current_sent = []
                    current_labels = []
            else:
                parts = line.split()
                if len(parts) >= 2:
                    word = parts[0]
                    label = parts[1]
                    current_sent.append(word)
                    current_labels.append(label)
    
    if current_sent:
        sentences.append(current_sent)
        labels.append(current_labels)
    
    return sentences, labels


if __name__ == "__main__":
    import os
    import random
    
    # Load real test data
    test_file = 'data/test.conll'
    
    if not os.path.exists(test_file):
        logger.error(f"Test file {test_file} not found")
        exit(1)
    
    sentences, true_labels_list = load_conll_data(test_file)
    
    logger.info(f"Loaded {len(sentences)} test sentences from {test_file}")
    
    # Simulate model predictions with ~85% accuracy
    # (More realistic than perfect predictions)
    random.seed(42)
    pred_labels_list = []
    
    for labels in true_labels_list:
        pred_labels = []
        for label in labels:
            # 85% chance correct, 15% chance wrong
            if random.random() < 0.85:
                pred_labels.append(label)
            else:
                # Random wrong label
                all_labels = ['O', 'B-ART', 'I-ART', 'B-PER', 'I-PER', 
                             'B-LOC', 'I-LOC', 'B-MAT', 'I-MAT', 'B-CON', 'I-CON']
                pred_labels.append(random.choice(all_labels))
        pred_labels_list.append(pred_labels)
    
    # Flatten for token-level metrics
    true_flat = [label for seq in true_labels_list for label in seq]
    pred_flat = [label for seq in pred_labels_list for label in seq]
    
    evaluator = NEREvaluator()
    print(evaluator.generate_report(true_flat, pred_flat))
