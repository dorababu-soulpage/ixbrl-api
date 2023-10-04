import json
import openpyxl
import requests
import pandas as pd
from bs4 import BeautifulSoup


def read_json_file(file_path, key):
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
        return data.get(key, None)


dts_file = "assets/dts.json"
concepts_file = "assets/concepts.json"
taxonomy_file = "assets/GAAP_Taxonomy_2023.xlsx"

# Read "Concepts" and "DTS" data from JSON files
DTS = read_json_file(dts_file, "DTS")
concepts = read_json_file(concepts_file, "Concepts")[0]


def get_taxonomy_values(element):
    df = pd.read_excel(taxonomy_file, sheet_name="Presentation")
    filtered_record = df[df["name"] == element].to_dict(orient="records")
    return filtered_record[0]


def populate_worksheet(worksheet, worksheet_name, data):
    if worksheet_name == "Concepts":
        # Insert data into the "Concepts" worksheet
        for category, records in data.items():
            concept_headers = records[0]
            worksheet.append([category])
            worksheet.append(list(concept_headers.keys()))

            for record in records:
                row_data = [record.get(header, None) for header in concept_headers]
                # Add the data to the worksheet
                worksheet.append(row_data)
            # Add an empty row
            worksheet.append([])

    if worksheet_name == "DTS":
        dts_headers = data[0]
        worksheet.append(list(dts_headers.keys()))

        for record in data:
            row_data = [record.get(header, None) for header in dts_headers]
            # Add the data to the worksheet
            worksheet.append(row_data)


def generate_concepts_dts_sheet(xlsx_file):
    # Create a new workbook
    workbook = openpyxl.Workbook()

    dts_worksheet_name = "DTS"
    concepts_worksheet_name = "Concepts"

    # Create the "Concepts" worksheet
    worksheet_concepts = workbook.active
    worksheet_concepts.title = concepts_worksheet_name
    populate_worksheet(worksheet_concepts, concepts_worksheet_name, concepts)

    # Create a new worksheet for "DTS"
    worksheet_dts = workbook.create_sheet(title=dts_worksheet_name)
    populate_worksheet(worksheet_dts, dts_worksheet_name, DTS)

    # Save the workbook to a file
    workbook.save(xlsx_file)
    print("Excel file generated successfully")


def add_html_elements_to_concept(html_elements_data):
    for record in html_elements_data:
        record_data = {}
        concept_headers = None

        # make definition as key in output dict
        definition = record.get("definition")

        # get concept headers
        for category, records in concepts.items():
            concept_headers = records[0]
            break

        for header in concept_headers.keys():
            record_data[header] = record.get(header, None)

        # add definition matched records into category list
        if definition not in concepts.keys():
            concepts[definition] = []
            concepts[definition].append(record_data)
        else:
            concepts[definition].append(record_data)


def extract_html_elements(file):
    # file = "https://deeplobe.s3.ap-south-1.amazonaws.com/mays4160726-10q.htm"

    # read tags from html and add into the exists concepts
    html_elements_data = []

    # Send an HTTP GET request to the URL
    response = requests.get(file)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all tags with attributes that start with "id" and have a value starting with "xdx_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("xdx_"))

        # Extract and print the attribute values
        for element in tags:
            try:
                name = element["id"].split("--")[1].split("_")[0]
                taxonomy_data = get_taxonomy_values(name)
                html_elements_data.append(taxonomy_data)
            except Exception as e:
                print(str(e))

    return html_elements_data


# def main():
#     html_file = "mays4160726-10q.htm"
#     html_elements = extract_html_elements(html_file)
#     add_html_elements_to_concept(html_elements)
#     generate_concepts_dts_sheet()

# main()
