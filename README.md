# Sivvy
A CSV editor for your terminal.

## About Sivvy

Sivvy (a kind of nickname for CSV) is a terminal editor for creating and editing CSV tables. It was written in Python and uses the built-in CSV functions to open and edit files. Sivvy uses {Python Tabulate](https://pypi.org/project/tabulate/) to display the data, which provides numerous output formats and designs. It is just a personal tool that I use to manage digital archives and does not claim to complement or even enrich the numerous other solutions for visualizing CSV data sets. However, any contributions are always welcome. 

## Features

* Numerous output formats: Simple, Grid, Markdown, HTML, and many more.
* Commands: Line number, column headers, program control
* Delimiter detection: Detects common CSV delimiters and sets them when opening the file for entering new data.
* Display range: Only displays the desired start/end rows on the screen.
* Position calculation: If the specified row index is higher than the next available row, the row can be created automatically, or a set of empty rows can be inserted up to the specified index.
* Multilingual: Interface in English and German, other languages can be added using the Gettext template.

## Installation

Simply load the repository and install Python dependencies, either using pip or your distribution's package manager:

`pip install -r requirements.txt`. 

Then enter `python sivvy.py <file>` to open the editor. For further help, use `python sivvy.py --help`.

You can also convert the script into an executable program file using Pyinstaller, which should allow easier CSV file opening with Sivvy in your file manager without using the command line:

`pyinstaller --onefile sivvy.py`

The finished program file can then be found in the Dist folder. 

## Development

Copyright (C) Steffen Schultz, released under the terms of the MIT license.
