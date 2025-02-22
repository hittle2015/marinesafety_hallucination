import os
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import defaultdict
import argparse
import sys

def download_nltk_dependencies():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK 'punkt' tokenizer...")
        nltk.download('punkt')

def is_text_file(filename):
    # You can extend this function to include more file extensions if needed
    return filename.lower().endswith('.txt')

def process_text(text):
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    
    # Convert words to lower case for case-insensitive unique count
    words_lower = [word.lower() for word in words if word.isalpha()]
    unique_words = set(words_lower)
    
    num_sentences = len(sentences)
    num_tokens = len(words_lower)
    num_unique_words = len(unique_words)
    avg_sentence_length = num_tokens / num_sentences if num_sentences > 0 else 0
    
    return {
        'num_sentences': num_sentences,
        'num_tokens': num_tokens,
        'num_unique_words': num_unique_words,
        'avg_sentence_length': avg_sentence_length
    }

def traverse_directory(root_dir):
    text_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if is_text_file(filename):
                full_path = os.path.join(dirpath, filename)
                text_files.append(full_path)
    return text_files

def main(directory):
    download_nltk_dependencies()
    
    text_files = traverse_directory(directory)
    if not text_files:
        print(f"No text files found in directory: {directory}")
        sys.exit(1)
    
    total_sentences = 0
    total_tokens = 0
    total_unique_words = set()
    
    print(f"Processing {len(text_files)} text files...\n")
    
    for file_path in text_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            # Try with a different encoding if utf-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        
        stats = process_text(text)
        total_sentences += stats['num_sentences']
        total_tokens += stats['num_tokens']
        # To maintain a global unique word set
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            words = word_tokenize(f.read())
            words_lower = [word.lower() for word in words if word.isalpha()]
            total_unique_words.update(words_lower)
        
        # Optional: Print stats per file
        # print(f"Processed {file_path}: {stats}")
    
    avg_sentence_length = total_tokens / total_sentences if total_sentences > 0 else 0
    
    print("==== Aggregated Statistics ====")
    print(f"Total Files Processed: {len(text_files)}")
    print(f"Number of Sentences: {total_sentences}")
    print(f"Number of Tokens (Words): {total_tokens}")
    print(f"Number of Unique Words: {len(total_unique_words)}")
    print(f"Average Sentence Length (in words): {avg_sentence_length:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process text files to extract linguistic statistics.")
    parser.add_argument('directory', type=str, help='Path to the root directory containing text files in subdirectories.')
    
    args = parser.parse_args()
    main(args.directory)
