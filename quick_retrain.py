#!/usr/bin/env python3
"""Quick retrain with fewer epochs for faster feedback"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

from src.finetune import NERFineTuner
from src.data_utils import load_and_prepare_data
from config import *
import torch
import config

def quick_retrain():
    """Quick retrain with 5 epochs for feedback"""
    
    print("="*80)
    print("QUICK RETRAIN - AUGMENTED DATA (5 EPOCHS)")
    print("="*80)
    
    output_dir = "outputs/quick_retrained"
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n[Loading datasets...]")
    train_loader, dev_loader, test_loader, tokenizer = load_and_prepare_data(
        TRAIN_FILE, DEV_FILE, TEST_FILE, MODEL_NAME, BATCH_SIZE
    )
    
    print(f"Train: {len(train_loader)} batches | Dev: {len(dev_loader)} | Test: {len(test_loader)}")
    
    print("\n[Initializing model...]")
    finetuner = NERFineTuner(
        model_name=MODEL_NAME,
        num_labels=NUM_LABELS,
        learning_rate=LEARNING_RATE,
        device="cpu"
    )
    
    print("\n[Training model (5 epochs)...]")
    best_model_path = finetuner.train(
        train_loader=train_loader,
        dev_loader=dev_loader,
        epochs=5,
        output_dir=output_dir
    )
    
    print(f"\n[Model saved to: {best_model_path}]")
    
    print("\n[Evaluating on test set...]")
    finetuner.model.eval()
    
    all_pred_labels = []
    all_true_labels = []
    total_loss = 0.0
    
    criterion = torch.nn.CrossEntropyLoss(
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
            
            total_loss += outputs.loss.item()
            preds = torch.argmax(outputs.logits, dim=2)
            all_pred_labels.extend(preds.cpu().numpy())
            all_true_labels.extend(labels.cpu().numpy())
    
    metrics = finetuner._calculate_metrics(all_true_labels, all_pred_labels)
    avg_loss = total_loss / len(test_loader)
    
    print("\n" + "="*80)
    print("RETRAINED MODEL - EVALUATION METRICS")
    print("="*80)
    
    print(f"\nTest Set Performance:")
    print(f"  Average Loss:              {avg_loss:.4f}")
    print(f"  Precision (weighted):      {metrics['precision']:.4f}")
    print(f"  Recall (weighted):         {metrics['recall']:.4f}")
    print(f"  F1 Score (weighted):       {metrics['f1']:.4f}")
    
    print(f"\nDataset (Augmented):")
    print(f"  Training:                  834 sentences")
    print(f"  Development:               166 sentences")
    print(f"  Test:                      168 sentences")
    
    print(f"\nModel Info:")
    print(f"  Model:                     {MODEL_NAME}")
    print(f"  Epochs Trained:            5")
    print(f"  Entity Types:              5 (ART, PER, LOC, MAT, CON)")
    print(f"  Device:                    CPU")
    
    print("\n" + "="*80)
    print("QUICK RETRAINING COMPLETED!")
    print("="*80)

if __name__ == "__main__":
    try:
        quick_retrain()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
