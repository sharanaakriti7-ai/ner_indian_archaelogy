#!/usr/bin/env python3
"""
Complete BERT + BiLSTM + CRF Model for Indian Archaeology NER
Research-grade implementation with focal loss and dropout control
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
import logging
from typing import List, Tuple, Optional, Dict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FocalLoss(nn.Module):
    """Focal Loss for handling class imbalance"""
    def __init__(self, alpha: float = 1.0, gamma: float = 2.0, ignore_index: int = -100):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.ignore_index = ignore_index
    
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            predictions: (batch_size, seq_len, num_labels)
            targets: (batch_size, seq_len)
        """
        # Reshape
        batch_size, seq_len, num_labels = predictions.shape
        predictions = predictions.reshape(-1, num_labels)
        targets = targets.reshape(-1)
        
        # Create mask for ignored indices
        mask = (targets != self.ignore_index).float()
        
        # Compute cross entropy
        ce_loss = F.cross_entropy(predictions, targets, reduction='none')
        
        # Compute focal term
        p_t = torch.exp(-ce_loss)
        focal_loss = self.alpha * ((1 - p_t) ** self.gamma) * ce_loss
        
        # Apply mask
        focal_loss = focal_loss * mask
        
        return focal_loss.sum() / (mask.sum() + 1e-8)


