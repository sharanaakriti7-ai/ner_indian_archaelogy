#!/usr/bin/env python3
"""
Complete Training Pipeline for NER
Includes:
- Multi-run training with different seeds
- Early stopping
- Gradient clipping and weight decay
- Loss tracking and visualization
- Best model saving
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, ConcatDataset
import numpy as np
import logging
from typing import Tuple, Dict, List, Optional
from tqdm import tqdm
import json
from pathlib import Path

logger = logging.getLogger(__name__)

from model_crf import TransformerCRFModel, FocalLoss
from utils import (
    set_seed, EarlyStopping, PercentageScheduler, count_parameters
)


class NERTrainer:
    """Comprehensive NER Training Pipeline"""
    
    def __init__(self, 
                 model: TransformerCRFModel,
                 train_dataset,
                 dev_dataset,
                 batch_size: int = 16,
                 learning_rate: float = 2e-5,
                 weight_decay: float = 0.01,
                 gradient_clip: float = 1.0,
                 dropout: float = 0.1,
                 use_focal_loss: bool = False,
                 device: str = 'cpu',
                 output_dir: str = 'outputs/'):
        
        self.model = model.to(device)
        self.train_dataset = train_dataset
        self.dev_dataset = dev_dataset
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.gradient_clip = gradient_clip
        self.dropout = dropout
        self.use_focal_loss = use_focal_loss
        self.device = device
        self.output_dir = output_dir
        
        # Setup optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Setup loss
        if use_focal_loss:
            self.criterion = FocalLoss(alpha=1.0, gamma=2.0)
            logger.info("✓ Using Focal Loss")
        else:
            self.criterion = nn.CrossEntropyLoss(ignore_index=-100)
            logger.info("✓ Using CrossEntropy Loss")
        
        # Tracking
        self.train_losses = []
        self.val_losses = []
        self.train_f1s = []
        self.val_f1s = []
        self.best_val_loss = float('inf')
        self.best_val_f1 = 0.0
        
        logger.info(f"✓ Trainer initialized")
        logger.info(f"  Model parameters: {count_parameters(self.model):,}")
        logger.info(f"  Learning rate: {learning_rate}")
        logger.info(f"  Weight decay: {weight_decay}")
        logger.info(f"  Gradient clip: {gradient_clip}")
        logger.info(f"  Dropout: {dropout}")
    
    def train_epoch(self, train_loader: DataLoader, epoch: int) -> Tuple[float, float]:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        total_correct = 0
        total_tokens = 0
        
        progress_bar = tqdm(train_loader, desc=f"Training Epoch {epoch}")
        
        for batch_idx, batch in enumerate(progress_bar):
            self.optimizer.zero_grad()
            
            # Move to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            emissions, loss = self.model(input_ids, attention_mask, labels)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(), 
                self.gradient_clip
            )
            
            self.optimizer.step()
            
            total_loss += loss.item()
            
            progress_bar.set_postfix({'loss': loss.item()})
        
        avg_loss = total_loss / len(train_loader)
        return avg_loss
    
    def evaluate(self, dev_loader: DataLoader) -> Tuple[float, Dict]:
        """Evaluate on development set"""
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in tqdm(dev_loader, desc="Evaluating"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                emissions, loss = self.model(input_ids, attention_mask, labels)
                total_loss += loss.item()
                
                # Get predictions
                _, predictions = self.model(input_ids, attention_mask)
                
                all_preds.extend(predictions)
                all_labels.extend(labels.cpu().numpy().tolist())
        
        avg_loss = total_loss / len(dev_loader)
        
        # Calculate metrics (placeholder - will be enhanced with seqeval)
        metrics = {'loss': avg_loss}
        
        return avg_loss, metrics
    
    def train(self, epochs: int = 30, early_stopping_patience: int = 3,
              warmup_steps: int = 500) -> Dict:
        """Complete training loop with early stopping"""
        
        # Data loaders
        train_loader = DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True
        )
        
        dev_loader = DataLoader(
            self.dev_dataset,
            batch_size=self.batch_size,
            shuffle=False
        )
        
        # Learning rate scheduler
        total_steps = len(train_loader) * epochs
        scheduler = PercentageScheduler(
            self.optimizer,
            total_steps=total_steps,
            warmup_steps=warmup_steps
        )
        
        # Early stopping
        early_stopping = EarlyStopping(patience=early_stopping_patience)
        
        logger.info(f"\n{'='*70}")
        logger.info("Starting Training")
        logger.info(f"{'='*70}")
        logger.info(f"Total epochs: {epochs}")
        logger.info(f"Total steps: {total_steps}")
        logger.info(f"Warmup steps: {warmup_steps}")
        
        for epoch in range(1, epochs + 1):
            logger.info(f"\n{'='*70}")
            logger.info(f"Epoch {epoch}/{epochs}")
            logger.info(f"{'='*70}")
            
            # Train
            train_loss = self.train_epoch(train_loader, epoch)
            self.train_losses.append(train_loss)
            logger.info(f"Train Loss: {train_loss:.4f}")
            
            # Update learning rate
            for _ in range(len(train_loader)):
                scheduler.step()
            
            # Evaluate
            val_loss, metrics = self.evaluate(dev_loader)
            self.val_losses.append(val_loss)
            logger.info(f"Val Loss: {val_loss:.4f}")
            
            # Save best model
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self._save_model('best_model')
                logger.info(f"✓ Saved best model (val loss: {val_loss:.4f})")
            
            # Check early stopping
            if early_stopping(val_loss):
                logger.info(f"✓ Early stopping at epoch {epoch}")
                break
        
        # Save final model
        self._save_model('final_model')
        logger.info(f"✓ Training complete. Final model saved.")
        
        return {
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'best_val_loss': self.best_val_loss,
            'epochs_trained': epoch
        }
    
    def _save_model(self, model_name: str) -> None:
        """Save model checkpoint"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        model_path = os.path.join(self.output_dir, model_name)
        Path(model_path).mkdir(parents=True, exist_ok=True)
        
        # Save model
        torch.save(self.model.state_dict(), os.path.join(model_path, 'pytorch_model.bin'))
        
        # Save config
        config = {
            'model_name': self.model.transformer.config.model_type,
            'num_labels': self.model.num_labels,
            'hidden_size': self.model.hidden_size,
            'dropout': self.dropout
        }
        with open(os.path.join(model_path, 'config.json'), 'w') as f:
            json.dump(config, f, indent=2)


