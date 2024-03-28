from itertools import groupby
import xml.etree.ElementTree as ET
from database import html_elements_data


class XSDGenerator:
    def __init__(self, data, ticker, filing_date, company_website):
        self.root = None
        self.data = data
        self.ticker = ticker
        self.filing_date = filing_date
        self.company_website = company_website
        # self.definitions = definitions
        self.grouped_data = self.group_data_by_role()

    def group_data_by_role(self):
        # Group data by RoleName using itertools.groupby
        grouped_data = {}
        for key, group in groupby(self.data, key=lambda x: x["RoleName"]):
            grouped_data[key] = list(group)
        return grouped_data

    def create_root_element(self):
        # Create root element with necessary attributes
        self.root = ET.Element(
            "xsd:schema",
            attrib={
                "targetNamespace": f"{self.company_website}/{self.filing_date}",
                "attributeFormDefault": "unqualified",
                "elementFormDefault": "qualified",
                "xmlns:dtr-types": "http://www.xbrl.org/dtr/type/2022-03-31",
                "xmlns:country": "http://xbrl.sec.gov/country/2023",
                "xmlns:ecd-sub": "http://xbrl.sec.gov/ecd-sub/2023",
                f"xmlns:{self.ticker}": f"{self.company_website}/{self.filing_date}",
                "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
                "xmlns:link": "http://www.xbrl.org/2003/linkbase",
                "xmlns:dei": "http://xbrl.sec.gov/dei/2023",
                "xmlns:xbrldt": "http://xbrl.org/2005/xbrldt",
                "xmlns:xbrli": "http://www.xbrl.org/2003/instance",
                "xmlns:enum2": "http://xbrl.org/2020/extensible-enumerations-2.0",
                "xmlns:srt": "http://fasb.org/srt/2023",
                "xmlns:us-gaap": "http://fasb.org/us-gaap/2023",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
            },
        )

    def create_xsd_import_elements(self):
        # Create xsd:import elements and append them to the root
        xsd_imports = [
            {
                "schemaLocation": "http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd",
                "namespace": "http://www.xbrl.org/2003/instance",
            },
            {
                "schemaLocation": "http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
                "namespace": "http://www.xbrl.org/2003/linkbase",
            },
            {
                "schemaLocation": "http://www.xbrl.org/2005/xbrldt-2005.xsd",
                "namespace": "http://xbrl.org/2005/xbrldt",
            },
            {
                "schemaLocation": "https://xbrl.sec.gov/dei/2023/dei-2023.xsd",
                "namespace": "http://xbrl.sec.gov/dei/2023",
            },
            {
                "schemaLocation": "https://www.xbrl.org/2020/extensible-enumerations-2.0.xsd",
                "namespace": "http://xbrl.org/2020/extensible-enumerations-2.0",
            },
            {
                "schemaLocation": "https://xbrl.sec.gov/ecd/2023/ecd-sub-2023.xsd",
                "namespace": "http://xbrl.sec.gov/ecd-sub/2023",
            },
            {
                "schemaLocation": "https://www.xbrl.org/dtr/type/2022-03-31/types.xsd",
                "namespace": "http://www.xbrl.org/dtr/type/2022-03-31",
            },
            {
                "schemaLocation": "https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd",
                "namespace": "http://fasb.org/us-gaap/2023",
            },
            {
                "schemaLocation": "https://xbrl.sec.gov/country/2023/country-2023.xsd",
                "namespace": "http://xbrl.sec.gov/country/2023",
            },
            {
                "schemaLocation": "https://xbrl.fasb.org/srt/2023/elts/srt-2023.xsd",
                "namespace": "http://fasb.org/srt/2023",
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

        # Join the words with spaces and add 'Statement - ' before the first word
        final_text = f"{converted_text_words[0]} - {' '.join(converted_text_words)}"
        return final_text

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

        for index, (role, role_data) in enumerate(self.grouped_data.items(), start=1):
            link_role_type = ET.Element(
                "link:roleType",
                attrib={
                    "roleURI": f"{self.company_website}/{self.filing_date}/role/{role}",
                    "id": role,
                },
            )

            # Create child elements for link:roleType
            link_role_type_elements = [
                {
                    "tag": "link:definition",
                    "text": f"{self.get_definition_index(str(index))} - {self.get_definition(role)}",
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
        custom_element = ET.Element(
            "xs:element",
            {
                "id": "msft_CommonStock025ParValueMember",
                "abstract": "true",
                "name": "CommonStock025ParValueMember",
                "nillable": "true",
                "xbrli:periodType": "duration",
                "substitutionGroup": "xbrli:item",
                "type": "dtr-types1:domainItemType",
            },
        )
        self.root.append(custom_element)

    def generate_xsd_schema(self):
        # Create an XML declaration
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'

        # Create comments after the XML declaration
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            "<!-- Creation Date : -->",
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
        filename = f"{ticker}-{filing_date}.xsd"
        # Optionally, write the XML to a file
        with open(filename, "w", encoding="US-ASCII") as file:
            file.write(xml_data)


# Example usage:
ticker = "msft"
filing_date = "20230630"
data = html_elements_data
company_website = "http://www.microsoft.com"

generator = XSDGenerator(data, ticker, filing_date, company_website)
generator.generate_xsd_schema()
