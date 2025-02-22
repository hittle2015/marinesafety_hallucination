import os
import re
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
from collections import defaultdict
import csv
from datetime import datetime
import textwrap
import os
import re
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd
from collections import defaultdict
import csv
from datetime import datetime
import textwrap

class HallucinationAnalyzer:
    def __init__(self, input_dir, output_file, verbose=False):
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.setup_logging(verbose)
        
        # Define hallucination annotation tags
        self.hallucination_types = {
            'UCE': r'\[UCE\]',  # Unit conversion Error
            'OGE': r'\[OGE\]',  # Overgeneration Error
            'UGE': r'\[UGE\]',  # undergeneration Error
            'NNE': r'\[NNE\]',  # named entitiy Error
            'DTE': r'\[DTE\]',  # date time  Error
            'MGE': r'\[MGE\]'  #  misgeneration Error
            # Add more hallucination types as needed
        }

    @staticmethod
    def setup_logging(verbose):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def count_hallucinations(self, text):
        """Count occurrences of each hallucination annotation tag in text"""
        counts = defaultdict(int)
        
        for hall_type, pattern in self.hallucination_types.items():
            counts[hall_type] = len(re.findall(pattern, text))
        
        return counts

    def analyze_file(self, file_path):
        """Analyze a single file for hallucination annotations"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.count_hallucinations(content)
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}")
            return defaultdict(int)

    def analyze_directories(self):
        """Analyze all files in the directory structure"""
        results = []
        total_files = 0
        processed_files = 0

        # Get learning models (oneshot, zeroshot, fewshot)
        learning_models = [d for d in self.input_dir.iterdir() if d.is_dir()]
        
        if not learning_models:
            logging.error(f"No subdirectories found in {self.input_dir}")
            return False

        for learning_model_dir in learning_models:
            learning_model = learning_model_dir.name
            logging.info(f"Processing learning model: {learning_model}")
            
            # Get model directories (llama, qwen, chatgpt)
            model_dirs = [d for d in learning_model_dir.iterdir() if d.is_dir()]
            
            if not model_dirs:
                logging.warning(f"No model directories found in {learning_model_dir}")
                continue

            for model_dir in model_dirs:
                model = model_dir.name
                logging.info(f"Processing model: {model}")
                
                # Get all text files in this directory
                text_files = list(model_dir.glob('*.txt'))
                total_files += len(text_files)
                
                if not text_files:
                    logging.warning(f"No text files found in {model_dir}")
                    continue

                for file_path in text_files:
                    processed_files += 1
                    logging.debug(f"Processing file {processed_files}/{total_files}: {file_path}")
                    
                    # Get hallucination counts
                    counts = self.analyze_file(file_path)
                    
                    # Add result to list
                    result = {
                        'learning_model': learning_model,
                        'model': model,
                        'file_name': file_path.stem,
                        'file_path': str(file_path.relative_to(self.input_dir))
                    }
                    # Add hallucination counts
                    result.update(counts)
                    results.append(result)
                    
                    logging.debug(f"Found hallucinations in {file_path.name}: {dict(counts)}")

        # Create DataFrame and save to CSV
        if results:
            df = pd.DataFrame(results)
            
            # Calculate totals
            df['total_hallucinations'] = df[[hall_type for hall_type in self.hallucination_types.keys()]].sum(axis=1)
            
            # Sort the DataFrame
            df = df.sort_values(['learning_model', 'model', 'file_name'])
            
            # Save to CSV
            df.to_csv(self.output_file, index=False)
            
            # Create summary
            self.create_summary(df)
            
            logging.info(f"\nProcessed {processed_files} of {total_files} files")
            logging.info(f"Results saved to {self.output_file}")
            return True
        else:
            logging.warning("No files were processed")
            return False

    def create_summary(self, df):
        """Create a summary report of the analysis"""
        summary_file = self.output_file.with_name(f"summary_{self.output_file.name}")
        
        # Group by learning_model and model
        group_summary = df.groupby(['learning_model', 'model']).agg({
            **{hall_type: ['sum', 'mean', 'std'] for hall_type in self.hallucination_types.keys()},
            'total_hallucinations': ['sum', 'mean', 'std'],
            'file_name': 'count'
        }).rename(columns={'file_name': 'total_files'})
        
        # Flatten column names
        group_summary.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] 
                               for col in group_summary.columns]
        
        # Calculate percentages
        for hall_type in self.hallucination_types.keys():
            group_summary[f'{hall_type}_percentage'] = (
                group_summary[f'{hall_type}_sum'] / group_summary['total_hallucinations_sum'] * 100
            )
        
        # Save summary
        group_summary.to_csv(summary_file)
        logging.info(f"Summary saved to {summary_file}")
        
        # Create detailed statistics
        stats_file = self.output_file.with_name(f"statistics_{self.output_file.name}")
        
        # Calculate statistics per learning model
        learning_model_stats = df.groupby('learning_model').agg({
            **{hall_type: ['sum', 'mean', 'std', 'max'] for hall_type in self.hallucination_types.keys()},
            'total_hallucinations': ['sum', 'mean', 'std', 'max']
        })
        
        # Calculate statistics per model
        model_stats = df.groupby('model').agg({
            **{hall_type: ['sum', 'mean', 'std', 'max'] for hall_type in self.hallucination_types.keys()},
            'total_hallucinations': ['sum', 'mean', 'std', 'max']
        })
        
        # Save detailed statistics
        with pd.ExcelWriter(stats_file) as writer:
            learning_model_stats.to_excel(writer, sheet_name='Learning_Model_Stats')
            model_stats.to_excel(writer, sheet_name='Model_Stats')
            group_summary.to_excel(writer, sheet_name='Combined_Stats')
        
        logging.info(f"Detailed statistics saved to {stats_file}")

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Analyze hallucination annotation frequencies in text files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            Expected directory structure:
              input_dir/
              ├── oneshot/
              │   ├── llama/
              │   ├── qwen/
              │   └── chatgpt/
              ├── zeroshot/
              │   ├── llama/
              │   ├── qwen/
              │   └── chatgpt/
              └── fewshot/
                  ├── llama/
                  ├── qwen/
                  └── chatgpt/
                  
            Hallucination annotation tags:
              [UCE] - Ungrounded Content Error
              [OGE] - On-Ground Error
              [UGE] - Under-Ground Error
              [CGE] - Cross-Ground Error
              [OSE] - Out-Source Error
              [ISE] - In-Source Error
              [CSE] - Cross-Source Error
        ''')
    )
    
    parser.add_argument('-i', '--input-directory',
                        required=True,
                        help='Root directory containing the directory structure')
    
    parser.add_argument('-o', '--output-file',
                        required=True,
                        help='Output CSV file path')
    
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Validate input directory
    if not os.path.isdir(args.input_directory):
        parser.error(f"Input directory does not exist: {args.input_directory}")

    try:
        analyzer = HallucinationAnalyzer(
            args.input_directory,
            args.output_file,
            args.verbose
        )
        
        success = analyzer.analyze_directories()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
