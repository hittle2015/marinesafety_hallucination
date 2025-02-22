# Basic usage
#python organize_files.py -i ./input_files -o ./organized_files

# With verbose output
#python organize_files.py -i ./input_files -o ./organized_files -v

# Dry run to preview changes
#python organize_files.py -i ./input_files -o ./or

import os
import re
import sys
import argparse
import logging
from pathlib import Path
import shutil
from datetime import datetime
import textwrap

class FileOrganizer:
    def __init__(self, input_dir, output_dir, verbose=False, dry_run=False):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.setup_logging(verbose)
        
        # Define pattern mappings
        self.shot_patterns = {
            'oneshot': ['one-shot', 'oneshot', '1-shot', '1shot'],
            'zeroshot': ['zero-shot', 'zeroshot', '0-shot', '0shot'],
            'fewshot': ['few-shot','fews-shot', 'fewshot', 'k-shot', 'kshot']
        }
        
        self.model_patterns = {
            'llama': ['llama', 'llama2', 'llama-2'],
            'qwen': ['qwen', 'qwen-7b', 'qwen-14b'],
            'chatgpt': ['chatgpt','chat', 'gpt', 'gpt-3.5', 'gpt-4']
        }

    @staticmethod
    def setup_logging(verbose):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def get_six_digit_number(self, filename):
        """Extract first 6-digit number from filename"""
        match = re.search(r'\d{6}', filename)
        return match.group(0) if match else None

    def determine_categories(self, filename):
        """
        Determine categories based on filename
        Returns tuple (shot_category, model_category)
        """
        filename_lower = filename.lower()
        
        # Find shot category
        shot_category = None
        for category, patterns in self.shot_patterns.items():
            if any(pattern.lower() in filename_lower for pattern in patterns):
                shot_category = category
                break
        
        # Find model category
        model_category = None
        for category, patterns in self.model_patterns.items():
            if any(pattern.lower() in filename_lower for pattern in patterns):
                model_category = category
                break
        
        return shot_category, model_category

    def organize_files(self):
        """Organize files into appropriate directories based on filename patterns"""
        # Get all text files
        text_files = list(self.input_dir.glob('**/*.txt'))
        
        if not text_files:
            logging.warning("No text files found in the input directory.")
            return False

        total_files = len(text_files)
        processed_files = 0
        successful_moves = 0
        unclassified_files = []
        
        logging.info(f"Found {total_files} text files to process")

        # Create statistics dictionary
        stats = {shot: {model: 0 for model in self.model_patterns.keys()}
                for shot in self.shot_patterns.keys()}
        stats['unclassified'] = 0

        for file_path in text_files:
            processed_files += 1
            logging.debug(f"Processing file {processed_files}/{total_files}: {file_path.name}")
            
            try:
                # Get categories from filename
                shot_cat, model_cat = self.determine_categories(file_path.name)
                
                # Get 6-digit number for new filename
                six_digit = self.get_six_digit_number(file_path.name)
                
                # Skip if we couldn't find necessary information
                if not all([shot_cat, model_cat, six_digit]):
                    logging.warning(f"Could not classify {file_path.name}")
                    unclassified_files.append(file_path)
                    stats['unclassified'] += 1
                    continue

                # Create target directory path and new filename
                target_dir = self.output_dir / shot_cat / model_cat
                new_filename = f"{six_digit}.txt"
                target_path = target_dir / new_filename

                if not self.dry_run:
                    # Create directory if it doesn't exist
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file to new location
                    shutil.copy2(file_path, target_path)
                    successful_moves += 1
                    stats[shot_cat][model_cat] += 1
                    logging.info(f"Moved: {file_path.name} → {shot_cat}/{model_cat}/{new_filename}")
                else:
                    logging.info(f"Would move: {file_path.name} → {shot_cat}/{model_cat}/{new_filename}")
                    successful_moves += 1
                    stats[shot_cat][model_cat] += 1

            except Exception as e:
                logging.error(f"Error processing {file_path.name}: {str(e)}")
                unclassified_files.append(file_path)
                stats['unclassified'] += 1

        # Print summary
        self.print_summary(stats, total_files, successful_moves)
        
        # Create report file
        if not self.dry_run:
            self.create_report(stats, unclassified_files)

        return successful_moves > 0

    def print_summary(self, stats, total_files, successful_moves):
        """Print organization summary"""
        summary = ["\nFile Organization Summary:"]
        summary.append("-" * 50)
        
        for shot in self.shot_patterns.keys():
            summary.append(f"\n{shot.upper()}:")
            for model, count in stats[shot].items():
                if count > 0:
                    summary.append(f"  {model}: {count} files")
        
        summary.append(f"\nUnclassified: {stats['unclassified']} files")
        summary.append("-" * 50)
        summary.append(f"Total files processed: {total_files}")
        summary.append(f"Successfully organized: {successful_moves}")
        summary.append(f"Unclassified: {stats['unclassified']}")
        
        logging.info("\n".join(summary))

    def create_report(self, stats, unclassified_files):
        """Create a detailed report file"""
        report_path = self.output_dir / "organization_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("File Organization Report\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")
            
            # Write statistics
            f.write("Organization Statistics:\n")
            for shot in self.shot_patterns.keys():
                f.write(f"\n{shot.upper()}:\n")
                for model, count in stats[shot].items():
                    if count > 0:
                        f.write(f"  {model}: {count} files\n")
            
            # Write unclassified files
            f.write("\nUnclassified Files:\n")
            for file_path in unclassified_files:
                f.write(f"  {file_path.name}\n")
            
            f.write("\nPattern Information:\n")
            f.write("Shot patterns:\n")
            for category, patterns in self.shot_patterns.items():
                f.write(f"  {category}: {', '.join(patterns)}\n")
            
            f.write("\nModel patterns:\n")
            for category, patterns in self.model_patterns.items():
                f.write(f"  {category}: {', '.join(patterns)}\n")

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Organize text files into directories based on filename patterns.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            Examples:
              # Basic usage:
              %(prog)s -i ./input_files -o ./organized_files
              
              # With verbose output:
              %(prog)s -i ./input_files -o ./organized_files -v
              
              # Dry run to see what would happen:
              %(prog)s -i ./input_files -o ./organized_files --dry-run
              
            File naming patterns:
              - Must contain a 6-digit number
              - Must contain a shot pattern (one-shot, zero-shot, few-shot)
              - Must contain a model pattern (llama, qwen, chatgpt)
        ''')
    )
    
    parser.add_argument('-i', '--input-directory',
                        required=True,
                        help='Source directory containing text files')
    
    parser.add_argument('-o', '--output-directory',
                        required=True,
                        help='Directory where organized files will be stored')
    
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')
    
    parser.add_argument('--dry-run',
                        action='store_true',
                        help='Show what would be done without making any changes')
    
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0.0',
                        help='Show program version number and exit')

    return parser

def validate_directories(input_dir, output_dir, dry_run=False):
    """Validate input and output directories"""
    if not os.path.isdir(input_dir):
        return False, f"Input directory does not exist: {input_dir}"
    
    if not dry_run:
        try:
            os.makedirs(output_dir, exist_ok=True)
            test_file = os.path.join(output_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True, ""
        except Exception as e:
            return False, f"Cannot write to output directory '{output_dir}': {str(e)}"
    
    return True, ""

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Validate directories (skip if dry run)
    is_valid, error_message = validate_directories(
        args.input_directory, 
        args.output_directory, 
        args.dry_run
    )
    if not is_valid:
        parser.error(error_message)

    try:
        organizer = FileOrganizer(
            args.input_directory,
            args.output_directory,
            args.verbose,
            args.dry_run
        )
        
        success = organizer.organize_files()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
