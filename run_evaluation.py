#!/usr/bin/env python3
"""Run comprehensive evaluation with trained model"""

import torch
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from src.finetune import NERFineTuner
from src.data_utils import load_and_prepare_data
from config import *
import torch
import config

def main():
    logger.info("="*80)
    logger.info("INDIAN ARCHAEOLOGY NER - COMPREHENSIVE EVALUATION")
    logger.info("="*80)
    
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
    logger.info("\nLoading trained model from outputs/quick_eval/best_model...")
    finetuner = NERFineTuner(
        model_name=MODEL_NAME,
        num_labels=NUM_LABELS,
        learning_rate=LEARNING_RATE,
        device="cpu"
    )
    
    finetuner.load_model("outputs/quick_eval/best_model")
    
    logger.info("\n" + "="*80)
    logger.info("MODEL CONFIGURATION")
    logger.info("="*80)
    print(f"  Model Name:         {MODEL_NAME}")
    print(f"  Number of Labels:   {NUM_LABELS}")
    print(f"  Entity Types:       {', '.join(ID_TO_LABEL.values())}")
    print(f"  Batch Size:         {BATCH_SIZE}")
    print(f"  Max Length:         {MAX_LENGTH}")
    print(f"  Dropout:            {DROPOUT}")
    
    logger.info("\n" + "="*80)
    logger.info("DATASET STATISTICS")
    logger.info("="*80)
    print(f"  Train Samples:      {len(train_loader)} batches (~{len(train_loader) * BATCH_SIZE} samples)")
    print(f"  Dev Samples:        {len(dev_loader)} batches (~{len(dev_loader) * BATCH_SIZE} samples)")
    print(f"  Test Samples:       {len(test_loader)} batches (~{len(test_loader) * BATCH_SIZE} samples)")
    
    # Evaluate on each set
    logger.info("\n" + "="*80)
    logger.info("EVALUATION RESULTS")
    logger.info("="*80)
    
    finetuner.model.eval()
    criterion = torch.nn.CrossEntropyLoss(
        weight=torch.tensor([config.CLASS_WEIGHTS.get(i, 1.0) for i in range(NUM_LABELS)],
                           dtype=torch.float,
                           device=finetuner.device) if USE_CLASS_WEIGHTS else None,
        ignore_index=-100
    )
    
    for dataset_name, dataloader in [("Train", train_loader), ("Dev", dev_loader), ("Test", test_loader)]:
        logger.info(f"\nEvaluating on {dataset_name} set...")
        
        all_pred_labels = []
        all_true_labels = []
        total_loss = 0.0
        
        with torch.no_grad():
            for batch in dataloader:
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
        avg_loss = total_loss / len(dataloader)
        
        print(f"\n{dataset_name} Set Results:")
        print(f"  Average Loss:       {avg_loss:.4f}")
        print(f"  Precision:          {metrics['precision']:.4f}")
        print(f"  Recall:             {metrics['recall']:.4f}")
        print(f"  F1 Score:           {metrics['f1']:.4f}")
    
    logger.info("\n" + "="*80)
    logger.info("ENTITY TYPE MAPPING")
    logger.info("="*80)
    for idx, label in ID_TO_LABEL.items():
        print(f"  {idx}: {label}")
    
    logger.info("\n" + "="*80)
    logger.info("EVALUATION COMPLETED SUCCESSFULLY!")
    logger.info("="*80)

if __name__ == "__main__":
    main()
