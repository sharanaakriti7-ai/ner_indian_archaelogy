#!/usr/bin/env python3
"""Data cleaning and augmentation script for Indian Archaeology NER"""

import os
import sys
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent))

# New data from user
NEW_SENTENCES = """
Sentence 1:
Excavators O
recorded O
Harappan B-PER
pottery B-ART
shards O
in O
trench B-CON
5 I-CON
near O
Harappa B-LOC

Sentence 2:
Achaemenid O
influence O
is O
noted O
in O
the O
300 B-PER
BCE I-PER
layers I-PER

Sentence 3:
The O
survey O
covered O
Mohenjo-daro B-LOC
and O
adjacent O
settlements O

Sentence 4:
Samples O
showed O
high O
copper B-MAT
content O

Sentence 5:
Field O
notes O
mention O
trench B-CON
A I-CON
as O
the O
primary O
context O

Sentence 6:
A O
fragment O
of O
a O
terracotta B-ART
figurine O
was O
catalogued O

Sentence 7:
Radiocarbon O
dates O
suggest O
Late B-PER
Harappan I-PER
phase I-PER

Sentence 8:
The O
team O
mapped O
the O
Indus B-LOC
Valley I-LOC
survey I-LOC

Sentence 9:
Microscopic O
analysis O
identified O
bronze B-MAT
alloy O

Sentence 10:
Excavation O
records O
list O
burial B-CON
2 I-CON
as O
a O
secondary O
deposit O

Sentence 11:
A O
copper B-ART
axe O
was O
photographed O

Sentence 12:
Stratigraphy O
places O
this O
find O
in O
the O
Gupta B-PER
period I-PER

Sentence 13:
The O
site O
at O
Dholavira B-LOC
has O
multiple O
mounds O

Sentence 14:
Residue O
tests O
detected O
organic O
residues O
on O
terracotta B-MAT

Sentence 15:
Contextual O
notes O
refer O
to O
layer B-CON
IV I-CON

Sentence 16:
A O
string O
of O
faience B-ART
beads O
was O
recorded O

Sentence 17:
Estimated O
occupation O
dates O
range O
from O
2600 B-PER
BCE I-PER
to O
1900 O

Sentence 18:
Surface O
survey O
near O
Rakhigarhi B-LOC
yielded O
shards O

Sentence 19:
Metallurgical O
reports O
mention O
tin B-MAT
traces O

Sentence 20:
The O
excavation O
team O
noted O
a O
burnt O
layer B-CON

Sentence 21:
A O
stone B-ART
celt O
was O
measured O

Sentence 22:
Ceramic O
typology O
is O
consistent O
with O
Early B-PER
Harappan I-PER

Sentence 23:
The O
archaeological O
survey O
mapped O
Lothal B-LOC

Sentence 24:
Thin-section O
analysis O
identified O
quartz B-MAT
grains O

Sentence 25:
Field O
journal O
records O
trench B-CON
12 I-CON
as O
a O
wet O
context O

Sentence 26:
A O
bronze B-ART
mirror O
was O
listed O

Sentence 27:
Pottery O
styles O
are O
dated O
to O
the O
Kushan B-PER
period I-PER

Sentence 28:
Remote O
sensing O
highlighted O
the O
Ghaggar B-LOC
riverbed I-LOC

Sentence 29:
Chemical O
tests O
showed O
lead B-MAT
contamination O

Sentence 30:
The O
report O
describes O
a O
secondary O
burial B-CON

Sentence 31:
A O
carved B-ART
seal O
was O
photographed O

Sentence 32:
Stratigraphic O
correlation O
links O
this O
horizon O
to O
the O
Iron B-PER
Age I-PER

Sentence 33:
Excavators O
noted O
a O
fortification O
at O
Kalibangan B-LOC

Sentence 34:
Microwear O
analysis O
suggests O
flint B-MAT
was O
used O
for O
cutting O

Sentence 35:
The O
context O
sheet O
labels O
layer B-CON
3 I-CON

Sentence 36:
A O
bronze B-ART
pin O
was O
found O

Sentence 37:
Ceramic O
phases O
are O
assigned O
to O
the O
Post-Gupta B-PER
period I-PER

Sentence 38:
Field O
teams O
surveyed O
the O
Sutlej B-LOC
floodplain I-LOC

Sentence 39:
Elemental O
analysis O
detected O
arsenic B-MAT

Sentence 40:
The O
excavation O
log O
records O
a O
trench B-CON
collapse O

Sentence 41:
A O
copper B-ART
pin O
was O
catalogued O

Sentence 42:
Typological O
comparison O
places O
this O
assemblage O
in O
the O
Early B-PER
Historic I-PER
period I-PER

Sentence 43:
The O
survey O
mapped O
Banawali B-LOC

Sentence 44:
Petrographic O
study O
identified O
shale B-MAT

Sentence 45:
Context O
notes O
mention O
a O
burial B-CON
pit I-CON

Sentence 46:
A O
terracotta B-ART
bangle O
was O
recorded O

Sentence 47:
Radiocarbon O
calibration O
gives O
a O
range O
around O
1500 B-PER
BCE I-PER

Sentence 48:
The O
excavation O
mapped O
the O
Narmada B-LOC
terrace I-LOC

Sentence 49:
X-ray O
fluorescence O
detected O
zinc B-MAT

Sentence 50:
Field O
notes O
list O
trench B-CON
7 I-CON
as O
sterile O

Sentence 51:
A O
stone B-ART
bead O
was O
measured O

Sentence 52:
Ceramic O
sequence O
is O
assigned O
to O
the O
Maurya B-PER
period I-PER

Sentence 53:
The O
team O
recorded O
a O
settlement O
at O
Ropar B-LOC

Sentence 54:
Compositional O
analysis O
showed O
silver B-MAT
in O
trace O
amounts O

Sentence 55:
The O
context O
form O
notes O
a O
posthole B-CON

Sentence 56:
A O
carved B-ART
terracotta O
panel O
was O
photographed O

Sentence 57:
Chronology O
places O
this O
phase O
in O
the O
Sunga B-PER
period I-PER

Sentence 58:
Geophysical O
survey O
identified O
an O
anomaly O
near O
Harappa B-LOC

Sentence 59:
Metallography O
revealed O
copper B-MAT
grain O
structure O

Sentence 60:
Excavation O
notes O
record O
a O
sealed B-CON
deposit I-CON

Sentence 61:
A O
bronze B-ART
figurine O
was O
listed O

Sentence 62:
Typology O
suggests O
Late B-PER
Harappan I-PER
occupation I-PER

Sentence 63:
The O
survey O
documented O
Dholavira B-LOC
mound I-LOC

Sentence 64:
Elemental O
spectra O
showed O
phosphorus B-MAT

Sentence 65:
Contextual O
records O
note O
a O
trench B-CON
edge I-CON

Sentence 66:
A O
polished B-ART
stone O
axe O
was O
catalogued O

Sentence 67:
Radiocarbon O
results O
indicate O
circa O
500 B-PER
CE I-PER

Sentence 68:
The O
excavation O
mapped O
the O
Ghazi B-LOC
mound I-LOC

Sentence 69:
Microscopic O
residue O
analysis O
found O
bitumen B-MAT

Sentence 70:
Field O
notes O
describe O
a O
secondary B-CON
fill I-CON

Sentence 71:
A O
copper B-ART
amulet O
was O
photographed O

Sentence 72:
Stratigraphy O
links O
this O
horizon O
to O
the O
Late B-PER
Bronze I-PER
Age I-PER

Sentence 73:
The O
survey O
recorded O
a O
site O
near O
Sarnath B-LOC

Sentence 74:
Petrographic O
analysis O
identified O
sandstone B-MAT

Sentence 75:
Context O
sheets O
note O
a O
burial B-CON
cluster I-CON

Sentence 76:
A O
faience B-ART
pendant O
was O
listed O

Sentence 77:
Ceramic O
phases O
are O
assigned O
to O
the O
Chalcolithic B-PER
period I-PER

Sentence 78:
Remote O
survey O
mapped O
the O
Saraswati B-LOC
course I-LOC

Sentence 79:
XRF O
analysis O
detected O
manganese B-MAT

Sentence 80:
Excavation O
logs O
record O
a O
trench B-CON
backfill I-CON

Sentence 81:
A O
carved B-ART
seal O
impression O
was O
photographed O

Sentence 82:
Typological O
comparison O
dates O
the O
assemblage O
to O
the O
Kushan B-PER
era I-PER

Sentence 83:
The O
team O
surveyed O
the O
Banawali B-LOC
perimeter I-LOC

Sentence 84:
Metallurgical O
tests O
showed O
bronze B-MAT
patination O

Sentence 85:
Context O
records O
list O
a O
layer B-CON
with O
ash O

Sentence 86:
A O
terracotta B-ART
rhyton O
was O
catalogued O

Sentence 87:
Radiocarbon O
calibration O
places O
this O
sample O
around O
1200 B-PER
BCE I-PER

Sentence 88:
The O
excavation O
mapped O
a O
settlement O
at O
Harappa B-LOC

Sentence 89:
Microscopic O
study O
identified O
hematite B-MAT

Sentence 90:
Field O
notes O
describe O
a O
trench B-CON
section I-CON

Sentence 91:
A O
bronze B-ART
spearhead O
was O
recorded O

Sentence 92:
Ceramic O
sequence O
is O
linked O
to O
the O
Early B-PER
Historic I-PER

Sentence 93:
The O
survey O
documented O
Rakhigarhi B-LOC
platform I-LOC

Sentence 94:
Elemental O
analysis O
detected O
cobalt B-MAT

Sentence 95:
Context O
forms O
note O
a O
burial B-CON
trench I-CON

Sentence 96:
A O
stone B-ART
cutter O
was O
measured O

Sentence 97:
Typology O
places O
this O
assemblage O
in O
the O
Gupta B-PER
period I-PER

Sentence 98:
Remote O
sensing O
identified O
an O
ancient O
channel O
near O
Dholavira B-LOC

Sentence 99:
Petrographic O
study O
showed O
granite B-MAT

Sentence 100:
Excavation O
notes O
record O
a O
sealed B-CON
floor I-CON

Sentence 101:
A O
faience B-ART
bead O
was O
catalogued O

Sentence 102:
Radiocarbon O
dates O
suggest O
circa O
200 B-PER
CE I-PER

Sentence 103:
The O
team O
surveyed O
the O
Sutlej B-LOC
terrace I-LOC

Sentence 104:
Chemical O
analysis O
detected O
phosphate B-MAT

Sentence 105:
Contextual O
records O
note O
a O
trench B-CON
boundary I-CON

Sentence 106:
A O
polished B-ART
copper O
mirror O
was O
recorded O

Sentence 107:
Typology O
links O
this O
assemblage O
to O
the O
Post-Gupta B-PER
period I-PER

Sentence 108:
The O
survey O
mapped O
Kalibangan B-LOC
mounds I-LOC

Sentence 109:
Microwear O
analysis O
suggests O
flint B-MAT
was O
used O
as O
a O
cutting O
implement O

Sentence 110:
Field O
notes O
describe O
a O
secondary B-CON
deposit I-CON

Sentence 111:
A O
bronze B-ART
buckle O
was O
photographed O

Sentence 112:
Ceramic O
phases O
are O
assigned O
to O
the O
Maurya B-PER
period I-PER

Sentence 113:
The O
excavation O
mapped O
a O
site O
near O
Sarnath B-LOC

Sentence 114:
Petrographic O
analysis O
identified O
limestone B-MAT

Sentence 115:
Context O
sheets O
note O
a O
burial B-CON
cluster I-CON

Sentence 116:
A O
terracotta B-ART
disk O
was O
listed O

Sentence 117:
Radiocarbon O
calibration O
gives O
a O
range O
around O
800 B-PER
BCE I-PER

Sentence 118:
The O
team O
surveyed O
the O
Ghaggar B-LOC
floodplain I-LOC

Sentence 119:
XRF O
spectra O
showed O
nickel B-MAT

Sentence 120:
Excavation O
logs O
record O
a O
trench B-CON
fill I-CON

Sentence 121:
A O
carved B-ART
seal O
was O
catalogued O

Sentence 122:
Typological O
comparison O
places O
this O
assemblage O
in O
the O
Kushan B-PER
period I-PER

Sentence 123:
The O
survey O
documented O
Lothal B-LOC

Sentence 124:
Metallurgical O
tests O
detected O
tin B-MAT

Sentence 125:
Contextual O
notes O
mention O
a O
trench B-CON
edge I-CON

Sentence 126:
A O
stone B-ART
celt O
was O
photographed O

Sentence 127:
Ceramic O
typology O
is O
consistent O
with O
the O
Late B-PER
Harappan I-PER
phase I-PER

Sentence 128:
The O
excavation O
mapped O
the O
Indus B-LOC
Valley I-LOC

Sentence 129:
Microscopic O
analysis O
identified O
hematite B-MAT

Sentence 130:
Field O
notes O
record O
a O
sealed B-CON
deposit I-CON

Sentence 131:
A O
bronze B-ART
pin O
was O
listed O

Sentence 132:
Radiocarbon O
results O
indicate O
circa O
50 B-PER
BCE I-PER

Sentence 133:
The O
team O
surveyed O
the O
Ropar B-LOC
mound I-LOC

Sentence 134:
Petrographic O
study O
identified O
shale B-MAT

Sentence 135:
Context O
forms O
note O
a O
posthole B-CON

Sentence 136:
A O
terracotta B-ART
bangle O
was O
recorded O

Sentence 137:
Typology O
suggests O
Early B-PER
Historic I-PER

Sentence 138:
Remote O
sensing O
highlighted O
an O
ancient O
channel O
near O
Dholavira B-LOC

Sentence 139:
Elemental O
analysis O
detected O
zinc B-MAT

Sentence 140:
Excavation O
notes O
describe O
a O
trench B-CON
collapse I-CON

Sentence 141:
A O
stone B-ART
bead O
was O
catalogued O

Sentence 142:
Ceramic O
sequence O
is O
assigned O
to O
the O
Gupta B-PER
period I-PER

Sentence 143:
The O
survey O
mapped O
Banawali B-LOC

Sentence 144:
Microwear O
analysis O
suggests O
flint B-ART
was O
used O
as O
a O
tool O

Sentence 145:
Field O
notes O
list O
trench B-CON
9 I-CON
as O
sterile O

Sentence 146:
A O
bronze B-ART
mirror O
was O
photographed O

Sentence 147:
Radiocarbon O
calibration O
places O
this O
sample O
around O
300 B-PER
BCE I-PER

Sentence 148:
The O
excavation O
mapped O
the O
Kalibangan B-LOC
mounds I-LOC

Sentence 149:
Chemical O
tests O
showed O
lead B-MAT
traces O

Sentence 150:
Contextual O
records O
note O
a O
burial B-CON
pit I-CON

Sentence 151:
A O
faience B-ART
pendant O
was O
listed O

Sentence 152:
Typology O
places O
this O
assemblage O
in O
the O
Chalcolithic B-PER
period I-PER

Sentence 153:
Remote O
survey O
mapped O
the O
Sutlej B-LOC
terrace I-LOC

Sentence 154:
XRF O
analysis O
detected O
manganese B-MAT

Sentence 155:
Excavation O
logs O
record O
a O
trench B-CON
backfill I-CON

Sentence 156:
A O
carved B-ART
seal O
impression O
was O
photographed O

Sentence 157:
Ceramic O
phases O
are O
assigned O
to O
the O
Maurya B-PER
period I-PER

Sentence 158:
The O
team O
surveyed O
the O
Ghaggar B-LOC

Sentence 159:
Petrographic O
analysis O
identified O
sandstone B-MAT

Sentence 160:
Context O
sheets O
note O
a O
burial B-CON
cluster I-CON

Sentence 161:
A O
terracotta B-ART
rhyton O
was O
catalogued O

Sentence 162:
Radiocarbon O
calibration O
gives O
a O
range O
around O
1500 B-PER
BCE I-PER

Sentence 163:
The O
excavation O
mapped O
a O
settlement O
at O
Harappa B-LOC

Sentence 164:
Microscopic O
study O
identified O
hematite B-MAT

Sentence 165:
Field O
notes O
describe O
a O
trench B-CON
section I-CON

Sentence 166:
A O
bronze B-ART
spearhead O
was O
recorded O

Sentence 167:
Typology O
links O
this O
assemblage O
to O
the O
Kushan B-PER
period I-PER

Sentence 168:
The O
survey O
documented O
Rakhigarhi B-LOC

Sentence 169:
Metallurgical O
tests O
detected O
tin B-MAT

Sentence 170:
Contextual O
notes O
mention O
a O
trench B-CON
edge I-CON

Sentence 171:
A O
stone B-ART
cutter O
was O
measured O

Sentence 172:
Ceramic O
typology O
is O
consistent O
with O
Late B-PER
Harappan I-PER
phase I-PER

Sentence 173:
The O
excavation O
mapped O
the O
Indus B-LOC
Valley I-LOC

Sentence 174:
Microscopic O
analysis O
identified O
quartz B-MAT
grains O

Sentence 175:
Field O
notes O
record O
a O
sealed B-CON
deposit I-CON

Sentence 176:
A O
bronze B-ART
pin O
was O
listed O

Sentence 177:
Radiocarbon O
results O
indicate O
circa O
500 B-PER
CE I-PER

Sentence 178:
The O
team O
surveyed O
the O
Dholavira B-LOC
mound I-LOC

Sentence 179:
Petrographic O
study O
identified O
granite B-MAT

Sentence 180:
Context O
forms O
note O
a O
posthole B-CON

Sentence 181:
A O
terracotta B-ART
disk O
was O
listed O

Sentence 182:
Typology O
suggests O
Early B-PER
Historic I-PER

Sentence 183:
Remote O
sensing O
highlighted O
an O
ancient O
channel O
near O
Banawali B-LOC

Sentence 184:
Elemental O
analysis O
detected O
phosphorus B-MAT

Sentence 185:
Excavation O
notes O
describe O
a O
trench B-CON
collapse I-CON

Sentence 186:
A O
stone B-ART
bead O
was O
catalogued O

Sentence 187:
Ceramic O
sequence O
is O
assigned O
to O
the O
Gupta B-PER
period I-PER

Sentence 188:
The O
survey O
mapped O
Kalibangan B-LOC

Sentence 189:
Microwear O
analysis O
suggests O
flint B-ART
was O
used O
as O
an O
implement O

Sentence 190:
Field O
notes O
list O
trench B-CON
11 I-CON
as O
sterile O

Sentence 191:
A O
bronze B-ART
buckle O
was O
photographed O

Sentence 192:
Radiocarbon O
calibration O
places O
this O
sample O
around O
1200 B-PER
BCE I-PER

Sentence 193:
The O
excavation O
mapped O
the O
Sutlej B-LOC

Sentence 194:
Chemical O
tests O
showed O
lead B-MAT
contamination O

Sentence 195:
Contextual O
records O
note O
a O
burial B-CON
cluster I-CON

Sentence 196:
A O
faience B-ART
pendant O
was O
listed O

Sentence 197:
Typology O
places O
this O
assemblage O
in O
the O
Chalcolithic B-PER
period I-PER

Sentence 198:
Remote O
survey O
mapped O
the O
Ghaggar B-LOC

Sentence 199:
Petrographic O
analysis O
identified O
sandstone B-MAT

Sentence 200:
Context O
sheets O
note O
a O
trench B-CON
boundary I-CON

Sentence 201:
A O
polished B-ART
stone O
axe O
was O
catalogued O

Sentence 202:
Radiocarbon O
results O
suggest O
circa O
50 B-PER
CE I-PER

Sentence 203:
The O
team O
surveyed O
the O
Ropar B-LOC

Sentence 204:
Microscopic O
study O
identified O
hematite B-MAT

Sentence 205:
Field O
notes O
describe O
a O
trench B-CON
section I-CON

Sentence 206:
A O
bronze B-ART
spearhead O
was O
recorded O

Sentence 207:
Typology O
links O
this O
assemblage O
to O
the O
Kushan B-PER
period I-PER

Sentence 208:
The O
survey O
documented O
Lothal B-LOC

Sentence 209:
Metallurgical O
tests O
detected O
tin B-MAT

Sentence 210:
Contextual O
notes O
mention O
a O
trench B-CON
edge I-CON

Sentence 211:
A O
stone B-ART
cutter O
was O
measured O

Sentence 212:
Ceramic O
typology O
is O
consistent O
with O
Late B-PER
Harappan I-PER
phase I-PER

Sentence 213:
The O
excavation O
mapped O
the O
Indus B-LOC
Valley I-LOC

Sentence 214:
Microscopic O
analysis O
identified O
quartz B-MAT
grains O

Sentence 215:
Field O
notes O
record O
a O
sealed B-CON
deposit I-CON

Sentence 216:
A O
bronze B-ART
pin O
was O
listed O

Sentence 217:
Radiocarbon O
results O
indicate O
circa O
300 B-PER
CE I-PER

Sentence 218:
The O
team O
surveyed O
the O
Dholavira B-LOC

Sentence 219:
Petrographic O
study O
identified O
granite B-MAT

Sentence 220:
Context O
forms O
note O
a O
posthole B-CON
"""

