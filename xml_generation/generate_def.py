from itertools import groupby
import xml.etree.ElementTree as ET
from database import html_elements_data


class DefXMLGenerator:
    def __init__(self, data, ticker, filing_date, company_website):
        # Initialize the DefXMLGenerator with provided data and metadata
        self.data = data
        self.ticker = ticker
        self.filing_date = filing_date
        self.company_website = company_website
        self.grouped_data = self.group_data_by_role()

    def group_data_by_role(self):
        # Group data by RoleName using itertools.groupby
        grouped_data = {}
        for key, group in groupby(self.data, key=lambda x: x["RoleName"]):
            grouped_data[key] = list(group)
        return grouped_data

    def create_role_ref_element(self, role_uri=None, xlink_href=None):
        # Create a roleRef element with specified attributes
        return ET.Element(
            "link:roleRef",
            attrib={
                "roleURI": role_uri,
                "xlink:href": xlink_href,
                "xlink:type": "simple",
            },
        )

    def create_definition_loc_element(
        self, parent_tag=None, label=None, xlink_href=None
    ):
        # Create a loc element for definitionLink with specified attributes
        return ET.SubElement(
            parent_tag,
            "link:loc",
            attrib={
                "xlink:type": "locator",
                "xlink:label": label,
                "xlink:href": xlink_href,
            },
        )

    def create_definition_arc_element(
        self, parent_tag=None, order=None, arc_role=None, xlink_from=None, xlink_to=None
    ):
        # Create a definitionArc element with specified attributes
        return ET.SubElement(
            parent_tag,
            "link:definitionArc",
            attrib={
                "xlink:arcrole": arc_role,
                "xlink:from": xlink_from,
                "xlink:to": xlink_to,
                "xlink:type": "arc",
                "order": order,
            },
        )

    def get_arcrole_refs_xml(self):
        # Define arcroleRefs data
        arcrole_refs_data = [
            {
                "arcroleURI": "http://xbrl.org/int/dim/arcrole/all",
                "xlink:href": "http://www.xbrl.org/2005/xbrldt-2005.xsd#all",
            },
            {
                "arcroleURI": "http://xbrl.org/int/dim/arcrole/hypercube-dimension",
                "xlink:href": "http://www.xbrl.org/2005/xbrldt-2005.xsd#hypercube-dimension",
            },
            {
                "arcroleURI": "http://xbrl.org/int/dim/arcrole/dimension-default",
                "xlink:href": "http://www.xbrl.org/2005/xbrldt-2005.xsd#dimension-default",
            },
            {
                "arcroleURI": "http://xbrl.org/int/dim/arcrole/dimension-domain",
                "xlink:href": "http://www.xbrl.org/2005/xbrldt-2005.xsd#dimension-domain",
            },
            {
                "arcroleURI": "http://xbrl.org/int/dim/arcrole/domain-member",
                "xlink:href": "http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member",
            },
        ]

        # Create arcroleRef elements
        arcrole_ref_elements = []
        for arcrole_ref_data in arcrole_refs_data:
            arcrole_ref = ET.Element(
                "link:arcroleRef",
                arcroleURI=arcrole_ref_data["arcroleURI"],
                xlink_type="simple",
                xlink_href=arcrole_ref_data["xlink:href"],
            )
            arcrole_ref_elements.append(arcrole_ref)

        arcrole_ref_elements_xml = "\n".join(
            [ET.tostring(e, encoding="utf-8").decode() for e in arcrole_ref_elements]
        )

        return arcrole_ref_elements_xml

    def generate_def_xml(self):
        # Create an XML declaration
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'

        # Comments after the XML declaration
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            "<!-- Creation Date : -->",
            "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
        ]

        # Create the root linkbase element with namespaces
        linkbase_element = ET.Element(
            "link:linkbase",
            attrib={
                "xsi:schemaLocation": "http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
                "xmlns:link": "http://www.xbrl.org/2003/linkbase",
                "xmlns:xbrldt": "http://xbrl.org/2005/xbrldt",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            },
        )

        role_ref_elements = []
        definition_links = []  # List to store presentationLink elements.

        # Iterate through grouped data and create roleRef and presentationLink elements
        for role_name, role_data in self.grouped_data.items():
            for record in role_data:
                role = record.get("RoleName")
                _element = record.get("Element")
                element = _element.replace("--", "_")
                label = record.get("PreferredLabel")
                _root_level_abstract = record.get("RootLevelAbstract")
                root_level_abstract = _root_level_abstract.replace("--", "_")

                # Create definitionLink root element
                definition_link = ET.Element(
                    "link:definitionLink",
                    attrib={
                        "xlink:role": f"{self.company_website}/role/{role}",
                        "xlink:type": "extended",
                    },
                )

                # Add definition loc elements
                root_level_abstract_loc = self.create_definition_loc_element(
                    parent_tag=definition_link,
                    label=f"loc_{root_level_abstract}",
                    xlink_href=f"https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd#{root_level_abstract}",
                )

                loc_entities = self.create_definition_loc_element(
                    parent_tag=definition_link,
                    label=f"loc_{element}",
                    xlink_href=f"https://xbrl.sec.gov/dei/2023/dei-2023.xsd#{element}",
                )

                # Add definition arc elements
                definition_arc = self.create_definition_arc_element(
                    parent_tag=definition_link,
                    order="1",
                    arc_role="http://www.xbrl.org/2003/arcrole/all",
                    xlink_from=f"loc_{root_level_abstract}",
                    xlink_to=f"loc_{element}",
                )

                definition_links.append(definition_link)

        # Convert each role_ref_element to XML string and concatenate
        role_ref_elements_xml = "\n".join(
            [ET.tostring(e, encoding="utf-8").decode() for e in role_ref_elements]
        )
        definition_links_xml = "\n".join(
            [ET.tostring(e, encoding="utf-8").decode() for e in definition_links]
        )
        arcrole_refs_xml = self.get_arcrole_refs_xml()

        # Concatenate XML declaration, comments, and linkbase element
        xml_data = (
            xml_declaration
            + "\n".join(comments_after_declaration)
            + "\n"
            + ET.tostring(linkbase_element, encoding="utf-8").decode()
            + "\n"
            + arcrole_refs_xml
            + role_ref_elements_xml  # Use the concatenated XML string
            + "\n"
            + definition_links_xml
        )

        self.save_xml_data(xml_data)

    def save_xml_data(self, xml_data):
        # Save the XML data into the pre.xml file.
        filename = f"{self.ticker}-{self.filing_date}_def.xml"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(xml_data)


ticker = "msft"
filing_date = "20230630"
data = html_elements_data
company_website = "http://www.microsoft.com"

# Example usage
data = html_elements_data  # Assuming html_elements_data is defined
generator = DefXMLGenerator(data, ticker, filing_date, company_website)
generator.generate_def_xml()
