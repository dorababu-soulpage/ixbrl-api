import os
import requests
import re, io, uuid
import pandas as pd
from bs4 import BeautifulSoup
from utils import s3_uploader, update_db_record


class RuleBasedTagging:
    def __init__(self, html_file, xlsx_file, file_id, cik, form_type):
        self.cik = cik
        self.file_id = file_id
        self.form_type = form_type
        self.html_file = html_file
        # read s3 url
        self.soup = self.fetch_and_parse_html(html_file)
        # read the local html
        # self.soup = self.fetch_and_parse_local_html(html_file)
        self.mappings = self.read_excel_sheet(xlsx_file, "Mapping")
        self.master_elements = self.read_excel_sheet(xlsx_file, "Master Element")

    def fetch_and_parse_html(self, html_file):
        response = requests.get(html_file)

        if response.status_code == 200:
            html_content = response.content
            soup = BeautifulSoup(html_content, "html.parser")
            return soup
        else:
            print(f"Failed to retrieve HTML. Status code: {response.status_code}")
            return None

    def fetch_and_parse_local_html(self, html_file):
        try:
            with open(html_file, "r", encoding="utf-8") as file:
                html_content = file.read()
                soup = BeautifulSoup(html_content, "html.parser")
                return soup
        except FileNotFoundError:
            print(f"Error: File not found - {html_file}")
            return None
        except Exception as e:
            print(f"An error occurred while parsing the HTML file: {str(e)}")
            return None

    def read_excel_sheet(self, file_path, sheet_name):
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Convert each row into a dictionary and append it to a list
        records = df.to_dict(orient="records")

        return records

    def clean_cell_text(self, cell):
        return re.sub(r"\s+", " ", cell.get_text(strip=True).replace("\n", "").strip())

    def extract_table_after_statement(self, soup: BeautifulSoup, statement: str):

        # List to store target tables
        target_tables = []

        # Find all bold tags in the HTML
        bold_tags_b = soup.find_all("b")

        # Find all font bold tags in the HTML
        bold_tags_font = soup.find_all(
            "font", style=lambda value: value and "font-weight:bold" in value.lower()
        )

        # Combine both lists
        bold_tags = bold_tags_b + bold_tags_font

        # Function to clean and format text
        def clean_text(text):
            return " ".join(text.strip().replace("\n", "").split())

        # Loop through each bold tag in the HTML
        for tag in bold_tags:
            # Check if the bold tag contains a line break
            if tag.find("br"):
                # Extract text with line breaks and clean it
                text = tag.get_text(separator="<br>")
                cleaned_list = [
                    clean_text(item) for item in text.split("<br>") if item.strip()
                ]
                # Loop through cleaned text items
                for cleaned_list_item in cleaned_list:
                    # Check if input text matches cleaned text item
                    if statement.lower() == cleaned_list_item.lower():
                        # Find the next table after the bold tag and append it to target_tables
                        next_table = tag.find_next("table")
                        target_tables.append(next_table)
            else:
                # If no line break, extract and clean the text
                text = tag.get_text().strip()
                cleaned_text = clean_text(text)
                # Check if input text matches cleaned text
                if statement.lower() == cleaned_text.lower():
                    # Find the next table after the bold tag and append it to target_tables
                    next_table = tag.find_next("table")
                    target_tables.append(next_table)

        # Return the list of target tables
        return target_tables

    def get_matching_records(self):

        #  Find the first record with matching CIK and Document Type
        matching_records = []

        for record in self.master_elements:
            cik_str = str(record["CIK"]).zfill(10)

            if (
                cik_str == self.cik.strip()
                and str(record.get("Document Type")) == self.form_type.strip()
            ):
                matching_records.append(record)
        return matching_records

    def get_element_occurrences(self, filtered_mappings):
        element_occurrences = {}
        for record in filtered_mappings:
            keyword = record.get("Element Label", "")
            _tag: str = record.get("Element Tagging", "")
            tag = _tag.replace("_", "--").replace(":", "--")

            element_type = record.get("Element Type", "")
            is_custom = record.get("Is_Custom", "")

            if keyword not in element_occurrences.keys():
                element_occurrences[keyword] = {"count": 1, "tags": [tag]}
            else:
                element_occurrences[keyword]["count"] += 1
                element_occurrences[keyword]["tags"].append(tag)

        return element_occurrences

    def find_element_add_id_attribute(self, filtered_mappings, target_table):
        element_occurrences = self.get_element_occurrences(filtered_mappings)

        total_rows = []
        total_row_data = []

        # Find all rows in the table
        rows = target_table.find_all("tr")

        # Iterate through each row and extract data
        for row in rows:
            # Find all cells (td) in the row
            cells = row.find_all(["td", "th"])

            # Extract and clean the text content of each cell
            row_data = [self.clean_cell_text(cell) for cell in cells]

            # Remove empty strings from the list
            row_data = list(filter(None, row_data))

            total_row_data.append(row_data)
            total_rows.append(row)

        for keyword, value in element_occurrences.items():
            item_index = []
            for _ in range(value.get("count"), 0, -1):
                # Iterate through the outer list
                for i, inner_list in enumerate(total_row_data):
                    # Check if 'ASSETS' is in the inner list
                    for target_value in inner_list:
                        if keyword == target_value:
                            item_index.append(i)

            for i, index in enumerate(item_index):
                try:
                    tag = value.get("tags")[i]
                    row = total_rows[index]
                    for td in row.find_all("td"):
                        if td.text:
                            formatted_text = (
                                td.text.replace(",", "")
                                .replace("(", "")
                                .replace(")", "")
                            )

                            # Converting to integer
                            try:
                                number_int = int(formatted_text)

                                inner_array = (
                                    str(td)
                                    .replace("</td>", "")
                                    .replace("<td", "")
                                    .split(">")
                                )
                                inner_array_string = ">".join(inner_array[1:])

                                inner_html = inner_array_string

                                td.string = ""
                                for tag in td.find_all():
                                    tag.decompose()

                                formatted_string = f'<font id="apex_90N_e{tag}_{uuid.uuid4().hex}">{inner_html}</font>'

                                # Replace the contents of the td element with the new HTML content
                                td.append(
                                    BeautifulSoup(formatted_string, "html.parser")
                                )
                            except Exception as e:
                                pass

                except Exception as e:
                    pass

    def start(self):
        matching_records = self.get_matching_records()

        if not matching_records:
            print("Error: 'matching_records' list is empty.")

        for matching_record in matching_records:
            statement: str = matching_record.get("Statement Name", "")
            target_tables = self.extract_table_after_statement(self.soup, statement)

            mapping_id = matching_record.get("Mapping ID", "")
            # Filter the list based on 'Mapping ID' equal to 1
            filtered_mappings = [
                element
                for element in self.mappings
                if element.get("Mapping ID") == mapping_id
            ]
            counter = 1
            for target_table in target_tables:
                print(statement, counter)
                self.find_element_add_id_attribute(filtered_mappings, target_table)
                counter = counter + 1
        # save into database
        self.save()

    def save(self):

        # Create a BytesIO object to store the modified HTML content
        html_bytes = io.BytesIO()

        # Convert the soup to a string and encode it to bytes
        html_bytes.write(str(self.soup).encode("utf-8"))

        # Extract the filename from the URL
        file_name = os.path.basename(self.html_file)

        # Add "_1" to the filename before the extension
        new_file_name = (
            os.path.splitext(file_name)[0] + "_1" + os.path.splitext(file_name)[1]
        )
        # Assuming s3_uploader is a function to upload the file to S3
        # Replace this with your actual S3 upload implementation
        url = s3_uploader(new_file_name, html_bytes)
        update_db_record(self.file_id, {"url": url, "inAutoTaggingProcess": False})
        print(f"{url} updated successfully in database")


# if __name__ == "__main__":
#     html_file_path = "sfb35772717-10k_1709205766138.htm"
#     xlsx_file = "https://deeplobe.s3.ap-south-1.amazonaws.com/Rule_Based_Tagging_OG_1709111231656.xlsx"
#     file_id = 55
#     cik = "0001090009"
#     form_type = "10-K"
#     rbt = RuleBasedTagging(html_file_path, xlsx_file, file_id, cik, form_type)
#     rbt.start()