def parse_new_data(text):
    """Parse new sentences from text format"""
    sentences = []
    current_sentence = []
    
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            if current_sentence:
                sentences.append(current_sentence)
                current_sentence = []
        elif line.startswith('Sentence'):
            continue
        else:
            parts = line.split()
            if len(parts) == 2:
                token, label = parts
                current_sentence.append((token, label))
    
    if current_sentence:
        sentences.append(current_sentence)
    
    return sentences

def validate_tags(sentences):
    """Validate BIO tags"""
    valid_tags = {'O', 'B-ART', 'I-ART', 'B-PER', 'I-PER', 'B-LOC', 'I-LOC', 
                  'B-MAT', 'I-MAT', 'B-CON', 'I-CON'}
    
    invalid_count = 0
    for sent_idx, sentence in enumerate(sentences):
        for token_idx, (token, label) in enumerate(sentence):
            if label not in valid_tags:
                print(f"[WARN] Sentence {sent_idx}, Token {token_idx}: Invalid tag '{label}' for token '{token}'")
                invalid_count += 1
                # Fix invalid tags
                if label not in valid_tags:
                    label = 'O'
                    sentences[sent_idx][token_idx] = (token, label)
    
    if invalid_count == 0:
        print(f"[PASS] All {len(sentences)} sentences have valid BIO tags")
    else:
        print(f"[WARN] Fixed {invalid_count} invalid tags")
    
    return sentences

