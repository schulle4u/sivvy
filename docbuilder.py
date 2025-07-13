# -*- coding: utf-8 -*-
import markdown
import sys
import os
from pathlib import Path


def convert_markdown_to_html(input_file, output_file=None, output_language="en"):
    """
    Converts markdown file into HTML

    Args:
        input_file (str): Path to markdown file
        output_file (str): Path to html output file (optional)
        output_language (str): Language code for HTML output (optional)
    """

    # Check input file
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return False

    # Set output file
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.with_suffix('.html')

    try:
        # Read markdown file
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Setup converter
        md = markdown.Markdown(extensions=[
            'extra',           # Additional markdown features
            'codehilite',      # Syntax Highlighting
            'toc',             # Table of contents
            'tables',          # Table support
            'attr_list'        # Attributes for html elements
        ])

        html_content = md.convert(markdown_content)

        # HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="{output_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sivvy</title>
    <link rel="stylesheet" type="text/css" media="all" href="style.css">
</head>
<body>
    <main role="main">
        {html_content}
    </main>
</body>
</html>"""

        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print(f"Converted successfully: {input_file} → {output_file}")
        return True

    except Exception as e:
        print(f"Error converting: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python docbuilder.py <input.md> [output.html] [lang=code]")
        print("Example: python docbuilder.py README.md")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_language = sys.argv[3] if len(sys.argv) > 3 else "en"

    convert_markdown_to_html(input_file, output_file, output_language)


if __name__ == "__main__":
    main()
