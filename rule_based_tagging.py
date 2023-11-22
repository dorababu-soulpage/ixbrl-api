import re, io, uuid
import pandas as pd
from bs4 import BeautifulSoup
from utils import s3_uploader


def read_excel_sheet(file_path, sheet_name):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Convert each row into a dictionary and append it to a list
    records = df.to_dict(orient="records")

    return records


def clean_cell_text(cell):
    return re.sub(r"\s+", " ", cell.get_text(strip=True).replace("\n", "").strip())


def add_tag_to_keyword(html_file, xlsx_file):
    # Read the content of the HTML file
    html_content = html_file.read()
    soup = BeautifulSoup(html_content, "html.parser")

    # read excel
    mappings = read_excel_sheet(xlsx_file, "Mapping")
    # statement_name = read_excel_sheet(file_path, "Statement Name")
    # master_elements = read_excel_sheet(file_path, "Master Element")

    for record in mappings:
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
                            # tag = f'<font id="xdx_40N_e{tag}_{uuid.uuid4().hex}">{keyword}</font>'
                            # cell.string.replace_with(BeautifulSoup(tag, "html.parser"))

                            # keyword is table row
                            # Find the <tr> tag and add the id attribute
                            row["id"] = f"xdx_40N_e{tag}_{uuid.uuid4().hex}"

    # Create a BytesIO object to store the modified HTML content
    html_bytes = io.BytesIO()

    # Convert the soup to a string and encode it to bytes
    html_bytes.write(str(soup).encode("utf-8"))

    # Use uuid to create a unique filename
    filename = f"{uuid.uuid4().hex}.html"

    # Assuming s3_uploader is a function to upload the file to S3
    # Replace this with your actual S3 upload implementation
    url = s3_uploader(filename, html_bytes)
    return url


# if __name__ == "__main__":
#     html_file_path = "mays4160726-10q.htm"
#     xlsx_file = "Rule_Based_Tagging.xlsx"
#     add_tag_to_keyword(html_file_path, xlsx_file)
