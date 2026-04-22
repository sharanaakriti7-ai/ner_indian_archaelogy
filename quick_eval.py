#!/usr/bin/env python3
import torch
import config
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
from src.data_utils import CoNLLDataset, NERDataset
from model_crf import TransformerCRFModel
from evaluate import NEREvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_quick_evaluation():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info("Loading test data...")
    
    test_conll = CoNLLDataset(config.TEST_FILE)
    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
    
    test_dataset = NERDataset(
        test_conll.sentences, test_conll.labels,
        tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
    )
    test_loader = DataLoader(test_dataset, batch_size=config.BATCH_SIZE, shuffle=False)
    
    logger.info(f"Loading untrained/DAPT model from {config.MODEL_NAME} for demonstration...")
    model = TransformerCRFModel(
        model_name=config.MODEL_NAME,
        num_labels=config.NUM_LABELS,
        dropout=config.DROPOUT,
        use_self_attention=getattr(config, 'USE_SELF_ATTENTION', False)
    )
    model.to(device)
    model.eval()
    
    all_preds = []
    all_labels = []
    
    logger.info("Generating predictions...")
    with torch.no_grad():
        for i, batch in enumerate(test_loader):
            # Only run 3 batches to be extremely fast
            if i >= 3:
                break
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].cpu().numpy()
            
            _, predictions = model(input_ids, attention_mask)
            
            all_preds.extend(predictions)
            all_labels.extend(labels)
            
    evaluator = NEREvaluator(config.ID_TO_LABEL)
    metrics = evaluator.evaluate_predictions(all_preds, all_labels)
    evaluator.print_summary(metrics)

if __name__ == "__main__":
    run_quick_evaluation()
