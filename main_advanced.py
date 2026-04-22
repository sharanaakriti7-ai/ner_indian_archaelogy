#!/usr/bin/env python3
"""
Advanced NER Pipeline Orchestration
Combines data augmentation, CRF, gazetteers, and comprehensive evaluation
Target: F1 > 0.60
"""

import os
import torch
import logging
from typing import List, Tuple
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

from augmentation import DataAugmenter, parse_conll_file, save_augmented_data
from gazetteer import ArchaeologyGazetteer, WeakSupervisionGenerator
from train_advanced import create_advanced_pipeline, NERDataset
from evaluate_advanced import NEREvaluator
from config import *
from transformers import AutoTokenizer


def load_conll_data(filepath: str) -> Tuple[List[List[str]], List[List[str]]]:
    """Load data from CoNLL file"""
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
                        current_sent.append(word)
                        current_labels.append(tag)
    
    if current_sent:
        sentences.append(current_sent)
        labels.append(current_labels)
    
    return sentences, labels


def step1_data_expansion():
    """Step 1: Expand dataset from 60 to 1000+ sentences"""
    logger.info("\n" + "="*70)
    logger.info("STEP 1: DATA EXPANSION")
    logger.info("="*70)
    
    from expand_dataset import expand_dataset
    
    if not os.path.exists('data/train_expanded.conll'):
        expand_dataset('data/train_expanded.conll', target_sentences=500)
    else:
        logger.info("✓ Expanded dataset already exists")
    
    # Count
    with open('data/train_expanded.conll') as f:
        num_sentences = len([l for l in f if l.startswith('# Sentence')])
    
    logger.info(f"✓ Total sentences: {num_sentences}")


def step2_data_augmentation():
    """Step 2: Augment data (3x per sentence)"""
    logger.info("\n" + "="*70)
    logger.info("STEP 2: DATA AUGMENTATION")
    logger.info("="*70)
    
    if not os.path.exists('data/train_augmented.conll'):
        # Load original data
        sentences = parse_conll_file('data/train.conll')
        logger.info(f"Loaded {len(sentences)} original sentences")
        
        # Initialize augmenter
        augmenter = DataAugmenter(seed=42)
        
        # Apply augmentation (3x)
        augmented = augmenter.apply_augmentation(sentences, augmentation_factor=3)
        
        # Oversample minority classes
        final_data = augmenter.oversample_minority_classes(augmented, target_per_class=50)
        
        # Save
        save_augmented_data(final_data, 'data/train_augmented.conll')
    else:
        logger.info("✓ Augmented dataset already exists")


def step3_weak_labels():
    """Step 3: Generate weak labels using gazetteer"""
    logger.info("\n" + "="*70)
    logger.info("STEP 3: WEAK LABEL GENERATION (GAZETTEER)")
    logger.info("="*70)
    
    gazetteer = ArchaeologyGazetteer()
    weak_gen = WeakSupervisionGenerator(gazetteer)
    
    # Load unlabeled sentences (pretrain corpus)
    with open('data/pretrain_corpus.txt') as f:
        unlabeled = [line.strip().split() for line in f if line.strip()]
    
    logger.info(f"Generating weak labels for {len(unlabeled)} unlabeled sentences...")
    weak_labels = weak_gen.generate_weak_labels(unlabeled)
    
    # Save weak-labeled data
    os.makedirs('data', exist_ok=True)
    with open('data/weak_labeled.conll', 'w') as f:
        f.write("# Weak-labeled sentences from gazetteer\n\n")
        for idx, (sent, labels) in enumerate(zip(unlabeled, weak_labels), 1):
            f.write(f"# Sentence {idx}\n")
            for word, label in zip(sent, labels):
                f.write(f"{word}\t{label}\n")
            f.write("\n")
    
    logger.info(f"✓ Weak-labeled data saved to data/weak_labeled.conll")


