## Basic usage - replace 'old' with 'new' in filenames:
#python rename_files.py -i ./input -o ./output -p "old" -r "new"
#
## Remove all numbers from filenames:
#python rename_files.py -i ./input -o ./output -p "\d+" -r ""
#
## Replace date format (e.g., 2023_file.txt → file_2023.txt):
#python rename_files.py -i ./input -o ./output -p "^(\d{4})_([a-z]+)" -r "\2_\1"
#
## Dry run to see what would be renamed:
#python rename_files.py -i ./input -o ./output -p "test" -r "prod" --dry-run
#
## Recursive renaming with verbose output:
#python rename_files.py -i ./input -o ./output -p "test" -r "prod" -R -v
#
## Include file extensions in pattern matching:
#python rename_files.py -i ./input -o ./output -p "\.txt$" -r ".text" --no-preserve-extension
#

import os
import re
import sys
import argparse
import logging
from pathlib import Path
import shutil
from datetime import datetime
import textwrap

class FileRenamer:
    def __init__(self, input_dir, output_dir, pattern, replacement, recursive=False, 
                 verbose=False, dry_run=False, preserve_extension=True):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.pattern = pattern
        self.replacement = replacement
        self.recursive = recursive
        self.dry_run = dry_run
        self.preserve_extension = preserve_extension
        self.setup_logging(verbose)
        
    @staticmethod
    def setup_logging(verbose):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def find_files(self):
        """Find all files in the input directory"""
        pattern = '**/*' if self.recursive else '*'
        return [f for f in self.input_dir.glob(pattern) if f.is_file()]

    def generate_new_name(self, filepath):
        """Generate new filename based on pattern and replacement"""
        if self.preserve_extension:
            stem = filepath.stem
            new_stem = re.sub(self.pattern, self.replacement, stem)
            return f"{new_stem}{filepath.suffix}"
        else:
            filename = filepath.name
            return re.sub(self.pattern, self.replacement, filename)

    def rename_files(self):
        """Rename files according to the pattern and save to output directory"""
        files = self.find_files()
        
        if not files:
            logging.warning("No files found in the input directory.")
            return False

        total_files = len(files)
        processed_files = 0
        successful_renames = 0
        rename_map = {}

        logging.info(f"Found {total_files} files to process")

        # First pass: check for naming conflicts
        for filepath in files:
            try:
                new_name = self.generate_new_name(filepath)
                new_path = self.output_dir / new_name
                
                if new_path in rename_map.values():
                    logging.error(f"Naming conflict: Multiple files would be renamed to {new_name}")
                    return False
                
                rename_map[filepath] = new_path
                
            except Exception as e:
                logging.error(f"Error processing {filepath}: {str(e)}")
                return False

        # Create output directory if it doesn't exist and not in dry run mode
        if not self.dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Second pass: perform the renaming
        for old_path, new_path in rename_map.items():
            processed_files += 1
            relative_old = old_path.relative_to(self.input_dir)
            relative_new = new_path.relative_to(self.output_dir)
            
            try:
                if self.dry_run:
                    logging.info(f"Would rename: {relative_old} → {relative_new}")
                    successful_renames += 1
                else:
                    # Copy file to new location with new name
                    shutil.copy2(old_path, new_path)
                    successful_renames += 1
                    logging.info(f"Renamed: {relative_old} → {relative_new}")
                
            except Exception as e:
                logging.error(f"Error renaming {relative_old}: {str(e)}")

        # Log summary
        summary = f"\nRenaming completed: {successful_renames} of {processed_files} files processed"
        if self.dry_run:
            summary = "[DRY RUN] " + summary
        logging.info(summary)

        return successful_renames > 0

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Rename files using regular expression pattern matching.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            Examples:
              # Replace 'old' with 'new' in filenames:
              %(prog)s -i ./input -o ./output -p "old" -r "new"
              
              # Remove numbers from filenames:
              %(prog)s -i ./input -o ./output -p "\d+" -r ""
              
              # Complex pattern with dry run:
              %(prog)s -i ./input -o ./output -p "^(\d{4})_([a-z]+)" -r "\\2_\\1" --dry-run
              
              # Recursive renaming with verbose output:
              %(prog)s -i ./input -o ./output -p "test" -r "prod" -R -v
        ''')
    )
    
    parser.add_argument('-i', '--input-directory',
                        required=True,
                        help='Source directory containing files to rename')
    
    parser.add_argument('-o', '--output-directory',
                        required=True,
                        help='Directory where renamed files will be saved')
    
    parser.add_argument('-p', '--pattern',
                        required=True,
                        help='Regular expression pattern to match in filenames')
    
    parser.add_argument('-r', '--replacement',
                        required=True,
                        help='Replacement string for matched pattern')
    
    parser.add_argument('-R', '--recursive',
                        action='store_true',
                        help='Process files in subdirectories recursively')
    
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')
    
    parser.add_argument('--dry-run',
                        action='store_true',
                        help='Show what would be renamed without making any changes')
    
    parser.add_argument('--no-preserve-extension',
                        action='store_true',
                        help='Apply pattern to entire filename including extension')
    
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0.0',
                        help='Show program version number and exit')

    return parser

def validate_directories(input_dir, output_dir):
    """Validate input and output directories"""
    if not os.path.isdir(input_dir):
        return False, f"Input directory does not exist: {input_dir}"
    
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create output directory '{output_dir}': {str(e)}"
    
    try:
        test_file = os.path.join(output_dir, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True, ""
    except Exception as e:
        return False, f"Cannot write to output directory '{output_dir}': {str(e)}"

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Validate directories (skip if dry run)
    if not args.dry_run:
        is_valid, error_message = validate_directories(args.input_directory, args.output_directory)
        if not is_valid:
            parser.error(error_message)

    try:
        # Validate regex pattern
        try:
            re.compile(args.pattern)
        except re.error as e:
            parser.error(f"Invalid regular expression pattern: {str(e)}")

        renamer = FileRenamer(
            args.input_directory,
            args.output_directory,
            args.pattern,
            args.replacement,
            args.recursive,
            args.verbose,
            args.dry_run,
            not args.no_preserve_extension
        )
        
        success = renamer.rename_files()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
