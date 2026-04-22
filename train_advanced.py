#!/usr/bin/env python3
"""
Advanced Training Pipeline with CRF, Data Augmentation, and Gazetteers
Targets F1 score > 0.60
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer
import numpy as np
import logging
from typing import Tuple, List, Dict, Optional
from tqdm import tqdm
from sklearn.metrics import precision_recall_fscore_support, f1_score
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

from model_crf import TransformerCRFModel, FocalLoss
from gazetteer import ArchaeologyGazetteer, WeakSupervisionGenerator
from config import *


class NERDataset(Dataset):
    """PyTorch Dataset for NER with proper label alignment"""
    
    def __init__(self, words_list: List[List[str]], labels_list: List[List[str]], 
                 tokenizer, max_length: int = 512, label_to_id: Dict[str, int] = None):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label_to_id = label_to_id or LABEL_TO_ID
        
        self.encodings = []
        self.labels = []
        
        for words, labels in zip(words_list, labels_list):
            # Tokenize with alignment
            encoding = tokenizer(
                words,
                is_split_into_words=True,
                max_length=max_length,
                truncation=True,
                padding='max_length',
                return_tensors='pt'
            )
            
            # Align labels with subword tokens
            word_ids = encoding.word_ids()
            aligned_labels = []
            previous_word_id = None
            
            for word_id in word_ids:
                if word_id is None:
                    aligned_labels.append(-100)  # Special tokens
                elif word_id != previous_word_id:
                    aligned_labels.append(self.label_to_id.get(labels[word_id], 0))
                else:
                    # Subword of previous token
                    aligned_labels.append(-100)
                
                previous_word_id = word_id
            
            self.encodings.append(encoding)
            self.labels.append(torch.tensor(aligned_labels))
    
    def __len__(self):
        return len(self.encodings)
    
    def __getitem__(self, idx):
        encoding = self.encodings[idx]
        labels = self.labels[idx]
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': labels
        }


class AdvancedTrainer:
    """Advanced trainer with CRF, focal loss, and gazetteer integration"""
    
    def __init__(self, model: TransformerCRFModel, device: str = 'cpu', 
                 use_focal_loss: bool = True, use_gazetteer: bool = True):
        self.model = model
        self.device = device
        self.use_focal_loss = use_focal_loss
        self.use_gazetteer = use_gazetteer
        
        if use_gazetteer:
            self.gazetteer = ArchaeologyGazetteer()
            self.weak_gen = WeakSupervisionGenerator(self.gazetteer)
        else:
            self.gazetteer = None
            self.weak_gen = None
        
        logger.info(f"✓ Trainer initialized (device: {device}, focal_loss: {use_focal_loss}, gazetteer: {use_gazetteer})")
    
    def train(self, train_loader: DataLoader, dev_loader: DataLoader, 
              test_loader: Optional[DataLoader] = None,
              epochs: int = 20, learning_rate: float = 2e-5,
              output_dir: str = "outputs/advanced_model",
              warmup_ratio: float = 0.1, weight_decay: float = 0.01,
              early_stopping_patience: int = 3,
              freeze_transformer_epochs: int = 2) -> Dict[str, float]:
        """
        Advanced training with multiple strategies
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Optimizer
        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler
        total_steps = len(train_loader) * epochs
        warmup_steps = int(total_steps * warmup_ratio)
        
        def get_linear_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps):
            def lr_lambda(current_step):
                if current_step < num_warmup_steps:
                    return float(current_step) / float(max(1, num_warmup_steps))
                return max(0.0, float(num_training_steps - current_step) / float(max(1, num_training_steps - num_warmup_steps)))
            return optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
        
        scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
        
        # Loss function
        if self.use_focal_loss:
            criterion = FocalLoss(alpha=0.25, gamma=2.0)
        else:
            criterion = nn.CrossEntropyLoss(ignore_index=-100)
        
        best_f1 = 0.0
        patience_counter = 0
        
        logger.info("\n" + "="*70)
        logger.info("ADVANCED NER TRAINING")
        logger.info("="*70)
        
        for epoch in range(epochs):
            logger.info(f"\nEpoch {epoch + 1}/{epochs}")
            
            # Freeze transformer for first few epochs
            if epoch < freeze_transformer_epochs:
                self.model.freeze_transformer()
            else:
                self.model.unfreeze_transformer()
            
            # Training phase
            train_loss = self._train_epoch(train_loader, optimizer, scheduler, criterion)
            logger.info(f"  Training Loss: {train_loss:.4f}")
            
            # Evaluation phase
            dev_metrics = self._evaluate(dev_loader)
            dev_f1 = dev_metrics['f1']
            
            logger.info(f"  Dev F1: {dev_f1:.4f} | Precision: {dev_metrics['precision']:.4f} | Recall: {dev_metrics['recall']:.4f}")
            
            # Save best model
            if dev_f1 > best_f1:
                best_f1 = dev_f1
                patience_counter = 0
                self._save_model(os.path.join(output_dir, "best_model"))
                logger.info(f"  ✓ Best model saved (F1: {best_f1:.4f})")
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    logger.info(f"  Early stopping triggered after {epoch + 1} epochs")
                    break
        
        # Final test evaluation
        if test_loader is not None:
            logger.info("\n" + "="*70)
            logger.info("TEST SET EVALUATION")
            logger.info("="*70)
            
            # Load best model
            self.model.load_state_dict(torch.load(os.path.join(output_dir, "best_model", "pytorch_model.bin"), map_location=self.device))
            test_metrics = self._evaluate(test_loader)
            
            logger.info(f"  Test F1: {test_metrics['f1']:.4f}")
            logger.info(f"  Test Precision: {test_metrics['precision']:.4f}")
            logger.info(f"  Test Recall: {test_metrics['recall']:.4f}")
            
            return test_metrics
        
        return dev_metrics
    
    def _train_epoch(self, train_loader, optimizer, scheduler, criterion) -> float:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        
        progress_bar = tqdm(train_loader, desc="Training")
        for batch_idx, batch in enumerate(progress_bar):
            optimizer.zero_grad()
            
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            emissions, loss = self.model(input_ids, attention_mask, labels)
            
            total_loss += loss.item()
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            progress_bar.set_postfix({'loss': loss.item()})
        
        return total_loss / len(train_loader)
    
    def _evaluate(self, eval_loader) -> Dict[str, float]:
        """Evaluate on development set"""
        self.model.eval()
        
        all_pred_labels = []
        all_true_labels = []
        
        with torch.no_grad():
            progress_bar = tqdm(eval_loader, desc="Evaluating")
            for batch in progress_bar:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Get predictions
                _, predictions = self.model(input_ids, attention_mask)
                
                # Collect
                all_pred_labels.extend(predictions)
                all_true_labels.extend(labels.cpu().numpy())
        
        # Calculate metrics
        metrics = self._calculate_metrics(all_true_labels, all_pred_labels)
        return metrics
    
    def _calculate_metrics(self, true_labels, pred_labels) -> Dict[str, float]:
        """Calculate evaluation metrics"""
        # Flatten and remove -100 (ignored labels)
        true_flat = []
        pred_flat = []
        
        for true_seq, pred_seq in zip(true_labels, pred_labels):
            for true_label, pred_label in zip(true_seq, pred_seq):
                if true_label != -100:
                    true_flat.append(true_label)
                    pred_flat.append(pred_label)
        
        if not true_flat:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        
        true_flat = np.array(true_flat)
        pred_flat = np.array(pred_flat)
        
        # Calculate metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_flat, pred_flat, average='weighted', zero_division=0
        )
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
        }
    
    def _save_model(self, path: str) -> None:
        """Save model and tokenizer"""
        os.makedirs(path, exist_ok=True)
        torch.save(self.model.state_dict(), os.path.join(path, "pytorch_model.bin"))
        logger.info(f"✓ Model saved to {path}")


