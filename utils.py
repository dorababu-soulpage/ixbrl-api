import json
import openpyxl
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


def read_json_file(file_path, key, filename=None):
    if key == "DTS":
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            # Text replacements
            text_replacements = {
                "mays-20230430.xsd": f"{filename}.xsd",
                "mays-20230430_pre.xml": f"{filename}_pre.xml",
                "mays-20230430_lab.xml":  f"{filename}_lab.xml",
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
    concepts = read_json_file(concepts_file, "Concepts", )[0]
    return DTS, concepts


def get_unique_context_elements(file):
    # Send an HTTP GET request to the URL
    response = requests.get(file)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all tags with attributes that start with "id" and have a value starting with "xdx_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("xdx_"))
        taxonomy_tags = []
        # Extract and print the attribute values
        for element in tags:
            try:
                taxonomy_tags.append(element["id"])
            except Exception as e:
                print(str(e))
        unique_contexts = {tag for tag in taxonomy_tags if any(element.startswith("c") for element in tag.split("_"))}

        
        return unique_contexts

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


def generate_concepts_dts_sheet(xlsx_file, concepts, DTS):

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


def add_html_elements_to_concept(html_elements_data, concepts):
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


def get_db_record(file_id):
    import psycopg2
    from decouple import config

    db = config("DATABASE_NAME")
    host = config("DATABASE_HOST")
    username = config("DATABASE_USERNAME")
    password = config("DATABASE_PASSWORD")

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
    
def duration_xml(resources,cik, from_, to_):
    # Create the dutation_context element
    dutation_context = ET.SubElement(resources, "xbrli:context", id=f"From{date_formate(from_)}{date_formate(to_)}")
    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(dutation_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier")
    identifier.set("scheme", "http://www.sec.gov/CIK")
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:period element and its child elements
    period = ET.SubElement(dutation_context, "xbrli:period")
    startdate = ET.SubElement(period, "xbrli:startdate")
    startdate.text = date_formate(from_)
    enddate = ET.SubElement(period, "xbrli:enddate")
    enddate.text = date_formate(to_)

def instance_xml(resources,cik, from_):
     # Create the instance_context element
    instance_context = ET.SubElement(resources, "xbrli:context", id=f"AsOf{date_formate(from_)}")
    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(instance_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier")
    identifier.set("scheme", "http://www.sec.gov/CIK")
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:period element and its child elements
    period = ET.SubElement(instance_context, "xbrli:period")
    instant = ET.SubElement(period, "xbrli:instant")
    instant.text = date_formate(from_)


def check_dimension(items):
    # Use a list comprehension to check if any item ends with "Member"
    has_member = any(item.endswith("Member") for item in items)

    if has_member:
        return True
    else:
       return False


def duration_dimension_xml(resources,cik, from_, to_,items):
    dimensions = list()
    members = list()
    for item in items:
        if item.startswith("us-gaap") and not item.endswith("Member"):
            dimensions.append(item)
        if item.endswith("Member"):
            members.append(item)
    context_id = f"From{date_formate(from_)}{date_formate(to_)}"
    for member in members:
        context_id+= f"_{member}".replace("--", "_")
    # Create the root element
    duration_dimension_context = ET.SubElement(resources, "xbrli:context", id =context_id)

    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(duration_dimension_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier", scheme="http://www.sec.gov/CIK")
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:segment element and its child elements
    segment = ET.SubElement(entity, "xbrli:segment")

    for dimension, member in zip(dimensions, members):
        explicit_member1 = ET.SubElement(segment, "xbrldi:explicitMember", dimension=f"{dimension}".replace("--",":"))
        explicit_member1.text = f"{member}".replace("--", ":")

    # Create xbrli:period element and its child elements
    period = ET.SubElement(duration_dimension_context, "xbrli:period")
    start_date = ET.SubElement(period, "xbrli:startDate")
    start_date.text = date_formate(from_)
    end_date = ET.SubElement(period, "xbrli:endDate")
    end_date.text = date_formate(to_)


def instance_dimension_xml(resources,cik, from_, items):
    dimensions = list()
    members = list()
    for item in items:
        if item.startswith("us-gaap") and not item.endswith("Member"):
            dimensions.append(item)
        if item.endswith("Member"):
            members.append(item)
    context_id = f"AsOf{date_formate(from_)}"
    for member in members:
        context_id+= f"{member}".replace("--", ":")
    # Create the root element
    instance_dimension_context = ET.SubElement(resources, "xbrli:context", id =context_id)

    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(instance_dimension_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier", scheme="http://www.sec.gov/CIK")
    identifier.text = f"{get_cik(cik)}"

    # Create xbrli:segment element and its child elements
    segment = ET.SubElement(entity, "xbrli:segment")

    explicit_member = ET.SubElement(segment, "xbrldi:explicitmember", dimension="us-gaap:AcceleratedShareRepurchasesDateAxis")
    explicit_member.text = "us-gaap:AboveMarketLeasesMember"

    for dimension, member in zip(dimensions, members):
        explicit_member1 = ET.SubElement(segment, "xbrldi:explicitMember", dimension=f"{dimension}".replace("--",":"))
        explicit_member1.text = f"{member}".replace("--", ":")

    # Create xbrli:period element and its child elements
    period = ET.SubElement(instance_dimension_context, "xbrli:period")
    instant = ET.SubElement(period, "xbrli:instant")
    instant.text = f"{date_formate(from_)}"



def generate_ix_header(file_id=None, filename=None):
    filename = filename
    record = get_db_record(file_id=file_id)


    cik = record.get("cik", None)
    period = record.get('period', None)
    period_from_ = record.get("periodFrom", None)
    period_to_ = record.get("periodTo", None)
    period_from = period_from_.strftime("%Y-%m-%d")
    period_to = period_to_.strftime("%Y-%m-%d")
    html_file = record.get("extra").get("url", "")


    units = record.get("unit", [])

    non_numeric_1_contextRef = f"From{period_from}to{period_to}"
    non_numeric_1_text =get_cik(cik)

    non_numeric_2_contextRef = f"From{period_from}to{period_to}"

    schema_ref_xlink_href = f"{filename}.xsd"

    context_id=f"From{period_from}to{period_to}"
    identifier_text =get_cik(cik)
    start_date_text = period_from
    end_date_text = period_to
 
    # Create the root element
    root = ET.Element("ix:header")

    # Create the 'ix:hidden' element
    hidden = ET.SubElement(root, "ix:hidden")

    # Create the 'ix:nonNumeric' elements within 'ix:hidden'
    non_numeric_1 = ET.SubElement(hidden, "ix:nonNumeric", contextRef=non_numeric_1_contextRef, name= "dei:EntityCentralIndexKey")
    non_numeric_1.text = non_numeric_1_text

    non_numeric_2 = ET.SubElement(hidden, "ix:nonNumeric", contextRef=non_numeric_2_contextRef, name="dei:AmendmentFlag")
    non_numeric_2.text = "false"

    # Create the 'ix:references' element
    references = ET.SubElement(root, "ix:references")

    # Create the 'link:schemaRef' element within 'ix:references'
    schema_ref = ET.SubElement(references, "link:schemaRef", {"xlink:href":schema_ref_xlink_href , "xlink:type": "simple"})

    # Create the 'ix:resources' element
    resources = ET.SubElement(root, "ix:resources")
    # Create the 'xbrli:context' element within 'ix:resources'
    context = ET.SubElement(resources, "xbrli:context", id=context_id)
    # Create the 'xbrli:entity' and 'xbrli:identifier' elements within 'xbrli:context'
    entity = ET.SubElement(context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier", scheme="http://www.sec.gov/CIK")
    identifier.text = identifier_text

    # create the context tags
    # Create the 'xbrli:period' element within 'xbrli:context'
    period = ET.SubElement(context, "xbrli:period")
    start_date = ET.SubElement(period, "xbrli:startDate")
    start_date.text = start_date_text
    end_date = ET.SubElement(period, "xbrli:endDate")
    end_date.text = end_date_text
    unique_contexts = get_unique_context_elements(html_file)
    for context in unique_contexts:
        elements = context.split("_")
        for element in elements:
            if element.startswith("c"):
                req_list = elements[elements.index(element):-1]
                # Remove empty values (empty strings) from the list
                filtered_list = [item for item in req_list if item]
                if len(filtered_list) >= 2:
                    result = check_first_two_numbers_or_not(filtered_list[:2])
                    # if True duration else instance
                    from_ = filtered_list[0].replace("c","")
                    to_ = filtered_list[1]
                    if result:
                        duration_dimension = check_dimension(filtered_list)
                        if duration_dimension:
                            duration_dimension_xml(resources,cik, from_, to_,filtered_list)
                        duration_xml(resources,cik, from_, to_)
                    else:
                        instance_dimension = check_dimension(filtered_list)
                        if instance_dimension:
                            instance_dimension_xml(resources,cik, from_,filtered_list)
                        instance_xml(resources,cik, from_)

    # create unit tags 
    for unit in units:
        if "denominator" not in unit.keys():
            # Create the 'xbrli:unit' elements within 'ix:resources'
            unit_usd = ET.SubElement(resources, "xbrli:unit", id=unit.get("name", None))
            measure_usd = ET.SubElement(unit_usd, "xbrli:measure")
            numerator = unit.get("numerator", None)
            measure_usd.text = f"iso4217:{unit.get(numerator, None)}"
        else:
            # Create the 'xbrli:unit' elements within 'ix:resources'
            unit_usd = ET.SubElement(resources, "xbrli:unit", id=unit.get("name", None))
            divide = ET.SubElement(unit_usd, "xbrli:divide")
            # 
            unit_numerator =  ET.SubElement(divide, "xbrli:unitNumerator")
            measure_usd = ET.SubElement(unit_numerator, "xbrli:measure")
            numerator = unit.get("numerator", None)
            measure_usd.text = f"iso4217:{numerator}"

            unit_denominator =  ET.SubElement(divide, "xbrli:unitDenominator")
            measure_usd = ET.SubElement(unit_denominator, "xbrli:measure")
            denominator = unit.get("denominator", None)
            measure_usd.text = f"iso4217:{denominator}"

    # Create an ElementTree object and serialize it to a string
    xml_str = ET.tostring(root,encoding="utf-8").decode("utf-8")
    return xml_str



def get_filename(html):
    original_filename = Path(html).stem
    if "-" in original_filename:
        split_string = original_filename.split("-")
        filename = split_string[0]
    else:
        filename = original_filename
    return filename