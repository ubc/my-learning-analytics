import csv
import json
import os

def csv_to_json(csv_file_path, json_file_path):
    data = []

    # Open the CSV file and read its content
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        # Convert each row into a dictionary and add it to the list
        for row in csv_reader:
            data.append(row)

    # Write the list of dictionaries as JSON to the output file
    with open(json_file_path, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

def convert_csv_folder_to_json(folder_path):
    # Loop through all the files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            csv_file_path = os.path.join(folder_path, filename)
            json_file_path = os.path.join(folder_path, filename.replace(".csv", ".json"))

            # Convert CSV to JSON
            csv_to_json(csv_file_path, json_file_path)
            print(f"Converted {csv_file_path} to {json_file_path}")

if __name__ == "__main__":
    # Replace with your folder path containing CSV files
    folder_path = "/Users/matthe/CodingProjects/my-learning-analytics/mylaData"

    convert_csv_folder_to_json(folder_path)
