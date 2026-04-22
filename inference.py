"""
Inference Script for Indian Archaeology NER
Make predictions on new text using trained models
"""

import os
import argparse
import logging
from typing import List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NERInference:
    """Inference for NER predictions"""
    
    def __init__(self, model_path: str, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        """Initialize inference engine with a trained model"""
        self.device = device
        self.model_path = model_path
        
        logger.info(f"Loading model from: {model_path}")
        try:
            self.model = AutoModelForTokenClassification.from_pretrained(model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model.to(device)
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def predict(self, text: str, return_confidence: bool = False) -> List[Tuple[str, str, float]]:
        """
        Predict NER tags for a single text
        
        Args:
            text: Input text (can be Hindi-English code-mixed)
            return_confidence: Whether to return confidence scores
        
        Returns:
            List of (token, tag, confidence) tuples
        """
        # Tokenize
        tokens = text.split()
        encodings = self.tokenizer(
            tokens,
            truncation=True,
            is_split_into_words=True,
            max_length=config.MAX_LENGTH,
            padding='max_length',
            return_tensors='pt'
        )
        
        # Inference
        with torch.no_grad():
            input_ids = encodings['input_ids'].to(self.device)
            attention_mask = encodings['attention_mask'].to(self.device)
            
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            
            logits = outputs.logits
        
        # Get predictions
        predictions = torch.argmax(logits, dim=2)[0]
        probabilities = torch.softmax(logits, dim=2)[0]
        
        # Align with original tokens
        results = []
        word_ids = encodings.word_ids()
        
        for idx, word_idx in enumerate(word_ids):
            if word_idx is not None and word_idx < len(tokens):
                # Only take first subword for each word
                if word_idx == 0 or word_ids[idx - 1] != word_idx:
                    pred_id = predictions[idx].item()
                    tag = config.ID_TO_LABEL[pred_id]
                    
                    if return_confidence:
                        confidence = probabilities[idx, pred_id].item()
                        results.append((tokens[word_idx], tag, confidence))
                    else:
                        results.append((tokens[word_idx], tag))
        
        return results
    
    def predict_batch(self, texts: List[str], return_confidence: bool = False):
        """
        Predict NER tags for multiple texts
        
        Args:
            texts: List of input texts
            return_confidence: Whether to return confidence scores
        
        Returns:
            List of predictions for each text
        """
        results = []
        for text in texts:
            results.append(self.predict(text, return_confidence))
        
        return results
    
    def format_output(self, predictions: List[Tuple[str, str]], include_tags: List[str] = None):
        """
        Format predictions for display
        
        Args:
            predictions: List of (token, tag) tuples
            include_tags: If specified, only show these tags (e.g., ['B-ART', 'I-ART'])
        
        Returns:
            Formatted string
        """
        output = []
        current_entity = []
        current_tag = None
        
        for token, tag in predictions:
            if tag == 'O':
                if current_entity:
                    entity_text = ' '.join(current_entity)
                    output.append(f"[{entity_text}] ({current_tag})")
                    current_entity = []
                    current_tag = None
            elif tag.startswith('B-'):
                if current_entity:
                    entity_text = ' '.join(current_entity)
                    output.append(f"[{entity_text}] ({current_tag})")
                
                entity_type = tag[2:]
                if include_tags is None or tag in include_tags:
                    current_entity = [token]
                    current_tag = entity_type
                else:
                    current_entity = []
                    current_tag = None
            
            elif tag.startswith('I-'):
                if current_tag and tag[2:] == current_tag:
                    current_entity.append(token)
                else:
                    if current_entity:
                        entity_text = ' '.join(current_entity)
                        output.append(f"[{entity_text}] ({current_tag})")
                    
                    entity_type = tag[2:]
                    if include_tags is None or tag in include_tags:
                        current_entity = [token]
                        current_tag = entity_type
                    else:
                        current_entity = []
                        current_tag = None
        
        if current_entity:
            entity_text = ' '.join(current_entity)
            output.append(f"[{entity_text}] ({current_tag})")
        
        return ' '.join(output)
    
    def extract_entities(self, text: str, entity_types: List[str] = None) -> dict:
        """
        Extract entities of specific types from text
        
        Args:
            text: Input text
            entity_types: List of entity types to extract (e.g., ['ART', 'LOC'])
        
        Returns:
            Dictionary mapping entity types to list of entities
        """
        predictions = self.predict(text)
        
        entities = {}
        current_entity = []
        current_type = None
        
        for token, tag in predictions:
            if tag.startswith('B-'):
                if current_entity:
                    entity_text = ' '.join(current_entity)
                    if current_type not in entities:
                        entities[current_type] = []
                    entities[current_type].append(entity_text)
                
                current_type = tag[2:]
                current_entity = [token]
            
            elif tag.startswith('I-') and current_type:
                current_entity.append(token)
            
            else:
                if current_entity:
                    entity_text = ' '.join(current_entity)
                    if current_type not in entities:
                        entities[current_type] = []
                    entities[current_type].append(entity_text)
                    current_entity = []
                    current_type = None
        
        if current_entity:
            entity_text = ' '.join(current_entity)
            if current_type not in entities:
                entities[current_type] = []
            entities[current_type].append(entity_text)
        
        # Filter by entity types if specified
        if entity_types:
            entities = {k: v for k, v in entities.items() if k in entity_types}
        
        return entities


def main():
    """Command-line interface for inference"""
    parser = argparse.ArgumentParser(
        description='NER Inference for Indian Archaeology Text'
    )
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained model')
    parser.add_argument('--text', type=str, default=None,
                       help='Text to analyze')
    parser.add_argument('--file', type=str, default=None,
                       help='Input file with texts (one per line)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file to save predictions')
    parser.add_argument('--confidence', action='store_true',
                       help='Show confidence scores')
    parser.add_argument('--entities', type=str, default=None,
                       help='Comma-separated entity types to extract (e.g., ART,LOC)')
    parser.add_argument('--format', choices=['tokens', 'entities', 'both'],
                       default='both',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Initialize inference
    try:
        inferencer = NERInference(args.model)
    except Exception as e:
        logger.error(f"Failed to initialize inference: {e}")
        return
    
    # Process input
    texts = []
    
    if args.text:
        texts = [args.text]
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(texts)} texts from {args.file}")
    else:
        logger.info("Enter text (Ctrl+D to end):")
        try:
            texts = []
            while True:
                line = input("> ").strip()
                if line:
                    texts.append(line)
        except EOFError:
            pass
    
    if not texts:
        logger.warning("No text provided")
        return
    
    # Entity types to extract
    entity_types = None
    if args.entities:
        entity_types = args.entities.split(',')
    
    # Make predictions
    predictions = inferencer.predict_batch(texts, return_confidence=args.confidence)
    
    # Format and display output
    output_lines = []
    
    for text, pred in zip(texts, predictions):
        logger.info(f"\nText: {text}")
        
        if args.format in ['tokens', 'both']:
            if args.confidence:
                for token, tag, conf in pred:
                    logger.info(f"  {token:20s} {tag:12s} ({conf:.4f})")
            else:
                for token, tag in pred:
                    logger.info(f"  {token:20s} {tag:12s}")
            
            output_lines.append(f"Text: {text}")
            output_lines.append("Tokens:")
            for item in pred:
                output_lines.append(f"  {item}")
        
        if args.format in ['entities', 'both']:
            entities = inferencer.extract_entities(text, entity_types)
            if entities:
                logger.info("Entities:")
                for entity_type, entity_list in entities.items():
                    for entity in set(entity_list):
                        logger.info(f"  {entity_type}: {entity}")
                
                output_lines.append("Entities:")
                for entity_type, entity_list in entities.items():
                    for entity in set(entity_list):
                        output_lines.append(f"  {entity_type}: {entity}")
        
        output_lines.append("")
    
    # Save output if specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        logger.info(f"Output saved to {args.output}")


if __name__ == "__main__":
    main()
