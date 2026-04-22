import os
import random

def split_data(input_file, train_ratio=0.7, dev_ratio=0.15):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Sentences are separated by double newlines
    # But let's split by double newlines and filter out empty strings and headers
    blocks = content.split('\n\n')
    
    sentences = []
    current_sentence = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
        
        # Check if block is a valid sentence (not just comments)
        valid_lines = [line for line in lines if not line.startswith('#')]
        if valid_lines:
            sentences.append(block)
            
    # Randomly shuffle
    random.seed(42)
    random.shuffle(sentences)
    
    total = len(sentences)
    train_end = int(total * train_ratio)
    dev_end = train_end + int(total * dev_ratio)
    
    train_sentences = sentences[:train_end]
    dev_sentences = sentences[train_end:dev_end]
    test_sentences = sentences[dev_end:]
    
    def write_sentences(sentences, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            for sent in sentences:
                f.write(sent + '\n\n')
                
    write_sentences(train_sentences, 'data/train.conll')
    write_sentences(dev_sentences, 'data/dev.conll')
    write_sentences(test_sentences, 'data/test.conll')
    
    print(f"Total: {total}")
    print(f"Train: {len(train_sentences)}")
    print(f"Dev: {len(dev_sentences)}")
    print(f"Test: {len(test_sentences)}")

if __name__ == '__main__':
    split_data('data/train_expanded.conll')
