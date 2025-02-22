import os
import csv
import nltk
from nltk.translate import bleu_score, meteor_score
from rouge import Rouge
from bert_score import score as bert_score

# Ensure WordNet is downloaded
nltk.download('wordnet')

# Set directories (update these paths as necessary)
parent_directories = ['oneshot', 'zeroshot', 'fewshot']
subdirectories = ['llama', 'qwen', 'chatgpt']
reference_dir = 'path/to/reference/files'  # Update this path
# Function to find corresponding reference files
def find_reference_file(target_filename):
    target_prefix = target_filename[-10:-4]  # Extract last 6 digits (assumes filename ends with digits)
    matching_references = []

    for ref_file in os.listdir(reference_dir):
        if ref_file.endswith('.txt') and ref_file[-10:-4] == target_prefix:
            matching_references.append(os.path.join(reference_dir, ref_file))

    return matching_references

# Function to compute scores
def compute_scores(target_file, reference_files):
    with open(target_file, 'r') as f:
        target_text = f.read().strip().splitlines()

    scores = {}
    for reference_file in reference_files:
        with open(reference_file, 'r') as f:
            reference_text = f.read().strip().splitlines()

        # Compute BLEU
        bleu = bleu_score.sentence_bleu([reference_text], target_text)

        # Compute METEOR
        meteor = meteor_score.meteor_score(reference_text, target_text)

        # Compute ROUGE-W
        rouge = Rouge()
        rouge_scores = rouge.get_scores(' '.join(target_text), ' '.join(reference_text))
        
        # Extract ROUGE-W score if available
        rouge_w = next((score['rouge-w']['f'] for score in rouge_scores if 'rouge-w' in score), 0)

        # Compute BERTScore
        P, R, F1 = bert_score(target_text, reference_text, lang='en', verbose=False)
        bert_score_p = P.mean().item()
        bert_score_r = R.mean().item()
        bert_score_f1 = F1.mean().item()

        scores[reference_file] = {
            'BLEU': bleu,
            'METEOR': meteor,
            'ROUGE-W': rouge_w,
            'BERTScore-P': bert_score_p,
            'BERTScore-R': bert_score_r,
            'BERT-F1': bert_score_f1
        }

    return scores

# Main processing loop
results = []

for parent_dir in parent_directories:
    for sub_dir in subdirectories:
        dir_path = os.path.join(parent_dir, sub_dir)
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.txt'):
                    target_file = os.path.join(dir_path, filename)
                    reference_files = find_reference_file(filename)

                    if reference_files:
                        scores = compute_scores(target_file, reference_files)
                        for ref_file, score_data in scores.items():
                            scores_sum = sum(score_data.values())
                            results.append({
                                'learning_model': sub_dir,
                                'model': parent_dir,
                                'file_name': filename,
                                'file_path': target_file,
                                'reference_file': ref_file,
                                'scores': score_data,
                                'sum': scores_sum
                            })

# Rank results
for idx, result in enumerate(sorted(results, key=lambda x: x['sum'], reverse=True), start=1):
    result['rank'] = idx

# Write to CSV
csv_file_path = 'automatic_scores.csv'
with open(csv_file_path, 'w', newline='') as csvfile:
    fieldnames = [
        'learning_model',
        'model',
        'file_name',
        'file_path',
        'reference_file',
        'BLEU',
        'METEOR',
        'ROUGE-W',
        'BERTScore-P',
        'BERTScore-R',
        'BERT-F1',
        'sum',
        'rank'
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for result in results:
        writer.writerow({
            'learning_model': result['learning_model'],
            'model': result['model'],
            'file_name': result['file_name'],
            'file_path': result['file_path'],
            'reference_file': result['reference_file'],
            'BLEU': result['scores']['BLEU'],
            'METEOR': result['scores']['METEOR'],
            'ROUGE-W': result['scores']['ROUGE-W'],
            'BERTScore-P': result['scores']['BERTScore-P'],
            'BERTScore-R': result['scores']['BERTScore-R'],
            'BERT-F1': result['scores']['BERT-F1'],
            'sum': result['sum'],
            'rank': result['rank']
        })

print(f"Scores computed and saved to {csv_file_path}")