def step4_advanced_training():
    """Step 4: Advanced training with CRF + Focal Loss + Gazetteer"""
    logger.info("\n" + "="*70)
    logger.info("STEP 4: ADVANCED TRAINING (CRF + FOCAL LOSS + GAZETTEER)")
    logger.info("="*70)
    
    # Load augmented training data
    train_sentences, train_labels = load_conll_data('data/train_augmented.conll')
    dev_sentences, dev_labels = load_conll_data('data/dev.conll')
    test_sentences, test_labels = load_conll_data('data/test.conll')
    
    logger.info(f"Train: {len(train_sentences)} sentences")
    logger.info(f"Dev: {len(dev_sentences)} sentences")
    logger.info(f"Test: {len(test_sentences)} sentences")
    
    # Run training
    results = create_advanced_pipeline(
        train_sentences=train_sentences,
        train_labels=train_labels,
        dev_sentences=dev_sentences,
        dev_labels=dev_labels,
        test_sentences=test_sentences,
        test_labels=test_labels,
        model_name="bert-base-multilingual-cased",
        batch_size=16,
        epochs=20,
        learning_rate=2e-5
    )
    
    return results


def step5_evaluation():
    """Step 5: Comprehensive evaluation"""
    logger.info("\n" + "="*70)
    logger.info("STEP 5: COMPREHENSIVE EVALUATION")
    logger.info("="*70)
    
    # Load best model and test data
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    from model_crf import TransformerCRFModel
    from train_advanced import AdvancedTrainer
    
    model = TransformerCRFModel(
        model_name="bert-base-multilingual-cased",
        num_labels=NUM_LABELS,
        dropout=0.1
    ).to(device)
    
    # Load best model weights
    model_path = "outputs/advanced_model/best_model/pytorch_model.bin"
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        logger.info("✓ Best model loaded")
    
    # Load test data
    test_sentences, test_labels = load_conll_data('data/test.conll')
    
    # Create dataset
    tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
    test_dataset = NERDataset(test_sentences, test_labels, tokenizer)
    
    from torch.utils.data import DataLoader
    test_loader = DataLoader(test_dataset, batch_size=16)
    
    # Evaluate
    evaluator = NEREvaluator()
    
    all_pred = []
    all_true = []
    
    model.eval()
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels']
            
            _, predictions = model(input_ids, attention_mask)
            all_pred.extend(predictions)
            all_true.extend(labels.numpy())
    
    # Flatten
    all_pred_flat = [label for seq in all_pred for label in seq]
    all_true_flat = [label for seq in all_true for label in seq]
    
    # Generate report
    report = evaluator.generate_report(all_true_flat, all_pred_flat)
    print("\n" + report)
    
    # Save report
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/evaluation_report.txt', 'w') as f:
        f.write(report)
    
    logger.info("✓ Evaluation report saved to outputs/evaluation_report.txt")
    
    # Plot confusion matrix
    evaluator.plot_confusion_matrix(all_true_flat, all_pred_flat, 
                                    'outputs/confusion_matrix.png')
    
    # Plot entity metrics
    per_entity = evaluator.compute_per_entity_metrics(all_true_flat, all_pred_flat)
    evaluator.plot_entity_metrics(per_entity, 'outputs/entity_metrics.png')


def main(args):
    """Run complete advanced NER pipeline"""
    
    logger.info("="*70)
    logger.info("ADVANCED INDIAN ARCHAEOLOGY NER PIPELINE")
    logger.info("Target: F1 > 0.60")
    logger.info("="*70)
    
    try:
        if args.step == 'all' or args.step == '1':
            step1_data_expansion()
        
        if args.step == 'all' or args.step == '2':
            step2_data_augmentation()
        
        if args.step == 'all' or args.step == '3':
            step3_weak_labels()
        
        if args.step == 'all' or args.step == '4':
            results = step4_advanced_training()
            logger.info(f"\nTest F1 Score: {results['f1']:.4f}")
        
        if args.step == 'all' or args.step == '5':
            step5_evaluation()
        
        logger.info("\n" + "="*70)
        logger.info("✓ PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*70)
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Advanced NER Pipeline for Indian Archaeology"
    )
    parser.add_argument(
        '--step',
        choices=['1', '2', '3', '4', '5', 'all'],
        default='all',
        help="Which step to run (default: all)"
    )
    
    args = parser.parse_args()
    exit(main(args))
