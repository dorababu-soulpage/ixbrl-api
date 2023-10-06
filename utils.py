import json
import openpyxl
import requests
import pandas as pd
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


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



def generate_ix_header(file_id=None):

    record = get_db_record(file_id=2)

    cik = record.get("cik", None)
    period = record.get('period', None)
    period_from_ = record.get("periodFrom", None)
    period_to_ = record.get("periodTo", None)
    period_from = period_from_.strftime("%Y-%m-%d")
    period_to = period_to_.strftime("%Y-%m-%d")


    units = record.get("unit", [])

    non_numeric_1_contextRef = f"From{period_from}to{period_to}"
    non_numeric_1_text =get_cik(cik)

    non_numeric_2_contextRef = f"From{period_from}to{period_to}"

    schema_ref_xlink_href = "mays-20230430.xsd"

    # context_id=f"From{period_from_}to{period_to}"
    # identifier_text =get_cik(cik)
    # start_date_text = "2023-02-01"
    # end_date_text = "2023-04-30"

    # unit_usd_id = "USD"
    # measure_usd_text = "iso4217:USD"

    # unit_shares_id = "Shares"
    # measure_shares_text = "xbrli:shares"

    # unit_usd_p_shares_id = "USDPShares"
    # measure_usd_numerator_text = "iso4217:USD"
    # measure_shares_denominator_text = "xbrli:shares"



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

    # todo create context

    # Create the 'xbrli:context' element within 'ix:resources'
    # context = ET.SubElement(resources, "xbrli:context", id=context_id)

    # # Create the 'xbrli:entity' and 'xbrli:identifier' elements within 'xbrli:context'
    # entity = ET.SubElement(context, "xbrli:entity")
    # identifier = ET.SubElement(entity, "xbrli:identifier", scheme="http://www.sec.gov/CIK")
    # identifier.text = identifier_text

    # # Create the 'xbrli:period' element within 'xbrli:context'
    # period = ET.SubElement(context, "xbrli:period")
    # start_date = ET.SubElement(period, "xbrli:startDate")
    # start_date.text = start_date_text
    # end_date = ET.SubElement(period, "xbrli:endDate")
    # end_date.text = end_date_text

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
    print(xml_str)
    soup = BeautifulSoup(xml_str, 'html.parser')
    print(soup.prettify())
    # return xml_str


generate_ix_header()


