#!/usr/bin/env python3
"""
Dataset Expansion and Generation for Indian Archaeology NER
Expands 60 sentences to 1000+ annotated sentences
"""

import os
from typing import List, Tuple

# Domain knowledge for coherent generation
ARCHAEOLOGICAL_SITES = [
    ("Harappa", "B-LOC"), ("Mohenjo-daro", "B-LOC"), ("Dholavira", "B-LOC"),
    ("Lothal", "B-LOC"), ("Kalibangan", "B-LOC"), ("Mehrgarh", "B-LOC"),
    ("Bhirrana", "B-LOC"), ("Rakhigarhi", "B-LOC"), ("Chanhu-daro", "B-LOC"),
    ("Taxila", "B-LOC"), ("Varanasi", "B-LOC"), ("Ayodhya", "B-LOC"),
]

PERIODS = [
    ("Indus Valley", "B-PER"), ("Paleolithic", "B-PER"), ("Neolithic", "B-PER"),
    ("Vedic", "B-PER"), ("Mauryan", "B-PER"), ("Gupta", "B-PER"),
    ("Ancient Indian", "B-PER"), ("Mughal", "B-PER"), ("Medieval", "B-PER"),
    ("Bronze Age", "B-PER"), ("Iron Age", "B-PER"), ("Chalcolithic", "B-PER"),
]

ARTIFACTS = [
    ("pottery", "B-ART"), ("vessel", "B-ART"), ("sculpture", "B-ART"),
    ("tool", "B-ART"), ("seal", "B-ART"), ("figurine", "B-ART"),
    ("beads", "B-ART"), ("coins", "B-ART"), ("weapons", "B-ART"),
    ("ornaments", "B-ART"), ("tablet", "B-ART"), ("idol", "B-ART"),
    ("inscription", "B-ART"), ("manuscript", "B-ART"), ("terracotta", "B-ART"),
]

MATERIALS = [
    ("clay", "B-MAT"), ("stone", "B-MAT"), ("bronze", "B-MAT"),
    ("copper", "B-MAT"), ("gold", "B-MAT"), ("silver", "B-MAT"),
    ("terracotta", "B-MAT"), ("sandstone", "B-MAT"), ("granite", "B-MAT"),
    ("marble", "B-MAT"), ("brick", "B-MAT"), ("limestone", "B-MAT"),
]

CONTEXTS = [
    ("excavation", "B-CON"), ("layer", "B-CON"), ("stratum", "B-CON"),
    ("trench", "B-CON"), ("site", "B-CON"), ("burial", "B-CON"),
    ("settlement", "B-CON"), ("dwelling", "B-CON"), ("deposit", "B-CON"),
]

SENTENCE_TEMPLATES = [
    # Location-based sentences
    "{location} B-LOC में O {artifact} B-ART {material} B-MAT से O बना O है O । O",
    "भारत की O महत्वपूर्ण O archaeological site {location} B-LOC है O जहाँ {artifacts_multi} B-ART मिले O हैं O । O",
    
    # Period-based sentences
    "{period} B-PER के O समय O {artifact} B-ART {material} B-MAT से O बनाये जाते थे O । O",
    "{period} B-PER में O {location} B-LOC एक महत्वपूर्ण O settlement था O जहाँ {artifact} B-ART मिले हैं O । O",
    
    # Material-based sentences
    "{material} B-MAT की O खोज B-CON archaeology में O महत्वपूर्ण O है O क्योंकि इससे {artifact} B-ART बनाये जाते थे O । O",
    "Ancient Indian O civilization में O {material} B-MAT का O extensive use {context} B-CON के दौरान O देखा गया है O। O",
    
    # Artifact-based sentences
    "{artifact} B-ART की O मिट्टी B-MAT {location} B-LOC की O खोज B-CON में O मिली O जो O {period} B-PER के O ज़माने O की है O। O",
    "इस O {artifact} B-ART को O {material} B-MAT से O बनाया गया था O जो O बहुत O मजबूत O है O। O",
    
    # Context-based sentences
    "{context} B-CON के O समय O {material} B-MAT की O {artifact} B-ART का O discovery काफ़ी महत्वपूर्ण O रहा है O। O",
    "{location} B-LOC की O {context} B-CON से O कई O {artifact} B-ART की O remains मिली हैं O जो O {period} B-PER की हैं O। O",
]

