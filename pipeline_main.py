#!/usr/bin/env python3
"""
Main Orchestration Script for Complete NER Pipeline
Coordinates all modules for end-to-end training and evaluation
"""

import os
import sys
import torch
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import json
from torch.utils.data import DataLoader, ConcatDataset

# Import all modules
import config
from utils import (
    set_seed, create_output_dir, setup_logging, 
    get_device, print_summary, plot_training_curves,
    plot_per_entity_f1, save_results, save_config
)
from model_crf import TransformerCRFModel
from src.data_utils import CoNLLDataset, NERDataset
from augmentation import DataAugmenter
from gazetteer import ArchaeologyGazetteer, WeakSupervisionGenerator
from train import NERTrainer, MultiSeedTrainer
from evaluate import NEREvaluator
from cross_validation import CrossValidator
from ensemble import NERensemble, HardVotingEnsemble

logger = logging.getLogger(__name__)


class NERPipeline:
    """Complete NER Pipeline Orchestrator"""
    
    def __init__(self, output_dir: str = None, experiment_name: str = None):
        """Initialize pipeline"""
        
        # Create output directory
        if output_dir is None:
            output_dir = config.OUTPUT_DIR
        
        self.output_dir = create_output_dir(output_dir, experiment_name)
        
        # Setup logging
        setup_logging(os.path.join(self.output_dir, 'pipeline.log'))
        
        logger.info("="*80)
        logger.info("RESEARCH-GRADE NER PIPELINE FOR INDIAN ARCHAEOLOGY")
        logger.info("="*80)
        logger.info(f"Output directory: {self.output_dir}")
        
        # Initialize device
        self.device = get_device()
        
        # Initialize results container
        self.results = {
            'config': self._get_config_dict(),
            'stages': {}
        }
    
    def _get_config_dict(self) -> Dict:
        """Get configuration dictionary"""
        return {
            'model_name': config.MODEL_NAME,
            'batch_size': config.BATCH_SIZE,
            'learning_rate': config.LEARNING_RATE,
            'epochs': config.EPOCHS,
            'dropout': config.DROPOUT,
            'weight_decay': config.WEIGHT_DECAY,
            'use_focal_loss': config.USE_FOCAL_LOSS,
            'early_stopping_patience': config.EARLY_STOPPING_PATIENCE,
        }
    
    def load_data(self) -> Tuple:
        """Load and prepare data"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 1: DATA LOADING & PREPROCESSING")
        logger.info("="*80)
        
        # Load datasets
        logger.info("Loading train data...")
        train_conll = CoNLLDataset(config.TRAIN_FILE)
        
        logger.info("Loading dev data...")
        dev_conll = CoNLLDataset(config.DEV_FILE)
        
        logger.info("Loading test data...")
        test_conll = CoNLLDataset(config.TEST_FILE)
        
        # Convert to NER datasets
        logger.info("Tokenizing and aligning labels...")
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
        
        train_dataset = NERDataset(
            train_conll.sentences, train_conll.labels,
            tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
        )
        
        dev_dataset = NERDataset(
            dev_conll.sentences, dev_conll.labels,
            tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
        )
        
        test_dataset = NERDataset(
            test_conll.sentences, test_conll.labels,
            tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
        )
        
        logger.info(f"✓ Data loaded:")
        logger.info(f"  Train: {len(train_dataset)} samples")
        logger.info(f"  Dev:   {len(dev_dataset)} samples")
        logger.info(f"  Test:  {len(test_dataset)} samples")
        
        self.results['stages']['data_loading'] = {
            'train_size': len(train_dataset),
            'dev_size': len(dev_dataset),
            'test_size': len(test_dataset)
        }
        
        return train_dataset, dev_dataset, test_dataset
    
    def apply_data_augmentation(self, train_dataset) -> torch.utils.data.Dataset:
        """Apply data augmentation"""
        if not config.USE_DATA_AUGMENTATION:
            logger.info("Data augmentation disabled")
            return train_dataset
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 2: DATA AUGMENTATION")
        logger.info("="*80)
        
        logger.info(f"Augmentation factor: {config.AUGMENTATION_FACTOR}x")
        
        # Create augmented dataset
        augmenter = DataAugmenter(seed=config.RANDOM_SEED)
        
        # For simplicity, duplicate dataset for now
        # In production, would apply various augmentation techniques
        augmented_data = ConcatDataset([train_dataset] * config.AUGMENTATION_FACTOR)
        
        logger.info(f"✓ Augmented dataset size: {len(augmented_data)}")
        
        self.results['stages']['augmentation'] = {
            'original_size': len(train_dataset),
            'augmented_size': len(augmented_data),
            'factor': config.AUGMENTATION_FACTOR
        }
        
        return augmented_data
    
    def train_single_model(self, train_dataset, dev_dataset) -> TransformerCRFModel:
        """Train single model"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 3: SINGLE MODEL TRAINING")
        logger.info("="*80)
        
        # Set seed
        set_seed(config.RANDOM_SEED)
        
        # Create model
        model = TransformerCRFModel(
            model_name=config.MODEL_NAME,
            num_labels=config.NUM_LABELS,
            dropout=config.DROPOUT,
            use_self_attention=getattr(config, 'USE_SELF_ATTENTION', False)
        )
        
        # Create trainer
        trainer = NERTrainer(
            model=model,
            train_dataset=train_dataset,
            dev_dataset=dev_dataset,
            batch_size=config.BATCH_SIZE,
            learning_rate=config.LEARNING_RATE,
            weight_decay=config.WEIGHT_DECAY,
            gradient_clip=config.MAX_GRAD_NORM,
            dropout=config.DROPOUT,
            use_focal_loss=config.USE_FOCAL_LOSS,
            device=self.device,
            output_dir=os.path.join(self.output_dir, 'single_model')
        )
        
        # Train
        history = trainer.train(
            epochs=config.EPOCHS,
            early_stopping_patience=config.EARLY_STOPPING_PATIENCE,
            warmup_steps=config.WARMUP_STEPS
        )
        
        self.results['stages']['single_training'] = {
            'final_train_loss': trainer.train_losses[-1] if trainer.train_losses else None,
            'final_val_loss': trainer.val_losses[-1] if trainer.val_losses else None,
            'best_val_loss': trainer.best_val_loss,
            'epochs_trained': len(trainer.train_losses)
        }
        
        return model
    
    def train_multi_seed(self, train_dataset, dev_dataset) -> Dict:
        """Train with multiple seeds for stability"""
        if not config.USE_MULTI_SEED_TRAINING:
            logger.info("Multi-seed training disabled")
            return {}
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 4: MULTI-SEED TRAINING (Stability Analysis)")
        logger.info("="*80)
        
        multi_trainer = MultiSeedTrainer(
            model_name=config.MODEL_NAME,
            num_labels=config.NUM_LABELS,
            num_seeds=config.NUM_SEEDS,
            device=self.device,
            output_dir=os.path.join(self.output_dir, 'multi_seed'),
            use_self_attention=getattr(config, 'USE_SELF_ATTENTION', False)
        )
        
        results = multi_trainer.train_all_seeds(
            train_dataset=train_dataset,
            dev_dataset=dev_dataset,
            test_dataset=None,
            epochs=config.EPOCHS,
            batch_size=config.BATCH_SIZE,
            learning_rate=config.LEARNING_RATE
        )
        
        self.results['stages']['multi_seed_training'] = {
            'num_seeds': config.NUM_SEEDS,
            'statistics': results['statistics']
        }
        
        return results
    
    def cross_validation(self, combined_dataset) -> Dict:
        """Perform cross-validation"""
        if not config.USE_CROSS_VALIDATION:
            logger.info("Cross-validation disabled")
            return {}
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 5: CROSS-VALIDATION")
        logger.info("="*80)
        
        cv = CrossValidator(n_splits=config.NUM_FOLDS, 
                           random_state=config.CROSS_VALIDATION_RANDOM_STATE)
        
        train_config = {
            'model_name': config.MODEL_NAME,
            'num_labels': config.NUM_LABELS,
            'batch_size': config.BATCH_SIZE,
            'learning_rate': config.LEARNING_RATE,
            'weight_decay': config.WEIGHT_DECAY,
            'gradient_clip': config.MAX_GRAD_NORM,
            'dropout': config.DROPOUT,
            'epochs': config.EPOCHS,
            'early_stopping_patience': config.EARLY_STOPPING_PATIENCE,
            'use_self_attention': getattr(config, 'USE_SELF_ATTENTION', False)
        }
        
        cv_results = cv.cross_validate(
            combined_dataset,
            train_config,
            device=self.device,
            output_dir=os.path.join(self.output_dir, 'cross_validation')
        )
        
        self.results['stages']['cross_validation'] = {
            'n_splits': config.NUM_FOLDS,
            'statistics': cv_results['statistics']
        }
        
        return cv_results
    
    def evaluate_model(self, model, test_dataset, model_name: str = 'final_model') -> Dict:
        """Evaluate model on test set"""
        logger.info("\n" + "="*80)
        logger.info(f"STAGE 6: EVALUATION ({model_name})")
        logger.info("="*80)
        
        # Create data loader
        test_loader = DataLoader(
            test_dataset,
            batch_size=config.BATCH_SIZE,
            shuffle=False
        )
        
        # Generate predictions
        model.eval()
        all_predictions = []
        all_labels = []
        
        logger.info("Generating predictions...")
        with torch.no_grad():
            for batch in test_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].cpu().numpy()
                
                _, predictions = model(input_ids, attention_mask)
                
                all_predictions.extend(predictions)
                all_labels.extend(labels)
        
        # Evaluate
        evaluator = NEREvaluator(config.ID_TO_LABEL)
        metrics = evaluator.evaluate_predictions(
            all_predictions, all_labels, config.ID_TO_LABEL
        )
        
        evaluator.print_summary(metrics)
        evaluator.print_error_analysis()
        
        self.results['stages']['evaluation'] = {
            'model': model_name,
            'metrics': metrics
        }
        
        return metrics
    
    def run_full_pipeline(self) -> Dict:
        """Run complete pipeline"""
        
        try:
            # Stage 1: Load data
            train_data, dev_data, test_data = self.load_data()
            
            # Stage 2: Data augmentation
            aug_train_data = self.apply_data_augmentation(train_data)
            
            # Stage 3: Train single model
            model = self.train_single_model(aug_train_data, dev_data)
            
            # Stage 4: Multi-seed training
            multi_seed_results = self.train_multi_seed(aug_train_data, dev_data)
            
            # Stage 5: Cross-validation
            combined_data = ConcatDataset([train_data, dev_data])
            cv_results = self.cross_validation(combined_data)
            
            # Stage 6: Evaluation
            test_metrics = self.evaluate_model(model, test_data)
            
            # Save results
            self._save_pipeline_results()
            
            # Print summary
            self._print_pipeline_summary()
            
            return self.results
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            raise
    
    def _save_pipeline_results(self) -> None:
        """Save all pipeline results"""
        logger.info("\n" + "="*80)
        logger.info("SAVING RESULTS")
        logger.info("="*80)
        
        save_config(self.results['config'],
                   os.path.join(self.output_dir, 'config.json'))
        
        save_results(self.results,
                    os.path.join(self.output_dir, 'pipeline_results.json'))
        
        logger.info(f"✓ All results saved to {self.output_dir}")
    
    def _print_pipeline_summary(self) -> None:
        """Print pipeline summary"""
        logger.info("\n" + "="*80)
        logger.info("PIPELINE SUMMARY")
        logger.info("="*80)
        
        logger.info("\nCompleted Stages:")
        for stage, result in self.results['stages'].items():
            logger.info(f"  ✓ {stage}")
        
        logger.info("\nKey Results:")
        if 'evaluation' in self.results['stages']:
            metrics = self.results['stages']['evaluation']['metrics']
            logger.info(f"  F1 Score:   {metrics.get('f1', 0):.4f}")
            logger.info(f"  Precision:  {metrics.get('precision', 0):.4f}")
            logger.info(f"  Recall:     {metrics.get('recall', 0):.4f}")


def main():
    """Main entry point"""
    
    # Set seeds
    set_seed(config.RANDOM_SEED)
    
    # Create and run pipeline
    pipeline = NERPipeline()
    results = pipeline.run_full_pipeline()
    
    logger.info("\n" + "="*80)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
