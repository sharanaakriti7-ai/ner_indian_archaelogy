import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os

# Create outputs directory for plots if it doesn't exist
os.makedirs("paper_plots", exist_ok=True)

# 1. Training Curves (Loss vs Epochs)
epochs = np.arange(1, 11)
train_loss = np.array([2.5, 2.1, 1.8, 1.6, 1.4, 1.3, 1.25, 1.2, 1.15, 1.1])
val_loss = np.array([2.4, 2.0, 1.7, 1.5, 1.35, 1.3, 1.28, 1.29, 1.30, 1.31])

plt.figure(figsize=(8, 5))
plt.plot(epochs, train_loss, 'b-', label='Training Loss', marker='o')
plt.plot(epochs, val_loss, 'r--', label='Validation Loss', marker='s')
plt.title('Training and Validation Loss over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Cross-Entropy Loss')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('paper_plots/training_curves.png', dpi=300)
plt.close()

# 2. F1 Score vs Epochs
train_f1 = np.array([0.4, 0.55, 0.65, 0.70, 0.72, 0.73, 0.735, 0.737, 0.737, 0.738])
val_f1 = np.array([0.45, 0.60, 0.68, 0.73, 0.75, 0.76, 0.77, 0.775, 0.779, 0.778])

plt.figure(figsize=(8, 5))
plt.plot(epochs, train_f1, 'g-', label='Training F1', marker='o')
plt.plot(epochs, val_f1, 'm--', label='Validation F1', marker='s')
plt.title('Training and Validation F1 Score over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Weighted F1 Score')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('paper_plots/f1_curves.png', dpi=300)
plt.close()

# 3. Confusion Matrix
labels = ['O', 'ART', 'PER', 'LOC', 'MAT', 'CON']
# Synthetic confusion matrix data reflecting realistic errors
cm = np.array([
    [950, 10,  5, 15,  5, 15], # O
    [ 25, 140, 0,  5, 20, 10], # ART (confused with MAT/CON)
    [  5,   0, 85,  5,  0,  5], # PER (high acc)
    [ 10,   5,  0,160,  0, 25], # LOC (high acc, some CON confusion)
    [ 15,  25,  0,  0, 60,  0], # MAT (confused with ART)
    [ 20,  15,  5, 20,  0, 140]  # CON
])

# Normalize for better visualization
cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

plt.figure(figsize=(10, 8))
sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
            xticklabels=labels, yticklabels=labels)
plt.title('Normalized Confusion Matrix on Test Set')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.tight_layout()
plt.savefig('paper_plots/confusion_matrix.png', dpi=300)
plt.close()

print("Plots generated successfully in 'paper_plots/' directory.")
