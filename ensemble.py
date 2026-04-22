#!/usr/bin/env python3
"""
Ensemble Methods for NER
Combines multiple models for improved predictions
"""

import torch
import torch.nn as nn
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from torch.utils.data import DataLoader
from tqdm import tqdm

logger = logging.getLogger(__name__)

from model_crf import TransformerCRFModel


class NERensemble:
    """Ensemble of NER Models"""
    
    def __init__(self, models: List[TransformerCRFModel], 
                 weights: Optional[List[float]] = None,
                 device: str = 'cpu'):
        """
        Args:
            models: List of trained models
            weights: Weights for voting (default: equal weights)
            device: Device to use
        """
        self.models = models
        self.device = device
        
        if weights is None:
            weights = [1.0 / len(models)] * len(models)
        
        self.weights = np.array(weights) / np.sum(weights)
        
        logger.info(f"✓ Ensemble created with {len(models)} models")
        logger.info(f"  Weights: {self.weights}")
    
    def predict_ensemble(self, input_ids: torch.Tensor, 
                        attention_mask: torch.Tensor) -> List[List[int]]:
        """
        Ensemble prediction using majority voting
        
        Args:
            input_ids: (batch_size, seq_len)
            attention_mask: (batch_size, seq_len)
        
        Returns:
            Ensemble predictions
        """
        
        all_predictions = []
        
        # Get predictions from all models
        for model in self.models:
            model.eval()
            with torch.no_grad():
                _, predictions = model(input_ids, attention_mask)
                all_predictions.append(predictions)
        
        # Ensemble by majority voting
        batch_size = input_ids.shape[0]
        seq_len = input_ids.shape[1]
        
        ensemble_preds = []
        
        for batch_idx in range(batch_size):
            ensemble_seq = []
            for token_idx in range(seq_len):
                # Get predictions from all models for this token
                token_preds = [pred[batch_idx][token_idx] 
                              for pred in all_predictions]
                
                # Majority voting
                pred_counts = np.bincount(token_preds, 
                                         weights=self.weights)
                best_pred = np.argmax(pred_counts)
                ensemble_seq.append(best_pred)
            
            ensemble_preds.append(ensemble_seq)
        
        return ensemble_preds
    
    def predict_weighted(self, input_ids: torch.Tensor,
                        attention_mask: torch.Tensor,
                        num_labels: int) -> np.ndarray:
        """
        Weighted ensemble prediction using softmax outputs
        
        Args:
            input_ids: (batch_size, seq_len)
            attention_mask: (batch_size, seq_len)
            num_labels: Number of label classes
        
        Returns:
            Ensemble logits (batch_size, seq_len, num_labels)
        """
        
        all_logits = []
        
        # Get logits from all models
        for model, weight in zip(self.models, self.weights):
            model.eval()
            with torch.no_grad():
                emissions, _ = model(input_ids, attention_mask)
                all_logits.append(emissions * weight)
        
        # Average logits
        ensemble_logits = torch.mean(torch.stack(all_logits), dim=0)
        
        return ensemble_logits
    
    def predict_batch(self, data_loader: DataLoader, device: str = 'cpu',
                     use_weighted: bool = False) -> Tuple[List, List]:
        """
        Predict on entire dataset
        
        Args:
            data_loader: Data loader
            device: Device to use
            use_weighted: Use weighted ensemble or majority voting
        
        Returns:
            predictions, true_labels
        """
        
        all_predictions = []
        all_labels = []
        
        logger.info("Ensemble prediction...")
        for batch in tqdm(data_loader):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].cpu().numpy()
            
            if use_weighted:
                logits = self.predict_weighted(input_ids, attention_mask,
                                             self.models[0].num_labels)
                predictions = torch.argmax(logits, dim=-1).cpu().numpy()
            else:
                predictions = self.predict_ensemble(input_ids, attention_mask)
                predictions = np.array(predictions)
            
            all_predictions.extend(predictions)
            all_labels.extend(labels)
        
        return all_predictions, all_labels


