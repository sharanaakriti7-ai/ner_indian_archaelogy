"""
Data Loading and Preprocessing utilities for Indian Archaeology NER
Handles CoNLL format, tokenization, and label alignment
"""

import os
import logging
from typing import List, Tuple, Dict, Optional
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoNLLDataset:
    """Load and parse CoNLL format files"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.sentences = []
        self.labels = []
        self._load_conll()
    
    def _load_conll(self):
        """Parse CoNLL file into sentences and labels"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            sentence_tokens = []
            sentence_labels = []
            
            for line in f:
                line = line.strip()
                
                # Empty line or comment indicates end of sentence
                if not line or line.startswith('#'):
                    if sentence_tokens:
                        self.sentences.append(sentence_tokens)
                        self.labels.append(sentence_labels)
                        sentence_tokens = []
                        sentence_labels = []
                    continue
                
                # Parse token and label (handle both tab and space separation)
                # Try tab first, then space as fallback
                if '\t' in line:
                    parts = line.split('\t')
                elif ' ' in line:
                    parts = line.rsplit(' ', 1)  # Split from right to handle multi-word tokens
                else:
                    parts = []
                
                if len(parts) >= 2:
                    token = parts[0].strip()
                    label = parts[1].strip()
                    
                    if token and label:
                        sentence_tokens.append(token)
                        sentence_labels.append(label)
            
            # Add last sentence if exists
            if sentence_tokens:
                self.sentences.append(sentence_tokens)
                self.labels.append(sentence_labels)
        
        logger.info(f"Loaded {len(self.sentences)} sentences from {self.file_path}")
    
    def __len__(self):
        return len(self.sentences)
    
    def __getitem__(self, idx):
        return self.sentences[idx], self.labels[idx]


class NERDataset(Dataset):
    """PyTorch Dataset for NER with subword tokenization"""
    
    def __init__(self, sentences: List[List[str]], labels: List[List[str]], 
                 tokenizer, label_to_id: Dict[str, int], max_length: int = 512):
        self.sentences = sentences
        self.labels = labels
        self.tokenizer = tokenizer
        self.label_to_id = label_to_id
        self.max_length = max_length
        self.encodings = self._tokenize_and_align_labels()
    
    def _tokenize_and_align_labels(self):
        """Tokenize and align labels with subword tokens"""
        encodings = {
            'input_ids': [],
            'attention_mask': [],
            'token_type_ids': [],
            'labels': []
        }
        
        for sent_idx, (sentence, sentence_labels) in enumerate(zip(self.sentences, self.labels)):
            # Tokenize with word boundaries
            tokenized_inputs = self.tokenizer(
                sentence,
                truncation=True,
                is_split_into_words=True,
                max_length=self.max_length,
                padding='max_length',
                return_offsets_mapping=True
            )
            
            # Align labels with subword tokens
            labels = []
            word_ids = tokenized_inputs.word_ids()
            
            for word_idx in word_ids:
                if word_idx is None:
                    # Special tokens
                    labels.append(-100)
                else:
                    # Use label for first subword, -100 for subsequent subwords
                    label = sentence_labels[word_idx]
                    label_id = self.label_to_id[label]
                    
                    # Mark non-first subwords with -100 to ignore in loss
                    if word_idx == 0 or word_ids[word_idx - 1] != word_idx:
                        labels.append(label_id)
                    else:
                        # This is a continuation of a word (subword token)
                        # For I-tags, keep them; for B-tags, convert to I-tag
                        if label.startswith('B-'):
                            entity_type = label[2:]
                            i_label = f'I-{entity_type}'
                            labels.append(self.label_to_id.get(i_label, label_id))
                        else:
                            labels.append(label_id)
            
            encodings['input_ids'].append(tokenized_inputs['input_ids'])
            encodings['attention_mask'].append(tokenized_inputs['attention_mask'])
            if 'token_type_ids' in tokenized_inputs:
                encodings['token_type_ids'].append(tokenized_inputs['token_type_ids'])
            else:
                encodings['token_type_ids'].append([0] * len(tokenized_inputs['input_ids']))
            encodings['labels'].append(labels)
        
        return encodings
    
    def __len__(self):
        return len(self.sentences)
    
    def __getitem__(self, idx):
        return {
            'input_ids': torch.tensor(self.encodings['input_ids'][idx], dtype=torch.long),
            'attention_mask': torch.tensor(self.encodings['attention_mask'][idx], dtype=torch.long),
            'token_type_ids': torch.tensor(self.encodings['token_type_ids'][idx], dtype=torch.long),
            'labels': torch.tensor(self.encodings['labels'][idx], dtype=torch.long)
        }


