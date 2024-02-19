import os
import requests
import re, io, uuid
import pandas as pd
from bs4 import BeautifulSoup
from utils import s3_uploader, update_db_record


def read_excel_sheet(file_path, sheet_name):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Convert each row into a dictionary and append it to a list
    records = df.to_dict(orient="records")

    return records


def clean_cell_text(cell):
    return re.sub(r"\s+", " ", cell.get_text(strip=True).replace("\n", "").strip())


def add_tag_to_keyword(file_id, html_file, xlsx_file, cik, form_type):
    response = requests.get(html_file)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        html_content = response.content
        soup = BeautifulSoup(html_content, "html.parser")
    else:
        print(f"Failed to retrieve HTML. Status code: {response.status_code}")

    # read excel
    master_elements = read_excel_sheet(xlsx_file, "Master Element")
    # Find the first record with CIK equal to target_cik

    #  Find the first record with matching CIK and Document Type
    matching_record = None

    for record in master_elements:
        cik_str = str(record["CIK"]).zfill(10)

        if (
            cik_str == cik.strip()
            and str(record.get("Document Type")) == form_type.strip()
        ):
            matching_record = record
            break

    print(matching_record, "========[matched record]========")

    mapping_id = None
    # Extract and print the 'Mapping ID' if a matching record was found
    if matching_record:
        mapping_id = matching_record["Mapping ID"]
        print(f"Mapping ID for CIK {cik} and Document Type {form_type}: {mapping_id}")
    else:
        print("No record found for CIK =", cik, "and Document Type =", form_type)

    mappings = read_excel_sheet(xlsx_file, "Mapping")
    # statement_name = read_excel_sheet(file_path, "Statement Name")
    # Filter the list based on 'Mapping ID' equal to 1
    filtered_mappings = [
        element for element in mappings if element.get("Mapping ID") == mapping_id
    ]

    for record in filtered_mappings:
        keyword = record.get("Element Lable", "")
        tag = record.get("Element Tagging", "")
        element_type = record.get("Element Type", "")
        is_custom = record.get("Is_Custom", "")

        # Find all rows in the table
        rows = soup.find_all("tr")

        # Iterate through each row and extract data
        for row in rows:
            # Find all cells (td) in the row
            cells = row.find_all(["td", "th"])

            # Extract and clean the text content of each cell
            row_data = [clean_cell_text(cell) for cell in cells]

            # Remove empty strings from the list
            row_data = list(filter(None, row_data))

            # Check if search term exists in the row data
            if keyword in row_data:
                # Modify the content of the corresponding cells
                for cell, modified_text in zip(cells, row_data):
                    if modified_text == keyword:
                        if cell.string is not None:
                            # keyword is not not table row
                            # tag = f'<font id="apex_40N_e{tag}_{uuid.uuid4().hex}">{keyword}</font>'
                            # cell.string.replace_with(BeautifulSoup(tag, "html.parser"))

                            # keyword is table row
                            # Find the <tr> tag and add the id attribute
                            row["id"] = f"apex_40N_e{tag}_{uuid.uuid4().hex}"

    # Create a BytesIO object to store the modified HTML content
    html_bytes = io.BytesIO()

    # Convert the soup to a string and encode it to bytes
    html_bytes.write(str(soup).encode("utf-8"))

    # Extract the filename from the URL
    file_name = os.path.basename(html_file)

    # Add "_1" to the filename before the extension
    new_file_name = (
        os.path.splitext(file_name)[0] + "_1" + os.path.splitext(file_name)[1]
    )
    # Assuming s3_uploader is a function to upload the file to S3
    # Replace this with your actual S3 upload implementation
    url = s3_uploader(new_file_name, html_bytes)
    update_db_record(file_id, {"url": url, "inAutoTaggingProcess": False})
    print("Url updated successfully in database")

    return


# if __name__ == "__main__":
#     html_file_path = "mays4160726-10q.htm"
#     xlsx_file = "Rule_Based_Tagging.xlsx"
#     add_tag_to_keyword(html_file_path, xlsx_file)
