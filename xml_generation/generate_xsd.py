import re, os
from datetime import datetime
from itertools import groupby

from xml.dom import minidom
import xml.etree.ElementTree as ET
from utils import get_custom_element_record


class XSDGenerator:
    def __init__(
        self, data, ticker, filing_date, company_website, client_id, taxonomy_year
    ):
        self.root = None
        self.data = data
        self.ticker = ticker
        self.filing_date = filing_date
        self.company_website = company_website
        self.client_id = client_id
        self.taxonomy_year = taxonomy_year
        self.output_file = f"data/{self.ticker}-{self.filing_date}/{self.ticker}-{self.filing_date}.xsd"
        # self.definitions = definitions
        self.grouped_data = self.group_data_by_role()

    def group_data_by_role(self):
        # Group data by RoleName using itertools.groupby
        grouped_data: dict[str, list] = {}
        roles_sorted_data = self.get_roles_sorted_data()

        for record in roles_sorted_data:
            role_name = record["RoleName"]
            if role_name in grouped_data.keys():
                grouped_data[role_name].append(record)
            else:
                grouped_data[role_name] = [record]
        return grouped_data

    def get_roles_sorted_data(self):
        document_elements = [
            record for record in self.data if record.get("RoleType") == "document"
        ]

        statement_elements = [
            record for record in self.data if record.get("RoleType") == "statement"
        ]

        disclosure_elements = [
            record for record in self.data if record.get("RoleType") == "disclosure"
        ]

        level_1_elements = []
        level_2_elements = []
        level_3_elements = []
        level_4_elements = []

        for disclosure_element in disclosure_elements:
            element_type: str = disclosure_element.get("Type")
            if element_type.startswith("80"):
                level_1_elements.append(disclosure_element)

            if element_type.startswith("84"):
                level_2_elements.append(disclosure_element)

            if element_type.startswith("89"):
                level_3_elements.append(disclosure_element)

            if element_type.startswith("90"):
                level_4_elements.append(disclosure_element)

        disclosure_elements = (
            level_1_elements + level_2_elements + level_3_elements + level_4_elements
        )

        final_data = document_elements + statement_elements + disclosure_elements
        return final_data

    def create_root_element(self):
        # Create root element with necessary attributes
        self.root = ET.Element(
            "xsd:schema",
            attrib={
                # common for every taxonomy
                "targetNamespace": f"http://{self.company_website}/{self.filing_date}",
                "attributeFormDefault": "unqualified",
                "elementFormDefault": "qualified",
                "xmlns:xbrldt": "http://xbrl.org/2005/xbrldt",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
                "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
                "xmlns:link": "http://www.xbrl.org/2003/linkbase",
                "xmlns:xbrli": f"http://www.xbrl.org/2003/instance",
                "xmlns:dtr-types": "http://www.xbrl.org/dtr/type/2022-03-31",
                "xmlns:enum2": "http://xbrl.org/2020/extensible-enumerations-2.0",
                # change based on the taxonomy year
                "xmlns:srt": f"http://fasb.org/srt/{self.taxonomy_year}",
                "xmlns:dei": f"http://xbrl.sec.gov/dei/{self.taxonomy_year}",
                "xmlns:us-gaap": f"http://fasb.org/us-gaap/{self.taxonomy_year}",
                "xmlns:country": f"http://xbrl.sec.gov/country/{self.taxonomy_year}",
                "xmlns:ecd": f"http://xbrl.sec.gov/ecd/{self.taxonomy_year}",
                "xmlns:sic": f"https://xbrl.sec.gov/sic/{self.taxonomy_year}/sic-{self.taxonomy_year}",
                "xmlns:stpr": f"https://xbrl.sec.gov/stpr/{self.taxonomy_year}/stpr-{self.taxonomy_year}",
                "xmlns:exch": f"https://xbrl.sec.gov/exch/{self.taxonomy_year}/exch-{self.taxonomy_year}",
                "xmlns:naics": f"https://xbrl.sec.gov/naics/{self.taxonomy_year}/naics-{self.taxonomy_year}",
                "xmlns:currency": f"https://xbrl.sec.gov/currency/{self.taxonomy_year}/currency-{self.taxonomy_year}",
                f"xmlns:{self.ticker}": f"http://{self.company_website}/{self.filing_date}",
            },
        )

    def create_xsd_import_elements(self):
        # Create xsd:import elements and append them to the root
        xsd_imports = [
            # common for every taxonomy
            {
                "namespace": "http://www.xbrl.org/2003/instance",
                "schemaLocation": "http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd",
            },
            {
                "namespace": "http://www.xbrl.org/2003/linkbase",
                "schemaLocation": "http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
            },
            {
                "namespace": "http://xbrl.org/2005/xbrldt",
                "schemaLocation": "http://www.xbrl.org/2005/xbrldt-2005.xsd",
            },
            # change based on the taxonomy year
            {
                "namespace": f"http://xbrl.org/2020/extensible-enumerations-2.0",
                "schemaLocation": f"https://www.xbrl.org/2020/extensible-enumerations-2.0.xsd",
            },
            {
                "namespace": f"http://www.xbrl.org/dtr/type/2022-03-31",
                "schemaLocation": f"https://www.xbrl.org/dtr/type/2022-03-31/types.xsd",
            },
            {
                "namespace": f"http://fasb.org/us-gaap/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.fasb.org/us-gaap/{self.taxonomy_year}/elts/us-gaap-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/country/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/country/{self.taxonomy_year}/country-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://fasb.org/srt/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.fasb.org/srt/{self.taxonomy_year}/elts/srt-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/ecd/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/ecd/{self.taxonomy_year}/ecd-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/dei/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/dei/{self.taxonomy_year}/dei-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/stpr/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/stpr/{self.taxonomy_year}/stpr-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/exch/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/exch/{self.taxonomy_year}/exch-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/currency/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/currency/{self.taxonomy_year}/currency-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/naics/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/naics/{self.taxonomy_year}/naics-{self.taxonomy_year}.xsd",
            },
            {
                "namespace": f"http://xbrl.sec.gov/sic/{self.taxonomy_year}",
                "schemaLocation": f"https://xbrl.sec.gov/sic/{self.taxonomy_year}/sic-{self.taxonomy_year}.xsd",
            },
        ]

        for xsd_import in xsd_imports:
            xsd_import_element = ET.Element("xsd:import", attrib=xsd_import)
            self.root.append(xsd_import_element)

    def get_definition(self, text):
        # Insert space before each uppercase letter (except the first one)
        converted_text = "".join(
            [
                " " + char if char.isupper() and i != 0 else char
                for i, char in enumerate(text)
            ]
        )

        # Split the text into words
        converted_text_words = converted_text.split()

        if converted_text:
            # Join the words with spaces and add 'Statement - ' before the first word
            # final_text = f"{converted_text_words[0]} - {' '.join(converted_text_words)}"
            final_text = f"{' '.join(converted_text_words)}"

            return final_text
        else:
            return ""

    def get_definition_index(self, value):
        original_string = "0000000"  # Original string with 7 zeros
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

    def create_xsd_annotation_and_appinfo(self):
        # Create xsd:annotation and xsd:appinfo elements
        xsd_annotation = ET.Element("xsd:annotation")

        xsd_appinfo = ET.Element("xsd:appinfo")

        # Create link:linkbaseRef elements
        linkbase_refs = [
            {
                "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
                "xlink:href": f"{self.ticker}-{self.filing_date}_lab.xml",
                "xlink:role": "http://www.xbrl.org/2003/role/labelLinkbaseRef",
                "xlink:title": "Labels link",
                "xlink:type": "simple",
            },
            {
                "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
                "xlink:href": f"{self.ticker}-{self.filing_date}_pre.xml",
                "xlink:role": "http://www.xbrl.org/2003/role/presentationLinkbaseRef",
                "xlink:title": "Presentation link",
                "xlink:type": "simple",
            },
            {
                "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
                "xlink:href": f"{self.ticker}-{self.filing_date}_def.xml",
                "xlink:role": "http://www.xbrl.org/2003/role/definitionLinkbaseRef",
                "xlink:title": "Definition link",
                "xlink:type": "simple",
            },
            {
                "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
                "xlink:href": f"{self.ticker}-{self.filing_date}_cal.xml",
                "xlink:role": "http://www.xbrl.org/2003/role/calculationLinkbaseRef",
                "xlink:title": "Calculation link",
                "xlink:type": "simple",
            },
        ]

        for linkbase_ref in linkbase_refs:
            linkbase_ref_element = ET.Element("link:linkbaseRef", attrib=linkbase_ref)
            xsd_appinfo.append(linkbase_ref_element)

        custom_elements = []
        for index, (role, role_data) in enumerate(self.grouped_data.items(), start=1):
            if role:
                # get each role type from the role
                try:
                    _role_data = role_data[0]
                    role_type: str = _role_data.get("RoleType")
                except:
                    pass

                for record in role_data:

                    axis_members: str = record.get("Axis_Member")
                    element_name: str = record.get("Element")
                    root_level_abstract: str = record.get("RootLevelAbstract")

                    if root_level_abstract.startswith("custom"):
                        custom_elements.append(root_level_abstract)

                    if element_name.startswith("custom"):
                        custom_elements.append(element_name)

                    if axis_members:
                        splitted = axis_members.split("__")

                        # Group by 3
                        groups = [
                            splitted[i : i + 3] for i in range(0, len(splitted), 3)
                        ]
                        for group in groups:
                            axis, domain, member = group

                            if axis.startswith("custom"):
                                custom_elements.append(axis)

                            if domain.startswith("custom"):
                                custom_elements.append(domain)

                            if member.startswith("custom"):
                                custom_elements.append(member)

                _role = (
                    role.replace("(", "")
                    .replace(")", "")
                    .replace(",", "")
                    .replace("-", "")
                    .replace("–", "")
                    .replace("/", "")
                    .replace("@", "")
                    .replace("=", "")
                    .replace("'", "")
                    .replace("’", "")
                    .replace("|", "")
                    .replace("%", "")
                    .replace("*", "")
                    .replace("$", "")
                    .replace("#", "")
                    .replace("!", "")
                    .replace("?", "")
                    .replace("[", "")
                    .replace("]", "")
                    .replace("+", "")
                    .replace("_", "")
                    .replace(".", "")
                    .replace("^", "")
                    .replace("&amp;", "")
                )

                role_without_spaces = re.sub(r"\s+", "", _role)

                link_role_type = ET.Element(
                    "link:roleType",
                    attrib={
                        "roleURI": f"http://{self.company_website}/{self.filing_date}/role/{role_without_spaces}",
                        "id": role_without_spaces,
                    },
                )
                # Create child elements for link:roleType
                link_role_type_elements = [
                    {
                        "tag": "link:definition",
                        "text": f"{self.get_definition_index(str(index))} - {role_type.capitalize()} - {role}",
                    },
                    {"tag": "link:usedOn", "text": "link:presentationLink"},
                    {"tag": "link:usedOn", "text": "link:calculationLink"},
                    {"tag": "link:usedOn", "text": "link:definitionLink"},
                ]

                for element_info in link_role_type_elements:
                    element = ET.Element(element_info["tag"])
                    element.text = element_info["text"]
                    link_role_type.append(element)

                # Append link:roleType to xsd:appinfo
                xsd_appinfo.append(link_role_type)

        # Append xsd:appinfo to xsd:annotation
        xsd_annotation.append(xsd_appinfo)

        # Append xsd:annotation to root
        self.root.append(xsd_annotation)

        # custom elements
        for custom_element in set(custom_elements):
            _, element_name = custom_element.split("--")
            custom_element_data = get_custom_element_record(
                self.client_id, element_name
            )
            if custom_element_data:
                element_data: dict = custom_element_data.get("data")
                data_type: str = custom_element_data.get("dataType", "")
                abstract: str = element_data.get("abstract", "")
                id = f"{custom_element}".replace("custom", self.ticker).replace(
                    "--", "_"
                )
                custom_element_attributes = {
                    "id": id,
                    "name": element_name,
                    "nillable": "true",
                    "type": data_type,
                }

                period = element_data.get("period", "")
                balance = element_data.get("balance", "")
                substitutionGroup = element_data.get("substitutionGroup", "")

                if abstract:
                    custom_element_attributes["abstract"] = abstract.lower()
                if period:
                    custom_element_attributes["xbrli:periodType"] = period
                if substitutionGroup:
                    custom_element_attributes["substitutionGroup"] = substitutionGroup
                if balance:
                    custom_element_attributes["balance"] = balance

                custom_element = ET.Element("xsd:element", custom_element_attributes)
                self.root.append(custom_element)

    def generate_xsd_schema(self):
        # Create an XML declaration
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'

        # Get current date and time with AM/PM
        current_datetime = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        # Create comments after the XML declaration
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            f"<!-- Creation Date : {current_datetime} -->",
            "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
        ]

        # Concatenate XML declaration and comments
        xml_data = xml_declaration + "\n".join(comments_after_declaration) + "\n"

        # Create the root element
        self.create_root_element()

        # Create xsd:import elements
        self.create_xsd_import_elements()

        # Create xsd:annotation and xsd:appinfo elements
        self.create_xsd_annotation_and_appinfo()

        # save xml data into file
        self.save_xml_data(xml_data)

    def save_xml_data(self, xml_data):
        # Serialize only the root element and its children
        xml_data += ET.tostring(self.root, encoding="US-ASCII").decode("utf-8")

        # Extract the directory from the output file path
        directory = os.path.dirname(self.output_file)

        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        reparsed = minidom.parseString(xml_data)
        pretty_xml_as_string = reparsed.toprettyxml(indent="  ")
        # Write the pretty-printed XML to a file

        with open(self.output_file, "w") as file:
            file.write(pretty_xml_as_string)


# # Example usage:
# ticker = "msft"
# filing_date = "20230630"
# data = html_elements_data
# company_website = "http://www.microsoft.com"

# generator = XSDGenerator(data, ticker, filing_date, company_website)
# generator.generate_xsd_schema()
