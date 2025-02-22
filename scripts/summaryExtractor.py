###########
## Basic usage
#python script.py -t ./documents -o ./output "Introduction" "Methods"
#
## With recursive search and verbose output
#python script.py -t ./documents -o ./output -r -v "Results" "Discussion"
#
## Using long-form arguments
#python script.py --target-directory ./docs --output ./results --recursive "Conclusion"
#
## Get help
#python script.py --help
###########


import os
from docx import Document
import textwrap
import re
import sys
import argparse
from pathlib import Path
import logging
from datetime import datetime

class DocumentProcessor:
    def __init__(self, input_dir, output_dir, patterns, recursive=False, verbose=False):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.patterns = patterns
        self.recursive = recursive
        self.setup_logging(verbose)

    @staticmethod
    def setup_logging(verbose):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def get_document_number(self, filename):
        """Extract 6-digit number from document filename"""
        basename = filename.stem
        if re.match(r'^\d{6}$', basename):
            return basename
        return None

    def extract_text_under_title(self, doc_path, title_pattern):
        """Extract text under a specific title pattern from a Word document"""
        try:
            doc = Document(doc_path)
            found_text = []
            found_title = None
            capture_text = False
            
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            
            for i, text in enumerate(paragraphs):
                if not capture_text:
                    if re.search(title_pattern, text, re.IGNORECASE):
                        capture_text = True
                        found_title = text
                        continue
                else:
                    if i < len(paragraphs) - 1:
                        next_text = paragraphs[i + 1]
                        if (len(next_text) < 100 and 
                            (next_text.endswith((':','।','.')) or 
                             re.match(r'^[IVX]+\.|\d+\.|\([a-zA-Z]\)', next_text))):
                            break
                    found_text.append(text)
            
            if found_text:
                return ('\n'.join(found_text), found_title)
            return None, None
            
        except Exception as e:
            logging.error(f"Error processing document {doc_path}: {str(e)}")
            return None, None

    def save_extracted_text(self, text, title, doc_number, source_doc, output_dir):
        """Save extracted text to a file in the specified output directory"""
        try:
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title[:50]
            output_filename = f"{doc_number}_{clean_title}.txt"
            output_path = output_dir / output_filename
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Source Document: {source_doc}\n")
                f.write(f"Original Title: {title}\n")
                f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(text)
            
            return True, output_filename
        except Exception as e:
            return False, f"Error saving {output_filename}: {str(e)}"

    def find_docx_files(self):
        """Find all matching .docx files in the input directory"""
        pattern = '**/*.docx' if self.recursive else '*.docx'
        return [f for f in self.input_dir.glob(pattern) 
                if self.get_document_number(f)]

    def process_documents(self):
        """Process all documents and extract text based on patterns"""
        doc_files = self.find_docx_files()
        
        if not doc_files:
            logging.warning("No documents with 6-digit filenames found in the directory.")
            return False

        total_files = len(doc_files)
        processed_files = 0
        successful_extractions = 0

        logging.info(f"Found {total_files} documents to process")

        for doc_path in doc_files:
            processed_files += 1
            doc_number = self.get_document_number(doc_path)
            
            logging.info(f"Processing {doc_path.name} ({processed_files}/{total_files})")
            
            for pattern in self.patterns:
                extracted_text, found_title = self.extract_text_under_title(doc_path, pattern)
                
                if extracted_text:
                    success, message = self.save_extracted_text(
                        extracted_text, 
                        found_title, 
                        doc_number, 
                        doc_path.name, 
                        self.output_dir
                    )
                    if success:
                        successful_extractions += 1
                        logging.info(f"Saved: {message}")
                    else:
                        logging.error(message)
                else:
                    logging.debug(f"Pattern '{pattern}' not found in {doc_path.name}")

        logging.info(f"\nProcessing completed: {successful_extractions} extractions from {processed_files} files")
        return True

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Extract text under specified titles from Word documents.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            Examples:
              %(prog)s -t ./documents -o ./output "Introduction" "Methods"
              %(prog)s --target-directory ./docs --output ./results --recursive "Results"
              %(prog)s -t ./docs -o ./out -v "Discussion" "Conclusion"
        ''')
    )
    
    parser.add_argument('-t', '--target-directory',
                        required=True,
                        help='Directory containing the Word documents')
    
    parser.add_argument('-o', '--output',
                        required=True,
                        help='Directory where extracted text files will be saved')
    
    parser.add_argument('patterns',
                        nargs='+',
                        help='One or more title patterns to search for')
    
    parser.add_argument('-r', '--recursive',
                        action='store_true',
                        help='Search for documents recursively in subdirectories')
    
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Validate input directory
    if not os.path.isdir(args.target_directory):
        parser.error(f"Input directory does not exist: {args.target_directory}")

    try:
        processor = DocumentProcessor(
            args.target_directory,
            args.output,
            args.patterns,
            args.recursive,
            args.verbose
        )
        
        success = processor.process_documents()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