def remove_duplicates(sentences):
    """Remove duplicate sentences"""
    seen = set()
    unique = []
    duplicates = 0
    
    for sentence in sentences:
        # Convert to tuple for hashing
        sent_tuple = tuple((token, label) for token, label in sentence)
        if sent_tuple not in seen:
            seen.add(sent_tuple)
            unique.append(sentence)
        else:
            duplicates += 1
    
    if duplicates == 0:
        print(f"[PASS] No duplicate sentences found")
    else:
        print(f"[WARN] Removed {duplicates} duplicate sentences")
    
    return unique

def save_conll_format(sentences, filename, start_idx=1):
    """Save sentences in CoNLL format"""
    with open(filename, 'w', encoding='utf-8') as f:
        for idx, sentence in enumerate(sentences, start=start_idx):
            f.write(f"# Sentence {idx}\n")
            for token, label in sentence:
                f.write(f"{token}\t{label}\n")
            f.write("\n")
    print(f"[PASS] Saved {len(sentences)} sentences to {filename}")

def get_statistics(sentences):
    """Get dataset statistics"""
    total_tokens = sum(len(sent) for sent in sentences)
    
    label_counts = Counter()
    entity_types = Counter()
    
    for sentence in sentences:
        for token, label in sentence:
            label_counts[label] += 1
            if label != 'O':
                entity_type = label.split('-')[1]
                entity_types[entity_type] += 1
    
    return {
        'sentences': len(sentences),
        'tokens': total_tokens,
        'labels': dict(label_counts),
        'entities': dict(entity_types)
    }

