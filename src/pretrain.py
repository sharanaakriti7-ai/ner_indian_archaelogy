"""
Domain-Adaptive Pretraining using Masked Language Modeling (MLM)
Further pre-trains mBERT on Indian archaeology corpus
"""

import os
import logging
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import LinearLR
from transformers import AutoModelForMaskedLM, AutoTokenizer
from transformers import DataCollatorForLanguageModeling
from tqdm import tqdm
import config
from src.data_utils import load_pretrain_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLMPretrainer:
    """Domain-Adaptive Pretraining with Masked Language Modeling"""
    
    def __init__(self, model_name: str = config.MODEL_NAME, 
                 learning_rate: float = config.PRETRAIN_LEARNING_RATE,
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        self.model_name = model_name
        self.learning_rate = learning_rate
        self.device = device
        
        # Load model and tokenizer
        logger.info(f"Loading model from {model_name}...")
        self.model = AutoModelForMaskedLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model.to(device)
        
        logger.info(f"Model loaded. Total parameters: {self.model.num_parameters():,}")
    
    def train(self, train_loader, epochs: int = config.PRETRAIN_EPOCHS,
              eval_loader=None, output_dir: str = config.MODEL_DIR):
        """
        Domain-adaptive pretraining on archaeology corpus
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
        
        best_loss = float('inf')
        
        for epoch in range(epochs):
            logger.info(f"\nEpoch {epoch + 1}/{epochs}")
            
            # Training phase
            train_loss = self._train_epoch(train_loader, optimizer, scheduler)
            
            logger.info(f"Training Loss: {train_loss:.4f}")
            
            # Evaluation phase
            if eval_loader:
                eval_loss = self._evaluate(eval_loader)
                logger.info(f"Evaluation Loss: {eval_loss:.4f}")
                
                # Save best model
                if eval_loss < best_loss:
                    best_loss = eval_loss
                    self._save_model(os.path.join(output_dir, f"{config.DOMAIN_MODEL_NAME}_best"))
                    logger.info(f"Saved best model with eval loss: {eval_loss:.4f}")
            else:
                self._save_model(os.path.join(output_dir, f"{config.DOMAIN_MODEL_NAME}_epoch_{epoch}"))
        
        # Save final model
        final_model_path = os.path.join(output_dir, config.DOMAIN_MODEL_NAME)
        self._save_model(final_model_path)
        logger.info(f"Pretraining complete. Model saved to {final_model_path}")
        
        return self.model
    
    def _train_epoch(self, train_loader, optimizer, scheduler):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        
        progress_bar = tqdm(train_loader, desc="Training")
        for batch_idx, batch in enumerate(progress_bar):
            optimizer.zero_grad()
            
            # Move to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            
            # Forward pass with MLM (model automatically masks 15% of tokens)
            # Add random masking
            inputs_embeds = None
            labels = input_ids.clone()
            
            # Mask tokens for MLM
            mask_prob = config.MLM_PROBABILITY
            rand = torch.rand(input_ids.shape)
            mask_arr = rand < mask_prob
            
            input_ids[mask_arr] = self.tokenizer.mask_token_id
            
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
            
            if (batch_idx + 1) % config.SAVE_CHECKPOINT_EVERY == 0:
                logger.info(f"Checkpoint at batch {batch_idx + 1}: Loss = {loss.item():.4f}")
        
        return total_loss / len(train_loader)
    
    def _evaluate(self, eval_loader):
        """Evaluate on validation set"""
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            progress_bar = tqdm(eval_loader, desc="Evaluating")
            for batch in progress_bar:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                
                # Mask tokens for MLM
                mask_prob = config.MLM_PROBABILITY
                rand = torch.rand(input_ids.shape)
                mask_arr = rand < mask_prob
                
                labels = input_ids.clone()
                input_ids[mask_arr] = self.tokenizer.mask_token_id
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                total_loss += loss.item()
                progress_bar.set_postfix({'loss': loss.item()})
        
        return total_loss / len(eval_loader)
    
    def _save_model(self, path: str):
        """Save model and tokenizer"""
        os.makedirs(path, exist_ok=True)
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load pretrained model"""
        logger.info(f"Loading pretrained model from {path}...")
        self.model = AutoModelForMaskedLM.from_pretrained(path)
        self.model.to(self.device)
        logger.info(f"Model loaded successfully")


def pretrain_domain_bert(pretrain_corpus: str = config.PRETRAIN_CORPUS_FILE,
                        epochs: int = config.PRETRAIN_EPOCHS,
                        batch_size: int = config.PRETRAIN_BATCH_SIZE,
                        output_dir: str = config.MODEL_DIR):
    """
    Main function to run domain-adaptive pretraining
    """
    logger.info("=" * 50)
    logger.info("Domain-Adaptive BERT Pretraining")
    logger.info("=" * 50)
    
    # Load data
    logger.info("Loading pretraining corpus...")
    train_loader, tokenizer = load_pretrain_data(
        pretrain_corpus,
        batch_size=batch_size
    )
    
    logger.info(f"Loaded {len(train_loader)} batches for pretraining")
    
    # Initialize pretrainer
    pretrainer = MLMPretrainer()
    
    # Train
    pretrainer.train(
        train_loader,
        epochs=epochs,
        eval_loader=None,  # Can add eval if you split the corpus
        output_dir=output_dir
    )
    
    logger.info("Pretraining completed successfully!")
    
    return pretrainer.model


if __name__ == "__main__":
    pretrain_domain_bert()
