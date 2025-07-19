# -*- coding: utf-8 -*-
# Sivvy - a terminal CSV editor
# Copyright (C) 2025 Steffen Schultz
import sys
import os
import gettext
import locale
import csv
import re
import argparse
import signal
import time
from pathlib import Path
from io import StringIO
from tabulate import tabulate


if sys.version_info < (3, 10):
    print("Error: This script requires Python version 3.10 or higher.")
    print(f"Your version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    sys.exit(1)


class Sivvy:
    # List of supported table output formats
    SUPPORTED_TABLE_FORMATS = [
        "plain", "simple", "github", "grid", "simple_grid", "rounded_grid", 
        "heavy_grid", "mixed_grid", "double_grid", "fancy_grid", "outline", "simple_outline", 
        "rounded_outline", "heavy_outline", "mixed_outline", "double_outline", "fancy_outline", 
        "pipe", "orgtbl", "asciidoc", "jira", "presto", "pretty", 
        "psql", "rst", "mediawiki", "moinmoin", "youtrack", "html", 
        "unsafehtml", "latex", "latex_raw", "latex_booktabs", "latex_longtable", 
        "textile", "tsv"
    ]

    def __init__(self, filename, display_range=None, table_format="simple", column_delimiter=",", manual_delimiter_set=False, output_filename=None):
        # Determine current script directory
        if getattr(sys, 'frozen', False):
            self.scriptdir = Path(sys.executable).parent
        else:
            self.scriptdir = Path(__file__).parent.absolute()

        # Set a nice title for windows users
        if os.name == 'nt': os.system('title Sivvy')

        # Status message system
        self.status_messages = []
        self.max_status_messages = 10
        self.show_all_messages = False

        # Parameters
        self.filename = filename
        self.data = []
        self.headers = []
        self.delimiter = column_delimiter
        self._manual_delimiter = manual_delimiter_set
        self.display_range = display_range
        self.deleted_rows = []  # Saves deleted rows for undo
        self.max_undo_history = 10

        # Setup our methods
        self.setup_signal_handlers()
        self.setup_localization()
        self.check_table_format(table_format)
        self._load_csv()

    def clear_console(self):
        """Clears the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful termination"""
        signal.signal(signal.SIGINT, self.handle_exit_signal)
        signal.signal(signal.SIGTERM, self.handle_exit_signal)

    def handle_exit_signal(self, signum, frame):
        """Handle exit signals"""
        print("\n Exiting...")
        sys.exit(0)

    def setup_localization(self):
        """Setup localization settings"""
        system_language = locale.getlocale()
        try:
            if os.name == 'nt':
                os.environ['LANG'] = system_language[0] + '.utf8'
                locale.setlocale(locale.LC_ALL, system_language[0] + '.utf8')
            else:
                locale.setlocale(locale.LC_ALL, '')
        except locale.Error as e:
            print(f"Warning: Error while setting locale: {e} Trying fallback to default 'C' locale.")
            try:
                locale.setlocale(locale.LC_ALL, 'C')
            except locale.Error as e_fallback:
                print(f"Error falling back to 'C' locale: {e_fallback}. Locale not set.")

        gettext.bindtextdomain('sivvy', str(self.scriptdir / 'locale'))
        gettext.textdomain('sivvy')
        self._ = gettext.gettext

    def _validate_filename(self, filename):
        """
        Validates a file name for problematic characters.

        Args:
            filename (str): file name to validate

        Returns:
            tuple: (is_valid, error_message)
                - is_valid (bool): True if valid, False if not valid
                - error_message (str): Error message for invalid file names
        """
        if not filename or not filename.strip():
            return False, self._("Filename cannot be empty.")

        # Remove whitespace
        filename = filename.strip()

        # Check for problematic characters (Windows and Unix)
        invalid_chars = '<>:"/\\|?*'
        found_invalid = [char for char in invalid_chars if char in filename]
        if found_invalid:
            return False, self._("Invalid characters in filename: %(chars)s") % {
                'chars': ', '.join(found_invalid)
            }

        # Check for reserved file names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 
                         'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            return False, self._("'%(name)s' is a reserved filename.") % {'name': filename}

        # Check for long file names (255 chars)
        if len(filename) > 255:
            return False, self._("Filename is too long (maximum 255 characters).")

        # Check if file name only contains dots
        if filename.replace('.', '').strip() == '':
            return False, self._("Filename cannot consist only of dots.")

        return True, ""

    def show_message(self, message, msg_type='info', pause=False, store=True):
        """
        Unified message handling system.

        Args:
            message (str): The message to display
            msg_type (str): 'info', 'warning', 'error' - determines formatting and behavior
            persist (bool): Whether message should persist across screen clears
            pause (bool): Whether to pause for user input after displaying
            store (bool): Whether to store message in status list
        """

        # Format message based on type
        formatted_message = self._format_message(message, msg_type)

        if store:
            self.status_messages.append({
                'message': formatted_message,
                'type': msg_type,
                'timestamp': self._get_current_time()
            })

            if len(self.status_messages) > self.max_status_messages:
                self.status_messages.pop(0)

        if msg_type == 'error' or msg_type == 'warning' or pause:
            print(formatted_message)
            if pause or msg_type == 'error':
                input(self._("Press Enter to continue..."))

    def _get_current_time(self):
        """Returns a simple timestamp."""
        return time.strftime("%H:%M:%S")

    def display_status_messages(self):
        """Show all saved status messages."""
        if not self.status_messages:
            return

        print("=" * 50)
        print(self._("Status Messages:"))
        print("=" * 50)

        messages_to_show = self.status_messages
        if not self.show_all_messages and len(self.status_messages) > 5:
            messages_to_show = self.status_messages[-5:]
            print(self._("(Showing last 5 messages - enter 's' to see all)"))

        for msg in messages_to_show:
            print(f"[{msg['timestamp']}] {msg['message']}")

        print("=" * 50)

    def clear_status_messages(self):
        """Deletes all saved messages."""
        self.status_messages = []

    def toggle_message_display(self):
        """Switches between compact and full message display."""
        self.show_all_messages = not self.show_all_messages
        status = self._("all") if self.show_all_messages else self._("recent")
        self.show_message(
            self._("Message display mode: %(mode)s") % {'mode': status}, 
            'info', 
            store=False
        )

    def _format_message(self, message, msg_type):
        """Format message based on type."""
        if msg_type == 'error':
            return f"\a❌ {message}"  # Bell sound + error icon
        elif msg_type == 'warning':
            return f"⚠  {message}"   # Warning icon
        else:
            return f"ℹ  {message}"    # Info icon

    def _get_headers_from_user(self):
        """Prompts the user to enter column names."""
        print(self._("Please enter column names separated by commas."))
        header_input = input(self._("Column names: "))
        headers = [h.strip() for h in header_input.split(',') if h.strip()]
        if not headers:
            self.show_message(self._("No column names entered. Using default headers."), 'info')
            headers = ["Column 1", "Column 2", "Column 3"]
        return headers

    def check_table_format(self, table_format):
        """Check if table output format is valid, otherwise use default."""
        if table_format in self.SUPPORTED_TABLE_FORMATS:
            self.table_format = table_format
        else:
            self.show_message(self._("Warning: Invalid output format '%(format)s' entered. Falling back to default format 'simple'.") % {'format': table_format}, 'warning')
            self.table_format = "simple"

    def _load_csv(self):
        """Loads a csv file or creates a new one."""
        try:
            with open(self.filename, 'r', newline='', encoding='utf-8') as csvfile:
                content = csvfile.read()

                if not content.strip():
                    self.show_message(
                        self._("File '%(file)s' is empty. Please enter column names:") % {'file': self.filename},
                        'warning'
                    )
                    self.headers = self._get_headers_from_user()
                    # self.delimiter = ','
                    self._save_csv(initial_save=True)
                    self.show_message(
                        self._("Created empty new file '%(file)s' with headers.") % {'file': self.filename}, 
                        'info'
                    )
                    return

                if not self._manual_delimiter:
                    detected_delimiter = self._detect_delimiter_from_content(content)
                    if detected_delimiter != self.delimiter:
                        self.delimiter = detected_delimiter
                else:
                    delimiter_display = self.readable_delimiter(self.delimiter)
                    self.show_message(
                        self._("Using manually set delimiter: %(delimiter)s") % {'delimiter': delimiter_display},
                        'info'
                    )

                csvfile_in_memory = StringIO(content)
                reader = csv.reader(csvfile_in_memory, delimiter=self.delimiter)

                try:
                    self.headers = next(reader)
                    self.data = list(reader)

                    self.show_message(
                        self._("Loaded file '%(file)s' with %(rows)s rows.") % {
                            'file': self.filename, 
                            'rows': len(self.data)
                        }, 
                        'info'
                    )

                except StopIteration:
                    self.show_message(
                        self._("File exists but appears to be empty after reading."), 
                        'warning'
                    )
                    self.headers = self._get_headers_from_user()
                    # self.delimiter = ','

        except FileNotFoundError:
            self.show_message(
                self._("File '%(file)s' not found. Creating a new file.") % {'file': self.filename}, 
                'warning',
            )
            self.headers = self._get_headers_from_user()
            # self.delimiter = ','
            self._save_csv(initial_save=True)

        except PermissionError:
            self.show_message(
                self._("Permission denied: Cannot access file '%(file)s'.") % {'file': self.filename},
                'error'
            )
            raise

        except UnicodeDecodeError as e:
            self.show_message(
                self._("File encoding error: %(error)s. Trying different encoding...") % {'error': e},
                'warning'
            )
            self._try_alternative_encodings()

    def _detect_delimiter_from_content(self, content):
        """Detects delimiter from file content."""
        try:
            sample = content[:1024] if len(content) > 1024 else content

            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)

            delimiter_display = self.readable_delimiter(dialect.delimiter)

            self.show_message(
                self._("Detected delimiter: %(delimiter)s") % {'delimiter': delimiter_display},
                'info'
            )

            return dialect.delimiter

        except csv.Error as e:
            self.show_message(
                self._("Could not detect delimiter automatically: %(error)s. Using comma (,).") % {'error': e},
                'warning'
            )
            return ','
        except Exception as e:
            self.show_message(
                self._("Unexpected error during delimiter detection: %(error)s. Using comma (,).") % {'error': e},
                'warning'
            )
            return ','

    def readable_delimiter(self, delimiter):
        """
        Makes non-printable delimiter characters readable.

        Args:
            delimiter (str): the delimiter

        Returns:
            str: A readable delimiter display
        """
        # Dictionary with most used non-printable characters
        non_printable_chars = {
            '\t': 'TAB',
            '\n': 'NEWLINE',
            '\r': 'CARRIAGE_RETURN',
            '\v': 'VERTICAL_TAB',
            '\f': 'FORM_FEED',
            ' ': 'SPACE',
            '\x00': 'NULL',
            '\x01': 'SOH',
            '\x02': 'STX',
            '\x03': 'ETX',
            '\x04': 'EOT',
            '\x05': 'ENQ',
            '\x06': 'ACK',
            '\x07': 'BELL',
            '\x08': 'BACKSPACE',
            '\x0e': 'SHIFT_OUT',
            '\x0f': 'SHIFT_IN',
            '\x10': 'DATA_LINK_ESCAPE',
            '\x11': 'DEVICE_CONTROL_1',
            '\x12': 'DEVICE_CONTROL_2',
            '\x13': 'DEVICE_CONTROL_3',
            '\x14': 'DEVICE_CONTROL_4',
            '\x15': 'NEGATIVE_ACK',
            '\x16': 'SYNCHRONOUS_IDLE',
            '\x17': 'END_TRANSMISSION_BLOCK',
            '\x18': 'CANCEL',
            '\x19': 'END_OF_MEDIUM',
            '\x1a': 'SUBSTITUTE',
            '\x1b': 'ESCAPE',
            '\x1c': 'FILE_SEPARATOR',
            '\x1d': 'GROUP_SEPARATOR',
            '\x1e': 'RECORD_SEPARATOR',
            '\x1f': 'UNIT_SEPARATOR'
        }

        if delimiter in non_printable_chars:
            return f"'{delimiter}' ({non_printable_chars[delimiter]})"

        elif delimiter.isprintable():
            return f"'{delimiter}'"

        else:
            hex_repr = ''.join(f'\\x{ord(c):02x}' for c in delimiter)
            return f"'{delimiter}' (HEX: {hex_repr})"

    def _try_alternative_encodings(self):
        """Fallback method to try different encodings if UTF-8 fails."""
        alternative_encodings = ['latin1', 'cp1252', 'iso-8859-1']

        for encoding in alternative_encodings:
            try:
                self.show_message(
                    self._("Trying encoding: %(encoding)s") % {'encoding': encoding},
                    'info'
                )

                with open(self.filename, 'r', newline='', encoding=encoding) as csvfile:
                    content = csvfile.read()

                    if not content.strip():
                        continue

                    self.delimiter = self._detect_delimiter_from_content(content)

                    csvfile_in_memory = StringIO(content)
                    reader = csv.reader(csvfile_in_memory, delimiter=self.delimiter)

                    self.headers = next(reader)
                    self.data = list(reader)

                    self.show_message(
                        self._("Successfully loaded with encoding %(encoding)s.") % {'encoding': encoding},
                        'info'
                    )
                    return

            except (UnicodeDecodeError, csv.Error):
                continue
            except Exception as e:
                self.show_message(
                    self._("Error with encoding %(encoding)s: %(error)s") % {'encoding': encoding, 'error': e},
                    'warning'
                )
                continue

        self.show_message(
            self._("Could not read file with any supported encoding. File may be corrupted."),
            'error'
        )
        raise UnicodeDecodeError("All encodings failed", b"", 0, 1, "Cannot decode file")

    def _save_csv(self, initial_save=False):
        """Saves current data to csv file."""
        try:
            with open(self.filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter)
                if self.headers:
                    writer.writerow(self.headers)
                else: 
                    writer.writerow(["Column 1", "Column 2", "Column 3"])

                writer.writerows(self.data)
            if not initial_save:
                # No special status messages here as the program exits anyway
                print(self._("Saved changes in '%(file)s'.") % {'file': self.filename})
        except IOError as e:
            print(self._("Error saving '%(file)s': %(error)s") % {'file': self.filename, 'error': e})
        except Exception as e:
            print(self._("An unexpected error occurred while saving: %(error)s") % {'error': e})

    def display_table(self, output_filename=None, show_index=True):
        """Displays data in the terminal as a formatted table, optionally with row limit."""
        data_to_display = self.data
        start_row, end_row = None, None

        if self.display_range:
            start_row = max(0, self.display_range[0] - 1) 
            end_row = min(len(self.data), self.display_range[1]) 

            if start_row < end_row:
                data_to_display = self.data[start_row:end_row]
                print("\n--- " + self._("Displaying rows %(start)s to %(end)s") % {'start': start_row + 1, 'end': end_row} + " ---")
            else:
                self.show_message("\n" + self._("Invalid or empty display range. Loading the entire file."), 'warning')
                data_to_display = self.data 
                self.display_range = None
                start_row, end_row = None, None

        if show_index:
            indexed_data = []
            for i, row in enumerate(data_to_display):
                original_index = (i + 1) + (start_row if start_row is not None else 0)
                padded_row = row + [''] * (len(self.headers) - len(row))
                indexed_data.append([original_index] + padded_row[:len(self.headers)]) 

            indexed_headers = [self._("Index")] + self.headers
            table_data = indexed_data
            table_headers = indexed_headers
        else:
            table_data = []
            for row in data_to_display:
                padded_row = row + [''] * (len(self.headers) - len(row))
                table_data.append(padded_row[:len(self.headers)])

            table_headers = self.headers

        table_output = tabulate(table_data, headers=table_headers, tablefmt=self.table_format, disable_numparse=True)

        if output_filename:
            try:
                output_path = Path(output_filename)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_filename, 'w', encoding='utf-8') as f:
                    print(table_output, file=f)
                self.show_message(
                    self._("The current table's output was exported to file '%(file)s'.") % {'file': output_filename},
                    'info'
                )

            except PermissionError:
                self.show_message(
                    self._("Permission denied: Cannot access file '%(file)s'.") % {'file': output_filename},
                    'error',
                    store=False
                )
                print(table_output)

            except OSError as e:
                self.show_message(
                    self._("Error saving '%(file)s': %(error)s") % {'file': output_filename, 'error': e},
                    'error',
                    store=False
                )
                print(table_output)

            except Exception as e:
                self.show_message(
                    self._("An unexpected error occurred while saving: %(error)s") % {'error': e},
                    'error',
                    store=False
                )
                print(table_output)

        else:
            print(table_output)

    def _edit_headers(self):
        """Edits the column headers."""
        print("\n--- " + self._("Editing column headers") + " ---")
        print(self._("Enter new values. Leave empty to retain the current value."))

        new_headers = []
        for i, header in enumerate(self.headers):
            new_value = input(self._("Column %(num)s (current: '%(current)s'): ") % {'num': i + 1, 'current': header}).strip()
            if new_value == '':
                new_headers.append(header)
            else:
                new_headers.append(new_value)

        self.headers = new_headers
        self.show_message(self._("Column headers have been updated."), 'info')

    def _edit_or_add_row(self, row_index):
        """Edits an existing row or adds a new one."""
        original_row_count = len(self.data)

        if row_index >= original_row_count:
            if row_index > original_row_count:
                # No status message, will be displayed below the table
                print(self._("Row index %(index)s is higher than the maximum number of rows (%(maxrows)s).") % {'index': row_index + 1, 'maxrows': original_row_count})
                fill_gap = input(self._("Should the gap be filled with %(rows)s empty rows?") % {'rows': row_index - original_row_count} + " (y/n): ").strip().lower()
                if fill_gap == 'y':
                    for _ in range(row_index - original_row_count):
                        self.data.append([''] * len(self.headers))
                    self.show_message(
                        self._("Added %(rows)s empty rows.") % {'rows': row_index - original_row_count}, 
                        'info'
                    )
                else:
                    row_index = original_row_count

            new_row = [''] * len(self.headers)
            self.data.append(new_row)
            self.show_message(self._("Adding new row %(index)s.") % {'index': row_index + 1}, 'info')

        row_to_edit = self.data[row_index] 

        print("\n--- " + self._("Editing row %(index)s") % {'index': row_index + 1} + " ---")
        print(self._("Enter new values. Leave empty to retain the current value."))

        edited_row = []
        for i, header in enumerate(self.headers):
            current_value = row_to_edit[i] if i < len(row_to_edit) else ''
            new_value = input(self._("%(header)s (current: '%(current)s'): ") % {'header': header, 'current': current_value}).strip()
            if new_value == '':
                edited_row.append(current_value)
            else:
                edited_row.append(new_value)

        self.data[row_index] = edited_row 

        self.show_message(self._("Row %(index)s has been updated.") % {'index': row_index + 1}, 'info')

    def _delete_row(self, row_index):
        """Deletes a row with confirmation"""
        if row_index < 0 or row_index >= len(self.data):
            self.show_message(
                self._("Invalid row index %(index)s. Valid range: 1-%(max)s") % {
                    'index': row_index + 1, 
                    'max': len(self.data)
                }, 
                'warning'
            )
            return False

        row_to_delete = self.data[row_index]
        print("\n--- " + self._("Deleting row %(index)s") % {'index': row_index + 1} + " ---")

        for i, (header, value) in enumerate(zip(self.headers, row_to_delete)):
            print(f"{header}: {value}")

        confirm = input(self._("Delete this row?") + " (y/n): ").strip().lower()

        if confirm == 'y':
            deleted_row = self.data.pop(row_index)
            self.show_message(
                self._("Row %(index)s deleted successfully.") % {'index': row_index + 1}, 
                'info'
            )

            self.deleted_rows.append({
                'index': row_index,
                'data': deleted_row,
                'timestamp': self._get_current_time()
            })

            if len(self.deleted_rows) > self.max_undo_history:
                self.deleted_rows.pop(0)

            return True
        else:
            self.show_message(self._("Aborted."), 'info')
            return False

    def _display_row(self, row_index):
        """Detailed row display"""
        if row_index < 0 or row_index >= len(self.data):
            self.show_message(
                self._("Invalid row index %(index)s. Valid range: 1-%(max)s") % {
                    'index': row_index + 1, 
                    'max': len(self.data)
                }, 
                'warning'
            )
            return False

        row_to_display = self.data[row_index]
        print("\n--- " + self._("Displaying row %(index)s") % {'index': row_index + 1} + " ---")

        for i, (header, value) in enumerate(zip(self.headers, row_to_display)):
            print(f"{header}: {value}")

        input(self._("Press Enter to continue..."))

    def _export_table(self):
        """Exports current table view as text file"""
        print(f"\n--- {self._('Table export')} ---")
        print(self._("This function exports the current table view as a text file in the program's directory."))
        print(self._("Enter the desired file name, press Enter for the default file name 'sivvy_output.txt' or 'c' to cancel."))

        while True:
            filename_input = input(self._("Export filename (default: 'sivvy_output.txt'): ")).strip()
            if filename_input.lower() == 'c':
                self.show_message(self._("Aborted."), 'info')
                break
            if not filename_input:
                filename_input = 'sivvy_output.txt'
            is_valid, error_message = self._validate_filename(filename_input)
            if not is_valid:
                print(f"❌ {error_message}")
                print(self._("Please enter a valid filename."))
                continue
            export_path = self.scriptdir / filename_input
            if export_path.exists():
                overwrite = input(self._("File '%(file)s' already exists. Overwrite?") % {'file': filename_input} + " (y/n): ").strip().lower()
                if overwrite != 'y':
                    self.show_message(self._("Aborted."), 'info')
                    break
            show_index_input = input(self._("Include row index in export?") + " (y/n): ").strip().lower()
            show_index = show_index_input == 'y'

            self.display_table(export_path, show_index)
            break

    def _parse_split_command(self, user_input):
        """Parse split commands."""
        parts = user_input.split()

        if len(parts) != 2:
            self.show_message(
                self._("Invalid split command. Usage: <command> <row_number>"), 
                'warning'
            )
            return None

        try:
            row_number = int(parts[1])
            if row_number <= 0:
                self.show_message(
                    self._("Row number must be positive."), 
                    'warning'
                )
                return None

            return row_number - 1

        except ValueError:
            self.show_message(
                self._("Invalid row number: %(number)s") % {'number': parts[1]}, 
                'warning'
            )
            return None

    def _show_undo_history(self):
        """Show undo history."""
        if not self.deleted_rows:
            self.show_message(self._("No deleted rows to restore."), 'info')
            return

        print(f"\n--- {self._('Undo History')} ---")
        for i, deleted_item in enumerate(reversed(self.deleted_rows)):
            print(f"{i + 1}. {self._('Row')} {deleted_item['index'] + 1} [{deleted_item['timestamp']}]")

            preview_data = deleted_item['data'][:3]
            preview_headers = self.headers[:3]
            preview_str = " | ".join([f"{h}: {v}" for h, v in zip(preview_headers, preview_data)])
            print(f"   {preview_str}{'...' if len(deleted_item['data']) > 3 else ''}")
            print()

    def _undo_delete(self):
        """Restores a deleted line."""
        if not self.deleted_rows:
            self.show_message(self._("No deleted rows to restore."), 'info')
            return

        self._show_undo_history()

        try:
            choice = input(self._("Enter number to restore (or press Enter to cancel): ")).strip()

            if not choice:
                self.show_message(self._("Aborted."), 'info')
                return

            undo_index = int(choice) - 1

            if undo_index < 0 or undo_index >= len(self.deleted_rows):
                self.show_message(
                    self._("Invalid choice. Please enter a number between 1 and %(max)s") % {
                        'max': len(self.deleted_rows)
                    }, 
                    'warning'
                )
                return

            deleted_item = self.deleted_rows[-(undo_index + 1)]

            print(f"\n{self._('Restoring row:')} {deleted_item['index'] + 1}")
            for header, value in zip(self.headers, deleted_item['data']):
                print(f"{header}: {value}")

            restore_position = input(
                self._("Restore at position (1-%(max)s, or Enter for original position %(orig)s): ") % {
                    'max': len(self.data) + 1,
                    'orig': deleted_item['index'] + 1
                }
            ).strip()

            if restore_position:
                try:
                    position = int(restore_position) - 1
                    if position < 0 or position > len(self.data):
                        self.show_message(self._("Invalid position. Using original position."), 'warning')
                        position = min(deleted_item['index'], len(self.data))
                except ValueError:
                    self.show_message(self._("Invalid position. Using original position."), 'warning')
                    position = min(deleted_item['index'], len(self.data))
            else:
                position = min(deleted_item['index'], len(self.data))

            self.data.insert(position, deleted_item['data'])

            self.deleted_rows.pop(-(undo_index + 1))

            self.show_message(
                self._("Row restored at position %(pos)s") % {'pos': position + 1}, 
                'info'
            )

        except ValueError:
            self.show_message(self._("Invalid input. Please enter a number."), 'warning')
        except Exception as e:
            self.show_message(
                self._("Error during undo: %(error)s") % {'error': e}, 
                'error'
            )

    def run(self):
        """Main editor loop"""
        while True:
            self.clear_console()

            print(self._("Welcome to Sivvy!"))

            # Show status messages above the table
            self.display_status_messages()

            self.display_table()

            print("=" * 50)
            user_input = input(self._("Command ('h' for help): ")).strip().lower()

            match user_input:
                case 'q':
                    confirm_exit = input(self._("Exit and save changes") + " (y/n): ").strip().lower()
                    if confirm_exit == 'y':
                        break
                    else:
                        self.show_message(self._("Aborted."), 'info')
                        continue
                case 's':
                    self.toggle_message_display()
                    continue
                case 'c':
                    self.clear_status_messages()
                    self.show_message(self._("Status messages cleared."), 'info')
                    continue
                case 'h':
                    print(f"\n--- {self._('Help')} ---")
                    print(self._("The following commands are available:"))
                    print(self._("- Enter row number to edit (0 for headers)"))
                    print(self._("- 'd <row_number>' to delete a row"))
                    print(self._("- 'u' to undo/restore deleted rows"))
                    print(self._("- 'v <row_number>' to display a row in a more detailed view"))
                    print(self._("- 'e' to export current table view as a file"))
                    print(self._("- 's' to toggle status message display"))
                    print(self._("- 'c' to clear status messages"))
                    print(self._("- 'q' to exit"))
                    input(self._("Press Enter to continue..."))
                    continue
                case '0':
                    self._edit_headers()
                    continue
                case 'u':
                    self._undo_delete()
                    continue
                case 'e':
                    self._export_table()
                    continue

                case _:
                    if user_input.startswith('d '):
                        row_index = self._parse_split_command(user_input)
                        if row_index is not None:
                            self._delete_row(row_index)
                        continue
                    elif user_input.startswith('v '):
                        row_index = self._parse_split_command(user_input)
                        if row_index is not None:
                            self._display_row(row_index)
                        continue

                    try:
                        row_index = int(user_input) - 1

                        if row_index < 0:
                            self.show_message(
                                self._("Invalid row index. Please enter a positive value or 0 for headers."), 
                                'warning'
                            )
                            continue

                        self._edit_or_add_row(row_index)

                    except ValueError:
                        self.show_message(
                            self._("Invalid input. Please enter a number, '0' for headers, or 'q' to exit."), 
                            'warning'
                        )
                    except Exception as e:
                        self.show_message(
                            self._("An unexpected error occurred: %(error)s") % {'error': e}, 
                            'error'
                        )

        self._save_csv()


