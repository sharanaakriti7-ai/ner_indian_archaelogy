#!/usr/bin/env python3
import os
import torch
import json
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
from model_crf import TransformerCRFModel
import config
from src.data_utils import CoNLLDataset, NERDataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_error_report():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 1. Load data
    logger.info("Loading dev data for error analysis...")
    dev_conll = CoNLLDataset(config.DEV_FILE)
    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
    dev_dataset = NERDataset(
        dev_conll.sentences, dev_conll.labels,
        tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
    )
    dev_loader = DataLoader(dev_dataset, batch_size=config.BATCH_SIZE, shuffle=False)
    
    # 2. Load model (use the single_model from pipeline)
    model_path = os.path.join(config.OUTPUT_DIR, 'single_model', 'best_model', 'pytorch_model.bin')
    if not os.path.exists(model_path):
        model_path = os.path.join(config.OUTPUT_DIR, 'single_model', 'final_model', 'pytorch_model.bin')
        
    if not os.path.exists(model_path):
        logger.warning(f"Model not found at {model_path}. Loading from {config.MODEL_NAME}")
        model_path = None
        
    logger.info(f"Loading model from {model_path}...")
    model = TransformerCRFModel(
        model_name=config.MODEL_NAME,
        num_labels=config.NUM_LABELS,
        dropout=config.DROPOUT,
        use_self_attention=getattr(config, 'USE_SELF_ATTENTION', False)
    )
    if model_path is not None:
        model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in dev_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].cpu().numpy()
            
            _, predictions = model(input_ids, attention_mask)
            
            all_preds.extend(predictions)
            all_labels.extend(labels)
            
    # 3. Analyze errors
    art_mat_confusion = []
    boundary_errors = []
    numeric_errors = []
    
    for seq_idx, (true_seq, pred_seq) in enumerate(zip(all_labels, all_preds)):
        sentence = dev_conll.sentences[seq_idx]
        word_idx = 0
        
        # This is a simplified token mapping since subwords are complex,
        # but we iterate over true tags to find mismatches
        for token_idx, (true_id, pred_id) in enumerate(zip(true_seq, pred_seq)):
            if true_id == -100:
                continue
                
            true_tag = config.ID_TO_LABEL.get(true_id, 'O')
            pred_tag = config.ID_TO_LABEL.get(pred_id, 'O')
            
            if true_tag != pred_tag:
                word = sentence[min(word_idx, len(sentence)-1)] if len(sentence) > 0 else "<unk>"
                
                error_entry = {
                    'sentence': " ".join(sentence),
                    'word': word,
                    'true_tag': true_tag,
                    'pred_tag': pred_tag
                }
                
                # ART vs MAT
                if ('ART' in true_tag and 'MAT' in pred_tag) or ('MAT' in true_tag and 'ART' in pred_tag):
                    art_mat_confusion.append(error_entry)
                    
                # Boundary error
                elif (true_tag[2:] == pred_tag[2:]) and (true_tag[0] != pred_tag[0]) and true_tag != 'O' and pred_tag != 'O':
                    boundary_errors.append(error_entry)
                    
                # Numeric error
                elif any(char.isdigit() for char in word):
                    numeric_errors.append(error_entry)
                    
            word_idx += 1

    # 4. Save report
    report = {
        'total_errors_analyzed': len(art_mat_confusion) + len(boundary_errors) + len(numeric_errors),
        'ART_vs_MAT_Confusions': art_mat_confusion[:10], # Save top 10
        'Boundary_Errors': boundary_errors[:10],
        'Numeric_Misclassifications': numeric_errors[:10]
    }
    
    report_path = os.path.join(config.OUTPUT_DIR, 'error_analysis_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Error analysis report generated at {report_path}")
    
    print("\n--- ERROR ANALYSIS SUMMARY ---")
    print(f"ART vs MAT Confusions: {len(art_mat_confusion)}")
    print(f"Boundary Errors: {len(boundary_errors)}")
    print(f"Numeric Misclassifications: {len(numeric_errors)}")

if __name__ == "__main__":
    generate_error_report()
