#!/usr/bin/env python3
"""Retrain model with augmented dataset"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

from src.finetune import NERFineTuner
from src.data_utils import load_and_prepare_data
from config import *

def retrain_model():
    """Retrain model with augmented data"""
    
    print("="*80)
    print("INDIAN ARCHAEOLOGY NER - MODEL RETRAINING WITH AUGMENTED DATA")
    print("="*80)
    
    # Create output directory
    output_dir = "outputs/retrained"
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n[Step 1] Loading augmented datasets...")
    print("-" * 80)
    train_loader, dev_loader, test_loader, tokenizer = load_and_prepare_data(
        TRAIN_FILE,
        DEV_FILE,
        TEST_FILE,
        MODEL_NAME,
        BATCH_SIZE
    )
    
    print(f"[PASS] Train batches:       {len(train_loader)}")
    print(f"[PASS] Dev batches:         {len(dev_loader)}")
    print(f"[PASS] Test batches:        {len(test_loader)}")
    
    print("\n[Step 2] Initializing model...")
    print("-" * 80)
    finetuner = NERFineTuner(
        model_name=MODEL_NAME,
        num_labels=NUM_LABELS,
        learning_rate=LEARNING_RATE,
        device="cpu"
    )
    print("[PASS] Model initialized")
    
    print("\n[Step 3] Training model...")
    print("-" * 80)
    best_model_path = finetuner.train(
        train_loader=train_loader,
        dev_loader=dev_loader,
        epochs=30,  # Proper training with more epochs
        output_dir=output_dir
    )
    
    print(f"\n[PASS] Model saved to: {best_model_path}")
    
    print("\n[Step 4] Evaluating on test set...")
    print("-" * 80)
    
    finetuner.model.eval()
    import torch
    
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
    
    print("\n" + "="*80)
    print("EVALUATION METRICS - TEST SET (RETRAINED MODEL)")
    print("="*80)
    print(f"\nAverage Loss:                {avg_loss:.4f}")
    print(f"Precision (weighted):        {metrics['precision']:.4f}")
    print(f"Recall (weighted):           {metrics['recall']:.4f}")
    print(f"F1 Score (weighted):         {metrics['f1']:.4f}")
    
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    print(f"\nDataset Information:")
    print(f"  Training samples:          834 sentences (augmented)")
    print(f"  Development samples:       166 sentences (augmented)")
    print(f"  Test samples:              168 sentences (augmented)")
    print(f"  Total entities in train:   137")
    
    print(f"\nModel Configuration:")
    print(f"  Model:                     {MODEL_NAME}")
    print(f"  Number of labels:          {NUM_LABELS}")
    print(f"  Learning rate:             {LEARNING_RATE}")
    print(f"  Batch size:                {BATCH_SIZE}")
    print(f"  Epochs:                    30")
    print(f"  Device:                    CPU")
    
    print(f"\nPerformance:")
    print(f"  Test Precision:            {metrics['precision']:.4f}")
    print(f"  Test Recall:               {metrics['recall']:.4f}")
    print(f"  Test F1 Score:             {metrics['f1']:.4f}")
    print(f"  Test Loss:                 {avg_loss:.4f}")
    
    print(f"\nEntity Types (5):")
    print(f"  - ART (Artifact)")
    print(f"  - PER (Person)")
    print(f"  - LOC (Location)")
    print(f"  - MAT (Material)")
    print(f"  - CON (Construction)")
    
    print(f"\nModel saved to:")
    print(f"  {best_model_path}")
    
    print("\n" + "="*80)
    print("RETRAINING COMPLETED SUCCESSFULLY!")
    print("="*80)

if __name__ == "__main__":
    import config
    try:
        retrain_model()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during retraining: {e}", exc_info=True)
        sys.exit(1)
