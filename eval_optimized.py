#!/usr/bin/env python3
"""
OPTIMIZED Evaluation & Inference Script
Fast predictions on test set with optimized model
"""

import json
import logging
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer

import config_optimized as config
from src.data_utils import load_conll_data, NERDataset
from train_optimized import OptimizedNERModel

# ============================================================================
# SETUP LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# OPTIMIZED EVALUATOR
# ============================================================================

class FastNEREvaluator:
    """Fast evaluation with optimized model"""
    
    def __init__(self, model, tokenizer, device="cuda"):
        self.model = model.to(device)
        self.tokenizer = tokenizer
        self.device = device
        self.model.eval()
        
        logger.info(f"Evaluator initialized on device: {device}")
    
    def predict_batch(self, input_ids, attention_mask):
        """Get predictions for a batch"""
        with torch.no_grad():
            logits, _ = self.model(input_ids, attention_mask)
            predictions = torch.argmax(logits, dim=-1)
        
        return predictions.cpu().numpy()
    
    def evaluate_dataset(self, dataset, batch_size=32):
        """Evaluate on dataset"""
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0
        )
        
        all_predictions = []
        all_labels = []
        
        for batch in tqdm(loader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].cpu().numpy()
            
            predictions = self.predict_batch(input_ids, attention_mask)
            
            all_predictions.append(predictions)
            all_labels.append(labels)
        
        return all_predictions, all_labels
    
    def compute_metrics(self, predictions, labels):
        """Compute entity-level metrics"""
        # Flatten
        pred_flat = [p for batch in predictions for p in batch]
        label_flat = [l for batch in labels for l in batch]
        
        pred_flat = [item for sublist in pred_flat for item in sublist]
        label_flat = [item for sublist in label_flat for item in sublist]
        
        # Ignore padding (-100)
        mask = [l != -100 for l in label_flat]
        pred_flat = [p for p, m in zip(pred_flat, mask) if m]
        label_flat = [l for l, m in zip(label_flat, mask) if m]
        
        # Compute accuracy
        correct = sum(p == l for p, l in zip(pred_flat, label_flat))
        accuracy = correct / len(label_flat) if label_flat else 0
        
        return {
            "accuracy": accuracy,
            "total_tokens": len(label_flat),
            "correct_tokens": correct
        }
    
    def predict_text(self, text: str):
        """Predict entities in raw text"""
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=config.MAX_LENGTH,
            return_tensors="pt"
        )
        
        # Predict
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        predictions = self.predict_batch(input_ids, attention_mask)
        
        # Decode predictions
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        pred_labels = predictions[0]
        
        # Map predictions to labels
        results = []
        for token, pred_id in zip(tokens, pred_labels):
            if token.startswith("##"):
                continue  # Skip subword tokens
            
            label = config.ID_TO_LABEL.get(int(pred_id), "O")
            results.append({
                "token": token,
                "label": label
            })
        
        return results

# ============================================================================
# MAIN EVALUATION
# ============================================================================

def main():
    """Main evaluation function"""
    
    logger.info("=" * 80)
    logger.info("OPTIMIZED NER EVALUATION")
    logger.info("=" * 80)
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    # ========================================================================
    # 1. LOAD MODEL
    # ========================================================================
    
    logger.info("\nLoading model...")
    
    # Find latest model
    outputs_dir = config.OUTPUT_DIR
    model_dirs = sorted(outputs_dir.glob("optimized_*"))
    
    if not model_dirs:
        logger.error("No optimized models found. Run train_optimized.py first")
        return
    
    latest_model_dir = model_dirs[-1] / "final_model"
    logger.info(f"Loading from: {latest_model_dir}")
    
    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
    model = OptimizedNERModel(config.MODEL_NAME, config.NUM_LABELS, freeze_layers=0)
    
    # Load weights
    state_dict = torch.load(latest_model_dir / "pytorch_model.bin", map_location=device)
    model.load_state_dict(state_dict)
    logger.info("Model loaded successfully")
    
    # ========================================================================
    # 2. LOAD TEST DATA
    # ========================================================================
    
    logger.info("\nLoading test data...")
    test_sentences, test_labels = load_conll_data(config.DATA_DIR / "test.conll")
    
    test_dataset = NERDataset(
        test_sentences, test_labels,
        tokenizer, config.MAX_LENGTH,
        label_to_id=config.LABEL_TO_ID
    )
    logger.info(f"Test dataset: {len(test_dataset)} samples")
    
    # ========================================================================
    # 3. EVALUATE
    # ========================================================================
    
    logger.info("\nEvaluating on test set...")
    
    evaluator = FastNEREvaluator(model, tokenizer, device=device)
    predictions, labels = evaluator.evaluate_dataset(test_dataset)
    
    metrics = evaluator.compute_metrics(predictions, labels)
    
    # ========================================================================
    # 4. DISPLAY RESULTS
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Correct tokens: {metrics['correct_tokens']} / {metrics['total_tokens']}")
    
    # Save results
    results_file = latest_model_dir.parent / "eval_results.json"
    with open(results_file, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Results saved to {results_file}")
    
    # ========================================================================
    # 5. EXAMPLE PREDICTIONS
    # ========================================================================
    
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE PREDICTIONS")
    logger.info("=" * 80)
    
    test_texts = [
        "Harappa is an ancient city in India.",
        "The pottery shows Vedic period characteristics.",
        "Mauryan artifacts were found at Dholavira."
    ]
    
    for text in test_texts:
        logger.info(f"\nText: {text}")
        predictions = evaluator.predict_text(text)
        logger.info("Entities:")
        for item in predictions:
            if item['label'] != 'O':
                logger.info(f"  {item['token']:15} -> {item['label']}")

if __name__ == "__main__":
    main()
