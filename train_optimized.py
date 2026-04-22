#!/usr/bin/env python3
"""
OPTIMIZED Fast NER Training Script
Complete pipeline optimized for speed (~2-6 hours total)
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm

from transformers import (
    AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
)

import config_optimized as config
from src.data_utils import load_conll_data, NERDataset

# ============================================================================
# SETUP LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# FOCAL LOSS IMPLEMENTATION
# ============================================================================

class FocalLoss(nn.Module):
    """Focal Loss for class imbalance"""
    def __init__(self, alpha=1.0, gamma=2.0, ignore_index=-100):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.ignore_index = ignore_index
    
    def forward(self, logits, labels):
        """
        Args:
            logits: (batch_size * seq_len, num_labels)
            labels: (batch_size * seq_len,)
        """
        # Flatten
        logits = logits.view(-1, logits.size(-1))
        labels = labels.view(-1)
        
        # Compute cross entropy
        ce_loss = nn.functional.cross_entropy(
            logits, labels, reduction='none', ignore_index=self.ignore_index
        )
        
        # Compute focal term
        p_t = torch.exp(-ce_loss)
        focal_loss = self.alpha * ((1 - p_t) ** self.gamma) * ce_loss
        
        # Average over non-ignored indices
        mask = (labels != self.ignore_index).float()
        loss = (focal_loss * mask).sum() / mask.sum().clamp(min=1)
        
        return loss

# ============================================================================
# OPTIMIZED MODEL
# ============================================================================

class OptimizedNERModel(nn.Module):
    """Optimized NER model with frozen layers"""
    
    def __init__(self, model_name, num_labels, freeze_layers=0):
        super().__init__()
        
        logger.info(f"Loading model: {model_name}")
        self.transformer = AutoModel.from_pretrained(model_name)
        self.hidden_size = self.transformer.config.hidden_size
        self.num_labels = num_labels
        
        # Freeze lower layers (70% of model)
        if freeze_layers > 0:
            self._freeze_layers(freeze_layers)
        
        # Classification head
        self.dropout = nn.Dropout(config.HIDDEN_DROPOUT)
        self.classifier = nn.Linear(self.hidden_size, num_labels)
        
        # Loss function
        if config.USE_FOCAL_LOSS:
            self.loss_fn = FocalLoss(
                alpha=config.FOCAL_LOSS_ALPHA,
                gamma=config.FOCAL_LOSS_GAMMA
            )
        else:
            self.loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
        
        logger.info(f"Model loaded: {num_labels} labels, hidden size: {self.hidden_size}")
        logger.info(f"Trainable parameters: {self._count_trainable_params():,}")
    
    def _freeze_layers(self, num_frozen):
        """Freeze bottom N transformer layers"""
        num_layers = len(self.transformer.encoder.layer)
        logger.info(f"Freezing bottom {num_frozen}/{num_layers} layers")
        
        # Freeze embeddings
        for param in self.transformer.embeddings.parameters():
            param.requires_grad = False
        
        # Freeze bottom N layers
        for i in range(min(num_frozen, num_layers)):
            for param in self.transformer.encoder.layer[i].parameters():
                param.requires_grad = False
    
    def _count_trainable_params(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def forward(self, input_ids, attention_mask, labels=None):
        # Transformer output
        outputs = self.transformer(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )
        
        sequence_output = outputs.last_hidden_state  # (batch_size, seq_len, hidden_size)
        
        # Classification
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)  # (batch_size, seq_len, num_labels)
        
        # Loss
        loss = None
        if labels is not None:
            loss = self.loss_fn(logits, labels)
        
        return logits, loss

# ============================================================================
# OPTIMIZED TRAINER
# ============================================================================

class OptimizedNERTrainer:
    """Fast NER trainer with early stopping"""
    
    def __init__(self, model, train_loader, eval_loader, device="cuda"):
        self.model = model.to(device)
        self.device = device
        self.train_loader = train_loader
        self.eval_loader = eval_loader
        
        # Optimizer
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=config.LEARNING_RATE,
            weight_decay=config.WEIGHT_DECAY
        )
        
        # Scheduler
        total_steps = len(train_loader) * config.NUM_EPOCHS
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=config.WARMUP_STEPS,
            num_training_steps=total_steps
        )
        
        # Early stopping
        self.best_loss = float('inf')
        self.patience_counter = 0
        self.early_stop = False
        
        # Metrics
        self.train_losses = []
        self.eval_losses = []
        
        logger.info(f"Trainer initialized:")
        logger.info(f"  Total steps: {total_steps}")
        logger.info(f"  Warmup steps: {config.WARMUP_STEPS}")
        logger.info(f"  Learning rate: {config.LEARNING_RATE}")
    
    def train_epoch(self, epoch):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        progress_bar = tqdm(
            self.train_loader,
            desc=f"Epoch {epoch + 1}/{config.NUM_EPOCHS}",
            unit="batch"
        )
        
        start_time = time.time()
        
        for batch_idx, batch in enumerate(progress_bar):
            # Move to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            logits, loss = self.model(input_ids, attention_mask, labels)
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                config.MAX_GRAD_NORM
            )
            
            # Update
            self.optimizer.step()
            self.scheduler.step()
            
            # Metrics
            total_loss += loss.item()
            avg_loss = total_loss / (batch_idx + 1)
            progress_bar.set_postfix({"loss": f"{avg_loss:.4f}"})
        
        epoch_time = time.time() - start_time
        avg_loss = total_loss / len(self.train_loader)
        self.train_losses.append(avg_loss)
        
        logger.info(f"Epoch {epoch + 1} - Loss: {avg_loss:.4f} - Time: {epoch_time:.1f}s")
        
        return avg_loss
    
    def evaluate(self):
        """Evaluate on validation set"""
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch in tqdm(self.eval_loader, desc="Evaluating"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                logits, loss = self.model(input_ids, attention_mask, labels)
                total_loss += loss.item()
        
        avg_loss = total_loss / len(self.eval_loader)
        self.eval_losses.append(avg_loss)
        
        logger.info(f"Validation Loss: {avg_loss:.4f}")
        
        return avg_loss
    
    def check_early_stopping(self, eval_loss):
        """Check if training should stop"""
        if eval_loss < self.best_loss - config.EARLY_STOPPING_THRESHOLD:
            self.best_loss = eval_loss
            self.patience_counter = 0
            return False
        else:
            self.patience_counter += 1
            if self.patience_counter >= config.EARLY_STOPPING_PATIENCE:
                logger.info(f"Early stopping triggered (patience={config.EARLY_STOPPING_PATIENCE})")
                self.early_stop = True
                return True
            return False
    
    def train(self):
        """Complete training loop"""
        logger.info("=" * 80)
        logger.info("STARTING OPTIMIZED NER TRAINING")
        logger.info("=" * 80)
        
        total_start = time.time()
        
        for epoch in range(config.NUM_EPOCHS):
            # Train
            train_loss = self.train_epoch(epoch)
            
            # Evaluate
            eval_loss = self.evaluate()
            
            # Check early stopping
            if self.check_early_stopping(eval_loss):
                break
        
        total_time = time.time() - total_start
        
        logger.info("=" * 80)
        logger.info("TRAINING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total training time: {total_time / 3600:.2f} hours")
        logger.info(f"Best validation loss: {self.best_loss:.4f}")
        logger.info(f"Epochs completed: {len(self.train_losses)}")
        
        return {
            "train_losses": self.train_losses,
            "eval_losses": self.eval_losses,
            "best_loss": self.best_loss,
            "total_time": total_time
        }
    
    def save_model(self, path):
        """Save model"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        torch.save(self.model.state_dict(), path / "pytorch_model.bin")
        self.model.transformer.config.save_pretrained(path)
        logger.info(f"Model saved to {path}")

