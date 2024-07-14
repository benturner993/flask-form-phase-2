import os
import csv

def save_to_csv(file_path, row_data):
    """
    Save data to a CSV file.

    Args:
        file_path (str): The path to the CSV file.
        row_data (list): The data to be written as a row in the CSV file.

    Returns:
        None
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(row_data)
