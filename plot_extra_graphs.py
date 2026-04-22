import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

os.makedirs("paper_plots", exist_ok=True)

# 4. Baselines Comparison Bar Chart
models = ['CRF', 'ArcheoBERTje', 'IndicBERT', 'mBERT', 'mBERT+Aug', 'mBERT+Focal', 'Final(mBERT+CRF+Focal)']
f1_scores = [0.5020, 0.5270, 0.5814, 0.6225, 0.7065, 0.7420, 0.7724]

plt.figure(figsize=(10, 6))
bars = plt.barh(models, f1_scores, color=sns.color_palette("viridis", len(models)))
plt.xlabel('Weighted F1 Score')
plt.title('Performance Comparison Across Baselines')
plt.xlim(0, 1.0)
for bar in bars:
    plt.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
             f'{bar.get_width():.4f}', va='center', ha='left')
plt.tight_layout()
plt.savefig('paper_plots/baselines_comparison.png', dpi=300)
plt.close()

# 5. Per-Entity Performance Bar Chart
entities = ['LOC', 'PER', 'ART', 'MAT', 'CON']
precision = [0.88, 0.86, 0.65, 0.62, 0.58]
recall = [0.89, 0.85, 0.70, 0.68, 0.61]
f1 = [0.885, 0.855, 0.674, 0.648, 0.594]

x = np.arange(len(entities))
width = 0.25

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width, precision, width, label='Precision', color='#4c72b0')
rects2 = ax.bar(x, recall, width, label='Recall', color='#dd8452')
rects3 = ax.bar(x + width, f1, width, label='F1 Score', color='#55a868')

ax.set_ylabel('Scores')
ax.set_title('Per-Entity Performance (Final Model)')
ax.set_xticks(x)
ax.set_xticklabels(entities)
ax.legend()
plt.tight_layout()
plt.savefig('paper_plots/per_entity_performance.png', dpi=300)
plt.close()

print("Extra plots generated successfully in 'paper_plots/' directory.")
