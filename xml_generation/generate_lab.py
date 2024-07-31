import os
from typing import Dict

from xml.dom import minidom
import xml.etree.ElementTree as ET

from utils import get_taxonomy_values
from utils import get_custom_element_record


class LabXMLGenerator:
    def __init__(
        self, data, filing_date, ticker, company_website, client_id, elements_data
    ):
        # Initialize the LabXMLGenerator with data, filing_date, ticker, and company_website.
        self.data = data
        self.filing_date = filing_date
        self.ticker = ticker
        self.company_website = company_website
        self.client_id = client_id
        self.output_file = f"data/{self.ticker}-{self.filing_date}/{self.ticker}-{self.filing_date}_lab.xml"
        self.element_data = []
        self.elements_data = elements_data

    def create_role_ref_element(self, parent=None, role_uri=None, xlink_href=None):
        return ET.SubElement(
            parent,
            "link:roleRef",
            attrib={
                "roleURI": role_uri,
                "xlink:type": "simple",
                "xlink:href": xlink_href,
            },
        )

    def create_label_element(
        self,
        parent_tag=None,
        id=None,
        xlink_label=None,
        xlink_role=None,
        label_text=None,
    ):
        if xlink_role is None:
            xlink_role = "http://www.xbrl.org/2003/role/label"
        label_element = ET.SubElement(
            parent_tag,
            "link:label",
            attrib={
                "id": id,
                "xlink:label": f"lab_{xlink_label}",
                "xlink:role": xlink_role,
                "xlink:type": "resource",
                "xml:lang": "en-US",
            },
        )
        label_element.text = label_text
        return label_element

    def create_label_loc_element(self, parent_tag=None, label=None, xlink_href=None):
        return ET.SubElement(
            parent_tag,
            "link:loc",
            attrib={
                "xlink:type": "locator",
                "xlink:label": label,
                "xlink:href": xlink_href,
            },
        )

    def get_href_url(self, element: str):
        if element.startswith("us-gaap"):
            return "https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd"
        if element.startswith("dei"):
            return "https://xbrl.sec.gov/dei/2023/dei-2023.xsd"
        if element.startswith("srt"):
            return "https://xbrl.fasb.org/srt/2023/elts/srt-2023.xsd"
        if element.startswith(self.ticker):
            return f"{self.ticker}-{self.filing_date}.xsd"

    def create_label_arc_element(
        self, parent_tag=None, order=None, arc_role=None, xlink_from=None, xlink_to=None
    ):
        return ET.SubElement(
            parent_tag,
            "link:labelArc",
            attrib={
                "xlink:arcrole": arc_role,
                "xlink:from": xlink_from,
                "xlink:to": xlink_to,
                "xlink:type": "arc",
                "order": order,
            },
        )

    def add_role_ref_elements(self, parent):
        labels_list = [
            "negatedPeriodStartLabel",
            "netLabel",
            "negatedNetLabel",
            "negatedTerseLabel",
            "negatedPeriodEndLabel",
            "negatedLabel",
            "negatedTotalLabel",
        ]

        role_ref_elements = []

        for label in labels_list:
            if label == "netLabel":
                href = f"http://www.xbrl.org/lrr/role/net-2009-12-16.xsd#{label}"
            else:
                href = f"http://www.xbrl.org/lrr/role/negated-2009-12-16.xsd#{label}"

            # Create role_ref_elements
            role_ref_element = self.create_role_ref_element(
                parent,
                role_uri=f"http://www.xbrl.org/2009/role/{label}",
                xlink_href=href,
            )
            role_ref_elements.append(role_ref_element)

        return role_ref_elements

    def get_preferred_label(self, element: str):
        label_text = None
        if element.startswith("custom"):
            label_text = element
        else:
            if "--" in element:
                _, name = element.split("--")
                element_value: dict = get_taxonomy_values(name)
                if element_value:
                    label_text = element_value.get("label", "")

        return label_text

    def find_element(self, element_data, element_name):
        for item in element_data:
            if item["element"] == element_name:
                return item
        return None

    def update_element_data(self, element, label_type, preferred_label=None):
        element_record = self.find_element(self.element_data, element)
        if not element_record:
            element_dict = {
                "element": element,
                "label_types": [label_type],
                "main_element": True,
                "preferred_label": (
                    preferred_label
                    if preferred_label
                    else self.get_preferred_label(element)
                ),
            }
            self.element_data.append(element_dict)
        else:
            label_types: list = element_record.get("label_types")
            if label_type not in label_types:
                label_types.append(label_type)

    def get_element_and_types(self):
        for record in self.data:
            for key, value in record.items():
                if key == "Element":
                    element = record.get("Element", "")
                    preferred_label = record.get("PreferredLabel", "")
                    if element:
                        self.update_element_data(
                            element,
                            record.get("PreferredLabelType", ""),
                            preferred_label,
                        )

                elif key in [
                    "PreElementParent",
                    "RootLevelAbstract",
                    "Axis_Member",
                    "Table",
                    "LineItem",
                ]:
                    item = record.get(key, "")
                    if item:
                        items = item.split("__")
                        for item in items:
                            # item = item.replace("--", "_")
                            self.update_element_data(item, "label")

        return self.element_data

    def generate_lab_xml(self):
        linkbase_element = ET.Element(
            "link:linkbase",
            attrib={
                "xsi:schemaLocation": "http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
                "xmlns:link": "http://www.xbrl.org/2003/linkbase",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            },
        )

        # add role ref elements
        role_ref_elements = self.add_role_ref_elements(parent=linkbase_element)

        elements_types: Dict[str, list] = {}
        main_elements_list = []

        label_link = ET.SubElement(
            linkbase_element,
            "link:labelLink",
            attrib={
                "xlink:role": "http://www.xbrl.org/2003/role/link",
                "xlink:type": "extended",
            },
        )
        main_elements_data = self.get_element_and_types()
        for main_element in main_elements_data:
            original_element = main_element
            element: str = main_element.get("element")
            element: str = element.replace("--", "_")
            if element.startswith("custom"):
                element = element.replace("custom", self.ticker)

            # Create location for elements.
            href_url = self.get_href_url(element)
            element_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{element}",
                xlink_href=f"{href_url}#{element}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{element}",
                "xlink_to": f"lab_{element}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            label_types: list = main_element.get("label_types")
            label_created = False
            for index, label_type in enumerate(label_types, start=1):

                label_text = ""
                documentation = ""

                if element.startswith(self.ticker):
                    _, name = element.split("_")
                    custom_element_data = get_custom_element_record(
                        self.client_id, name
                    )
                    if custom_element_data:
                        label_text = custom_element_data.get("label", "")

                    if custom_element_data:
                        data = custom_element_data.get("data")
                        documentation = data.get("documentation")
                else:
                    if "_" in element:
                        _, name = element.split("_")
                        element_value: dict = get_taxonomy_values(name)
                        if element_value:
                            label_text = main_element.get("preferred_label", "")

                if label_created is False:
                    # create label
                    self.create_label_element(
                        parent_tag=label_link,
                        id=f"lab_{element}_1_label_en-US",
                        xlink_label=element,
                        xlink_role=f"http://www.xbrl.org/2003/role/label",
                        label_text=label_text,
                    )
                    label_created = True

                    if documentation:
                        # documentation entry
                        self.create_label_element(
                            parent_tag=label_link,
                            id=f"lab_{element}_1_doc_en-US",
                            xlink_label=element,
                            xlink_role="http://www.xbrl.org/2003/role/documentation",
                            label_text=documentation,
                        )

                # create remaining lables
                if label_type and label_type != "label":
                    if label_type == "negatedLabel":
                        # create terseLabel
                        self.create_label_element(
                            parent_tag=label_link,
                            id=f"lab_{element}_{index}_{label_type}_en-US",
                            xlink_label=element,
                            xlink_role=f"http://www.xbrl.org/2009/role/{label_type}",
                            label_text=label_text,
                        )
                    else:
                        # create terseLabel
                        self.create_label_element(
                            parent_tag=label_link,
                            id=f"lab_{element}_{index}_{label_type}_en-US",
                            xlink_label=element,
                            xlink_role=f"http://www.xbrl.org/2003/role/{label_type}",
                            label_text=label_text,
                        )

            main_elements_list.append(element)

        root_level_abstract = None
        for el in main_elements_list:
            if el.endswith("Abstract"):
                root_level_abstract = el
                break

        if self.elements_data:
            # hidden line items
            # EntityCentralIndexKey
            href_url = self.get_href_url(f"dei--EntityCentralIndexKey")
            element_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_dei_EntityCentralIndexKey",
                xlink_href=f"{href_url}#dei_EntityCentralIndexKey",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{root_level_abstract}",
                "xlink_to": f"lab_dei_EntityCentralIndexKey",
            }
            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            hidden_label_text = ""
            element_value: dict = get_taxonomy_values("EntityCentralIndexKey")

            if element_value:
                hidden_label_text = element_value.get("label", "")

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_dei_EntityCentralIndexKey_1_label_en-US",
                xlink_label="lab_dei_EntityCentralIndexKey",
                xlink_role=f"http://www.xbrl.org/2003/role/label",
                label_text=hidden_label_text,
            )

            for element in self.elements_data:
                # if element not in main elements list, add element
                if f"dei_{element}" not in main_elements_list:
                    # Create location for elements.
                    href_url = self.get_href_url(f"dei--{element}")
                    element_loc = self.create_label_loc_element(
                        parent_tag=label_link,
                        label=f"loc_dei_{element}",
                        xlink_href=f"{href_url}#dei_{element}",
                    )

                    # Common arguments for create_label_arc_element
                    arc_args = {
                        "parent_tag": label_link,
                        "order": "1",
                        "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                        "xlink_from": f"loc_{root_level_abstract}",
                        "xlink_to": f"lab_dei_{element}",
                    }

                    # Create presentationArc element and append it to presentation_links list.
                    label_arc = self.create_label_arc_element(**arc_args)

                    hidden_label_text = ""
                    element_value: dict = get_taxonomy_values(element)

                    if element_value:
                        hidden_label_text = element_value.get("label", "")

                    # create label
                    self.create_label_element(
                        parent_tag=label_link,
                        id=f"lab_dei_{element}_1_label_en-US",
                        xlink_label=f"lab_dei_{element}",
                        xlink_role=f"http://www.xbrl.org/2003/role/label",
                        label_text=hidden_label_text,
                    )

        # XML declaration and comments.
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            "<!-- Creation Date : -->",
            "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
        ]

        # Combine XML elements
        xml_data = (
            xml_declaration
            + "\n".join(comments_after_declaration)
            + "\n"
            + ET.tostring(linkbase_element, encoding="utf-8").decode()
        )
        self.save_xml_data(xml_data)

    def save_xml_data(self, xml_data):
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


# # Usage example:
# ticker = "msft"
# filing_date = "20230630"
# data = html_elements_data
# company_website = "http://www.microsoft.com"

# # Instantiate the class
# generator = LabXMLGenerator(data, filing_date, ticker, company_website)
# generator.generate_lab_xml()
