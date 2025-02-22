import os
import sys
from collections import defaultdict
import argparse
import csv

def parse_arguments():
    parser = argparse.ArgumentParser(description="Count frequencies of specified hallucinations in files with a specific filename pattern within a directory tree.")
    parser.add_argument(
        "-r", "--root_dir", 
        type=str, 
        required=True, 
        help="Root directory to start searching from."
    )
    parser.add_argument(
        "-p", "--file_pattern", 
        type=str, 
        required=True, 
        help="Filename pattern that files should start with (e.g., 'log_')."
    )
    parser.add_argument(
        "-s", "--strings", 
        type=str, 
        nargs='+', 
        required=True, 
        help="List of hallucinations to count in the files."
    )
    parser.add_argument(
        "-o", "--output_file", 
        type=str, 
        default="output.csv", 
        help="Output CSV file to save the results. Defaults to 'output.csv'."
    )
    return parser.parse_args()

def find_matching_files(root_dir, file_pattern):
    """
    Traverse the directory tree and yield paths to files that start with the given pattern.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.startswith(file_pattern):
                yield os.path.join(dirpath, filename)

def count_strings_in_file(file_path, target_strings):
    """
    Count the occurrences of each target string in the given file.
    """
    counts = defaultdict(int)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                for target in target_strings:
                    # Here, we're counting overlapping occurrences and case-sensitive
                    # Modify the logic if you need case-insensitive or whole word matches
                    counts[target] += line.count(target)
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    return counts

def aggregate_counts(files, target_strings):
    """
    Aggregate counts of target strings across all files.
    """
    aggregated = defaultdict(int)
    for file_path in files:
        file_counts = count_strings_in_file(file_path, target_strings)
        for target in target_strings:
            aggregated[target] += file_counts.get(target, 0)
    return aggregated

def save_to_csv(aggregated_counts, output_file):
    """
    Save the aggregated counts to a CSV file.
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['String', 'Frequency']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for string, count in aggregated_counts.items():
                writer.writerow({'String': string, 'Frequency': count})
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}", file=sys.stderr)

def main():
    args = parse_arguments()
    
    print("Searching for matching files...")
    matching_files = list(find_matching_files(args.root_dir, args.file_pattern))
    print(f"Found {len(matching_files)} files starting with '{args.file_pattern}'.")
    
    if not matching_files:
        print("No files found. Exiting.")
        return
    
    print("Counting string frequencies...")
    aggregated_counts = aggregate_counts(matching_files, args.strings)
    
    print("Saving results...")
    save_to_csv(aggregated_counts, args.output_file)

if __name__ == "__main__":
    main()
