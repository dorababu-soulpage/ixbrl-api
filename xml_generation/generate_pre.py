from itertools import groupby
from labels import labels_dict
import xml.etree.ElementTree as ET
from database import html_elements_data


class PreXMLGenerator:
    def __init__(self, data, filing_date, ticker, company_website):
        # Initialize the PreXMLGenerator with data, filing_date, ticker, and company_website.
        self.data = data
        self.filing_date = filing_date
        self.ticker = ticker
        self.company_website = company_website
        self.grouped_data = {}  # Dictionary to store grouped data by RoleName.

    def get_preferred_label(self, label: str):

        for key, value in labels_dict.items():
            if key.replace(" ", "").lower() == label.replace(" ", "").lower():
                print(label, value)
                return value

    def group_data_by_role(self):
        # Group the data by RoleName using itertools groupby and store it in grouped_data.
        for key, group in groupby(self.data, key=lambda x: x["RoleName"]):
            self.grouped_data[key] = list(group)

    def create_role_ref_element(self, role_uri=None, xlink_href=None):
        # Create an XML element for roleRef with roleURI and xlink:href attributes.
        return ET.Element(
            "link:roleRef",
            attrib={
                "roleURI": role_uri,
                "xlink:href": xlink_href,
                "xlink:type": "simple",
            },
        )

    def create_presentation_loc_element(
        self, parent_tag=None, label=None, xlink_href=None
    ):
        # Create an XML element for loc with xlink:type, xlink:label, and xlink:href attributes.
        return ET.SubElement(
            parent_tag,
            "link:loc",
            attrib={
                "xlink:type": "locator",
                "xlink:label": label,
                "xlink:href": xlink_href,
            },
        )

    def create_presentation_arc_element(
        self,
        parent_tag=None,
        order=None,
        arc_role=None,
        xlink_from=None,
        xlink_to=None,
        preferred_label=None,
    ):
        attrib = {
            "order": order,
            "xlink:arcrole": arc_role,
            "xlink:from": xlink_from,
            "xlink:to": xlink_to,
            "xlink:type": "arc",
        }

        if preferred_label is not None:
            attrib["preferredLabel"] = preferred_label

        return ET.SubElement(parent_tag, "link:presentationArc", attrib=attrib)

    def generate_pre_xml(self):
        # Create the root linkbase element with XML namespaces and schema location.
        linkbase_element = ET.Element(
            "link:linkbase",
            attrib={
                "xmlns:link": "http://www.xbrl.org/2003/linkbase",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
            },
        )

        # Group data by RoleName.
        self.group_data_by_role()

        role_ref_elements = []  # List to store roleRef elements.
        presentation_links = []  # List to store presentationLink elements.

        # Iterate through grouped data and create roleRef and presentationLink elements.
        for role_name, role_data in self.grouped_data.items():
            for record in role_data:
                role = record.get("RoleName")
                _element: str = record.get("Element")
                element = _element.replace("--", "_")
                label = record.get("PreferredLabel")
                label_type = record.get("PreferredLabelType")
                preferred_label = self.get_preferred_label(label_type)
                _root_level_abstract = record.get("RootLevelAbstract")
                root_level_abstract = _root_level_abstract.replace("--", "_")

                # Create roleRef element and append it to role_ref_elements list.
                role_ref_element = self.create_role_ref_element(
                    role_uri=f"{self.company_website}/{self.filing_date}/taxonomy/role/Role_{role}",
                    xlink_href=f"{self.ticker}-{self.filing_date}.xsd#Role_{role}",
                )
                role_ref_elements.append(role_ref_element)

                # Create presentationLink element and append it to presentation_links list.
                presentation_link = ET.Element(
                    "link:presentationLink",
                    attrib={
                        "xlink:role": f"{self.company_website}/role/Role_{role}",
                        "xlink:type": "extended",
                    },
                )

                # Create presentation loc elements for root_level_abstract and element.
                root_level_abstract_loc = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{root_level_abstract}",
                    xlink_href=f"https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd#{root_level_abstract}",
                )

                loc_entities = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{element}",
                    xlink_href=f"https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd#{element}",
                )

                # Common arguments for create_presentation_arc_element
                arc_args = {
                    "parent_tag": presentation_link,
                    "order": "1",
                    "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                    "xlink_from": f"loc_{root_level_abstract}",
                    "xlink_to": f"loc_{element}",
                }

                # Add label-specific argument
                if label:
                    arc_args["preferred_label"] = preferred_label
                # Create presentationArc element and append it to presentation_links list.
                presentation_arc = self.create_presentation_arc_element(**arc_args)

                presentation_links.append(presentation_link)

        # XML declaration and comments.
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            "<!-- Creation Date : -->",
            "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
        ]

        # Convert role_ref_elements and presentation_links to XML strings.
        role_ref_elements_xml = "\n".join(
            [ET.tostring(e, encoding="utf-8").decode() for e in role_ref_elements]
        )
        presentation_links_xml = "\n".join(
            [ET.tostring(e, encoding="utf-8").decode() for e in presentation_links]
        )

        # Concatenate XML data and save it into the pre.xml file.
        xml_data = (
            xml_declaration
            + "\n".join(comments_after_declaration)
            + "\n"
            + ET.tostring(linkbase_element, encoding="utf-8").decode()
            + "\n"
            + role_ref_elements_xml
            + "\n"
            + presentation_links_xml
        )
        self.save_xml_data(xml_data)

    def save_xml_data(self, xml_data):
        # Save the XML data into the pre.xml file.
        filename = f"{self.ticker}-{self.filing_date}_pre.xml"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(xml_data)


# Example usage:
ticker = "msft"
filing_date = "20230630"
data = html_elements_data
company_website = "http://www.microsoft.com"

# Initialize the PreXMLGenerator and generate the pre.xml file.
generator = PreXMLGenerator(data, filing_date, ticker, company_website)
generator.generate_pre_xml()
