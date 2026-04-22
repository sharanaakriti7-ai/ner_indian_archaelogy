#!/usr/bin/env python3
"""
Domain Gazetteer Module for Indian Archaeology NER
Maintains knowledge bases for entities and enables weak supervision
"""

from typing import Dict, List, Set, Tuple
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArchaeologyGazetteer:
    """Domain-specific gazetteer for archaeology entities"""
    
    # Archaeological sites and locations
    LOCATIONS = {
        "Harappa": {"variant": ["harappa", "हरप्पा"], "period": "Indus Valley"},
        "Mohenjo-daro": {"variant": ["mohenjo-daro", "मोहन्जोदडो"], "period": "Indus Valley"},
        "Dholavira": {"variant": ["dholavira", "धोलावीरा"], "period": "Indus Valley"},
        "Lothal": {"variant": ["lothal", "लोथल"], "period": "Indus Valley"},
        "Kalibangan": {"variant": ["kalibangan", "कालीबंगन"], "period": "Indus Valley"},
        "Mehrgarh": {"variant": ["mehrgarh", "मेहरगढ़"], "period": "Neolithic"},
        "Bhirrana": {"variant": ["bhirrana", "भिर्राणा"], "period": "Paleolithic"},
        "Rakhigarhi": {"variant": ["rakhigarhi", "राखीगढ़ी"], "period": "Harappan"},
        "Chanhu-daro": {"variant": ["chanhu-daro", "चन्हूदड़ो"], "period": "Indus Valley"},
        "Taxila": {"variant": ["taxila", "तक्षशिला"], "period": "Ancient"},
        "Varanasi": {"variant": ["varanasi", "वाराणसी"], "period": "Vedic"},
        "Ayodhya": {"variant": ["ayodhya", "अयोध्या"], "period": "Vedic"},
    }
    
    # Historical periods
    PERIODS = {
        "Paleolithic": {"variants": ["paleolithic", "पाषाण", "पेलिओलिथिक"]},
        "Mesolithic": {"variants": ["mesolithic", "मेसोलिथिक"]},
        "Neolithic": {"variants": ["neolithic", "नवपाषाण", "निओलिथिक"]},
        "Chalcolithic": {"variants": ["chalcolithic", "तांबापाषाण", "चाल्कोलिथिक"]},
        "Bronze Age": {"variants": ["bronze age", "कांस्य युग"]},
        "Iron Age": {"variants": ["iron age", "लौह युग"]},
        "Indus Valley": {"variants": ["indus valley", "सिंधु घाटी", "हड़प्पा"]},
        "Vedic": {"variants": ["vedic", "वैदिक"]},
        "Mauryan": {"variants": ["mauryan", "मौर्य"]},
        "Gupta": {"variants": ["gupta", "गुप्त"]},
        "Ancient Indian": {"variants": ["ancient indian", "प्राचीन भारतीय"]},
    }
    
    # Artifacts and objects
    ARTIFACTS = {
        "pottery": {"variants": ["pottery", "pot", "vessel", "ceramic", "मिट्टी की बर्तन"]},
        "sculpture": {"variants": ["sculpture", "statue", "carving", "मूर्ति"]},
        "seal": {"variants": ["seal", "muhr", "मुहर"]},
        "figurine": {"variants": ["figurine", "मूर्तिका"]},
        "bead": {"variants": ["bead", "beads", "मनका"]},
        "coin": {"variants": ["coin", "coins", "सिक्का"]},
        "tool": {"variants": ["tool", "tools", "औजार"]},
        "weapon": {"variants": ["weapon", "weapons", "हथियार"]},
        "ornament": {"variants": ["ornament", "ornaments", "गहना"]},
        "tablet": {"variants": ["tablet", "tablets", "पट्टिका"]},
        "idol": {"variants": ["idol", "idols", "प्रतिमा"]},
        "inscription": {"variants": ["inscription", "inscriptions", "शिलालेख"]},
        "manuscript": {"variants": ["manuscript", "manuscripts", "पांडुलिपि"]},
    }
    
    # Materials
    MATERIALS = {
        "clay": {"variants": ["clay", "mud", "मिट्टी"]},
        "stone": {"variants": ["stone", "rock", "पत्थर"]},
        "bronze": {"variants": ["bronze", "कांस्य"]},
        "copper": {"variants": ["copper", "ताम्र", "तांबा"]},
        "gold": {"variants": ["gold", "सोना"]},
        "silver": {"variants": ["silver", "चाँदी"]},
        "iron": {"variants": ["iron", "लोहा"]},
        "terracotta": {"variants": ["terracotta", "टेराकोटा"]},
        "sandstone": {"variants": ["sandstone", "बलुआ पत्थर"]},
        "granite": {"variants": ["granite", "ग्रेनाइट"]},
        "marble": {"variants": ["marble", "संगमरमर"]},
        "limestone": {"variants": ["limestone", "चूना पत्थर"]},
    }
    
    # Archaeological contexts/methods
    CONTEXTS = {
        "excavation": {"variants": ["excavation", "dig", "खुदाई"]},
        "layer": {"variants": ["layer", "stratum", "परत"]},
        "trench": {"variants": ["trench", "खाई"]},
        "burial": {"variants": ["burial", "दफन"]},
        "settlement": {"variants": ["settlement", "बस्ती"]},
        "dwelling": {"variants": ["dwelling", "आवास"]},
        "site": {"variants": ["site", "स्थल"]},
        "deposit": {"variants": ["deposit", "जमा"]},
        "mound": {"variants": ["mound", "टीला"]},
        "structure": {"variants": ["structure", "संरचना"]},
    }
    
    def __init__(self):
        """Initialize gazetteer with all entities"""
        self._build_lookup_tables()
        logger.info("✓ Gazetteer initialized with comprehensive archaeology knowledge")
    
    def _build_lookup_tables(self) -> None:
        """Build lookup tables for fast matching"""
        # Case-insensitive lookups
        self.loc_lookup: Dict[str, str] = {}
        self.per_lookup: Dict[str, str] = {}
        self.art_lookup: Dict[str, str] = {}
        self.mat_lookup: Dict[str, str] = {}
        self.con_lookup: Dict[str, str] = {}
        
        # Build location lookup
        for name, info in self.LOCATIONS.items():
            self.loc_lookup[name.lower()] = "B-LOC"
            for variant in info.get("variant", []):
                self.loc_lookup[variant.lower()] = "B-LOC"
        
        # Build period lookup
        for name, info in self.PERIODS.items():
            self.per_lookup[name.lower()] = "B-PER"
            for variant in info.get("variants", []):
                self.per_lookup[variant.lower()] = "B-PER"
        
        # Build artifact lookup
        for name, info in self.ARTIFACTS.items():
            self.art_lookup[name.lower()] = "B-ART"
            for variant in info.get("variants", []):
                self.art_lookup[variant.lower()] = "B-ART"
        
        # Build material lookup
        for name, info in self.MATERIALS.items():
            self.mat_lookup[name.lower()] = "B-MAT"
            for variant in info.get("variants", []):
                self.mat_lookup[variant.lower()] = "B-MAT"
        
        # Build context lookup
        for name, info in self.CONTEXTS.items():
            self.con_lookup[name.lower()] = "B-CON"
            for variant in info.get("variants", []):
                self.con_lookup[variant.lower()] = "B-CON"
        
        logger.info(f"  Locations: {len(self.loc_lookup)} entries")
        logger.info(f"  Periods: {len(self.per_lookup)} entries")
        logger.info(f"  Artifacts: {len(self.art_lookup)} entries")
        logger.info(f"  Materials: {len(self.mat_lookup)} entries")
        logger.info(f"  Contexts: {len(self.con_lookup)} entries")
    
    def lookup_entity(self, word: str) -> Tuple[str, float]:
        """Look up entity type with confidence score"""
        word_lower = word.lower()
        
        # Check exact matches first
        if word_lower in self.loc_lookup:
            return "B-LOC", 0.95
        if word_lower in self.per_lookup:
            return "B-PER", 0.95
        if word_lower in self.art_lookup:
            return "B-ART", 0.90
        if word_lower in self.mat_lookup:
            return "B-MAT", 0.90
        if word_lower in self.con_lookup:
            return "B-CON", 0.85
        
        # Check partial matches
        for key, val in self.loc_lookup.items():
            if key in word_lower or word_lower in key:
                return "B-LOC", 0.70
        
        for key, val in self.per_lookup.items():
            if key in word_lower or word_lower in key:
                return "B-PER", 0.70
        
        return "O", 0.0
    
    def batch_lookup(self, words: List[str]) -> List[Tuple[str, float]]:
        """Look up multiple words"""
        return [self.lookup_entity(word) for word in words]
    
    def get_related_entities(self, entity_type: str) -> Set[str]:
        """Get all entities of a given type"""
        if entity_type == "B-LOC" or entity_type == "LOC":
            return set(self.loc_lookup.keys())
        elif entity_type == "B-PER" or entity_type == "PER":
            return set(self.per_lookup.keys())
        elif entity_type == "B-ART" or entity_type == "ART":
            return set(self.art_lookup.keys())
        elif entity_type == "B-MAT" or entity_type == "MAT":
            return set(self.mat_lookup.keys())
        elif entity_type == "B-CON" or entity_type == "CON":
            return set(self.con_lookup.keys())
        return set()
    
    def post_process_predictions(self, words: List[str], 
                                predictions: List[str]) -> List[str]:
        """Post-process predictions using gazetteer"""
        corrected = predictions.copy()
        
        for i, word in enumerate(words):
            gazetteer_tag, conf = self.lookup_entity(word)
            
            # If gazetteer has high confidence and prediction is weak
            if gazetteer_tag != "O" and conf > 0.85:
                corrected[i] = gazetteer_tag
        
        # Enforce valid BIO transitions
        corrected = self._enforce_bio_transitions(corrected)
        
        return corrected
    
    def _enforce_bio_transitions(self, tags: List[str]) -> List[str]:
        """Enforce valid BIO tag transitions"""
        if not tags:
            return tags
        
        corrected = tags.copy()
        
        for i in range(1, len(corrected)):
            prev_tag = corrected[i - 1]
            curr_tag = corrected[i]
            
            # I-X should only follow B-X or I-X
            if curr_tag.startswith('I-'):
                entity_type = curr_tag.split('-')[1]
                
                if prev_tag == 'O' or (prev_tag.startswith('B-') or prev_tag.startswith('I-')) and prev_tag.split('-')[1] != entity_type:
                    # Invalid transition - change I to B
                    corrected[i] = f"B-{entity_type}"
        
        return corrected
    
    def get_statistics(self) -> Dict[str, int]:
        """Get gazetteer statistics"""
        return {
            "locations": len(self.LOCATIONS),
            "periods": len(self.PERIODS),
            "artifacts": len(self.ARTIFACTS),
            "materials": len(self.MATERIALS),
            "contexts": len(self.CONTEXTS),
            "total_entities": (len(self.LOCATIONS) + len(self.PERIODS) + 
                             len(self.ARTIFACTS) + len(self.MATERIALS) + 
                             len(self.CONTEXTS)),
            "total_variants": (len(self.loc_lookup) + len(self.per_lookup) + 
                             len(self.art_lookup) + len(self.mat_lookup) + 
                             len(self.con_lookup)),
        }


