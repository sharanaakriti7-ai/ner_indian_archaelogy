#!/usr/bin/env python3
"""
Cross-Validation Framework for NER
Implements k-fold cross-validation with proper data splitting
"""

import torch
import numpy as np
import logging
from typing import List, Tuple, Dict, Optional
from sklearn.model_selection import KFold
from torch.utils.data import Subset, DataLoader
import os
from pathlib import Path

logger = logging.getLogger(__name__)

from train import NERTrainer
from model_crf import TransformerCRFModel
from evaluate import NEREvaluator


class CrossValidator:
    """K-Fold Cross-Validation for NER"""
    
    def __init__(self, n_splits: int = 5, random_state: int = 42):
        self.n_splits = n_splits
        self.random_state = random_state
        self.results = []
    
    def cross_validate(self, dataset, train_config: Dict,
                      device: str = 'cpu',
                      output_dir: str = 'outputs/cv') -> Dict:
        """
        Perform cross-validation
        
        Args:
            dataset: Full dataset
            train_config: Training configuration
            device: Device to use
            output_dir: Output directory
        """
        
        kfold = KFold(n_splits=self.n_splits, shuffle=True, 
                     random_state=self.random_state)
        
        fold_results = []
        all_val_metrics = []
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Starting {self.n_splits}-Fold Cross-Validation")
        logger.info(f"{'='*70}\n")
        
        # Create indices
        indices = np.arange(len(dataset))
        
        for fold_idx, (train_indices, val_indices) in enumerate(kfold.split(indices)):
            logger.info(f"\n{'='*70}")
            logger.info(f"Fold {fold_idx + 1}/{self.n_splits}")
            logger.info(f"{'='*70}")
            
            # Create subsets
            train_subset = Subset(dataset, train_indices.tolist())
            val_subset = Subset(dataset, val_indices.tolist())
            
            logger.info(f"Train size: {len(train_subset)}")
            logger.info(f"Val size: {len(val_subset)}")
            
            # Create model
            model = TransformerCRFModel(
                model_name=train_config.get('model_name', 'bert-base-multilingual-cased'),
                num_labels=train_config.get('num_labels', 11),
                dropout=train_config.get('dropout', 0.1),
                use_self_attention=train_config.get('use_self_attention', False)
            )
            
            # Create trainer
            fold_output_dir = os.path.join(output_dir, f'fold_{fold_idx + 1}')
            trainer = NERTrainer(
                model=model,
                train_dataset=train_subset,
                dev_dataset=val_subset,
                batch_size=train_config.get('batch_size', 16),
                learning_rate=train_config.get('learning_rate', 2e-5),
                weight_decay=train_config.get('weight_decay', 0.01),
                gradient_clip=train_config.get('gradient_clip', 1.0),
                dropout=train_config.get('dropout', 0.1),
                device=device,
                output_dir=fold_output_dir
            )
            
            # Train
            history = trainer.train(
                epochs=train_config.get('epochs', 30),
                early_stopping_patience=train_config.get('early_stopping_patience', 3)
            )
            
            fold_results.append({
                'fold': fold_idx + 1,
                'history': history,
                'best_val_loss': trainer.best_val_loss
            })
            
            all_val_metrics.append(trainer.best_val_loss)
        
        # Compute statistics
        stats = self._compute_cv_statistics(fold_results, all_val_metrics)
        
        return {
            'fold_results': fold_results,
            'statistics': stats,
            'n_splits': self.n_splits
        }
    
    def _compute_cv_statistics(self, fold_results: List[Dict],
                              all_val_metrics: List[float]) -> Dict:
        """Compute cross-validation statistics"""
        
        stats = {
            'mean_val_loss': float(np.mean(all_val_metrics)),
            'std_val_loss': float(np.std(all_val_metrics)),
            'min_val_loss': float(np.min(all_val_metrics)),
            'max_val_loss': float(np.max(all_val_metrics)),
            'per_fold': []
        }
        
        for result in fold_results:
            stats['per_fold'].append({
                'fold': result['fold'],
                'best_val_loss': result['best_val_loss']
            })
        
        logger.info(f"\n{'='*70}")
        logger.info("CROSS-VALIDATION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Mean Val Loss: {stats['mean_val_loss']:.4f} ± {stats['std_val_loss']:.4f}")
        logger.info(f"Min Val Loss:  {stats['min_val_loss']:.4f}")
        logger.info(f"Max Val Loss:  {stats['max_val_loss']:.4f}")
        logger.info(f"\nPer-Fold Results:")
        for fold_stat in stats['per_fold']:
            logger.info(f"  Fold {fold_stat['fold']}: {fold_stat['best_val_loss']:.4f}")
        
        return stats