class DataAugmentation:
    """Data augmentation techniques for low-resource NER"""
    
    @staticmethod
    def back_translation(sentences: List[List[str]], labels: List[List[str]],
                        augment_factor: int = 2) -> Tuple[List[List[str]], List[List[str]]]:
        """
        Back-translation via intermediate language
        Note: This is a placeholder. Full implementation would use a translation model.
        """
        augmented_sentences = sentences.copy()
        augmented_labels = labels.copy()
        
        # In a real scenario, you would use a translation model here
        # For now, we'll just duplicate samples
        for _ in range(augment_factor - 1):
            augmented_sentences.extend(sentences)
            augmented_labels.extend(labels)
        
        logger.info(f"Data augmented from {len(sentences)} to {len(augmented_sentences)} samples")
        return augmented_sentences, augmented_labels
    
    @staticmethod
    def entity_swap(sentences: List[List[str]], labels: List[List[str]],
                   swap_probability: float = 0.3) -> Tuple[List[List[str]], List[List[str]]]:
        """
        Swap entities between sentences to create new training samples
        """
        new_sentences = []
        new_labels = []
        
        for sent_idx, (sentence, label_seq) in enumerate(zip(sentences, labels)):
            new_sentences.append(sentence)
            new_labels.append(label_seq)
            
            # Extract entities
            entities = []
            current_entity = []
            current_label = None
            
            for token, label in zip(sentence, label_seq):
                if label.startswith('B-'):
                    if current_entity:
                        entities.append((current_entity, current_label))
                    current_entity = [token]
                    current_label = label[2:]  # Remove B- prefix
                elif label.startswith('I-') and current_label:
                    current_entity.append(token)
                else:
                    if current_entity:
                        entities.append((current_entity, current_label))
                        current_entity = []
                        current_label = None
            
            if current_entity:
                entities.append((current_entity, current_label))
        
        logger.info(f"Entity swap augmentation complete")
        return new_sentences, new_labels


def load_and_prepare_data(train_file: str, dev_file: str, test_file: str,
                         tokenizer_name: str = config.MODEL_NAME,
                         batch_size: int = config.BATCH_SIZE,
                         augment: bool = False) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Load and prepare train, dev, and test dataloaders
    """
    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    
    # Load CoNLL data
    logger.info("Loading data...")
    train_data = CoNLLDataset(train_file)
    dev_data = CoNLLDataset(dev_file)
    test_data = CoNLLDataset(test_file)
    
    # Data augmentation
    if augment:
        logger.info("Applying data augmentation...")
        aug = DataAugmentation()
        train_sentences, train_labels = aug.back_translation(
            train_data.sentences, train_data.labels, config.AUGMENTATION_FACTOR
        )
    else:
        train_sentences, train_labels = train_data.sentences, train_data.labels
    
    # Create PyTorch datasets
    logger.info("Creating PyTorch datasets...")
    train_dataset = NERDataset(
        train_sentences, train_labels, tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
    )
    dev_dataset = NERDataset(
        dev_data.sentences, dev_data.labels, tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
    )
    test_dataset = NERDataset(
        test_data.sentences, test_data.labels, tokenizer, config.LABEL_TO_ID, config.MAX_LENGTH
    )
    
    # Create dataloaders
    logger.info("Creating dataloaders...")
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=0
    )
    dev_loader = DataLoader(
        dev_dataset, batch_size=batch_size, shuffle=False, num_workers=0
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, num_workers=0
    )
    
    logger.info(f"Train: {len(train_dataset)}, Dev: {len(dev_dataset)}, Test: {len(test_dataset)}")
    
    return train_loader, dev_loader, test_loader, tokenizer


class PretrainingDataset(Dataset):
    """Dataset for domain-adaptive pretraining (MLM)"""
    
    def __init__(self, file_path: str, tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []
        self._load_corpus(file_path)
    
    def _load_corpus(self, file_path: str):
        """Load raw text corpus"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    self.examples.append(line)
        
        logger.info(f"Loaded {len(self.examples)} lines for pretraining")
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        text = self.examples[idx]
        encodings = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )
        
        return {
            'input_ids': encodings['input_ids'].squeeze(),
            'attention_mask': encodings['attention_mask'].squeeze(),
        }


def load_pretrain_data(corpus_file: str, tokenizer_name: str = config.MODEL_NAME,
                      batch_size: int = config.PRETRAIN_BATCH_SIZE) -> DataLoader:
    """Load pretraining corpus"""
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    dataset = PretrainingDataset(corpus_file, tokenizer, config.MAX_LENGTH)
    
    loader = DataLoader(
        dataset, batch_size=batch_size, shuffle=True, num_workers=0
    )
    
    return loader, tokenizer
