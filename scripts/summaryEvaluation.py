import argparse
import os
import re
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from rouge_score import rouge_scorer
import bert_score
import pandas as pd
import torch

# Ensure necessary NLTK data is downloaded
nltk.download('wordnet')
nltk.download('punkt')

def read_summaries(reference_dir, generated_base_dir):
    """
    Reads and matches generated summaries with reference summaries based on filename patterns.

    Args:
        reference_dir (str): Path to the directory containing reference summaries.
        generated_base_dir (str): Path to the base directory containing generated summaries.

    Returns:
        list of dict: Each dictionary contains generated summary, reference summary, 
                      learning mode, and model.
    """
    # Pattern to match filenames ending with six digits plus '.txt'
    reference_pattern = re.compile(r'(\d{6})\.txt$')  # Extracts six digits at the end before '.txt'
    generated_pattern = re.compile(r'^(\d{6})\.txt$')  # Matches '201301.txt' exactly

    # Create a mapping from identifier to reference summary path
    reference_mapping = {}
    for ref_file in os.listdir(reference_dir):
        match = reference_pattern.search(ref_file)
        if match:
            identifier = match.group(1)  # Extract the six-digit identifier
            # Ensure no duplicate identifiers
            if identifier in reference_mapping:
                print(f"Warning: Duplicate reference identifier {identifier} found in '{ref_file}'. Previous reference will be overwritten.")
            reference_mapping[identifier] = os.path.join(reference_dir, ref_file)
        else:
            print(f"Warning: Reference file '{ref_file}' does not match the expected pattern and will be skipped.")

    summary_pairs = []

    # Traverse the generated summaries directory
    for root, dirs, files in os.walk(generated_base_dir):
        for file in files:
            gen_match = generated_pattern.match(file)
            if gen_match:
                identifier = gen_match.group(1)
                gen_path = os.path.join(root, file)

                # Extract learning mode and model from the relative path
                try:
                    # Get the relative path from generated_base_dir to the current file
                    relative_path = os.path.relpath(gen_path, generated_base_dir)
                    path_parts = relative_path.split(os.sep)

                    if len(path_parts) < 3:
                        print(f"Warning: Unexpected directory structure for generated summary '{gen_path}'. Expected '<Learning_Mode>/<Model>/<filename>'. Skipping.")
                        learning_mode = 'Unknown'
                        model = 'Unknown'
                    else:
                        learning_mode, model = path_parts[0], path_parts[1]
                except Exception as e:
                    print(f"Warning: Error extracting Learning_Mode and Model from path '{gen_path}': {e}")
                    learning_mode = 'Unknown'
                    model = 'Unknown'

                # Find the corresponding reference summary
                ref_path = reference_mapping.get(identifier, None)
                if ref_path and os.path.exists(ref_path):
                    try:
                        with open(gen_path, 'r', encoding='utf-8') as f:
                            generated_summary = f.read().strip()
                        with open(ref_path, 'r', encoding='utf-8') as f:
                            reference_summary = f.read().strip()

                        if not generated_summary:
                            print(f"Warning: Generated summary at '{gen_path}' is empty. Skipping.")
                            continue
                        if not reference_summary:
                            print(f"Warning: Reference summary at '{ref_path}' is empty. Skipping.")
                            continue

                        summary_pairs.append({
                            'Generated_Summary': generated_summary,
                            'Reference_Summary': reference_summary,
                            'Learning_Mode': learning_mode,
                            'Model': model
                        })
                    except Exception as e:
                        print(f"Error reading summaries for identifier {identifier}: {e}")
                else:
                    print(f"Warning: Reference summary for identifier '{identifier}' not found. Generated summary at '{gen_path}' will be skipped.")

    return summary_pairs

