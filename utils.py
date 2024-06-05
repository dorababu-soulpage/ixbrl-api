import os
import json

import boto3
from PIL import Image
from boto3.session import Session

import openpyxl
import requests
import pandas as pd
from lxml import html
from pathlib import Path
from decouple import config
from bs4 import BeautifulSoup
from lxml import etree

# import xml.etree.ElementTree as etree
from constants import namespace
from datetime import datetime


def read_json_file(file_path, key, filename=None):
    if key == "DTS":
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            # Text replacements
            text_replacements = {
                "widget-2019-12-31.xsd": f"{filename}.xsd",
                "widget-2019-12-31_def.xml": f"{filename}_def.xml",
                "widget-2019-12-31_cal.xml": f"{filename}_cal.xml",
                "widget-2019-12-31_pre.xml": f"{filename}_pre.xml",
                "widget-2019-12-31_lab.xml": f"{filename}_lab.xml",
            }

            # Iterate through the JSON and perform text replacements
            for item in data["DTS"]:
                file_href = item.get("file, href or role definition")
                if file_href in text_replacements:
                    item["file, href or role definition"] = text_replacements[file_href]
            return data.get(key, None)
    else:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            return data.get(key, None)


dts_file = "assets/dts.json"
concepts_file = "assets/concepts.json"
taxonomy_file = "assets/GAAP_Taxonomy_2023.xlsx"


def initialize_concepts_dts(filename):
    # Read "Concepts" and "DTS" data from JSON files
    DTS = read_json_file(dts_file, "DTS", filename=filename)
    concepts = read_json_file(concepts_file, "Concepts")[0]
    return DTS, concepts


def get_unique_context_elements(file):
    # Send an HTTP GET request to the URL
    response = requests.get(file)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))
        taxonomy_tags = []
        # Extract and print the attribute values
        for element in tags:

            try:
                taxonomy_tags.append(element["id"])
            except Exception as e:
                print(str(e))

        html_tags = [element.split("_c")[1] for element in taxonomy_tags]
        unique_contexts = []
        for tag in html_tags:
            unique_content = tag.split("_")[:-1]
            if unique_content not in unique_contexts:
                unique_contexts.append(unique_content)

        # Remove empty string values from each inner list
        cleaned_data = [
            [value for value in inner_list if value != ""]
            for inner_list in unique_contexts
        ]
        return cleaned_data


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


def generate_concepts_dts_sheet(xlsx_file, xlsx_file_store_loc, concepts, DTS):
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

    # create viewer folder
    Path(xlsx_file_store_loc).mkdir(parents=True, exist_ok=True)

    # Save the workbook to a file
    workbook.save(xlsx_file)
    print("Excel file generated successfully")


