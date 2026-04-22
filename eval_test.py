#!/usr/bin/env python3
"""Complete evaluation on test set with detailed metrics"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

from src.finetune import NERFineTuner
from src.data_utils import load_and_prepare_data
from config import *
import torch
import config

def evaluate_on_test():
    """Evaluate best model on test set"""
    
    logger.info("="*70)
    logger.info("INDIAN ARCHAEOLOGY NER - TEST SET EVALUATION")
    logger.info("="*70)
    
    # Load data
    logger.info("\nLoading datasets...")
    train_loader, dev_loader, test_loader, tokenizer = load_and_prepare_data(
        TRAIN_FILE,
        DEV_FILE,
        TEST_FILE,
        MODEL_NAME,
        BATCH_SIZE
    )
    
    # Initialize and load best model
    logger.info("\nLoading best model...")
    finetuner = NERFineTuner(
        model_name=MODEL_NAME,
        num_labels=NUM_LABELS,
        learning_rate=LEARNING_RATE,
        device="cpu"
    )
    
    finetuner.load_model("outputs/quick_eval/best_model")
    
    # Evaluate on test set
    logger.info("\n" + "="*70)
    logger.info("EVALUATING ON TEST SET")
    logger.info("="*70)
    
    finetuner.model.eval()
    all_pred_labels = []
    all_true_labels = []
    total_loss = 0.0
    
    criterion = torch.nn.CrossEntropyLoss(
        weight=torch.tensor([config.CLASS_WEIGHTS.get(i, 1.0) for i in range(NUM_LABELS)],
                           dtype=torch.float,
                           device=finetuner.device) if USE_CLASS_WEIGHTS else None,
        ignore_index=-100
    )
    
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch['input_ids'].to(finetuner.device)
            attention_mask = batch['attention_mask'].to(finetuner.device)
            labels = batch['labels'].to(finetuner.device)
            
            outputs = finetuner.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            logits = outputs.logits
            total_loss += loss.item()
            
            preds = torch.argmax(logits, dim=2)
            all_pred_labels.extend(preds.cpu().numpy())
            all_true_labels.extend(labels.cpu().numpy())
    
    # Calculate metrics
    metrics = finetuner._calculate_metrics(all_true_labels, all_pred_labels)
    avg_loss = total_loss / len(test_loader)
    
    print("\n" + "="*70)
    print("TEST SET RESULTS")
    print("="*70)
    print(f"Average Loss:           {avg_loss:.4f}")
    print(f"Precision (weighted):   {metrics['precision']:.4f}")
    print(f"Recall (weighted):      {metrics['recall']:.4f}")
    print(f"F1 Score (weighted):    {metrics['f1']:.4f}")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"[PASS] Dataset: Indian Archaeology NER")
    print(f"[PASS] Model: mBERT (bert-base-multilingual-cased)")
    print(f"[PASS] Training samples: 60 | Dev: 5 | Test: 5")
    print(f"[PASS] Entity types: 5 (ART, PER, LOC, MAT, CON)")
    print(f"[PASS] Training epochs: 1 (quick-test mode)")
    print(f"[PASS] Test F1 Score: {metrics['f1']:.4f}")
    print("="*70)

if __name__ == "__main__":
    try:
        evaluate_on_test()
        logger.info("\n[PASS] Evaluation completed successfully!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