def compute_bleu(generated, reference):
    """
    Computes BLEU score for a single summary pair.

    Args:
        generated (str): Generated summary.
        reference (str): Reference summary.

    Returns:
        float: BLEU score.
    """
    # Tokenize the summaries
    reference_tokens = nltk.word_tokenize(reference.lower())
    generated_tokens = nltk.word_tokenize(generated.lower())

    if not generated_tokens:
        return 0.0  # Avoid division by zero

    # BLEU expects a list of references
    bleu_score = sentence_bleu(
        [reference_tokens],
        generated_tokens,
        weights=(0.25, 0.25, 0.25, 0.25),  # BLEU-4
        smoothing_function=SmoothingFunction().method1
    )
    return bleu_score

def compute_rouge_w(generated, reference):
    """
    Computes ROUGE-W score for a single summary pair.

    **Note:** ROUGE-W is less commonly available. Approximated using ROUGE-L.

    Args:
        generated (str): Generated summary.
        reference (str): Reference summary.

    Returns:
        float: ROUGE-W (approximated by ROUGE-L) F1 score.
    """
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, generated)
    rouge_l_f1 = scores['rougeL'].fmeasure
    return rouge_l_f1

def compute_meteor(generated, reference):
    """
    Computes METEOR score for a single summary pair.

    Args:
        generated (str): Generated summary.
        reference (str): Reference summary.

    Returns:
        float: METEOR score.
    """
    # Ensure that both generated and reference are strings
    if not isinstance(generated, str) or not isinstance(reference, str):
        raise TypeError("Both generated and reference summaries must be strings for METEOR score computation.")

    # METEOR expects a list of references and a hypothesis string
    meteor = meteor_score([reference], generated)
    return meteor

def compute_bertscore(df, model_name='bert-base-uncased', lang='en'):
    """
    Computes BERTScore for all summary pairs in the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing 'Generated_Summary' and 'Reference_Summary' columns.
        model_name (str): BERT model name.
        lang (str): Language of the summaries.

    Returns:
        pd.DataFrame: DataFrame with BERT Precision, Recall, and F1 scores.
    """
    print("Computing BERTScore. This may take a while depending on the number of summaries and hardware...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    P, R, F1 = bert_score.score(
        df['Generated_Summary'].tolist(), 
        df['Reference_Summary'].tolist(), 
        model_type=model_name,
        lang=lang, 
        verbose=True,
        rescale_with_baseline=True,
        device=device
    )
    df['BERT_P'] = P.tolist()
    df['BERT_R'] = R.tolist()
    df['BERT_F1'] = F1.tolist()
    return df

