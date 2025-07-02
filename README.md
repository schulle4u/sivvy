# Sivvy
A CSV editor for your terminal.

## About Sivvy

Sivvy (a kind of nickname for CSV) is a terminal editor for creating and editing CSV tables. It was written in Python and uses the built-in CSV functions to open and edit files. Sivvy uses [Python Tabulate](https://pypi.org/project/tabulate/) to display the data, which provides numerous output formats and designs. It is just a personal tool that I use to manage digital archives and does not claim to complement or even enrich the numerous other solutions for visualizing CSV data sets. However, any contributions are always welcome. 

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

## Usage

After opening a CSV file, the table appears on the screen as formatted output. In addition to the table's actual columns, the row index - the number of the table row - is specified in the first column. The editor assumes that the first table row contains the column headers. Therefore row index 1 is the first data row, not the header row. To edit or create a new row, enter the corresponding row index in the command line below the table and press Enter. This opens the editing screen where you can enter a new data record or edit existing ones. To change the header, enter 0 as the row index. Above the table is the status display, which shows all success and error messages.

Sivvy also supports a few simple commands for controlling the program. You can call up a list of all commands at any time by typing "h" in the command line.

* "s" to toggle status message display (all or 5 most recent messages)
* "c" to clear status messages
* "h" to print a list of available commands
* "q" to exit the program

## Development

Copyright (C) Steffen Schultz, released under the terms of the MIT license.