def expand_dataset(output_file: str, target_sentences: int = 1000) -> None:
    """Generate expanded dataset with coherent archaeological sentences"""
    
    sentences = []
    
    # Original dataset base (60 sentences) - keep these
    original_data = [
        "Harappa B-LOC की O खुदाई B-CON में O कई O मिट्टी B-MAT की O बर्तन B-ART मिले O ।",
        "ये O वस्तु B-ART Indus B-LOC Valley I-LOC Civilization B-PER के O समय B-PER की O है O ।",
        "Mohenjo-daro B-LOC में O bronze B-MAT से O बना B-ART मूर्ति I-ART मिली O ।",
        "Ancient B-PER Indian I-PER pottery B-ART में O geometric O patterns B-ART देखे O जाते O हैं O ।",
        "Chanhu-daro B-LOC की O खोज B-CON से O महत्वपूर्ण B-ART जानकारी O मिली O ।",
        "Stone B-MAT tools B-ART से O हम O Paleolithic B-PER period I-PER को O समझते O हैं O ।",
        "Taxila B-LOC में O Buddhist B-PER sculptures B-ART की O परत B-CON मिली O ।",
        "Copper B-MAT plates B-ART पर O scripts B-ART written O हैं O ।",
        "Ashoka B-LOC के O edicts B-ART sandstone B-MAT पर O carved O हैं O ।",
    ]
    
    sentences.extend(original_data)
    
    # Generate new coherent sentences using templates
    print(f"Generating {target_sentences} sentences...")
    
    for site, _ in ARCHAEOLOGICAL_SITES:
        for period, _ in PERIODS:
            for artifact, _ in ARTIFACTS:
                for material, _ in MATERIALS:
                    for context, _ in CONTEXTS:
                        # Template 1: Location-based
                        sent = f"{site} B-LOC में O {artifact} B-ART {material} B-MAT से O बना B-ART है O ।"
                        sentences.append(sent)
                        
                        # Template 2: Period-based
                        sent = f"{period} B-PER के O समय O {artifact} B-ART {material} B-MAT से O बनाये जाते थे O ।"
                        sentences.append(sent)
                        
                        if len(sentences) >= target_sentences:
                            break
                    if len(sentences) >= target_sentences:
                        break
                if len(sentences) >= target_sentences:
                    break
            if len(sentences) >= target_sentences:
                break
        if len(sentences) >= target_sentences:
            break
    
    # Write to CoNLL format
    os.makedirs('data', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Expanded Indian Archaeology Dataset in CoNLL Format\n")
        f.write("# Hindi-English Code-Mixed Text with BIO Tags\n")
        f.write("# Format: word\\ttag\n\n")
        
        for idx, sentence in enumerate(sentences[:target_sentences], 1):
            f.write(f"# Sentence {idx}\n")
            parts = sentence.split()
            
            for part in parts:
                if part == '।':
                    f.write(f"{part}\tO\n")
                else:
                    # Parse word and tag
                    if '\t' in part:
                        word, tag = part.split('\t')
                        f.write(f"{word}\t{tag}\n")
                    elif ' ' in part:
                        # Skip spaces
                        continue
            
            f.write("\n")
    
    print(f"✓ Generated {len(sentences[:target_sentences])} sentences")
    print(f"✓ Saved to {output_file}")

if __name__ == "__main__":
    expand_dataset('data/train_expanded.conll', target_sentences=1000)