def main():
    print("="*80)
    print("DATA CLEANING AND AUGMENTATION SCRIPT")
    print("="*80)
    
    print("\n[Step 1] Parsing new data...")
    new_sentences = parse_new_data(NEW_SENTENCES)
    print(f"[PASS] Parsed {len(new_sentences)} new sentences")
    
    print("\n[Step 2] Validating BIO tags...")
    new_sentences = validate_tags(new_sentences)
    
    print("\n[Step 3] Removing duplicates...")
    new_sentences = remove_duplicates(new_sentences)
    
    print("\n[Step 4] Computing statistics...")
    stats = get_statistics(new_sentences)
    print(f"[PASS] Statistics:")
    print(f"  - Sentences: {stats['sentences']}")
    print(f"  - Tokens: {stats['tokens']}")
    print(f"  - Entity Types: {', '.join(stats['entities'].keys())}")
    print(f"  - Entity Counts:")
    for entity_type, count in sorted(stats['entities'].items()):
        print(f"    * {entity_type}: {count}")
    print(f"  - Label Distribution:")
    for label, count in sorted(stats['labels'].items(), key=lambda x: -x[1])[:5]:
        print(f"    * {label}: {count}")
    
    print("\n[Step 5] Saving augmented data...")
    # Create augmented dataset (80% train, 10% dev, 10% test split)
    total = len(new_sentences)
    train_split = int(total * 0.8)
    dev_split = int(total * 0.9)
    
    train_data = new_sentences[:train_split]
    dev_data = new_sentences[train_split:dev_split]
    test_data = new_sentences[dev_split:]
    
    # Save with proper formatting
    save_conll_format(train_data, "data/new_train.conll")
    save_conll_format(dev_data, "data/new_dev.conll", start_idx=len(train_data)+1)
    save_conll_format(test_data, "data/new_test.conll", start_idx=len(train_data)+len(dev_data)+1)
    
    print("\n[Step 6] Merging with existing data...")
    # Read existing data
    def read_conll(filename):
        sentences = []
        current = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    if current:
                        sentences.append(current)
                        current = []
                else:
                    parts = line.split('\t')
                    if len(parts) == 2:
                        current.append(tuple(parts))
        if current:
            sentences.append(current)
        return sentences
    
    try:
        existing_train = read_conll("data/train.conll")
        existing_dev = read_conll("data/dev.conll")
        existing_test = read_conll("data/test.conll")
        
        merged_train = existing_train + train_data
        merged_dev = existing_dev + dev_data
        merged_test = existing_test + test_data
        
        # Backup originals
        import shutil
        shutil.copy("data/train.conll", "data/train.conll.backup")
        shutil.copy("data/dev.conll", "data/dev.conll.backup")
        shutil.copy("data/test.conll", "data/test.conll.backup")
        
        # Save merged
        save_conll_format(merged_train, "data/train.conll")
        save_conll_format(merged_dev, "data/dev.conll", start_idx=len(merged_train)+1)
        save_conll_format(merged_test, "data/test.conll", start_idx=len(merged_train)+len(merged_dev)+1)
        
        print(f"[PASS] Merged data:")
        print(f"  - Train: {len(existing_train)} + {len(train_data)} = {len(merged_train)}")
        print(f"  - Dev: {len(existing_dev)} + {len(dev_data)} = {len(merged_dev)}")
        print(f"  - Test: {len(existing_test)} + {len(test_data)} = {len(merged_test)}")
        
    except FileNotFoundError as e:
        print(f"[WARN] Could not merge with existing data: {e}")
    
    print("\n" + "="*80)
    print("DATA CLEANING COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nNew files created:")
    print("  - data/train.conll (updated)")
    print("  - data/dev.conll (updated)")
    print("  - data/test.conll (updated)")
    print("  - data/train.conll.backup")
    print("  - data/dev.conll.backup")
    print("  - data/test.conll.backup")

if __name__ == "__main__":
    main()
