import requests
from pathlib import Path
from bs4 import BeautifulSoup

from utils import (
    extract_html_elements,
    add_datatype_tags,
    generate_ix_header,
    remove_ix_namespaces,
    add_html_attributes,
)


class XHTMLGenerator:
    def __init__(self, filing_date, ticker, file_id, html_file):
        # Initialize class attributes
        self.file_id = file_id
        self.html_file = html_file
        self.output_file = f"{ticker}-{filing_date}.htm"  # Output file name
        self.xsd_filename = f"{ticker}-{filing_date}.xsd"  # XSD file name
        # Extract HTML elements from the provided HTML file
        self.html_elements = extract_html_elements(html_file, only_id=True)

    def generate_xhtml_file(self):
        # Retrieve HTML content from the provided URL
        response = requests.get(self.html_file)
        if response.status_code == 200:
            html_content = response.text

            # Parse HTML using Beautiful Soup
            soup = BeautifulSoup(html_content, "html.parser")

            # Check if body tag exists
            body_tag = soup.body

            # If body tag doesn't exist, create one and add the content inside
            if not body_tag:
                # Create a basic HTML structure
                basic_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title></title>
                </head>
                <body>
                </body>
                </html>"""

                # Parse the basic HTML structure
                basic_soup = BeautifulSoup(basic_html, "html.parser")

                # Insert provided content inside the body tag of the basic HTML structure
                body_tag = basic_soup.body
                body_tag.append(BeautifulSoup(html_content, "html.parser"))

                # Update the soup variable with the modified basic_soup
                soup = basic_soup

            # Parse HTML content to BeautifulSoup object and add datatype tags
            soup = add_datatype_tags(str(soup), self.html_elements)

            # Create a hidden div element to store XBRL header information
            div_element = soup.new_tag("div", style="display: none")

            # Generate XBRL header and append it to the div element
            ix_header = generate_ix_header(
                file_id=self.file_id, xsd_filename=self.xsd_filename
            )

            div_element.append(BeautifulSoup(ix_header, "xml"))
            try:
                # Try to locate body and head tags within the HTML structure
                body = soup.body
                head_tag = soup.head
                # Insert meta tag specifying content type within head tag
                meta_tag = soup.new_tag("meta")
                meta_tag.attrs["http-equiv"] = "Content-Type"
                meta_tag.attrs["content"] = "text/html"
                head_tag.insert(0, meta_tag)
                # Insert the hidden div element at the beginning of the body tag
                body.insert(0, div_element)
            except Exception as e:
                print("Body Element Not found")

            # Prettify the HTML content and write it to the output file
            prettified_html = soup.prettify("ascii", formatter="html")

            with open(self.output_file, "wb") as out_file:
                # Write XML declaration to the output file
                xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
                xml_declaration_bytes = xml_declaration.encode("utf-8")
                out_file.write(xml_declaration_bytes)

                # Write prettified HTML content to the output file
                out_file.write(prettified_html)

            # Process the output file to remove namespaces and add/modify HTML attributes
            with open(self.output_file, "r", encoding="utf-8") as f:
                html_content = f.read()
                # Remove XBRL namespaces from the HTML content
                html_content = remove_ix_namespaces(html_content)

                # Add or modify HTML attributes
                html_attributes = add_html_attributes()
                print(html_attributes)

                # Replace font tags with span tags and append HTML attributes
                html_content = (
                    html_content.replace("&nbsp;", "&#160;")
                    .replace("&rsquo;", "&#180;")
                    .replace("&sect;", "&#167;")
                    .replace("&ndash;", "&#8211;")
                    .replace("&ldquo;", "&#8220;")
                    .replace("&rdquo;", "&#8221;")
                    .replace("<font", "<span>")
                    .replace("</font>", "</span>")
                    .replace("<html>", html_attributes)
                )

                # Write the modified HTML content back to the output file
                with open(self.output_file, "w", encoding="utf-8") as output_file:
                    output_file.write(html_content)
