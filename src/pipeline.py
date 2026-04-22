"""
Complete Training Pipeline for Domain-Specific BERT NER
Orchestrates pretraining, fine-tuning, and evaluation
"""

import os
import sys
import logging
import argparse
from datetime import datetime

import config
from src.data_utils import load_and_prepare_data, load_pretrain_data
from src.pretrain import MLMPretrainer
from src.finetune import NERFineTuner, cross_validate_ner
from src.evaluation import NEREvaluator, evaluate_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrainingPipeline:
    """Complete training pipeline"""
    
    def __init__(self, experiment_name: str = None):
        self.experiment_name = experiment_name or f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = os.path.join(config.OUTPUT_DIR, self.experiment_name)
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Experiment: {self.experiment_name}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def run_full_pipeline(self, pretrain: bool = True, finetune: bool = True,
                         cross_val: bool = False, evaluate: bool = True):
        """
        Run complete pipeline: pretrain -> finetune -> evaluate
        """
        logger.info("=" * 70)
        logger.info("STARTING FULL TRAINING PIPELINE")
        logger.info("=" * 70)
        
        pretrained_model_path = None
        
        # Step 1: Domain-Adaptive Pretraining
        if pretrain:
            logger.info("\n" + "=" * 70)
            logger.info("STEP 1: DOMAIN-ADAPTIVE PRETRAINING (MLM)")
            logger.info("=" * 70)
            
            pretrained_model_path = self._run_pretraining()
        else:
            pretrained_model_path = config.MODEL_NAME
            logger.info(f"Skipping pretraining. Using base model: {pretrained_model_path}")
        
        # Step 2: NER Fine-tuning
        if finetune:
            logger.info("\n" + "=" * 70)
            logger.info("STEP 2: NER FINE-TUNING")
            logger.info("=" * 70)
            
            if cross_val:
                self._run_cross_validation(pretrained_model_path)
            else:
                self._run_finetuning(pretrained_model_path)
        
        # Step 3: Evaluation
        if evaluate:
            logger.info("\n" + "=" * 70)
            logger.info("STEP 3: EVALUATION AND ERROR ANALYSIS")
            logger.info("=" * 70)
            
            self._run_evaluation()
        
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
    
    def _run_pretraining(self) -> str:
        """Run domain-adaptive pretraining"""
        logger.info("Loading pretraining corpus...")
        train_loader, tokenizer = load_pretrain_data(
            config.PRETRAIN_CORPUS_FILE,
            config.MODEL_NAME,
            config.PRETRAIN_BATCH_SIZE
        )
        
        logger.info(f"Pretraining on {len(train_loader)} batches")
        
        # Initialize pretrainer
        pretrainer = MLMPretrainer(
            model_name=config.MODEL_NAME,
            learning_rate=config.PRETRAIN_LEARNING_RATE
        )
        
        # Train
        model_path = os.path.join(self.output_dir, config.DOMAIN_MODEL_NAME)
        pretrainer.train(
            train_loader,
            epochs=config.PRETRAIN_EPOCHS,
            eval_loader=None,
            output_dir=self.output_dir
        )
        
        logger.info(f"Pretraining completed. Model saved to {model_path}")
        return model_path
    
    def _run_finetuning(self, model_name: str = config.MODEL_NAME):
        """Run NER fine-tuning"""
        logger.info("Loading NER data...")
        train_loader, dev_loader, test_loader, tokenizer = load_and_prepare_data(
            config.TRAIN_FILE,
            config.DEV_FILE,
            config.TEST_FILE,
            model_name,
            config.BATCH_SIZE,
            augment=True
        )
        
        logger.info(f"Data loaded:")
        logger.info(f"  Train: {len(train_loader)} batches")
        logger.info(f"  Dev: {len(dev_loader)} batches")
        logger.info(f"  Test: {len(test_loader)} batches")
        
        # Initialize fine-tuner
        finetuner = NERFineTuner(
            model_name=model_name,
            learning_rate=config.LEARNING_RATE
        )
        
        # Train
        model_dir = os.path.join(self.output_dir, 'ner_models')
        finetuner.train(
            train_loader,
            dev_loader,
            epochs=config.EPOCHS,
            output_dir=model_dir
        )
        
        logger.info(f"Fine-tuning completed. Model saved to {model_dir}")
    
    def _run_cross_validation(self, model_name: str = config.MODEL_NAME):
        """Run cross-validation fine-tuning"""
        logger.info(f"Running {config.NUM_FOLDS}-fold cross-validation...")
        
        cv_output_dir = os.path.join(self.output_dir, 'cross_validation')
        fold_results = cross_validate_ner(
            config.TRAIN_FILE,
            n_splits=config.NUM_FOLDS,
            output_dir=cv_output_dir
        )
        
        logger.info(f"Cross-validation completed with {len(fold_results)} folds")
        logger.info(f"Results saved to {cv_output_dir}")
    
    def _run_evaluation(self):
        """Run evaluation and error analysis"""
        model_path = os.path.join(self.output_dir, 'ner_models', 'best_model')
        
        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}")
            logger.info("Skipping evaluation")
            return
        
        results = evaluate_model(
            model_path,
            config.TEST_FILE,
            self.output_dir
        )
        
        logger.info(f"Evaluation completed. Results saved to {self.output_dir}")
        logger.info(f"Entity-Level F1: {results['entity_metrics']['f1']:.4f}")
        logger.info(f"Token-Level F1: {results['token_metrics']['f1']:.4f}")
    
    def predict_on_new_text(self, sentences, model_path: str = None):
        """
        Make predictions on new text
        """
        if model_path is None:
            model_path = os.path.join(self.output_dir, 'ner_models', 'best_model')
        
        if not os.path.exists(model_path):
            logger.error(f"Model not found at {model_path}")
            return None
        
        evaluator = NEREvaluator(model_path)
        predictions = evaluator.model.predict(sentences)
        
        return predictions


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Domain-Specific BERT NER for Indian Archaeology'
    )
    parser.add_argument('--experiment-name', type=str, default=None,
                       help='Experiment name for output directory')
    parser.add_argument('--no-pretrain', action='store_true',
                       help='Skip pretraining step')
    parser.add_argument('--no-finetune', action='store_true',
                       help='Skip fine-tuning step')
    parser.add_argument('--cross-val', action='store_true',
                       help='Use cross-validation instead of simple split')
    parser.add_argument('--no-eval', action='store_true',
                       help='Skip evaluation step')
    parser.add_argument('--quick-test', action='store_true',
                       help='Run quick test with small epochs')
    
    args = parser.parse_args()
    
    # Quick test mode (for development)
    if args.quick_test:
        logger.info("QUICK TEST MODE: Using reduced epochs")
        config.PRETRAIN_EPOCHS = 1
        config.EPOCHS = 2
    
    # Initialize pipeline
    pipeline = TrainingPipeline(experiment_name=args.experiment_name)
    
    # Run pipeline
    pipeline.run_full_pipeline(
        pretrain=not args.no_pretrain,
        finetune=not args.no_finetune,
        cross_val=args.cross_val,
        evaluate=not args.no_eval
    )
    
    logger.info(f"\nResults saved to: {pipeline.output_dir}")


if __name__ == "__main__":
    main()
