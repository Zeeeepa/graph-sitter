#!/usr/bin/env python3
"""
CSV Reader Script

This script reads a CSV file and prints the first 5 rows.
"""

import csv
import sys

def read_csv(file_path):
    """
    Read a CSV file and print the first 5 rows.
    
    Args:
        file_path (str): Path to the CSV file
    """
    try:
        with open(file_path, 'r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file)
            
            # Print header
            header = next(csv_reader)
            print("Header:", header)
            
            # Print first 5 rows
            print("\nFirst 5 rows:")
            for i, row in enumerate(csv_reader):
                if i < 5:
                    print(f"Row {i+1}: {row}")
                else:
                    break
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Check if file path is provided as command line argument
    if len(sys.argv) < 2:
        print("Usage: python csv_reader.py <path_to_csv_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    read_csv(file_path)

if __name__ == "__main__":
    main()

