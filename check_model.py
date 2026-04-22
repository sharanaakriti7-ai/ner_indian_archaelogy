import os
import json

print('=== FINAL MODEL ANALYSIS ===\n')

models = {
    'best_model': 'outputs/quick_eval/best_model/',
    'final_model': 'outputs/quick_eval/final_model/'
}

for model_name, model_path in models.items():
    if os.path.exists(model_path):
        print(f'{model_name.upper()}:')
        print(f'  Path: {model_path}')
        
        # Get config
        config_path = os.path.join(model_path, 'config.json')
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            print(f'  Model Type: {config.get("model_type", "?")}')
            print(f'  Num Labels: {config.get("num_labels", "?")}')
            print(f'  Hidden Size: {config.get("hidden_size", "?")}')
        
        # Get file sizes
        print(f'  Files:')
        total_size = 0
        for file in os.listdir(model_path):
            file_path = os.path.join(model_path, file)
            if os.path.isfile(file_path):
                size_mb = os.path.getsize(file_path) / 1024 / 1024
                total_size += size_mb
                print(f'    - {file}: {size_mb:.1f} MB')
        print(f'  Total Size: {total_size:.1f} MB')
        print()

print('CURRENT MODEL BEING USED:')
print('-' * 60)
print('Default: outputs/quick_eval/best_model/')
print()
print('EXPLANATION:')
print('  • best_model: Best checkpoint during training')
print('                (evaluated on dev set, lowest loss/highest F1)')
print('  • final_model: Final checkpoint after all epochs')
print('                (may not be the best, could have overfit)')
print()
print('RECOMMENDATION:')
print('  ✓ Use best_model for inference (production)')
print('  ✓ best_model achieves best validation performance')
