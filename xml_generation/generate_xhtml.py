import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

from utils import (
    get_cik,
    get_db_record,
    extract_html_elements,
    add_datatype_tags,
    remove_ix_namespaces,
    add_html_attributes,
)

from lxml import etree
from constants import namespace
from xml_generation.html_parser import HtmlTagParser


class XHTMLGenerator:
    def __init__(self, data, filing_date, ticker, cik, file_id, html_file):
        # Initialize class attributes
        self.cik = cik
        self.data = data
        self.ticker = ticker
        self.file_id = file_id
        self.html_file = html_file
        self.output_file = f"{ticker}-{filing_date}.htm"  # Output file name
        self.xsd_filename = f"{ticker}-{filing_date}.xsd"  # XSD file name
        # Extract HTML elements from the provided HTML file
        self.html_elements = extract_html_elements(html_file, only_id=True)

    def get_period_axis_unique_records(slef, data):
        unique_entries = {}

        for entry in data:
            if entry["Period"]:  # Exclude entries where "Period" value is empty
                key = (entry["Period"], entry["Axis_Member"])
                if key not in unique_entries:
                    unique_entries[key] = entry
        unique_entries = list(unique_entries.values())
        return unique_entries

    def formatted_to_date(self, date_str):
        # Convert to datetime object
        date_obj = datetime.strptime(date_str, "%Y%m%d")

        # Format the datetime object as "YYYY-MM-DD"
        formatted_date_str = date_obj.strftime("%Y-%m-%d")

        return formatted_date_str

    def created_context_ref(self, resources):
        unique_entries = self.get_period_axis_unique_records(self.data)
        for record in unique_entries:
            period_date: str = record.get("Period")
            axis_member: str = record.get("Axis_Member")

            if period_date and axis_member:
                splitted = axis_member.split("__")

                _axis, _domain, _member = splitted
                axis = _axis.replace("--", "_")
                domain = _domain.replace("--", "_")
                member = _member.replace("--", "_")

                period_date_str = self.formatted_to_date(period_date)

                # Create the root element
                dimension_root = etree.SubElement(resources, "context")
                dimension_root.set("id", f"AsOf{period_date_str}_{member}")

                # Create the entity element
                entity = etree.SubElement(dimension_root, "entity")
                identifier = etree.SubElement(entity, "identifier")
                identifier.set("scheme", "http://www.sec.gov/CIK")
                identifier.text = self.cik

                # Add the segment element
                segment = etree.SubElement(entity, "segment")
                explicitMember = etree.SubElement(
                    segment,
                    "{http://xbrl.org/2006/xbrldi}explicitMember",
                    nsmap={"xbrldi": namespace.get("xbrldi")},
                )
                explicitMember.set("dimension", axis.replace("_", ":"))
                explicitMember.text = member.replace("_", ":")

                # Add the period element
                period = etree.SubElement(dimension_root, "period")
                instant = etree.SubElement(period, "instant")
                instant.text = period_date_str

            else:
                if "__" in period_date:
                    from_, to = period_date.split("__")

                    from_date_str = self.formatted_to_date(from_)
                    to_date_str = self.formatted_to_date(to)

                    # Create the root element
                    context_root = etree.SubElement(resources, "context")
                    context_root.set("id", f"FROM{from_date_str}TO{to_date_str}")

                    # Create the entity element
                    entity = etree.SubElement(context_root, "entity")
                    identifier = etree.SubElement(entity, "identifier")
                    identifier.set("scheme", "http://www.sec.gov/CIK")
                    identifier.text = self.cik

                    # Create the period element
                    period = etree.SubElement(context_root, "period")
                    startDate = etree.SubElement(period, "startDate")
                    startDate.text = from_date_str
                    endDate = etree.SubElement(period, "endDate")
                    endDate.text = to_date_str

                else:
                    period: str = record.get("Period")
                    period_date_str = self.formatted_to_date(period_date)
                    # Create the root element
                    context_root = etree.SubElement(resources, "context")
                    context_root.set("id", f"AsOf{period_date_str}")

                    # Create the entity element
                    entity = etree.SubElement(context_root, "entity")
                    identifier = etree.SubElement(entity, "identifier")
                    identifier.set("scheme", "http://www.sec.gov/CIK")
                    identifier.text = self.cik

                    # Create the period element
                    period = etree.SubElement(context_root, "period")
                    instant = etree.SubElement(period, "instant")
                    instant.text = period_date_str

    def create_units(self, resources, units):
        for unit in units:
            # check custom unit or not
            name = unit.get("name")
            custom_unit = unit.get("customUnit")
            if custom_unit:
                custom_root = etree.SubElement(resources, "unit", id=name)

                # Create the measure element
                measure = etree.SubElement(custom_root, "measure")
                measure.text = f"{self.ticker}:{name}"

            if "denominator" not in unit.keys() and custom_unit is False:

                # Create the root element
                numerator_root = etree.SubElement(resources, "unit", id=name)

                # Create the divide element
                divide = etree.SubElement(numerator_root, "divide")

                # Create the unitNumerator element
                unitNumerator = etree.SubElement(divide, "unitNumerator")

                # Create the measure element for unitNumerator
                measure_numerator = etree.SubElement(unitNumerator, "measure")
                measure_numerator.text = f"iso4217:{name}"

            if (
                "numerator" in unit.keys()
                and "denominator" in unit.keys()
                and not custom_unit
            ):
                # Create the root element
                nd_root = etree.SubElement(resources, "unit", id=name)

                # Create the divide element
                divide = etree.SubElement(nd_root, "divide")

                # Create the unitNumerator element
                unitNumerator = etree.SubElement(divide, "unitNumerator")

                # Create the measure element for unitNumerator
                measure_numerator = etree.SubElement(unitNumerator, "measure")
                measure_numerator.text = f"iso4217:{name}"

                # Create the unitDenominator element
                unitDenominator = etree.SubElement(divide, "unitDenominator")

                # Create the measure element for unitDenominator
                measure_denominator = etree.SubElement(unitDenominator, "measure")
                measure_denominator.text = name

    def save_html_file(self, prettified_html):
        with open(self.output_file, "wb") as out_file:
            # Write XML declaration to the output file
            xml_declaration = """
            <?xml version="1.0" encoding="utf-8"?>
            <!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->
            <!-- Creation Date : -->
            <!-- Copyright (c) Apex CoVantage All Rights Reserved. -->
            \n"""
            xml_declaration_bytes = xml_declaration.encode("utf-8")
            out_file.write(xml_declaration_bytes)

            # Write prettified HTML content to the output file
            out_file.write(prettified_html)

    def get_datatype_data(self, data_type):
        with open("assets/elements.json", "r") as json_file:
            data = json.load(json_file)
            for record in data:
                if record.get("datatype") == data_type:
                    return record

    def get_context_id(self, data):
        context_id = None
        # Extract Period and Axis_Member data from the input dictionary
        period_date: str = data.get("Period")
        axis_member: str = data.get("Axis_Member")

        # If both Period and Axis_Member are present
        if period_date and axis_member:
            # Split Axis_Member to extract the relevant member
            splitted = axis_member.split("__")
            _, _, _member = splitted
            member = _member.replace("--", "_")

            # Format period_date to a specific date format
            period_date_str = self.formatted_to_date(period_date)

            # Create context_id based on Period date and Axis member
            context_id = f"AsOf{period_date_str}_{member}"
        else:
            if period_date:
                # If Period is present but Axis_Member is not
                if "__" in period_date:
                    # If Period contains a range, split it into start and end dates
                    from_, to = period_date.split("__")

                    # Format start and end dates
                    from_date_str = self.formatted_to_date(from_)
                    to_date_str = self.formatted_to_date(to)

                    # Create context_id based on date range
                    context_id = f"FROM{from_date_str}TO{to_date_str}"
                else:
                    # If Period is a single date
                    # Format period_date to a specific date format
                    period_date_str = self.formatted_to_date(period_date)

                    # Create context_id based on single date
                    context_id = f"AsOf{period_date_str}"

        return context_id

    def get_datatype(self, element):
        datatypes_dict = {
            "us-gaap--Cash": "xbrli:monetaryItemType",
            "dei--DocumentType": "dei:submissionTypeItemType",
            "us-gaap--AssetsAbstract": "xbrli:stringItemType",
            "us-gaap--InventoryNet": "xbrli:monetaryItemType",
            "dei--DocumentPeriodEndDate": "xbrli:dateItemType",
            "custom--NumberOfPages": "dei:submissionTypeItemType",
            "us-gaap--AssetsCurrent": "dei:submissionTypeItemType",
            "us-gaap--AssetsCurrentAbstract": "xbrli:stringItemType",
            "us-gaap--AccountsReceivableNetCurrent": "xbrli:monetaryItemType",
            "dei--EntityCommonStockSharesOutstanding": "dei:submissionTypeItemType",
            "us-gaap--PrepaidExpenseAndOtherAssetsCurrent": "xbrli:monetaryItemType",
            "us-gaap--OrganizationConsolidationAndPresentationOfFinancialStatementsDisclosureAndSignificantAccountingPoliciesTextBlock": "dei:submissionTypeItemType",
        }

        return datatypes_dict.get(element, "dei:submissionTypeItemType")

    def generate_datatypes_tags(self):
        # Parse HTML content to BeautifulSoup object and add datatype tags
        with open(self.output_file, "r", encoding="utf-8") as f:
            html_content = f.read()
            soup = BeautifulSoup(html_content, "html.parser")

            # Find all tags with attributes that start with "id" and have a value starting with "apex_"
            tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

            parser = HtmlTagParser()
            for tag in tags:
                tag_id = tag.get("id", "")
                data = parser.process_tag(tag_id)

                # data_type = data.get("DataType")
                data_type = self.get_datatype(data.get("Element"))

                data_type_record = self.get_datatype_data(data_type)
                datatype_element = data_type_record.get("element", "")
                datatype_attributes = data_type_record.get("attributes", "")

                # Create new nonNumeric or Numeric tag
                non_numeric_tag = soup.new_tag(datatype_element)

                for attribute in datatype_attributes:
                    if attribute == "contextRef":
                        context_id = self.get_context_id(data)
                        non_numeric_tag["contextRef"] = context_id

                    if attribute == "unitRef":
                        unit: str = data.get("Unit", "")
                        non_numeric_tag["unitRef"] = unit

                    if attribute == "name":
                        element: str = data.get("Element", "")
                        non_numeric_tag["name"] = element.replace("--", ":")

                    if attribute == "decimals":
                        precision: str = data.get("Precision", "")
                        non_numeric_tag["decimals"] = precision

                    if attribute == "scale":
                        counted_as: str = data.get("CountedAs", "")
                        non_numeric_tag["scale"] = counted_as

                    if attribute == "format":
                        non_numeric_tag["format"] = ""

                    if attribute == "id":
                        uniq_id = data.get("UniqueId", "")
                        non_numeric_tag["id"] = uniq_id

                non_numeric_tag.string = tag.text

                # Replace original font tag with new Numeric or nonNumeric tag
                font_tag = soup.find("font", id=tag_id)

                if font_tag:
                    font_tag.replace_with(non_numeric_tag)

            # Update the output file with the new soup data
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(str(soup))

    def generate_ix_header(self):
        record = get_db_record(file_id=self.file_id)

        period_from_ = record.get("periodFrom", None)
        period_to_ = record.get("periodTo", None)
        period_from = period_from_.strftime("%Y-%m-%d")
        period_to = period_to_.strftime("%Y-%m-%d")

        units = record.get("unit", [])

        non_numeric_1_contextRef = f"From{period_from}to{period_to}"
        non_numeric_1_text = self.cik

        non_numeric_2_contextRef = f"From{period_from}to{period_to}"

        schema_ref_xlink_href = self.xsd_filename

        # Create the root element
        root = etree.Element(
            "{http://www.xbrl.org/2013/inlineXBRL}header",
            nsmap={"ix": namespace.get("ix")},
        )

        # Create the 'ix:hidden' element
        hidden = etree.SubElement(root, "{http://www.xbrl.org/2013/inlineXBRL}hidden")

        # Create the 'ix:nonNumeric' elements within 'ix:hidden'
        non_numeric_1 = etree.SubElement(
            hidden,
            "{http://www.xbrl.org/2013/inlineXBRL}nonNumeric",
            contextRef=non_numeric_1_contextRef,
            name="dei:EntityCentralIndexKey",
        )
        non_numeric_1.text = non_numeric_1_text

        non_numeric_2 = etree.SubElement(
            hidden,
            "{http://www.xbrl.org/2013/inlineXBRL}nonNumeric",
            contextRef=non_numeric_2_contextRef,
            name="dei:AmendmentFlag",
        )
        non_numeric_2.text = "false"

        # Create the 'ix:references' element
        references = etree.SubElement(
            root, "{http://www.xbrl.org/2013/inlineXBRL}references"
        )

        # Create the 'link:schemaRef' element within 'ix:references'
        schema_ref = etree.SubElement(
            references,
            "{http://www.xbrl.org/2003/linkbase}schemaRef",
            {
                "{http://www.w3.org/1999/xlink}href": schema_ref_xlink_href,
                "{http://www.w3.org/1999/xlink}type": "simple",
            },
            nsmap={"link": namespace.get("link"), "xlink": namespace.get("xlink")},
        )

        # Create the 'ix:resources' element
        resources = etree.SubElement(
            root,
            "{http://www.xbrl.org/2013/inlineXBRL}resources",
            nsmap={"ix": namespace.get("ix")},
        )

        self.created_context_ref(resources)
        self.create_units(resources, units)

        # # Create an ElementTree object and serialize it to a string
        xml_str = etree.tostring(root, encoding="utf-8").decode("utf-8")
        return xml_str

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

            # # Parse HTML content to BeautifulSoup object and add datatype tags
            # soup = add_datatype_tags(str(soup), self.html_elements)

            # Create a hidden div element to store XBRL header information
            div_element = soup.new_tag("div", style="display: none")

            # Generate XBRL header and append it to the div element
            ix_header = self.generate_ix_header()

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

            self.save_html_file(prettified_html)
            self.generate_datatypes_tags()

            # # Process the output file to remove namespaces and add/modify HTML attributes
            # with open(self.output_file, "r", encoding="utf-8") as f:
            #     html_content = f.read()
            #     # Remove XBRL namespaces from the HTML content
            #     html_content = remove_ix_namespaces(html_content)

            #     # Add or modify HTML attributes
            #     html_attributes = add_html_attributes()
            #     print(html_attributes)

            #     # Replace font tags with span tags and append HTML attributes
            #     html_content = (
            #         html_content.replace("&nbsp;", "&#160;")
            #         .replace("&rsquo;", "&#180;")
            #         .replace("&sect;", "&#167;")
            #         .replace("&ndash;", "&#8211;")
            #         .replace("&ldquo;", "&#8220;")
            #         .replace("&rdquo;", "&#8221;")
            #         .replace("<font", "<span>")
            #         .replace("</font>", "</span>")
            #         .replace("<html>", html_attributes)
            #     )

            #     # Write the modified HTML content back to the output file
            #     with open(self.output_file, "w", encoding="utf-8") as output_file:
            #         output_file.write(html_content)
