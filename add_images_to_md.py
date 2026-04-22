import codecs

with codecs.open("RESEARCH_PAPER.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    
    if "| **Our Model (mBERT+CRF+FL)** | **0.7121** | **0.8439** | **0.7724** |" in line:
        new_lines.append("\n![Baselines Comparison](paper_plots/baselines_comparison.png)\n*Figure 1: Comparing our final model against the baselines.*\n")
    
    elif "On the other hand, MAT and CON struggled a bit more (~0.60 to 0.65 F1)." in line:
        new_lines.append("\n![Per-Entity Performance](paper_plots/per_entity_performance.png)\n*Figure 2: Precision, Recall, and F1 Score for individual entity classes.*\n")
        new_lines.append("\n![F1 Curves](paper_plots/f1_curves.png)\n*Figure 3: Training and Validation F1 Scores over epochs.*\n")
        
    elif "Even though the model improved, it still makes some funny mistakes." in line:
        new_lines.append("\n![Confusion Matrix](paper_plots/confusion_matrix.png)\n*Figure 4: Confusion Matrix on our Test Set. Notice the confusion between MAT and ART.*\n")

with codecs.open("RESEARCH_PAPER.md", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Images successfully added to RESEARCH_PAPER.md!")