def add_html_elements_to_concept(html_elements_data, concepts: dict, DTS: list):
    concept_headers = {
        "label": "label",
        "prefix": "prefix",
        "name": "name",
        "type": "type",
        "substitutionGroup": "substitutionGroup",
        "periodType": "periodType",
        "balance": "balance",
        "abstract": "abstract",
        "nillable": "nillable",
        "depth": "depth",
        "preferred label": "preferredLabel",
        "calculation parent": "parent",
        "calculation weight": "calculationWeight",
        "dimension default": "dimensionDefault",
        # "baseTypePrefix": "baseTypePrefix",
        # "baseType": "baseType",
        # "minInclusive": "minInclusive",
    }
    for record in html_elements_data:
        record_data = {}

        # make definition as key in output dict
        name = record.get("name")
        definition = record.get("definition")
        parenthetical = record.get("definition")

        # concept_keys =
        # # get concept headers
        # for category, records in concepts.items():
        #     concept_headers = records[0]
        #     break
        for header, value in concept_headers.items():
            if record.get(value, None) == "credit":
                record.update({"calculationWeight": 1})
            if record.get(value, None) == "debit":
                record.update({"calculationWeight": -1})

            record_data[header] = record.get(value, None)

        counter = 1
        if parenthetical:
            parenthetical_definition = f"{definition} - parenthetical"
            # add definition matched records into category list
            if parenthetical_definition not in concepts.keys():
                concepts[parenthetical_definition] = []
                concepts[parenthetical_definition].append(record_data)

                # change number
                parts = parenthetical_definition.split("-")
                formatted_number = f"{counter:06d}"
                result_string = f"{formatted_number} - {' - '.join(parts[1:]).strip()}"
                counter += 1

                # add parenthetical_definition into DTS sheet also
                new_parenthetical_definition = {
                    "specification": "extension",
                    "file type": "role",
                    "file, href or role definition": result_string,
                    "namespace URI": f"http://xbrl.us/widgetexample/role/{name}",
                }

                DTS.append(new_parenthetical_definition)
            else:
                concepts[parenthetical_definition].append(record_data)

        # add definition matched records into category list
        if definition not in concepts.keys():
            concepts[definition] = []
            concepts[definition].append(record_data)

            # change number
            parts = definition.split("-")
            formatted_number = f"{counter:06d}"
            result_string = f"{formatted_number} - {' - '.join(parts[1:]).strip()}"
            counter += 1

            # add definition into DTS sheet also
            new_definition = {
                "specification": "extension",
                "file type": "role",
                "file, href or role definition": result_string,
                "namespace URI": f"http://xbrl.us/widgetexample/role/{name}",
            }

            DTS.append(new_definition)
        else:
            concepts[definition].append(record_data)


# sheets initializations
element_df = pd.read_excel(taxonomy_file, sheet_name="Elements")
presentation_df = pd.read_excel(taxonomy_file, sheet_name="Presentation")


def get_taxonomy_values(element):
    try:
        filtered_df = element_df[element_df["name"] == element].to_dict(
            orient="records"
        )[0]
        return filtered_df
    except Exception as e:
        return None


def extract_html_elements(file, only_id=False) -> list[dict]:
    # # file = "https://deeplobe.s3.ap-south-1.amazonaws.com/mays4160726-10q.htm"

    # # read tags from html and add into the exists concepts
    html_tags_data = []

    # Send an HTTP GET request to the URL
    response = requests.get(file)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        # html_content = response.text
        html_content = response.content

        soup = BeautifulSoup(html_content, "html.parser")

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

        for tag in tags:
            # Find the <font> element by its ID
            font_element = soup.find("font", id=tag["id"])

            # Check if the <font> element exists
            if font_element:
                # Traverse up the DOM tree to find the parent <table> element
                table = font_element.find_parent("table")

                # Check if the table is found
                if table and "id" in table.attrs:
                    tag_id = tag["id"].split("_")
                    table_id = table["id"].split("_")
                    final_id = "_".join(tag_id[:-1] + table_id[2:])
                    if only_id:
                        html_tags_data.append(final_id)
                    else:
                        html_tags_data.append(
                            {
                                "role": table.get("role", ""),
                                "label": table.get("title", ""),
                                "id": final_id,
                            }
                        )
                else:
                    element_role = tag.get("role", "")
                    element_label = tag.get("title", "")
                    element_id = tag.get("id", "")
                    if only_id:
                        html_tags_data.append(element_id)
                    else:
                        html_tags_data.append(
                            {
                                "role": element_role,
                                "label": element_label,
                                "id": element_id,
                            }
                        )

    return html_tags_data


def get_cik(value):
    original_string = "0000000000"  # Original string with 10 zeros
    value_to_insert = value

    # Calculate the length of the original string
    original_length = len(original_string)

    # Check if the original string is longer than the value to insert
    if original_length >= len(value_to_insert):
        # Calculate the number of zeros to append
        zeros_to_append = original_length - len(value_to_insert)

        # Create the updated string by appending zeros and the input value
        updated_string = "0" * zeros_to_append + value_to_insert
    else:
        # If the original string is shorter, return the input value as is
        updated_string = value_to_insert

    return updated_string


