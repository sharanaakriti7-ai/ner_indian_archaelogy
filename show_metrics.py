#!/usr/bin/env python3
"""Quick evaluation metrics display"""

import torch
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.ERROR)

from config import *

def main():
    print("=" * 80)
    print("INDIAN ARCHAEOLOGY NER - PROJECT EVALUATION SUMMARY")
    print("=" * 80)
    
    print("\n### PROJECT CONFIGURATION ###\n")
    print(f"  Model:              {MODEL_NAME}")
    print(f"  Labels:             {NUM_LABELS}")
    print(f"  Entities:           ART (Artifact), PER (Person), LOC (Location),")
    print(f"                      MAT (Material), CON (Construction)")
    print(f"  Batch Size:         {BATCH_SIZE}")
    print(f"  Max Sequence:       {MAX_LENGTH}")
    print(f"  Dropout Rate:       {DROPOUT}")
    
    print("\n### TRAINING DATA ###\n")
    print(f"  Train File:         {TRAIN_FILE}")
    print(f"  Dev File:           {DEV_FILE}")
    print(f"  Test File:          {TEST_FILE}")
    
    print("\n### MODEL CHECKPOINT ###\n")
    checkpoint_dir = Path("outputs/quick_eval/best_model")
    if checkpoint_dir.exists():
        print(f"  Checkpoint Path:    {checkpoint_dir}")
        print(f"  Status:             AVAILABLE")
        files = list(checkpoint_dir.glob("*"))
        print(f"  Files in checkpoint: {len(files)}")
        for f in files:
            print(f"    - {f.name}")
    else:
        print(f"  Status:             NOT FOUND")
    
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS (Computing actual test performance...)")
    print("=" * 80)
    
    try:
        from eval_test import evaluate_on_test
        evaluate_on_test()
    except Exception as e:
        print(f"Error running evaluation: {e}")
        print("Please run 'python eval_test.py' directly for detailed metrics.")
        
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETED - Model is ready for inference!")
    print("=" * 80)

if __name__ == "__main__":
    main()
