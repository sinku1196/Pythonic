import os
import csv

start_directory = "downloads"  # Use '.' for the current directory, or specify a path e.g., '/home/user/docs'

print(f"--- Traversing directory: {start_directory} using os.walk() ---")


def get_second_line_first_value(csv_file_path):
    with open(csv_file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        second_row = next(reader)
        return second_row[0]


for root, dirs, files in os.walk(start_directory):
    for file in files:
        full_file_path = os.path.join(root, file)

        if full_file_path.endswith(".csv"):
            start_month = get_second_line_first_value(full_file_path)
            client = full_file_path.split("\\")[2]
            print(f"Client: {client} - Start month: {start_month}")
