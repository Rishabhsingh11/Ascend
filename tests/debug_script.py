"""Debug script to see raw line extraction from PDF."""

import pdfplumber
import json

def debug_extract_lines(file_path: str):
    """Extract and display all lines with metadata."""
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\n{'='*80}")
            print(f"PAGE {page_num}")
            print(f"{'='*80}\n")
            
            chars = page.chars
            if not chars:
                continue
            
            # Group characters into lines
            current_line_top = chars[0]['top']
            line_chars = []
            line_number = 0
            
            for char in chars:
                if abs(char['top'] - current_line_top) > 3:
                    if line_chars:
                        line_text = "".join([c['text'] for c in line_chars])
                        font_size = line_chars[0]['size']
                        font_name = line_chars[0]['fontname']
                        bold = 'bold' in font_name.lower() or 'bd' in font_name.lower()
                        
                        print(f"Line {line_number:3d} | Font: {font_size:5.1f} | Bold: {bold:5} | Text: {line_text.strip()}")
                        line_number += 1
                    
                    line_chars = [char]
                    current_line_top = char['top']
                else:
                    line_chars.append(char)
            
            # Last line
            if line_chars:
                line_text = "".join([c['text'] for c in line_chars])
                font_size = line_chars[0]['size']
                font_name = line_chars[0]['fontname']
                bold = 'bold' in font_name.lower() or 'bd' in font_name.lower()
                
                print(f"Line {line_number:3d} | Font: {font_size:5.1f} | Bold: {bold:5} | Text: {line_text.strip()}")

if __name__ == "__main__":
    debug_extract_lines(r"C:\\Users\\RishabhSingh\\Desktop\\Project\\Ascend-\\test_input\\Rishabh_Singh_Resume.pdf")