class MultiSeedTrainer:
    """Train model with multiple random seeds for stability analysis"""
    
    def __init__(self, model_name: str, num_labels: int, num_seeds: int = 5,
                 device: str = 'cpu', output_dir: str = 'outputs/', use_self_attention: bool = False):
        self.model_name = model_name
        self.num_labels = num_labels
        self.num_seeds = num_seeds
        self.device = device
        self.output_dir = output_dir
        self.use_self_attention = use_self_attention
        self.results = []
    
    def train_all_seeds(self, train_dataset, dev_dataset, test_dataset,
                       epochs: int = 30, batch_size: int = 16,
                       learning_rate: float = 2e-5) -> Dict:
        """Train model with different seeds"""
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Starting Multi-Seed Training ({self.num_seeds} seeds)")
        logger.info(f"{'='*70}\n")
        
        all_train_losses = []
        all_val_losses = []
        all_f1_scores = []
        
        for seed_idx in range(self.num_seeds):
            logger.info(f"\n{'#'*70}")
            logger.info(f"SEED RUN {seed_idx + 1}/{self.num_seeds} (seed={42 + seed_idx})")
            logger.info(f"{'#'*70}")
            
            seed = 42 + seed_idx
            set_seed(seed)
            
            # Create model
            model = TransformerCRFModel(
                model_name=self.model_name,
                num_labels=self.num_labels,
                dropout=0.1,
                use_self_attention=self.use_self_attention
            )
            
            # Create trainer
            seed_output_dir = os.path.join(self.output_dir, f'seed_{seed}')
            trainer = NERTrainer(
                model=model,
                train_dataset=train_dataset,
                dev_dataset=dev_dataset,
                batch_size=batch_size,
                learning_rate=learning_rate,
                device=self.device,
                output_dir=seed_output_dir
            )
            
            # Train
            history = trainer.train(epochs=epochs)
            
            all_train_losses.append(trainer.train_losses)
            all_val_losses.append(trainer.val_losses)
            
            self.results.append({
                'seed': seed,
                'train_losses': trainer.train_losses,
                'val_losses': trainer.val_losses,
                'best_val_loss': trainer.best_val_loss
            })
        
        # Compute statistics
        stats = self._compute_statistics()
        
        return {
            'results': self.results,
            'statistics': stats,
            'all_train_losses': all_train_losses,
            'all_val_losses': all_val_losses
        }
    
    def _compute_statistics(self) -> Dict:
        """Compute mean and std of metrics across seeds"""
        
        val_losses = [r['best_val_loss'] for r in self.results]
        
        stats = {
            'mean_val_loss': float(np.mean(val_losses)),
            'std_val_loss': float(np.std(val_losses)),
            'min_val_loss': float(np.min(val_losses)),
            'max_val_loss': float(np.max(val_losses)),
            'num_seeds': len(self.results)
        }
        
        logger.info(f"\n{'='*70}")
        logger.info("MULTI-SEED STATISTICS")
        logger.info(f"{'='*70}")
        logger.info(f"Mean Val Loss: {stats['mean_val_loss']:.4f} ± {stats['std_val_loss']:.4f}")
        logger.info(f"Min Val Loss:  {stats['min_val_loss']:.4f}")
        logger.info(f"Max Val Loss:  {stats['max_val_loss']:.4f}")
        
        return stats
