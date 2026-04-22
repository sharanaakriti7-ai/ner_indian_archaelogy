"""
Evaluation and Error Analysis for NER Models
Includes entity-level metrics, confusion analysis, and visualization
"""

import os
import logging
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from collections import defaultdict, Counter
import config
from src.data_utils import CoNLLDataset, NERDataset
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NEREvaluator:
    """Comprehensive evaluation and error analysis for NER"""
    
    def __init__(self, model_path: str, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        self.model_path = model_path
        self.device = device
        
        logger.info(f"Loading model from {model_path}...")
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model.to(device)
        self.model.eval()
        
        logger.info("Model loaded successfully")
    
    def evaluate_on_file(self, test_file: str, batch_size: int = config.BATCH_SIZE):
        """
        Evaluate model on CoNLL test file
        """
        # Load data
        data = CoNLLDataset(test_file)
        dataset = NERDataset(data.sentences, data.labels, self.tokenizer, config.LABEL_TO_ID)
        loader = DataLoader(dataset, batch_size=batch_size)
        
        all_pred_labels = []
        all_true_labels = []
        
        with torch.no_grad():
            for batch in loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                logits = outputs.logits
                preds = torch.argmax(logits, dim=2)
                
                all_pred_labels.extend(preds.cpu().numpy())
                all_true_labels.extend(labels.cpu().numpy())
        
        return all_true_labels, all_pred_labels, data
    
    def calculate_token_level_metrics(self, true_labels, pred_labels):
        """
        Calculate token-level precision, recall, F1
        """
        true_flat = []
        pred_flat = []
        
        for true_seq, pred_seq in zip(true_labels, pred_labels):
            for true_label, pred_label in zip(true_seq, pred_seq):
                if true_label != -100:
                    true_flat.append(true_label)
                    pred_flat.append(pred_label)
        
        true_flat = np.array(true_flat)
        pred_flat = np.array(pred_flat)
        
        # Overall metrics
        precision = precision_score(true_flat, pred_flat, average='weighted', zero_division=0)
        recall = recall_score(true_flat, pred_flat, average='weighted', zero_division=0)
        f1 = f1_score(true_flat, pred_flat, average='weighted', zero_division=0)
        
        # Macro metrics
        precision_macro = precision_score(true_flat, pred_flat, average='macro', zero_division=0)
        recall_macro = recall_score(true_flat, pred_flat, average='macro', zero_division=0)
        f1_macro = f1_score(true_flat, pred_flat, average='macro', zero_division=0)
        
        # Per-class metrics
        precision_per_class = precision_score(true_flat, pred_flat, average=None, zero_division=0)
        recall_per_class = recall_score(true_flat, pred_flat, average=None, zero_division=0)
        f1_per_class = f1_score(true_flat, pred_flat, average=None, zero_division=0)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'precision_macro': precision_macro,
            'recall_macro': recall_macro,
            'f1_macro': f1_macro,
            'precision_per_class': precision_per_class,
            'recall_per_class': recall_per_class,
            'f1_per_class': f1_per_class,
            'true_flat': true_flat,
            'pred_flat': pred_flat,
        }
    
    def calculate_entity_level_metrics(self, sentences, true_labels, pred_labels):
        """
        Calculate entity-level precision, recall, F1
        Extract entities from BIO tags and compare
        """
        
        def extract_entities(sentence, labels):
            """Extract entities from BIO tags"""
            entities = []
            current_entity = []
            current_label = None
            current_start = 0
            
            for idx, (token, label_id) in enumerate(zip(sentence, labels)):
                if label_id == -100:
                    continue
                
                label = config.ID_TO_LABEL[label_id]
                
                if label.startswith('B-'):
                    if current_entity:
                        entities.append({
                            'type': current_label,
                            'tokens': current_entity,
                            'start': current_start
                        })
                    current_entity = [token]
                    current_label = label[2:]
                    current_start = idx
                elif label.startswith('I-') and current_label:
                    current_entity.append(token)
                else:
                    if current_entity:
                        entities.append({
                            'type': current_label,
                            'tokens': current_entity,
                            'start': current_start
                        })
                        current_entity = []
                        current_label = None
            
            if current_entity:
                entities.append({
                    'type': current_label,
                    'tokens': current_entity,
                    'start': current_start
                })
            
            return entities
        
        # Extract entities
        true_entities = []
        pred_entities = []
        
        for sent_idx, (sentence, true_labels_seq, pred_labels_seq) in enumerate(
            zip(sentences, true_labels, pred_labels)
        ):
            true_ents = extract_entities(sentence, true_labels_seq)
            pred_ents = extract_entities(sentence, pred_labels_seq)
            
            true_entities.extend([(sent_idx, e) for e in true_ents])
            pred_entities.extend([(sent_idx, e) for e in pred_ents])
        
        # Calculate metrics
        tp = 0  # True positives
        fp = 0  # False positives
        fn = 0  # False negatives
        
        for pred_sent_idx, pred_ent in pred_entities:
            found = False
            for true_sent_idx, true_ent in true_entities:
                if (pred_sent_idx == true_sent_idx and
                    pred_ent['type'] == true_ent['type'] and
                    pred_ent['start'] == true_ent['start'] and
                    ''.join(pred_ent['tokens']) == ''.join(true_ent['tokens'])):
                    tp += 1
                    found = True
                    break
            if not found:
                fp += 1
        
        fn = len(true_entities) - tp
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'total_true': len(true_entities),
            'total_pred': len(pred_entities)
        }
    
    def error_analysis(self, true_labels, pred_labels):
        """
        Analyze common error types
        """
        errors = {
            'B_vs_I': 0,  # B-tag vs I-tag confusion
            'entity_type_confusion': defaultdict(lambda: defaultdict(int)),  # ART vs MAT, etc.
            'false_positives': [],  # Predicted entity not in true
            'false_negatives': [],  # True entity not predicted
            'correct': 0
        }
        
        for true_seq, pred_seq in zip(true_labels, pred_labels):
            for true_label_id, pred_label_id in zip(true_seq, pred_seq):
                if true_label_id == -100:
                    continue
                
                true_label = config.ID_TO_LABEL[true_label_id]
                pred_label = config.ID_TO_LABEL[pred_label_id]
                
                if true_label == pred_label:
                    errors['correct'] += 1
                elif true_label.startswith('B-') and pred_label.startswith('I-'):
                    errors['B_vs_I'] += 1
                elif true_label != 'O' and pred_label != 'O':
                    true_type = true_label.split('-')[1]
                    pred_type = pred_label.split('-')[1]
                    errors['entity_type_confusion'][true_type][pred_type] += 1
                elif pred_label != 'O':
                    errors['false_positives'].append((true_label, pred_label))
                else:
                    errors['false_negatives'].append((true_label, pred_label))
        
        return errors
    
    def print_evaluation_report(self, test_file: str, output_file: str = None):
        """
        Generate comprehensive evaluation report
        """
        logger.info("Starting evaluation...")
        
        # Evaluate
        true_labels, pred_labels, data = self.evaluate_on_file(test_file)
        
        # Token-level metrics
        token_metrics = self.calculate_token_level_metrics(true_labels, pred_labels)
        
        # Entity-level metrics
        entity_metrics = self.calculate_entity_level_metrics(
            data.sentences, true_labels, pred_labels
        )
        
        # Error analysis
        errors = self.error_analysis(true_labels, pred_labels)
        
        # Print report
        report = []
        report.append("=" * 60)
        report.append("NER EVALUATION REPORT")
        report.append("=" * 60)
        
        report.append("\n### TOKEN-LEVEL METRICS ###")
        report.append(f"Precision (Weighted): {token_metrics['precision']:.4f}")
        report.append(f"Recall (Weighted):    {token_metrics['recall']:.4f}")
        report.append(f"F1-Score (Weighted):  {token_metrics['f1']:.4f}")
        report.append(f"\nPrecision (Macro):    {token_metrics['precision_macro']:.4f}")
        report.append(f"Recall (Macro):       {token_metrics['recall_macro']:.4f}")
        report.append(f"F1-Score (Macro):     {token_metrics['f1_macro']:.4f}")
        
        report.append("\n### ENTITY-LEVEL METRICS ###")
        report.append(f"True Positives:   {entity_metrics['tp']}")
        report.append(f"False Positives:  {entity_metrics['fp']}")
        report.append(f"False Negatives:  {entity_metrics['fn']}")
        report.append(f"Total True:       {entity_metrics['total_true']}")
        report.append(f"Total Predicted:  {entity_metrics['total_pred']}")
        report.append(f"\nPrecision: {entity_metrics['precision']:.4f}")
        report.append(f"Recall:    {entity_metrics['recall']:.4f}")
        report.append(f"F1-Score:  {entity_metrics['f1']:.4f}")
        
        report.append("\n### PER-CLASS METRICS ###")
        for label_id, label in config.ID_TO_LABEL.items():
            if label != 'O':
                report.append(
                    f"{label:10s}: P={token_metrics['precision_per_class'][label_id]:.4f} "
                    f"R={token_metrics['recall_per_class'][label_id]:.4f} "
                    f"F1={token_metrics['f1_per_class'][label_id]:.4f}"
                )
        
        report.append("\n### ERROR ANALYSIS ###")
        report.append(f"Correct Predictions: {errors['correct']}")
        report.append(f"B vs I Confusion:    {errors['B_vs_I']}")
        report.append(f"False Positives:     {len(errors['false_positives'])}")
        report.append(f"False Negatives:     {len(errors['false_negatives'])}")
        
        report.append("\n### ENTITY TYPE CONFUSION ###")
        for true_type, confusion in errors['entity_type_confusion'].items():
            for pred_type, count in confusion.items():
                report.append(f"  {true_type} -> {pred_type}: {count} times")
        
        report.append("\n" + "=" * 60)
        
        report_text = "\n".join(report)
        logger.info(report_text)
        
        # Save to file if specified
        if output_file:
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
        
        return {
            'token_metrics': token_metrics,
            'entity_metrics': entity_metrics,
            'errors': errors
        }
    
    def visualize_confusion_matrix(self, test_file: str, output_dir: str = 'outputs'):
        """
        Generate confusion matrix visualization
        """
        true_labels, pred_labels, _ = self.evaluate_on_file(test_file)
        token_metrics = self.calculate_token_level_metrics(true_labels, pred_labels)
        
        # Get confusion matrix
        cm = confusion_matrix(token_metrics['true_flat'], token_metrics['pred_flat'])
        
        # Plot
        plt.figure(figsize=(14, 12))
        labels = [config.ID_TO_LABEL[i] for i in range(config.NUM_LABELS)]
        sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels)
        plt.title('Token Classification Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'confusion_matrix.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Confusion matrix saved to {output_path}")
        
        return cm


def evaluate_model(model_path: str, test_file: str, output_dir: str = 'outputs'):
    """
    Main evaluation function
    """
    evaluator = NEREvaluator(model_path)
    
    # Print report
    results = evaluator.print_evaluation_report(
        test_file,
        output_file=os.path.join(output_dir, 'evaluation_report.txt')
    )
    
    # Visualize confusion matrix
    evaluator.visualize_confusion_matrix(test_file, output_dir)
    
    logger.info("Evaluation completed!")
    return results


if __name__ == "__main__":
    evaluate_model(
        os.path.join(config.MODEL_DIR, "best_model"),
        config.TEST_FILE,
        config.OUTPUT_DIR
    )