class CRFLayer(nn.Module):
    """Conditional Random Field Layer for NER"""
    
    def __init__(self, num_labels: int, batch_first: bool = True):
        super().__init__()
        self.num_labels = num_labels
        self.batch_first = batch_first
        
        # Transition matrix (num_labels x num_labels)
        # transitions[i, j] = score of transition from label i to label j
        self.transitions = nn.Parameter(torch.randn(num_labels, num_labels))
        
        # Start and end transitions
        self.start_transitions = nn.Parameter(torch.randn(num_labels))
        self.end_transitions = nn.Parameter(torch.randn(num_labels))
        
        # Initialize transitions
        nn.init.xavier_uniform_(self.transitions)
        nn.init.normal_(self.start_transitions)
        nn.init.normal_(self.end_transitions)
    
    def forward(self, emissions: torch.Tensor, mask: torch.Tensor, 
                tags: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            emissions: (batch_size, seq_len, num_labels)
            mask: (batch_size, seq_len) boolean mask
            tags: (batch_size, seq_len) true labels
        
        Returns:
            If tags provided: negative log-likelihood loss
            Else: best path (viterbi decoding)
        """
        if tags is not None:
            # Calculate loss
            return self._neg_log_likelihood(emissions, mask, tags)
        else:
            # Viterbi decoding
            return self.viterbi_decode(emissions, mask)
    
    def _neg_log_likelihood(self, emissions: torch.Tensor, mask: torch.Tensor,
                            tags: torch.Tensor) -> torch.Tensor:
        """Calculate negative log-likelihood loss"""
        # emissions: (batch_size, seq_len, num_labels)
        # mask: (batch_size, seq_len)
        # tags: (batch_size, seq_len)
        
        batch_size, seq_len = tags.size()
        
        # Score of the true path
        gold_score = self._score_sentence(emissions, mask, tags)
        
        # Score of all paths
        partition_function = self._forward_algorithm(emissions, mask)
        
        # Loss
        loss = partition_function - gold_score
        return loss.mean()
    
    def _score_sentence(self, emissions: torch.Tensor, mask: torch.Tensor,
                       tags: torch.Tensor) -> torch.Tensor:
        """Score a sequence of tags"""
        batch_size, seq_len = tags.size()
        device = emissions.device
        
        score = torch.zeros(batch_size, device=device)
        
        # Create mask for valid labels (ignore -100 padding indices)
        valid_mask = (tags != -100).float()
        
        # Replace -100 with 0 for indexing (will be masked out anyway)
        tags_safe = tags.clone()
        tags_safe[tags == -100] = 0
        
        # Add start transition (only for first valid position)
        score += self.start_transitions[tags_safe[:, 0]] * valid_mask[:, 0]
        
        # Add transitions and emissions
        for i in range(1, seq_len):
            prev_tags = tags_safe[:, i - 1]
            curr_tags = tags_safe[:, i]
            
            # Score = emission + transition
            transition_scores = self.transitions[prev_tags, curr_tags]
            emission_scores = emissions[torch.arange(batch_size), i, curr_tags]
            
            # Apply mask to ignore padding positions
            current_valid = valid_mask[:, i]
            masked_scores = (transition_scores + emission_scores) * current_valid
            score += masked_scores
        
        # Add end transition (use last valid tag)
        last_tags_safe = tags_safe.clone()
        last_tags_safe[tags == -100] = 0
        
        # For end transition, find last valid position per sequence
        for b in range(batch_size):
            last_valid = (valid_mask[b] == 1).nonzero(as_tuple=False)
            if len(last_valid) > 0:
                last_idx = last_valid[-1].item()
                score[b] += self.end_transitions[last_tags_safe[b, last_idx]]
        
        return score

    def _forward_algorithm(self, emissions: torch.Tensor, 
                          mask: torch.Tensor) -> torch.Tensor:
        """Forward algorithm to compute partition function"""
        batch_size, seq_len, num_labels = emissions.size()
        device = emissions.device
        
        # Initialize
        viterbi = self.start_transitions + emissions[:, 0, :]  # (batch_size, num_labels)
        
        # Forward pass
        for i in range(1, seq_len):
            # (batch_size, num_labels, 1) + (batch_size, 1, num_labels)
            # = (batch_size, num_labels, num_labels)
            viterbi_prev = viterbi.unsqueeze(2)
            transitions = self.transitions.unsqueeze(0)  # (1, num_labels, num_labels)
            
            # Max over previous labels
            # (batch_size, num_labels, num_labels) -> (batch_size, num_labels)
            viterbi_new = torch.logsumexp(viterbi_prev + transitions, dim=1)
            viterbi_new = viterbi_new + emissions[:, i, :]
            
            # Apply mask (use non-inplace operation)
            viterbi = torch.where(mask[:, i].unsqueeze(1), viterbi_new, viterbi)
        
        # Add end transition (non-inplace)
        viterbi = viterbi + self.end_transitions
        
        # Sum over all labels
        return torch.logsumexp(viterbi, dim=1)
    
    def viterbi_decode(self, emissions: torch.Tensor, 
                      mask: torch.Tensor) -> List[List[int]]:
        """Viterbi decoding to find best path"""
        batch_size, seq_len, num_labels = emissions.size()
        device = emissions.device
        
        # Initialize
        viterbi = self.start_transitions + emissions[:, 0, :]  # (batch_size, num_labels)
        backpointers = []
        
        # Forward pass with backpointers
        for i in range(1, seq_len):
            viterbi_prev = viterbi.unsqueeze(2)  # (batch_size, num_labels, 1)
            transitions = self.transitions.unsqueeze(0)  # (1, num_labels, num_labels)
            
            viterbi_new = viterbi_prev + transitions  # (batch_size, num_labels, num_labels)
            viterbi_new += emissions[:, i, :].unsqueeze(1)
            
            # Best previous label
            viterbi_best, backpointer = torch.max(viterbi_new, dim=1)
            backpointers.append(backpointer)
            
            # Update viterbi
            viterbi = torch.where(mask[:, i].unsqueeze(1), viterbi_best, viterbi)
        
        # Add end transition
        viterbi += self.end_transitions
        
        # Backtrack to find best path
        best_paths = []
        for batch_idx in range(batch_size):
            best_label = torch.argmax(viterbi[batch_idx])
            path = [best_label.item()]
            
            for i in range(len(backpointers) - 1, -1, -1):
                best_label = backpointers[i][batch_idx, best_label]
                path.append(best_label.item())
            
            path.reverse()
            best_paths.append(path)
        
        return best_paths


class TransformerCRFModel(nn.Module):
    """Transformer + BiLSTM + CRF for NER"""
    
    def __init__(self, model_name: str, num_labels: int, dropout: float = 0.1, use_self_attention: bool = False):
        super().__init__()
        self.num_labels = num_labels
        self.use_self_attention = use_self_attention
        
        # Load transformer
        self.transformer = AutoModel.from_pretrained(model_name)
        self.hidden_size = self.transformer.config.hidden_size
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # BiLSTM layer
        self.lstm = nn.LSTM(
            input_size=self.hidden_size,
            hidden_size=self.hidden_size // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        
        # Self-Attention Layer
        if self.use_self_attention:
            self.self_attention = nn.MultiheadAttention(
                embed_dim=self.hidden_size,
                num_heads=8,
                dropout=dropout,
                batch_first=True
            )
        
        # Projection to num_labels
        self.classifier = nn.Linear(self.hidden_size, num_labels)
        
        # CRF layer
        self.crf = CRFLayer(num_labels, batch_first=True)
        
        logger.info(f"Model initialized: {model_name}")
        logger.info(f"  Hidden size: {self.hidden_size}")
        logger.info(f"  Num labels: {num_labels}")
        logger.info(f"  Self-attention: {self.use_self_attention}")
    
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor,
                labels: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Args:
            input_ids: (batch_size, seq_len)
            attention_mask: (batch_size, seq_len)
            labels: (batch_size, seq_len) optional
        
        Returns:
            logits: (batch_size, seq_len, num_labels)
            loss: scalar if labels provided
        """
        # Transformer forward
        outputs = self.transformer(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )
        
        sequence_output = outputs.last_hidden_state  # (batch_size, seq_len, hidden_size)
        
        # Dropout
        sequence_output = self.dropout(sequence_output)
        
        # BiLSTM
        lstm_output, _ = self.lstm(sequence_output)
        
        # Self Attention
        if self.use_self_attention:
            # Multihead attention expects query, key, value
            attn_output, _ = self.self_attention(
                query=lstm_output,
                key=lstm_output,
                value=lstm_output
            )
            # Add & Norm like standard transformer block
            lstm_output = lstm_output + attn_output
            
        # Projection
        emissions = self.classifier(lstm_output)  # (batch_size, seq_len, num_labels)
        
        if labels is not None:
            # CRF loss
            loss = self.crf(emissions, attention_mask.bool(), labels)
            return emissions, loss
        else:
            # Viterbi decoding
            predictions = self.crf.viterbi_decode(emissions, attention_mask.bool())
            return emissions, predictions
    
    def freeze_transformer(self) -> None:
        """Freeze transformer weights"""
        for param in self.transformer.parameters():
            param.requires_grad = False
        logger.info("✓ Transformer weights frozen")
    
    def unfreeze_transformer(self) -> None:
        """Unfreeze transformer weights"""
        for param in self.transformer.parameters():
            param.requires_grad = True
        logger.info("✓ Transformer weights unfrozen")
    
    def get_trainable_params(self) -> int:
        """Get number of trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class FocalLoss(nn.Module):
    """Focal Loss for handling class imbalance"""
    
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
    
    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            inputs: (batch_size * seq_len, num_labels)
            targets: (batch_size * seq_len,)
        """
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        
        # Get probability of true class
        p = torch.exp(-ce_loss)
        
        # Focal loss: -(1 - p_t)^gamma * log(p_t)
        focal_loss = self.alpha * (1 - p) ** self.gamma * ce_loss
        
        return focal_loss.mean()


if __name__ == "__main__":
    # Test model
    device = "cpu"
    model = TransformerCRFModel(
        model_name="bert-base-multilingual-cased",
        num_labels=11,
        dropout=0.1
    ).to(device)
    
    # Test forward pass
    batch_size, seq_len = 4, 20
    input_ids = torch.randint(0, 119547, (batch_size, seq_len)).to(device)
    attention_mask = torch.ones(batch_size, seq_len).to(device)
    labels = torch.randint(0, 11, (batch_size, seq_len)).to(device)
    
    # With labels (training)
    emissions, loss = model(input_ids, attention_mask, labels)
    logger.info(f"✓ Forward pass successful")
    logger.info(f"  Emissions shape: {emissions.shape}")
    logger.info(f"  Loss: {loss.item():.4f}")
    
    # Without labels (inference)
    emissions, predictions = model(input_ids, attention_mask)
    logger.info(f"  Predictions shape: {len(predictions)}")
    logger.info(f"  Trainable parameters: {model.get_trainable_params():,}")
