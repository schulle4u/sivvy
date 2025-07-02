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

    def __init__(self, filename, display_range=None, table_format="simple"):
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
        self.delimiter = ','
        self.display_range = display_range

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

        print("="*50)
        print(self._("Status Messages:"))
        print("="*50)

        messages_to_show = self.status_messages
        if not self.show_all_messages and len(self.status_messages) > 5:
            messages_to_show = self.status_messages[-5:]
            print(self._("(Showing last 5 messages - enter 's' to see all)"))

        for msg in messages_to_show:
            print(f"[{msg['timestamp']}] {msg['message']}")

        print("="*50)

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
                    self.delimiter = ','
                    self._save_csv(initial_save=True)
                    self.show_message(
                        self._("Created empty new file '%(file)s' with headers.") % {'file': self.filename}, 
                        'info'
                    )
                    return
                self.delimiter = self._detect_delimiter_from_content(content)

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
                    self.delimiter = ','

        except FileNotFoundError:
            self.show_message(
                self._("File '%(file)s' not found. Creating a new file.") % {'file': self.filename}, 
                'warning',
            )
            self.headers = self._get_headers_from_user()
            self.delimiter = ','
            self._save_csv(initial_save=True)

        except PermissionError:
            self.show_message(
                self._("Permission denied: Cannot read file '%(file)s'.") % {'file': self.filename},
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

            self.show_message(
                self._("Detected delimiter: '%(delimiter)s'") % {'delimiter': dialect.delimiter},
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

    def display_table(self):
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

        indexed_data = []
        for i, row in enumerate(data_to_display):
            original_index = (i + 1) + (start_row if start_row is not None else 0)

            padded_row = row + [''] * (len(self.headers) - len(row))
            indexed_data.append([original_index] + padded_row[:len(self.headers)]) 

        indexed_headers = [self._("Index")] + self.headers
        print(tabulate(indexed_data, headers=indexed_headers, tablefmt=self.table_format, disable_numparse=True))

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

    def run(self):
        """Main editor loop"""
        while True:
            self.clear_console()

            print(self._("Welcome to Sivvy!"))

            # Show status messages above the table
            self.display_status_messages()

            self.display_table()

            print("="*50)
            user_input = input(self._("Command ('h' for help): ")).strip().lower()

            if user_input == 'q':
                confirm_exit = input(self._("Exit and save changes") + " (y/n): ").strip().lower()
                if confirm_exit == 'y':
                    break
                else:
                    self.show_message(self._("Aborted."), 'info')
                    continue

            elif user_input == 's':
                self.toggle_message_display()
                continue

            elif user_input == 'c':
                self.clear_status_messages()
                self.show_message(self._("Status messages cleared."), 'info')
                continue

            elif user_input == 'h':
                print(self._("Commands:"))
                print(self._("- Enter row number to edit (0 for headers)"))
                print(self._("- 's' to toggle status message display"))
                print(self._("- 'c' to clear status messages"))
                print(self._("- 'q' to exit"))
                input(self._("Press Enter to continue..."))
                continue

            elif user_input == '0':
                self._edit_headers()
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

    args = parser.parse_args()

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

    app = Sivvy(args.filename, display_range, args.format)
    app.run()


if __name__ == "__main__":
    main()