def date_formate(input_date):
    from datetime import datetime

    # Convert the input date to the "YYYY-MM-DD" format
    formatted_date = datetime.strptime(input_date, "%Y%m%d").strftime("%Y-%m-%d")
    return formatted_date


def check_first_two_numbers_or_not(filtered_list):
    # Attempt to convert the first two values to integers
    try:
        first_value = int(filtered_list[0].replace("c", ""))
        second_value = int(filtered_list[1])
        return True
    except ValueError:
        return False


def duration_xml(resources, cik, from_, to_):
    # Create the dutation_context element
    dutation_context = etree.SubElement(
        resources,
        "{http://www.xbrl.org/2003/instance}context",
        id=f"From{date_formate(from_)}to{date_formate(to_)}",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    # Create xbrli:entity element and its child elements
    entity = etree.SubElement(
        dutation_context, "{http://www.xbrl.org/2003/instance}entity"
    )
    identifier = etree.SubElement(
        entity, "{http://www.xbrl.org/2003/instance}identifier"
    )
    identifier.set("scheme", "http://www.sec.gov/CIK")
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:period element and its child elements
    period = etree.SubElement(
        dutation_context,
        "{http://www.xbrl.org/2003/instance}period",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    startdate = etree.SubElement(
        period,
        "{http://www.xbrl.org/2003/instance}startDate",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    startdate.text = date_formate(from_)
    enddate = etree.SubElement(
        period,
        "{http://www.xbrl.org/2003/instance}endDate",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    enddate.text = date_formate(to_)


def instance_xml(resources, cik, from_):
    # Create the instance_context element
    instance_context = etree.SubElement(
        resources,
        "{http://www.xbrl.org/2003/instance}context",
        id=f"AsOf{date_formate(from_)}",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    # Create xbrli:entity element and its child elements
    entity = etree.SubElement(
        instance_context,
        "{http://www.xbrl.org/2003/instance}entity",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    identifier = etree.SubElement(
        entity,
        "{http://www.xbrl.org/2003/instance}identifier",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    identifier.set("scheme", "http://www.sec.gov/CIK")
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:period element and its child elements
    period = etree.SubElement(
        instance_context,
        "{http://www.xbrl.org/2003/instance}period",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    instant = etree.SubElement(
        period,
        "{http://www.xbrl.org/2003/instance}instant",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    instant.text = date_formate(from_)


def check_dimension(items):
    # Use a list comprehension to check if any item ends with "Member"
    has_member = any(item.endswith("Member") for item in items)

    if has_member:
        return True
    else:
        return False


def duration_dimension_xml(resources, cik, from_, to_, items):
    dimensions = list()
    members = list()
    for item in items:
        if item.startswith("us-gaap") and not item.endswith("Member"):
            dimensions.append(item)
        if item.endswith("Member"):
            members.append(item)
    context_id = f"From{date_formate(from_)}to{date_formate(to_)}"
    for member in members:
        context_id += f"_{member}".replace("--", "_")
    # Create the root element
    duration_dimension_context = etree.SubElement(
        resources,
        "{http://www.xbrl.org/2003/instance}context",
        id=context_id,
        nsmap={"xbrli": namespace.get("xbrli")},
    )

    # Create xbrli:entity element and its child elements
    entity = etree.SubElement(
        duration_dimension_context,
        "{http://www.xbrl.org/2003/instance}entity",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    identifier = etree.SubElement(
        entity,
        "{http://www.xbrl.org/2003/instance}identifier",
        scheme="http://www.sec.gov/CIK",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:segment element and its child elements
    segment = etree.SubElement(
        entity,
        "{http://www.xbrl.org/2003/instance}segment",
        nsmap={"xbrli": namespace.get("xbrli")},
    )

    for dimension, member in zip(dimensions, members):
        explicit_member1 = etree.SubElement(
            segment,
            "{http://www.xbrl.org/2003/instance}explicitMember",
            dimension=f"{dimension}".replace("--", ":"),
            nsmap={"xbrli": namespace.get("xbrli")},
        )
        explicit_member1.text = f"{member}".replace("--", ":")

    # Create xbrli:period element and its child elements
    period = etree.SubElement(
        duration_dimension_context,
        "{http://www.xbrl.org/2003/instance}period",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    start_date = etree.SubElement(
        period,
        "{http://www.xbrl.org/2003/instance}startDate",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    start_date.text = date_formate(from_)
    end_date = etree.SubElement(
        period,
        "{http://www.xbrl.org/2003/instance}endDate",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    end_date.text = date_formate(to_)


def instance_dimension_xml(resources, cik, from_, items):
    dimensions = list()
    members = list()
    for item in items:
        if item.startswith("us-gaap") and not item.endswith("Member"):
            dimensions.append(item)
        if item.endswith("Member"):
            members.append(item)
    context_id = f"AsOf{date_formate(from_)}"
    for member in members:
        context_id += f"{member}".replace("--", ":")
    # Create the root element
    instance_dimension_context = etree.SubElement(
        resources,
        "{http://www.xbrl.org/2003/instance}context",
        id=context_id,
        nsmap={"xbrli": namespace.get("xbrli")},
    )

    # Create xbrli:entity element and its child elements
    entity = etree.SubElement(
        instance_dimension_context,
        "{http://www.xbrl.org/2003/instance}entity",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    identifier = etree.SubElement(
        entity,
        "{http://www.xbrl.org/2003/instance}identifier",
        scheme="http://www.sec.gov/CIK",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:segment element and its child elements
    segment = etree.SubElement(
        entity,
        "{http://www.xbrl.org/2003/instance}segment",
        nsmap={"xbrli": namespace.get("xbrli")},
    )

    explicit_member = etree.SubElement(
        segment,
        "{http://xbrl.org/2006/xbrldi}explicitmember",
        dimension="us-gaap:AcceleratedShareRepurchasesDateAxis",
        nsmap={"xbrldi": namespace.get("xbrldi")},
    )
    explicit_member.text = "us-gaap:AboveMarketLeasesMember"

    for dimension, member in zip(dimensions, members):
        explicit_member1 = etree.SubElement(
            segment,
            "{http://xbrl.org/2006/xbrldi}:explicitMember",
            dimension=f"{dimension}".replace("--", ":"),
            nsmap={"xbrldi": namespace.get("xbrldi")},
        )
        explicit_member1.text = f"{member}".replace("--", ":")

    # Create xbrli:period element and its child elements
    period = etree.SubElement(
        instance_dimension_context,
        "{http://www.xbrl.org/2003/instance}period",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    instant = etree.SubElement(
        period,
        "{http://www.xbrl.org/2003/instance}instant",
        nsmap={"xbrli": namespace.get("xbrli")},
    )
    instant.text = f"{date_formate(from_)}"


def get_filename(html):
    original_filename = Path(html).stem
    if "-" in original_filename:
        split_string = original_filename.split("-")
        filename = split_string[0]
    else:
        filename = original_filename
    return filename


db = config("DATABASE_NAME")
host = config("DATABASE_HOST")
username = config("DATABASE_USERNAME")
password = config("DATABASE_PASSWORD")


def get_client_record(client_id):
    import psycopg2

    db_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
    try:
        # Attempt to connect and execute queries
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM clients where id={client_id}")
        row = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_db_record(file_id):
    import psycopg2

    db_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
    try:
        # Attempt to connect and execute queries
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM files where id={file_id}")
        row = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_split_file_record(file_id):
    import psycopg2

    db_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
    try:
        # Attempt to connect and execute queries
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM splitfiles where id={file_id}")
        row = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_client_record(client_id):
    import psycopg2

    db_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
    try:
        # Attempt to connect and execute queries
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM clients where id={client_id}")
        row = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def update_db_record(file_id, data):
    import psycopg2

    db_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
    try:
        # Attempt to connect and execute queries
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        # Convert the new data to a JSON string
        new_json_data = json.dumps(data)

        # SQL query to update the JSON field
        # SQL query to update the JSON field using -> operator
        update_sql = f"""
            UPDATE files
            SET extra = extra || %s::jsonb
            WHERE id = %s
        """
        # Execute the SQL query with parameters
        cursor.execute(update_sql, (new_json_data, file_id))
        # Commit the changes and close the connection
        connection.commit()

    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def s3_uploader(name, body):
    """
    Uploads files to an S3 server and returns the URL.

    Parameters:
    - name: Name/key to store the file in the S3 bucket.
    - body: BytesIO object representing the content of the file.

    Returns:
    - The URL of the uploaded file on S3.
    """
    access_key = config("AWS_S3_ACCESS_KEY_ID")
    secret_key = config("AWS_S3_SECRET_ACCESS_KEY")
    region = config("AWS_S3_REGION")
    bucket = config("AWS_S3_BUCKET_NAME")

    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    s3 = session.resource("s3")

    # Upload the file
    s3.Bucket(bucket).put_object(
        Key=name,
        Body=body.getvalue(),
        ACL="public-read",
        ContentType="application/octet-stream",
    )

    # Generate and return the URL
    return f"https://{bucket}.s3.amazonaws.com/{name}"


def generate_xml_comments(filepath=None):
    # Specify the directory containing the XML files
    directory_path = filepath

    # Lines to add
    lines_to_add = [
        "<!-- Field: Doc-Info; Name: Generator; Value: Apex; Version: 1.0 -->",
        "<!-- Field: Doc-Info; Name: VendorURI; Value: https://ixbrl-tagging-tool-cyan.vercel.app -->",
        "<!-- Field: Doc-Info; Name: Status; Value: 0x00000000 -->",
    ]

    # Iterate through each file in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory_path, filename)

            # Open the XML file and read its content
            with open(file_path, "r", encoding="utf-8") as file:
                xml_content = file.read()

            # Parse the XML content with BeautifulSoup
            soup = BeautifulSoup(xml_content, "xml")

            # Get the root element
            root = soup.find(name=True)

            # Insert the lines before the root element
            for line in reversed(lines_to_add):
                root.insert_before(BeautifulSoup(line, "html.parser"))

            # Write the modified content back to the file
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(str(soup.prettify()))


def get_element_name_type(html_elements, name):
    for html_element in html_elements:
        if html_element.get("name") == name:
            element_type = html_element.get("type", None)
            prefix = html_element.get("prefix", None)
            name = html_element.get("name", None)
            return element_type, f"{prefix}:{name}"


def get_format_value(data_type, input_text):
    with open("assets/format.json", "r") as json_file:
        data = json.load(json_file)
        for record in data:
            if (
                record.get("Datatype 1") == data_type
                or record.get("Datatype 2") == data_type
                or record.get("Datatype 3") == data_type
                or record.get("Datatype 4") == data_type
            ):
                formate_value = record.get("Format Code", "")
                return formate_value
        else:
            return ""


def add_datatype_tags(html_content, html_elements):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")

    # Find all FONT tags with ID starting with "apex"
    filtered_fonts_tags = soup.find_all(
        "font", id=lambda value: value and value.startswith("apex")
    )

    for tag in filtered_fonts_tags:
        try:
            tag_data = tag["id"].split("--")[0].split("_")
            element_id = f"{tag_data[0]}_{tag_data[1]}"
            name = tag["id"].split("--")[1].split("_")[0]
            data_type, element_name = get_element_name_type(html_elements, name)
            # get tagged elements
            tag_names = tag["id"].split("--")
            elements = [
                tag_names.replace("__us-gaap", "") for tag_names in tag_names[1:]
            ]
            if len(elements) > 1:
                context = elements[0].split("_c")[1].split("__")[0]
                parsed_date = datetime.strptime(context, "%Y%m%d")
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                # From2023-05-162023-05-16_us-gaap_CommonStockMember
                val = elements[-1].split("_")[0]
                contextRef = f"From{formatted_date}to{formatted_date}_us-gaap_{val}"

            else:
                context = elements[0].split("_c")[1].split("__")[0]
                parsed_date = datetime.strptime(context, "%Y%m%d")
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                # AsOf2023-05-16
                contextRef = f"Asof{formatted_date}"
            if data_type:
                # read elements.json
                with open("assets/elements.json", "r") as json_file:
                    data = json.load(json_file)
                    for record in data:
                        if record.get("datatype") == data_type:
                            new_tag = soup.new_tag(record.get("element"))
                            for attr in record.get("attributes"):
                                # Adding attributes to the new tag
                                if attr == "contextRef":
                                    new_tag[attr] = contextRef
                                elif attr == "name":
                                    new_tag[attr] = element_name
                                elif attr == "id":
                                    new_tag[attr] = element_id
                                elif attr == "format":
                                    format_value = get_format_value(data_type, tag.text)
                                    new_tag[attr] = format_value
                                else:
                                    new_tag[attr] = ""
                            # Append the text to the new tag
                            new_tag.append(tag.text)
                            tag.string = ""
                            # Replace the original tag with the new_tag
                            tag.append(new_tag)

        except Exception as e:
            pass
            # print(str(e))
    return soup

    # with open(output_file, "w") as output_file:
    #     output_file.write(str(soup))


def remove_ix_namespaces(html_content):
    for key, value in namespace.items():
        namespace_format = f'xmlns:{key}="{value}"'
        html_content = html_content.replace(namespace_format, "")

    return html_content


def get_definitions(file):
    # Send an HTTP GET request to the URL
    response = requests.get(file)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

    roles = [tag.get("id", "") for tag in tags]
    definitions = []

    for _role in roles:
        role = _role.split("--")
        _definition = role[1].split(":")
        definition = _definition[1].split("_")[0]
        # TODO: Ned to extract role information from tag
        role = "DocumentDocumentAndEntityInformation"
        if definition not in definitions:
            definitions.append({"definition": definition, "role": role})

    return definitions


def get_custom_element_record(client_id, element):
    import psycopg2

    db_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
    try:
        # Attempt to connect and execute queries
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM custom_elements WHERE name = %s;", (element,))
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        for row in rows:
            record = dict(zip(columns, row))
            name = record.get("name")
            client_id = record.get("clientId")
            if element == name and client_id == client_id:
                return record
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_element_record(name, prefix, taxonomy_id):
    import psycopg2

    db_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
    try:
        # Attempt to connect and execute queries
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()

        query = """
        SELECT * FROM elements
        WHERE name = %s AND prefix = %s AND "taxonomyId" = %s
        """

        cursor.execute(query, (name, prefix, taxonomy_id))

        row = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        record = dict(zip(columns, row))
        return record

        # for row in rows:
        #     record = dict(zip(columns, row))
        #     print(record)
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def read_images_from_folder(folder_path):
    images = []
    for filename in os.listdir(folder_path):
        if filename.endswith(
            (".png", ".jpg", ".jpeg", ".bmp", ".gif")
        ):  # Add other extensions if needed
            img_path = os.path.join(folder_path, filename)
            img = Image.open(img_path)
            images.append((filename, img_path))
    return images


def upload_image_to_s3(file_path, bucket, object_name=None):
    """Upload a file to an S3 bucket and return the URL"""
    access_key = config("AWS_S3_ACCESS_KEY_ID")
    secret_key = config("AWS_S3_SECRET_ACCESS_KEY")
    region = config("AWS_S3_REGION")

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    s3 = session.resource("s3")

    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        s3.Bucket(bucket).put_object(
            Key=object_name,
            Body=open(file_path, "rb"),
            ACL="public-read",
            ContentType="application/octet-stream",
        )
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        return None

    return f"https://{bucket}.s3.amazonaws.com/{object_name}"
