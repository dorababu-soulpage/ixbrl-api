import json, os
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup, Comment

from utils import get_db_record, extract_html_elements, remove_ix_namespaces

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
        self.output_file = f"data/{ticker}-{filing_date}/{ticker}-{filing_date}.htm"
        self.xsd_filename = f"{ticker}-{filing_date}.xsd"  # XSD file name
        # Extract HTML elements from the provided HTML file
        self.html_elements = extract_html_elements(html_file, only_id=True)

    def add_html_attributes(self):
        # Create a BeautifulSoup object
        soup = BeautifulSoup("", "html.parser")

        # Create the html tag
        html_tag = soup.new_tag("html")

        # Add attributes to the html tag
        html_tag["xmlns"] = "http://www.w3.org/1999/xhtml"
        html_tag["xmlns:xs"] = "http://www.w3.org/2001/XMLSchema-instance"
        html_tag["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
        html_tag["xmlns:xbrli"] = "http://www.xbrl.org/2003/instance"
        html_tag["xmlns:xbrldi"] = "http://xbrl.org/2006/xbrldi"
        html_tag["xmlns:xbrldt"] = "http://xbrl.org/2005/xbrldt"
        html_tag["xmlns:iso4217"] = "http://www.xbrl.org/2003/iso4217"
        html_tag["xmlns:ix"] = "http://www.xbrl.org/2013/inlineXBRL"
        html_tag["xmlns:ixt"] = (
            "http://www.xbrl.org/inlineXBRL/transformation/2020-02-12"
        )
        html_tag["xmlns:ixt-sec"] = (
            "http://www.sec.gov/inlineXBRL/transformation/2015-08-31"
        )
        html_tag["xmlns:link"] = "http://www.xbrl.org/2003/linkbase"
        html_tag["xmlns:dei"] = "http://xbrl.sec.gov/dei/2023"
        html_tag["xmlns:ref"] = "http://www.xbrl.org/2006/ref"
        html_tag["xmlns:us-gaap"] = "http://fasb.org/us-gaap/2023"
        html_tag["xmlns:us-roles"] = "http://fasb.org/us-roles/2023"
        html_tag["xmlns:country"] = "http://xbrl.sec.gov/country/2023"
        html_tag["xmlns:srt"] = "http://fasb.org/srt/2023"
        html_tag["xmlns:fult"] = "http://fult.com/20230516"
        html_tag["xml:lang"] = "en-US"
        html_tag["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        html_tag["xmlns:ecd"] = "http://xbrl.sec.gov/ecd/2023"

        return str(html_tag).replace("</html>", "")

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

    def save_html_file(self, soup):
        # Extract the directory from the output file path
        directory = os.path.dirname(self.output_file)

        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Update the output file with the new soup data
        with open(self.output_file, "wb") as out_file:
            html_content: str = soup.prettify()
            html_content = html_content.replace(
                "<continuation />", "</ix:continuation >"
            )
            html_content = html_content.replace(" <continuation", " <ix:continuation")
            html_content = html_content.replace("/>", ">")
            html_content = html_content.replace(
                "<ix:continuation>", "</ix:continuation>"
            )
            # add HTML attributes in the html
            html_attributes = self.add_html_attributes()
            html_content = html_content.replace("<html>", html_attributes)

            # Write XML declaration to the output file
            xml_declaration = """
                <?xml version="1.0" encoding="utf-8"?>
                <!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->
                <!-- Creation Date : -->
                <!-- Copyright (c) Apex CoVantage All Rights Reserved. -->
                \n"""

            # Encode XML declaration to bytes and write to file
            xml_declaration_bytes = xml_declaration.encode("utf-8")
            out_file.write(xml_declaration_bytes)

            # Encode prettified HTML content to bytes and write to file
            html_content_bytes = html_content.encode("utf-8")

            # Write prettified HTML content to the output file
            out_file.write(html_content_bytes)

    def get_datatype_data(self, data_type):
        with open("assets/elements.json", "r") as json_file:
            data = json.load(json_file)
            for record in data:
                if record.get("datatype") == data_type:
                    return record

    def create_continuation_tags(self, soup, start_id, end_id):

        # Find the first <p> tag with the specified ID
        first_id_tag = soup.find("p", id=start_id)
        random_number = random.randint(100, 999)
        count = 1

        continuation_start_tag = f'<ix:continuation id="f-{random_number}-{count}" continuedAt="f-{random_number}-{count+1}">'
        count += 1

        first_id_tag.insert_after(BeautifulSoup(continuation_start_tag, "xml"))

        # Find the second <p> tag with the specified ID
        second_id_tag = soup.find("p", id=end_id)
        second_id_tag.insert_after(BeautifulSoup("<ix:continuation>", "xml"))

        output_html = ""

        if first_id_tag and second_id_tag:
            # Find all tags, comments, and strings between the first and second IDs
            current_tag = first_id_tag.next_sibling

            while current_tag and current_tag != second_id_tag:
                if isinstance(current_tag, Comment):
                    # Include comment in the output
                    output_html += f"<!--{current_tag}-->"
                    comment = str(current_tag).strip()
                    if comment.startswith("Field: /Page"):
                        continuation_start_tag = f'<ix:continuation id="f-{random_number}-{count}" continuedAt="f-{random_number}-{count+1}">'
                        count += 1

                        current_tag.insert_after(
                            BeautifulSoup(continuation_start_tag, "xml")
                        )

                    if comment.startswith("Field: Page; Sequence"):
                        current_tag.insert_before(
                            BeautifulSoup("<ix:continuation>", "xml")
                        )

                else:
                    output_html += str(current_tag)
                current_tag = current_tag.next_sibling

        parser = HtmlTagParser()
        data = parser.process_tag(start_id)
        # create new Numeric or nonNumeric tag
        datatype_tag = self.create_datatype_tag(
            soup, data, first_id_tag, note_section=True
        )
        if first_id_tag.find_all():
            # Add all contents from the specific <p> tag to the new tag
            for inner_tag in first_id_tag.find_all():
                datatype_tag.append(inner_tag)
        datatype_tag["id"] = f"f-{random_number}"
        style = first_id_tag.get("style")
        datatype_tag["id"] = f"f-{random_number}"
        datatype_tag["style"] = style
        first_id_tag.replace_with(datatype_tag)
        return soup

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

    def get_format_value(self, data_type, input_text):

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

    def create_datatype_tag(self, soup, data, tag, note_section=None):
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
                data_type = self.get_datatype(data.get("Element"))
                format_value = self.get_format_value(data_type, tag.text)
                non_numeric_tag["format"] = format_value

            if attribute == "id":
                is_footnote = data.get("have_footnote")
                if is_footnote:
                    uniq_id = is_footnote[0]
                else:
                    uniq_id = data.get("UniqueId", "")
                non_numeric_tag["id"] = uniq_id

        if note_section:
            return non_numeric_tag
        else:
            non_numeric_tag.string = tag.text
            return non_numeric_tag

    def generate_datatypes_tags(self, soup):

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

        parser = HtmlTagParser()
        for tag in tags:
            tag_id = tag.get("id", "")
            data = parser.process_tag(tag_id)

            # create new Numeric or nonNumeric tag
            datatype_tag = self.create_datatype_tag(soup, data, tag)

            # Replace original font tag with new Numeric or nonNumeric tag
            font_tag = soup.find("font", id=tag_id)

            if font_tag:
                font_tag.replace_with(datatype_tag)

        return soup

    def ixt_continuation(self, soup: BeautifulSoup):

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

        start_tag_ids = []
        end_tag_ids = []
        for tag in tags:
            tag_id: str = tag.get("id", "")
            # notes start section
            if tag_id.startswith("apex_80"):
                start_tag_ids.append(tag_id)
            # notes end section
            if tag_id.startswith("apex_81"):
                end_tag_ids.append(tag_id)

        for start_id, end_id in zip(start_tag_ids, end_tag_ids):
            soup = self.create_continuation_tags(soup, start_id, end_id)

        return soup

    def add_footnote_ix_header(self, soup: BeautifulSoup, from_ref, to_ref):
        # Find the ix:resources element
        resources = soup.find("ix:resources")

        # Define the relationships
        relationship = soup.new_tag("ix:relationship", fromRefs=from_ref, toRefs=to_ref)

        # Find the last xbrli:unit element if it exists
        last_unit = (
            resources.find_all("xbrli:unit")[-1]
            if resources.find_all("xbrli:unit")
            else None
        )

        # Insert relationships after the last xbrli:unit element if it exists, otherwise append to resources
        if last_unit:
            if relationship not in resources:
                last_unit.insert_after(relationship)
        else:
            if relationship not in resources:
                resources.append(relationship)

    def foot_notes(self, soup: BeautifulSoup):

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

        foot_note_tag_ids: list = []
        footnote_id_dict: dict = {}
        # Find all foot note tags and crated ix:footnote tag for that"
        for index, tag in enumerate(tags, start=100):
            parser = HtmlTagParser()
            tag_id: str = tag.get("id", "")
            # notes start section
            if tag_id.startswith("apex_F0"):
                foot_note_tag_ids.append(tag_id)
                # Create new footnote tag
                footnote_id = f"Footnote{index}"
                ix_footnote_tag = soup.new_tag("ix:footnote")
                ix_footnote_tag["id"] = footnote_id
                ix_footnote_tag["xml:lang"] = "en-US"

                ix_footnote_tag.string = tag.text
                tag.replace_with(ix_footnote_tag)

                splitted = tag_id.split("_")
                footnote_id_dict[splitted[-1]] = footnote_id

        # add footnotes relationship to ix header
        for tag in tags:
            tag_id: str = tag.get("id", "")
            data = parser.process_tag(tag_id)
            is_footnote: list = data.get("have_footnote")
            if is_footnote:
                from_ref = is_footnote[0]
                to_ref = footnote_id_dict.get(from_ref)
                self.add_footnote_ix_header(soup, from_ref, to_ref)

        return soup

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

            # update the footnote to soup object
            soup = self.foot_notes(soup)
            soup = self.generate_datatypes_tags(soup)
            soup = self.ixt_continuation(soup)

            # finally save the html file
            self.save_html_file(soup)

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
