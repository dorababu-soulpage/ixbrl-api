import json
import openpyxl


def convert_excel_to_json(excel_file):
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active

    json_data = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        # Extract data from each row
        data_type, element, *attributes = row

        # Create a dictionary for each row
        json_object = {
            "datatype": data_type,
            "element": element,
            "attributes": [
                attribute for attribute in attributes if attribute is not None
            ],
        }

        # Append the object to the list
        json_data.append(json_object)

    return json.dumps(json_data, indent=4)


# Convert the Excel sheet to JSON format.
json_data = convert_excel_to_json("data/elements.xlsx")

with open("elements.json", "w") as json_file:
    json_file.write(json_data)