def main():
    parser = argparse.ArgumentParser(
        description="A simple csv editor for your terminal.",
        epilog="Source code is available at https://github.com/schulle4u/sivvy",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "filename",
        help="Csv file path, will be created if it doesn't exist."
    )

    parser.add_argument(
        "-r", "--range",
        type=str,
        help="Display only a specific set of rows. Format: START-END (e.g. 50-80)."
    )

    parser.add_argument(
        "-f", "--format",
        type=str,
        default="simple",
        help="Defines table output format (e.g. plain, simple, grid, html, latex, tsv). Default: grid.\n"
             "Available formats: " + ", ".join(Sivvy.SUPPORTED_TABLE_FORMATS)
    )

    parser.add_argument(
        "-d", "--delimiter",
        type=str,
        default=None,
        help="Manually set a column delimiter if automatic detection fails."
             "Use 'TAB' for tab character, 'SPACE' for space. Examples: ';', 'TAB', '|'"
    )

    args = parser.parse_args()

    processed_delimiter = ","
    manual_delimiter_set = False

    if args.delimiter is not None:
        manual_delimiter_set = True
        delimiter_input = args.delimiter.strip()

        delimiter_mapping = {
            'TAB': '\t',
            'SPACE': ' ',
            'SEMICOLON': ';',
            'PIPE': '|',
            'COMMA': ','
        }

        if delimiter_input.upper() in delimiter_mapping:
            processed_delimiter = delimiter_mapping[delimiter_input.upper()]
        elif len(delimiter_input) == 1:
            processed_delimiter = delimiter_input
        else:
            try:
                processed_delimiter = delimiter_input.encode().decode('unicode_escape')
                if len(processed_delimiter) != 1:
                    print(f"Error: Delimiter must be exactly one character or one of allowed keywords. Got: '{processed_delimiter}' (length: {len(processed_delimiter)})")
                    print("Valid examples: ';', 'TAB', '|', ','")
                    sys.exit(1)
            except Exception as e:
                print(f"Error: Invalid delimiter '{delimiter_input}': {e}")
                print("Valid examples: ';', 'TAB', '|', ','")
                sys.exit(1)

    display_range = None
    if args.range:
        match = re.match(r'^(\d+)-(\d+)$', args.range)
        if match:
            try:
                start_val = int(match.group(1))
                end_val = int(match.group(2))
                if start_val <= 0 or end_val <= 0 or start_val > end_val:
                    print(f"Warning: Invalid range '{args.range}'. Expecting positive numbers and start <= end.")
                else:
                    display_range = (start_val, end_val)
            except ValueError:
                print(f"Warning: Invalid number format in range '{args.range}'.")
        else:
            print(f"Warning: Invalid range format '{args.range}'. Expecting format 'start-end'.")

    app = Sivvy(args.filename, display_range, args.format, processed_delimiter, manual_delimiter_set)
    app.run()


if __name__ == "__main__":
    main()