def create_advanced_pipeline(train_sentences: List[List[str]], 
                           train_labels: List[List[str]],
                           dev_sentences: List[List[str]], 
                           dev_labels: List[List[str]],
                           test_sentences: List[List[str]], 
                           test_labels: List[List[str]],
                           model_name: str = "bert-base-multilingual-cased",
                           batch_size: int = 16,
                           epochs: int = 20,
                           learning_rate: float = 2e-5) -> Dict[str, float]:
    """Create complete advanced training pipeline"""
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")
    
    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Create datasets
    logger.info("Creating datasets...")
    train_dataset = NERDataset(train_sentences, train_labels, tokenizer)
    dev_dataset = NERDataset(dev_sentences, dev_labels, tokenizer)
    test_dataset = NERDataset(test_sentences, test_labels, tokenizer)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    dev_loader = DataLoader(dev_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)
    
    logger.info(f"  Train: {len(train_loader)} batches")
    logger.info(f"  Dev: {len(dev_loader)} batches")
    logger.info(f"  Test: {len(test_loader)} batches")
    
    # Create model
    logger.info(f"\nCreating model: {model_name}")
    model = TransformerCRFModel(
        model_name=model_name,
        num_labels=NUM_LABELS,
        dropout=0.1,
        use_self_attention=getattr(config, 'USE_SELF_ATTENTION', False) if 'config' in globals() else False
    ).to(device)
    
    logger.info(f"Trainable parameters: {model.get_trainable_params():,}")
    
    # Create trainer
    trainer = AdvancedTrainer(
        model=model,
        device=device,
        use_focal_loss=True,
        use_gazetteer=True
    )
    
    # Train
    results = trainer.train(
        train_loader=train_loader,
        dev_loader=dev_loader,
        test_loader=test_loader,
        epochs=epochs,
        learning_rate=learning_rate,
        output_dir="outputs/advanced_model",
        freeze_transformer_epochs=2,
        early_stopping_patience=5
    )
    
    return results


if __name__ == "__main__":
    logger.info("Advanced NER training module loaded successfully!")