def main():
    parser = argparse.ArgumentParser(description="Compute BLEU, ROUGE-W, METEOR, and BERTScore for generated summaries.")
    parser.add_argument('--generated_base_dir', type=str, required=True, help='Path to the base directory containing generated summaries.')
    parser.add_argument('--reference_dir', type=str, required=True, help='Path to the directory containing reference summaries.')
    parser.add_argument('--output_csv', type=str, default='summary_evaluation_scores.csv', help='Path to save the CSV with evaluation scores.')
    parser.add_argument('--bert_model', type=str, default='bert-base-uncased', help='BERT model to use for BERTScore.')
    parser.add_argument('--language', type=str, default='en', help='Language of the summaries for BERTScore.')

    args = parser.parse_args()

    print("Reading and matching summaries...")
    summary_pairs = read_summaries(args.reference_dir, args.generated_base_dir)
    print(f"Number of matched summary pairs: {len(summary_pairs)}\n")

    if not summary_pairs:
        print("No summary pairs found. Exiting.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(summary_pairs)

    # Compute BLEU, ROUGE-W, and METEOR for each pair
    print("Computing BLEU, ROUGE-W, and METEOR scores for each summary pair...")
    try:
        df['BLEU'] = df.apply(lambda row: compute_bleu(row['Generated_Summary'], row['Reference_Summary']), axis=1)
    except Exception as e:
        print(f"Error computing BLEU scores: {e}")
        df['BLEU'] = None

    try:
        df['ROUGE-W'] = df.apply(lambda row: compute_rouge_w(row['Generated_Summary'], row['Reference_Summary']), axis=1)
    except Exception as e:
        print(f"Error computing ROUGE-W scores: {e}")
        df['ROUGE-W'] = None

    try:
        df['METEOR'] = df.apply(lambda row: compute_meteor(row['Generated_Summary'], row['Reference_Summary']), axis=1)
    except TypeError as te:
        print(f"TypeError in METEOR score computation: {te}")
        df['METEOR'] = None
    except Exception as e:
        print(f"Error computing METEOR scores: {e}")
        df['METEOR'] = None

    # Compute BERTScore for all pairs
    print("\nComputing BERTScore for all summary pairs...")
    try:
        df = compute_bertscore(df, model_name=args.bert_model, lang=args.language)
    except Exception as e:
        print(f"Error computing BERTScore: {e}")
        df['BERT_P'] = None
        df['BERT_R'] = None
        df['BERT_F1'] = None

    # Save detailed scores to CSV
    print(f"\nSaving detailed scores to {args.output_csv}...")
    try:
        df.to_csv(args.output_csv, index=False)
        print(f"Detailed scores have been saved to '{args.output_csv}'.")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

    # Compute average scores
    avg_bleu = df['BLEU'].mean() if df['BLEU'].notnull().any() else 0
    avg_rouge_w = df['ROUGE-W'].mean() if df['ROUGE-W'].notnull().any() else 0
    avg_meteor = df['METEOR'].mean() if df['METEOR'].notnull().any() else 0
    avg_bert_p = df['BERT_P'].mean() if df['BERT_P'].notnull().any() else 0
    avg_bert_r = df['BERT_R'].mean() if df['BERT_R'].notnull().any() else 0
    avg_bert_f1 = df['BERT_F1'].mean() if df['BERT_F1'].notnull().any() else 0

    print("\n======= Average Evaluation Metrics =======")
    print(f"Average BLEU Score: {avg_bleu:.4f}")
    print(f"Average ROUGE-W (ROUGE-L) F1 Score: {avg_rouge_w:.4f}")
    print(f"Average METEOR Score: {avg_meteor:.4f}")
    print(f"Average BERTScore Precision: {avg_bert_p:.4f}")
    print(f"Average BERTScore Recall: {avg_bert_r:.4f}")
    print(f"Average BERTScore F1: {avg_bert_f1:.4f}")
    print("========================================\n")

    # Compute metrics grouped by Learning Mode and Model
    print("======= Evaluation Metrics by Learning Mode and Model =======")
    group_cols = ['Learning_Mode', 'Model']
    grouped = df.groupby(group_cols).agg({
        'BLEU': 'mean',
        'ROUGE-W': 'mean',
        'METEOR': 'mean',
        'BERT_P': 'mean',
        'BERT_R': 'mean',
        'BERT_F1': 'mean'
    }).reset_index()

    # Format floating numbers to four decimal places
    grouped['BLEU'] = grouped['BLEU'].round(4)
    grouped['ROUGE-W'] = grouped['ROUGE-W'].round(4)
    grouped['METEOR'] = grouped['METEOR'].round(4)
    grouped['BERT_P'] = grouped['BERT_P'].round(4)
    grouped['BERT_R'] = grouped['BERT_R'].round(4)
    grouped['BERT_F1'] = grouped['BERT_F1'].round(4)

    print(grouped.to_string(index=False))
    print("================================================================\n")

    # Save grouped metrics to a separate CSV
    grouped_output_csv = 'grouped_evaluation_metrics.csv'
    print(f"Saving grouped metrics to {grouped_output_csv}...")
    try:
        grouped.to_csv(grouped_output_csv, index=False)
        print(f"Grouped metrics have been saved to '{grouped_output_csv}'.\n")
    except Exception as e:
        print(f"Error saving grouped metrics to CSV: {e}")

if __name__ == "__main__":
    main()
