"""
NER Fine-tuning on Domain-Adapted BERT
Token classification with proper subword handling and cross-validation
"""

import os
import logging
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import LinearLR
from torch.utils.data import DataLoader
from transformers import AutoModelForTokenClassification, AutoTokenizer
import numpy as np
from tqdm import tqdm
from sklearn.model_selection import KFold
import config
from src.data_utils import CoNLLDataset, NERDataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NERFineTuner:
    """Fine-tune BERT for NER task with BIO tagging"""
    
    def __init__(self, model_name: str = config.MODEL_NAME,
                 num_labels: int = config.NUM_LABELS,
                 learning_rate: float = config.LEARNING_RATE,
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        self.model_name = model_name
        self.num_labels = num_labels
        self.learning_rate = learning_rate
        self.device = device
        
        logger.info(f"Loading model from {model_name}...")
        self.model = AutoModelForTokenClassification.from_pretrained(
            model_name, num_labels=num_labels
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model.to(device)
        
        # Calculate class weights for imbalanced dataset
        self.class_weights = torch.tensor(
            [config.CLASS_WEIGHTS.get(i, 1.0) for i in range(num_labels)],
            dtype=torch.float,
            device=device
        ) if config.USE_CLASS_WEIGHTS else None
        
        logger.info(f"Model loaded. Total parameters: {self.model.num_parameters():,}")
    
    def train(self, train_loader: DataLoader, dev_loader: DataLoader,
              epochs: int = config.EPOCHS,
              output_dir: str = config.MODEL_DIR,
              warmup_steps: int = config.WARMUP_STEPS):
        """
        Fine-tune BERT for NER
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Optimizer
        optimizer = AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=config.WEIGHT_DECAY
        )
        
        # Learning rate scheduler
        total_steps = len(train_loader) * epochs
        scheduler = LinearLR(
            optimizer,
            start_factor=1.0,
            end_factor=0.1,
            total_iters=total_steps
        )
        
        # Loss function with class weights
        if self.class_weights is not None:
            criterion = nn.CrossEntropyLoss(
                weight=self.class_weights,
                ignore_index=-100
            )
        else:
            criterion = nn.CrossEntropyLoss(ignore_index=-100)
        
        best_loss = float('inf')
        best_f1 = 0.0
        
        for epoch in range(epochs):
            logger.info(f"\n{'='*50}")
            logger.info(f"Epoch {epoch + 1}/{epochs}")
            logger.info(f"{'='*50}")
            
            # Training phase
            train_loss = self._train_epoch(train_loader, optimizer, scheduler, criterion)
            logger.info(f"Training Loss: {train_loss:.4f}")
            
            # Evaluation phase
            eval_loss, eval_metrics = self._evaluate(dev_loader, criterion)
            logger.info(f"Evaluation Loss: {eval_loss:.4f}")
            logger.info(f"Eval Metrics: {eval_metrics}")
            
            # Save best model
            if config.SAVE_BEST_MODEL and eval_loss < best_loss:
                best_loss = eval_loss
                if eval_metrics.get('f1', 0) > best_f1:
                    best_f1 = eval_metrics['f1']
                    self._save_model(os.path.join(output_dir, "best_model"))
                    logger.info(f"Saved best model with F1: {best_f1:.4f}")
        
        # Save final model
        final_model_path = os.path.join(output_dir, "final_model")
        self._save_model(final_model_path)
        logger.info(f"Training complete. Model saved to {final_model_path}")
        
        return self.model
    
    def _train_epoch(self, train_loader, optimizer, scheduler, criterion):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        
        progress_bar = tqdm(train_loader, desc="Training")
        for batch_idx, batch in enumerate(progress_bar):
            optimizer.zero_grad()
            
            # Move to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            total_loss += loss.item()
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), config.MAX_GRAD_NORM)
            optimizer.step()
            scheduler.step()
            
            progress_bar.set_postfix({'loss': loss.item()})
        
        return total_loss / len(train_loader)
    
    def _evaluate(self, eval_loader, criterion):
        """Evaluate on development set"""
        self.model.eval()
        total_loss = 0.0
        
        all_pred_labels = []
        all_true_labels = []
        
        with torch.no_grad():
            progress_bar = tqdm(eval_loader, desc="Evaluating")
            for batch in progress_bar:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                logits = outputs.logits
                total_loss += loss.item()
                
                # Get predictions
                preds = torch.argmax(logits, dim=2)
                
                # Collect for metrics calculation
                all_pred_labels.extend(preds.cpu().numpy())
                all_true_labels.extend(labels.cpu().numpy())
                
                progress_bar.set_postfix({'loss': loss.item()})
        
        # Calculate metrics
        metrics = self._calculate_metrics(all_true_labels, all_pred_labels)
        
        return total_loss / len(eval_loader), metrics
    
    def _calculate_metrics(self, true_labels, pred_labels):
        """Calculate Precision, Recall, F1 scores"""
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        # Flatten and remove -100 (ignored labels)
        true_flat = []
        pred_flat = []
        
        for true_seq, pred_seq in zip(true_labels, pred_labels):
            for true_label, pred_label in zip(true_seq, pred_seq):
                if true_label != -100:
                    true_flat.append(true_label)
                    pred_flat.append(pred_label)
        
        true_flat = np.array(true_flat)
        pred_flat = np.array(pred_flat)
        
        # Calculate metrics
        precision = precision_score(true_flat, pred_flat, average='weighted', zero_division=0)
        recall = recall_score(true_flat, pred_flat, average='weighted', zero_division=0)
        f1 = f1_score(true_flat, pred_flat, average='weighted', zero_division=0)
        
        # Per-class metrics
        precision_per_class = precision_score(true_flat, pred_flat, average=None, zero_division=0)
        recall_per_class = recall_score(true_flat, pred_flat, average=None, zero_division=0)
        f1_per_class = f1_score(true_flat, pred_flat, average=None, zero_division=0)
        
        metrics = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'precision_per_class': precision_per_class,
            'recall_per_class': recall_per_class,
            'f1_per_class': f1_per_class,
        }
        
        return metrics
    
    def _save_model(self, path: str):
        """Save model and tokenizer"""
        os.makedirs(path, exist_ok=True)
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load pretrained model"""
        logger.info(f"Loading model from {path}...")
        self.model = AutoModelForTokenClassification.from_pretrained(path, num_labels=self.num_labels)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model.to(self.device)
        logger.info(f"Model loaded successfully")
    
    def predict(self, sentences: list, return_confidence: bool = False):
        """
        Predict NER labels for new sentences
        """
        self.model.eval()
        
        predictions = []
        
        with torch.no_grad():
            for sentence in sentences:
                # Tokenize
                encodings = self.tokenizer(
                    sentence,
                    truncation=True,
                    is_split_into_words=True,
                    max_length=config.MAX_LENGTH,
                    padding='max_length',
                    return_tensors='pt'
                )
                
                input_ids = encodings['input_ids'].to(self.device)
                attention_mask = encodings['attention_mask'].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                logits = outputs.logits
                preds = torch.argmax(logits, dim=2)[0]
                
                # Align with original tokens
                word_ids = encodings.word_ids()
                sentence_preds = []
                
                for word_idx in word_ids:
                    if word_idx is not None:
                        label_id = preds[word_idx].item()
                        label = config.ID_TO_LABEL[label_id]
                        
                        if not sentence_preds or word_ids[word_idx - 1] != word_idx:
                            sentence_preds.append((sentence[word_idx], label))
                
                predictions.append(sentence_preds)
        
        return predictions


def cross_validate_ner(train_file: str, n_splits: int = config.NUM_FOLDS,
                       output_dir: str = config.OUTPUT_DIR):
    """
    Cross-validation for NER with multiple folds
    """
    logger.info(f"Starting {n_splits}-fold cross-validation for NER")
    
    # Load all data
    data = CoNLLDataset(train_file)
    sentences = np.array(data.sentences)
    labels = np.array(data.labels)
    
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=config.RANDOM_SEED)
    
    fold_results = []
    
    for fold, (train_idx, val_idx) in enumerate(kf.split(sentences)):
        logger.info(f"\n{'='*50}")
        logger.info(f"Fold {fold + 1}/{n_splits}")
        logger.info(f"{'='*50}")
        
        # Split data
        train_sents = sentences[train_idx].tolist()
        train_labels = labels[train_idx].tolist()
        val_sents = sentences[val_idx].tolist()
        val_labels = labels[val_idx].tolist()
        
        # Create datasets
        tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
        train_dataset = NERDataset(train_sents, train_labels, tokenizer, config.LABEL_TO_ID)
        val_dataset = NERDataset(val_sents, val_labels, tokenizer, config.LABEL_TO_ID)
        
        # Create dataloaders
        train_loader = DataLoader(train_dataset, batch_size=config.BATCH_SIZE, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=config.BATCH_SIZE)
        
        # Train
        finetuner = NERFineTuner()
        finetuner.train(train_loader, val_loader, epochs=config.EPOCHS,
                       output_dir=os.path.join(output_dir, f"fold_{fold}"))
        
        # Store results
        fold_results.append({
            'fold': fold,
            'model': finetuner,
            'val_size': len(val_sents)
        })
    
    logger.info("\nCross-validation completed!")
    return fold_results


if __name__ == "__main__":
    # Load data
    from src.data_utils import load_and_prepare_data
    
    train_loader, dev_loader, test_loader, tokenizer = load_and_prepare_data(
        config.TRAIN_FILE, config.DEV_FILE, config.TEST_FILE
    )
    
    # Fine-tune
    finetuner = NERFineTuner()
    finetuner.train(train_loader, dev_loader)