# ============================================================================
# MAIN TRAINING SCRIPT
# ============================================================================

def main():
    """Main training function"""
    
    # Create output directory
    output_dir = config.OUTPUT_DIR / f"optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory: {output_dir}")
    
    # ========================================================================
    # 1. LOAD DATA
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("STAGE 1: LOADING DATA")
    logger.info("=" * 80)
    
    logger.info("Loading training data...")
    train_sentences, train_labels = load_conll_data(config.DATA_DIR / "train.conll")
    logger.info(f"Loaded {len(train_sentences)} training samples")
    
    logger.info("Loading dev data...")
    dev_sentences, dev_labels = load_conll_data(config.DATA_DIR / "dev.conll")
    logger.info(f"Loaded {len(dev_sentences)} dev samples")
    
    logger.info("Loading test data...")
    test_sentences, test_labels = load_conll_data(config.DATA_DIR / "test.conll")
    logger.info(f"Loaded {len(test_sentences)} test samples")
    
    # ========================================================================
    # 2. CREATE TOKENIZER & DATASETS
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("STAGE 2: CREATING DATASETS")
    logger.info("=" * 80)
    
    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
    
    train_dataset = NERDataset(
        train_sentences, train_labels,
        tokenizer, config.MAX_LENGTH,
        label_to_id=config.LABEL_TO_ID
    )
    
    dev_dataset = NERDataset(
        dev_sentences, dev_labels,
        tokenizer, config.MAX_LENGTH,
        label_to_id=config.LABEL_TO_ID
    )
    
    logger.info(f"Train dataset: {len(train_dataset)} samples")
    logger.info(f"Dev dataset: {len(dev_dataset)} samples")
    
    # ========================================================================
    # 3. CREATE DATALOADERS
    # ========================================================================
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    dev_loader = DataLoader(
        dev_dataset,
        batch_size=config.EVAL_BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    # ========================================================================
    # 4. CREATE MODEL
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("STAGE 3: CREATING MODEL")
    logger.info("=" * 80)
    
    num_frozen = config.NUM_FROZEN_LAYERS if config.USE_FROZEN_LAYERS else 0
    model = OptimizedNERModel(
        config.MODEL_NAME,
        config.NUM_LABELS,
        freeze_layers=num_frozen
    )
    
    # ========================================================================
    # 5. TRAIN
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("STAGE 4: TRAINING")
    logger.info("=" * 80)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    trainer = OptimizedNERTrainer(model, train_loader, dev_loader, device=device)
    results = trainer.train()
    
    # ========================================================================
    # 6. SAVE RESULTS
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("STAGE 5: SAVING RESULTS")
    logger.info("=" * 80)
    
    # Save model
    model_path = output_dir / "final_model"
    trainer.save_model(model_path)
    
    # Save metrics
    metrics = {
        "train_losses": results["train_losses"],
        "eval_losses": results["eval_losses"],
        "best_loss": results["best_loss"],
        "total_time_hours": results["total_time"] / 3600,
        "config": {
            "model_name": config.MODEL_NAME,
            "max_length": config.MAX_LENGTH,
            "batch_size": config.BATCH_SIZE,
            "learning_rate": config.LEARNING_RATE,
            "num_epochs": config.NUM_EPOCHS,
            "frozen_layers": config.NUM_FROZEN_LAYERS if config.USE_FROZEN_LAYERS else 0,
        }
    }
    
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Results saved to {output_dir}")
    
    # ========================================================================
    # 7. FINAL SUMMARY
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Model: {config.MODEL_NAME}")
    logger.info(f"Max sequence length: {config.MAX_LENGTH}")
    logger.info(f"Batch size: {config.BATCH_SIZE}")
    logger.info(f"Epochs: {len(results['train_losses'])}/{config.NUM_EPOCHS}")
    logger.info(f"Total time: {results['total_time'] / 3600:.2f} hours")
    logger.info(f"Best validation loss: {results['best_loss']:.4f}")
    logger.info(f"Output: {output_dir}")
    logger.info("=" * 80 + "\n")

if __name__ == "__main__":
    main()
