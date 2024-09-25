import json
import csv

# Define input JSON file and output CSV file names
json_file_name = 'CognitoUsers.json'
csv_file_name = 'CognitoUsers2.csv'

# Read JSON data from the file
try:
    with open(json_file_name, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
except FileNotFoundError:
    print(f"Error: The file '{json_file_name}' was not found.")
    exit()
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from the file '{json_file_name}'.")
    exit()

# Check if json_data is a list of dictionaries
if not isinstance(json_data, list):
    print("Error: JSON data is not a list.")
    exit()

# Extract CSV headers from the JSON keys
csv_headers = set()
for record in json_data:
    csv_headers.update(record.keys())

csv_headers = list(csv_headers)  # Convert to list for CSV writer

# Write data to CSV file
try:
    with open(csv_file_name, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
        csv_writer.writeheader()  # Write CSV headers
        for record in json_data:
            csv_writer.writerow(record)  # Write each JSON object as a row in the CSV file

    print(f"Data successfully written to {csv_file_name}")

except IOError as e:
    print(f"Error writing to CSV file: {e}")
