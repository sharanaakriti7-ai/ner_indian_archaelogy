#!/usr/bin/env python3
"""
Utility functions for NER pipeline
Includes seeding, plotting, and general helpers
"""

import os
import sys
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def set_seed(seed: int) -> None:
    """Set random seed for reproducibility"""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    logger.info(f"✓ Random seed set to {seed}")


def create_output_dir(output_dir: str, experiment_name: str = None) -> str:
    """Create output directory with timestamp"""
    if experiment_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"experiment_{timestamp}"
    
    full_path = os.path.join(output_dir, experiment_name)
    Path(full_path).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"✓ Output directory created: {full_path}")
    return full_path


def setup_logging(log_file: str) -> None:
    """Setup logging to file and console"""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)


def plot_training_curves(train_losses: List[float], val_losses: List[float],
                        train_f1s: List[float], val_f1s: List[float],
                        output_dir: str) -> None:
    """Plot training and validation curves"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss curve
    axes[0].plot(train_losses, label='Train Loss', marker='o')
    axes[0].plot(val_losses, label='Validation Loss', marker='s')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training vs Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # F1 curve
    axes[1].plot(train_f1s, label='Train F1', marker='o')
    axes[1].plot(val_f1s, label='Validation F1', marker='s')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('F1 Score')
    axes[1].set_title('Training vs Validation F1')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'training_curves.png')
    plt.savefig(plot_path, dpi=150)
    logger.info(f"✓ Training curves saved to {plot_path}")
    plt.close()


def plot_confusion_matrix(confusion_matrix: np.ndarray, id_to_label: Dict[int, str],
                         output_dir: str) -> None:
    """Plot confusion matrix"""
    plt.figure(figsize=(12, 10))
    
    # Create labels
    labels = [id_to_label.get(i, f"Label_{i}") for i in range(len(confusion_matrix))]
    
    # Plot
    sns.heatmap(confusion_matrix, annot=True, fmt='d', cmap='Blues',
                xticklabels=labels, yticklabels=labels, cbar=True)
    
    plt.title('Confusion Matrix - NER Predictions')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, 'confusion_matrix.png')
    plt.savefig(plot_path, dpi=150)
    logger.info(f"✓ Confusion matrix saved to {plot_path}")
    plt.close()


def plot_per_entity_f1(entity_metrics: Dict[str, Dict[str, float]],
                      output_dir: str) -> None:
    """Plot per-entity F1 scores"""
    entities = list(entity_metrics.keys())
    f1_scores = [entity_metrics[e]['f1'] for e in entities]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(entities, f1_scores, color='steelblue', alpha=0.8)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}', ha='center', va='bottom')
    
    plt.ylabel('F1 Score')
    plt.title('Per-Entity F1 Scores')
    plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, 'per_entity_f1.png')
    plt.savefig(plot_path, dpi=150)
    logger.info(f"✓ Per-entity F1 plot saved to {plot_path}")
    plt.close()


def save_results(results: Dict[str, Any], output_dir: str, filename: str = 'results.json') -> None:
    """Save results to JSON file"""
    results_path = os.path.join(output_dir, filename)
    
    # Convert numpy types to Python types for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_to_serializable(item) for item in obj]
        return obj
    
    serializable_results = convert_to_serializable(results)
    
    with open(results_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"✓ Results saved to {results_path}")


def save_config(config_dict: Dict[str, Any], output_dir: str) -> None:
    """Save configuration to JSON file"""
    config_path = os.path.join(output_dir, 'config.json')
    
    with open(config_path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    logger.info(f"✓ Config saved to {config_path}")


def print_summary(summary: Dict[str, Any]) -> None:
    """Print results summary"""
    print("\n" + "="*80)
    print("FINAL RESULTS SUMMARY")
    print("="*80)
    
    for key, value in summary.items():
        if isinstance(value, dict):
            print(f"\n{key}:")
            for k, v in value.items():
                if isinstance(v, float):
                    print(f"  {k}: {v:.4f}")
                else:
                    print(f"  {k}: {v}")
        elif isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    print("="*80 + "\n")


def get_device() -> str:
    """Get device (cuda or cpu)"""
    if torch.cuda.is_available():
        device = 'cuda'
        logger.info(f"✓ Using CUDA: {torch.cuda.get_device_name(0)}")
    else:
        device = 'cpu'
        logger.info(f"✓ Using CPU")
    return device


def count_parameters(model) -> int:
    """Count total trainable parameters"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def freeze_embeddings(model) -> None:
    """Freeze embedding layer"""
    try:
        for param in model.transformer.embeddings.parameters():
            param.requires_grad = False
        logger.info("✓ Embeddings frozen")
    except:
        logger.warning("Could not freeze embeddings")


def unfreeze_embeddings(model) -> None:
    """Unfreeze embedding layer"""
    try:
        for param in model.transformer.embeddings.parameters():
            param.requires_grad = True
        logger.info("✓ Embeddings unfrozen")
    except:
        logger.warning("Could not unfreeze embeddings")


class EarlyStopping:
    """Early stopping handler"""
    
    def __init__(self, patience: int = 3, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score = None
        self.early_stop = False
    
    def __call__(self, val_metric: float) -> bool:
        if self.best_score is None:
            self.best_score = val_metric
            return False
        
        if val_metric > self.best_score - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                logger.info(f"⚠ Early stopping triggered after {self.patience} patience steps")
                return True
        else:
            self.best_score = val_metric
            self.counter = 0
        
        return False


class PercentageScheduler:
    """Learning rate scheduler with warmup"""
    
    def __init__(self, optimizer, total_steps: int, warmup_steps: int):
        self.optimizer = optimizer
        self.total_steps = total_steps
        self.warmup_steps = warmup_steps
        self.current_step = 0
        
        # Initialize initial_lr in all param groups
        for param_group in self.optimizer.param_groups:
            if 'initial_lr' not in param_group:
                param_group['initial_lr'] = param_group['lr']
    
    def step(self) -> None:
        """Update learning rate"""
        if self.current_step < self.warmup_steps:
            # Linear warmup
            lr_scale = float(self.current_step) / float(max(1, self.warmup_steps))
        else:
            # Linear decay
            progress = float(self.current_step - self.warmup_steps) / float(
                max(1, self.total_steps - self.warmup_steps)
            )
            lr_scale = max(0.0, 1.0 - progress)
        
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = param_group['initial_lr'] * lr_scale
        
        self.current_step += 1