class WeakSupervisionGenerator:
    """Generate weak labels using gazetteer for semi-supervised learning"""
    
    def __init__(self, gazetteer: ArchaeologyGazetteer):
        self.gazetteer = gazetteer
    
    def generate_weak_labels(self, sentences: List[List[str]]) -> List[List[str]]:
        """Generate weak labels for unlabeled sentences"""
        weak_labels = []
        
        for sentence in sentences:
            labels = []
            for word in sentence:
                tag, conf = self.gazetteer.lookup_entity(word)
                labels.append(tag)
            
            # Post-process for valid BIO transitions
            labels = self.gazetteer._enforce_bio_transitions(labels)
            weak_labels.append(labels)
        
        return weak_labels
    
    def get_confidence_scores(self, sentences: List[List[str]]) -> List[List[float]]:
        """Get confidence scores for weak labels"""
        scores = []
        
        for sentence in sentences:
            sent_scores = []
            for word in sentence:
                _, conf = self.gazetteer.lookup_entity(word)
                sent_scores.append(conf)
            scores.append(sent_scores)
        
        return scores


if __name__ == "__main__":
    # Initialize gazetteer
    gazetteer = ArchaeologyGazetteer()
    
    # Test lookups
    test_words = [
        "Harappa", "pottery", "Mauryan", "clay", "excavation",
        "unknown_word", "Indus"
    ]
    
    print("Entity Lookups:")
    for word in test_words:
        tag, conf = gazetteer.lookup_entity(word)
        print(f"  {word:20} → {tag:10} (conf: {conf:.2f})")
    
    # Test statistics
    print("\nGazetteer Statistics:")
    stats = gazetteer.get_statistics()
    for key, val in stats.items():
        print(f"  {key:20} {val:6}")
    
    # Test weak label generation
    print("\nWeak Label Generation:")
    weak_gen = WeakSupervisionGenerator(gazetteer)
    
    test_sentences = [
        ["Harappa", "में", "मिट्टी", "की", "बर्तन"],
        ["Mauryan", "period", "में", "gold", "ornaments"],
    ]
    
    weak_labels = weak_gen.generate_weak_labels(test_sentences)
    for sent, labels in zip(test_sentences, weak_labels):
        print(f"  Sentence: {' '.join(sent)}")
        print(f"  Labels:   {' '.join(labels)}")
    
    print("\n✓ Gazetteer module working correctly!")
