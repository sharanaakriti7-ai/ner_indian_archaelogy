import os
import torch
from transformers import (
    AutoModelForMaskedLM,
    AutoTokenizer,
    LineByLineTextDataset,
    DataCollatorForLanguageModeling
)
from torch.utils.data import DataLoader
from torch.optim import AdamW
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_dapt(
    model_name="bert-base-multilingual-cased",
    train_file="data/pretrain_corpus.txt",
    output_dir="models/indian-archaeology-bert",
    epochs=3,
    batch_size=8
):
    logger.info(f"Starting Domain Adaptive Pretraining (DAPT) using {model_name}")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 1. Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForMaskedLM.from_pretrained(model_name)
    model.to(device)
    
    # 2. Load dataset
    logger.info(f"Loading dataset from {train_file}")
    dataset = LineByLineTextDataset(
        tokenizer=tokenizer,
        file_path=train_file,
        block_size=128
    )
    
    # 3. Data collator for MLM
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=True, mlm_probability=0.15
    )
    
    dataloader = DataLoader(dataset, batch_size=batch_size, collate_fn=data_collator)
    optimizer = AdamW(model.parameters(), lr=5e-5)
    
    # 6. Train
    logger.info("Starting MLM training...")
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for step, batch in enumerate(dataloader):
            optimizer.zero_grad()
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        logger.info(f"Epoch {epoch+1} | Loss: {total_loss/len(dataloader):.4f}")
    
    # 7. Save final model
    logger.info(f"Saving domain-adapted model to {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.info("DAPT completed successfully!")

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    # We use a small number of epochs for quick execution
    run_dapt(epochs=3)