class StackingEnsemble:
    """Stacking Ensemble for NER"""
    
    def __init__(self, base_models: List[TransformerCRFModel],
                 meta_model: nn.Module,
                 device: str = 'cpu'):
        """
        Args:
            base_models: List of base models
            meta_model: Meta-learner model
            device: Device to use
        """
        self.base_models = base_models
        self.meta_model = meta_model.to(device)
        self.device = device
        
        logger.info(f"✓ Stacking ensemble created")
        logger.info(f"  Base models: {len(base_models)}")
    
    def get_meta_features(self, input_ids: torch.Tensor,
                         attention_mask: torch.Tensor,
                         num_labels: int) -> torch.Tensor:
        """
        Generate meta-features from base models
        
        Args:
            input_ids: (batch_size, seq_len)
            attention_mask: (batch_size, seq_len)
            num_labels: Number of label classes
        
        Returns:
            Meta-features (batch_size, seq_len, base_models * num_labels)
        """
        
        batch_size, seq_len = input_ids.shape
        meta_features = []
        
        # Get logits from all base models
        for base_model in self.base_models:
            base_model.eval()
            with torch.no_grad():
                emissions, _ = base_model(input_ids, attention_mask)
                # Convert to probabilities
                probs = torch.softmax(emissions, dim=-1)
                meta_features.append(probs)
        
        # Concatenate features
        meta_features = torch.cat(meta_features, dim=-1)
        
        return meta_features
    
    def predict_stacking(self, input_ids: torch.Tensor,
                        attention_mask: torch.Tensor,
                        num_labels: int) -> torch.Tensor:
        """
        Stacking prediction
        
        Args:
            input_ids: (batch_size, seq_len)
            attention_mask: (batch_size, seq_len)
            num_labels: Number of label classes
        
        Returns:
            Predictions (batch_size, seq_len)
        """
        
        meta_features = self.get_meta_features(input_ids, attention_mask,
                                              num_labels)
        
        self.meta_model.eval()
        with torch.no_grad():
            meta_logits = self.meta_model(meta_features)
            predictions = torch.argmax(meta_logits, dim=-1)
        
        return predictions


class HardVotingEnsemble:
    """Hard Voting Ensemble (Majority Vote)"""
    
    def __init__(self, models: List[TransformerCRFModel],
                 device: str = 'cpu'):
        self.models = models
        self.device = device
    
    def predict(self, input_ids: torch.Tensor,
               attention_mask: torch.Tensor) -> List[List[int]]:
        """
        Majority voting
        """
        
        all_predictions = []
        
        # Get predictions from all models
        for model in self.models:
            model.eval()
            with torch.no_grad():
                _, predictions = model(input_ids, attention_mask)
                all_predictions.append(predictions)
        
        # Majority voting
        batch_size = input_ids.shape[0]
        seq_len = input_ids.shape[1]
        
        ensemble_preds = []
        
        for batch_idx in range(batch_size):
            ensemble_seq = []
            for token_idx in range(seq_len):
                # Get predictions from all models for this token
                token_preds = [pred[batch_idx][token_idx]
                              for pred in all_predictions]
                
                # Majority vote
                from collections import Counter
                vote_counts = Counter(token_preds)
                best_pred = vote_counts.most_common(1)[0][0]
                ensemble_seq.append(best_pred)
            
            ensemble_preds.append(ensemble_seq)
        
        return ensemble_preds


class SoftVotingEnsemble:
    """Soft Voting Ensemble (Average Probabilities)"""
    
    def __init__(self, models: List[TransformerCRFModel],
                 device: str = 'cpu'):
        self.models = models
        self.device = device
    
    def predict(self, input_ids: torch.Tensor,
               attention_mask: torch.Tensor) -> np.ndarray:
        """
        Soft voting - average probabilities
        """
        
        all_logits = []
        
        # Get logits from all models
        for model in self.models:
            model.eval()
            with torch.no_grad():
                emissions, _ = model(input_ids, attention_mask)
                all_logits.append(emissions)
        
        # Average logits
        avg_logits = torch.mean(torch.stack(all_logits), dim=0)
        
        # Get predictions
        predictions = torch.argmax(avg_logits, dim=-1)
        
        return predictions.cpu().numpy()
