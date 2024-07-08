import re, os
from itertools import groupby

from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml_generation.labels import labels_dict


class PreXMLGenerator:
    def __init__(
        self, data, filing_date, ticker, company_website, client_id, elements_data
    ):
        # Initialize the PreXMLGenerator with data, filing_date, ticker, and company_website.
        self.data = data
        self.filing_date = filing_date
        self.ticker = ticker
        self.company_website = company_website
        self.client_id = client_id
        self.output_file = f"data/{self.ticker}-{self.filing_date}/{self.ticker}-{self.filing_date}_pre.xml"
        # Dictionary to store grouped data by RoleName.
        self.grouped_data: dict[str, list] = {}
        self.elements_data = elements_data

    def get_preferred_label(self, label: str):
        for key, value in labels_dict.items():
            if key.replace(" ", "").lower() == label.replace(" ", "").lower():
                return value

    def group_data_by_role(self):
        for record in self.data:
            role_name = record["RoleName"]
            if role_name in self.grouped_data.keys():
                self.grouped_data[role_name].append(record)
            else:
                self.grouped_data[role_name] = [record]

    def create_role_ref_element(self, parent=None, role_uri=None, xlink_href=None):
        # Create an XML element for roleRef with roleURI and xlink:href attributes.
        return ET.SubElement(
            parent,
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

    def get_href_url(self, element: str):
        if element.startswith("us-gaap"):
            return "https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd"
        if element.startswith("dei"):
            return "https://xbrl.sec.gov/dei/2023/dei-2023.xsd"
        if element.startswith("srt"):
            return "https://xbrl.fasb.org/srt/2023/elts/srt-2023.xsd"
        if element.startswith(self.ticker):
            return f"{self.ticker}-{self.filing_date}.xsd"
        if element.startswith("country"):
            return "http://xbrl.sec.gov/country/2023.xsd"
        if element.startswith("currency"):
            return "https://xbrl.sec.gov/currency/2023/currency-2023.xsd"
        if element.startswith("exch"):
            return "https://xbrl.sec.gov/exch/2023/exch-2023.xsd"
        if element.startswith("naics"):
            return "https://xbrl.sec.gov/naics/2023/naics-2023.xsd"
        if element.startswith("sic"):
            return "https://xbrl.sec.gov/sic/2023/sic-2023.xsd"
        if element.startswith("stpr"):
            return "https://xbrl.sec.gov/stpr/2023/stpr-2023.xsd"

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

    def generate_elements_xml(
        self,
        role_data,
        presentation_links,
        presentation_link,
        line_item,
        dimension=False,
    ):
        initial_record = role_data[0]

        root_level_abstract = initial_record.get("RootLevelAbstract")
        _pre_element_parent: str = initial_record.get("PreElementParent")
        pre_element_parent_created = False

        # root level abstract and pre element parent is same don't create pre element parent
        # consider root level abstract as a pre element parent

        # pre parent element
        if root_level_abstract != _pre_element_parent:
            pre_element_parent = _pre_element_parent
            if pre_element_parent and pre_element_parent_created is False:
                pre_element_parent_xlink_href = self.get_href_url(pre_element_parent)
                pre_element_parent_loc = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{pre_element_parent}",
                    xlink_href=f"{pre_element_parent_xlink_href}#{pre_element_parent}",
                )

                # Add definition arc elements
                definition_arc = self.create_presentation_arc_element(
                    parent_tag=presentation_link,
                    order="1",
                    arc_role="http://xbrl.org/int/dim/arcrole/parent-child",
                    xlink_from=f"loc_{line_item}",
                    xlink_to=f"loc_{pre_element_parent}",
                )

                pre_element_parent_created = True

        # main elements
        elements_list: list = []
        element_occurrences: dict = {}

        for index, record in enumerate(role_data, start=1):

            _element: str = record.get("Element")
            if _element:
                element = _element.replace("--", "_")

                label_type = record.get("PreferredLabelType")
                preferred_label = self.get_preferred_label(label_type)
                root_level_abstract = record.get("RootLevelAbstract")

                _pre_element_parent: str = record.get("PreElementParent")
                if _pre_element_parent:
                    pre_element_parent = _pre_element_parent.replace("--", "_")
                else:
                    pre_element_parent: str = root_level_abstract
                    pre_element_parent = _pre_element_parent.replace("--", "_")

                if element not in elements_list:
                    # main elements
                    if element.startswith("custom"):
                        element = element.replace("custom", self.ticker)
                        element_loc = self.create_presentation_loc_element(
                            parent_tag=presentation_link,
                            label=f"loc_{element}",
                            xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{element}",
                        )

                    else:
                        href_url = self.get_href_url(element)
                        element_loc = self.create_presentation_loc_element(
                            parent_tag=presentation_link,
                            label=f"loc_{element}",
                            xlink_href=f"{href_url}#{element}",
                        )

                    if pre_element_parent:
                        xlink_from = pre_element_parent
                    else:
                        xlink_from = root_level_abstract

                    # calculate xlink from element element occurrence
                    if xlink_from not in element_occurrences:
                        element_occurrences[xlink_from] = 1
                    else:
                        element_occurrences[xlink_from] = (
                            element_occurrences[xlink_from] + 1
                        )

                    if pre_element_parent_created is False:
                        # Common arguments for create_presentation_arc_element
                        arc_args = {
                            "parent_tag": presentation_link,
                            "order": str(element_occurrences.get(xlink_from)),
                            "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                            "xlink_from": f"loc_{line_item}",
                            "xlink_to": f"loc_{element}",
                            "preferred_label": preferred_label,
                        }

                        pre_element_parent_created = True
                    else:
                        # Common arguments for create_presentation_arc_element
                        arc_args = {
                            "parent_tag": presentation_link,
                            "order": str(element_occurrences.get(xlink_from)),
                            "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                            "xlink_from": f"loc_{xlink_from}".replace("--", "_"),
                            "xlink_to": f"loc_{element}",
                            "preferred_label": preferred_label,
                        }

                    # Create presentationArc element and append it to presentation_links list.
                    presentation_arc = self.create_presentation_arc_element(**arc_args)

                    # add element into elements list
                    elements_list.append(element)

        presentation_links.append(presentation_link)

    def generate_dimension_xml(
        self,
        role_data,
        dimension_records,
        presentation_link,
        presentation_links,
        root_level_abstract,
    ):
        is_table_loc_created = False
        dimension_records_list = []
        members_list = []
        member_order = 1
        # iterate through dimension records
        for index, record in enumerate(dimension_records):
            _table = record.get("Table")
            table = _table.replace("--", "_")

            order = record.get("Indenting")
            axis_members: str = record.get("Axis_Member")

            _line_item: str = record.get("LineItem")
            line_item = _line_item.replace("--", "_")

            label = record.get("PreferredLabel")
            label_type = record.get("PreferredLabelType")
            preferred_label = self.get_preferred_label(label_type)

            if table and is_table_loc_created is False:
                # table location
                table_xlink_href = self.get_href_url(table)
                table_loc = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{table}",
                    xlink_href=f"{table_xlink_href}#{table}",
                )

                # Common arguments for create_presentation_arc_element
                arc_args = {
                    "parent_tag": presentation_link,
                    "order": "1",
                    "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                    "xlink_from": f"loc_{root_level_abstract}",
                    "xlink_to": f"loc_{table}",
                }

                # Create presentationArc element and append it to presentation_links list.
                presentation_arc = self.create_presentation_arc_element(**arc_args)
                is_table_loc_created = True

            splitted = axis_members.split("__")

            # Group by 3
            groups = [splitted[i : i + 3] for i in range(0, len(splitted), 3)]
            for group in groups:
                _axis, _domain, _member = group
                axis = _axis.replace("--", "_").replace("custom", self.ticker)
                domain = _domain.replace("--", "_").replace("custom", self.ticker)
                member = _member.replace("--", "_").replace("custom", self.ticker)

                dimension_record = (axis, domain)
                if dimension_record not in dimension_records_list:

                    # axis location
                    axis_xlink_href = self.get_href_url(axis)
                    axis_loc = self.create_presentation_loc_element(
                        parent_tag=presentation_link,
                        label=f"loc_{axis}",
                        xlink_href=f"{axis_xlink_href}#{axis}",
                    )

                    # Common arguments for create_presentation_arc_element
                    arc_args = {
                        "parent_tag": presentation_link,
                        "order": "1",
                        "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                        "xlink_from": f"loc_{table}",
                        "xlink_to": f"loc_{axis}",
                    }

                    # Create presentationArc element and append it to presentation_links list.
                    presentation_arc = self.create_presentation_arc_element(**arc_args)

                    # domain location
                    domain_xlink_href = self.get_href_url(domain)
                    domain_loc = self.create_presentation_loc_element(
                        parent_tag=presentation_link,
                        label=f"loc_{domain}",
                        xlink_href=f"{domain_xlink_href}#{domain}",
                    )

                    # Common arguments for create_presentation_arc_element
                    arc_args = {
                        "parent_tag": presentation_link,
                        "order": "1",
                        "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                        "xlink_from": f"loc_{axis}",
                        "xlink_to": f"loc_{domain}",
                    }

                    # Create presentationArc element and append it to presentation_links list.
                    presentation_arc = self.create_presentation_arc_element(**arc_args)

                    dimension_records_list.append(dimension_record)

                if member not in members_list:
                    # member location
                    member_xlink_href = self.get_href_url(member)
                    member_loc = self.create_presentation_loc_element(
                        parent_tag=presentation_link,
                        label=f"loc_{member}",
                        xlink_href=f"{member_xlink_href}#{member}",
                    )

                    # Common arguments for create_presentation_arc_element
                    arc_args = {
                        "parent_tag": presentation_link,
                        "order": str(member_order),
                        "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                        "xlink_from": f"loc_{domain}",
                        "xlink_to": f"loc_{member}",
                    }

                    # Create presentationArc element and append it to presentation_links list.
                    presentation_arc = self.create_presentation_arc_element(**arc_args)
                    members_list.append(member)
                    member_order += 1

            # add line item only for last item
            if index == len(dimension_records) - 1:
                # line item location
                line_item_xlink_href = self.get_href_url(line_item)
                line_item_loc = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{line_item}",
                    xlink_href=f"{line_item_xlink_href}#{line_item}",
                )

                # Common arguments for create_presentation_arc_element
                arc_args = {
                    "parent_tag": presentation_link,
                    "order": "2",
                    "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                    "xlink_from": f"loc_{table}",
                    "xlink_to": f"loc_{line_item}",
                }

                # Create presentationArc element and append it to presentation_links list.
                presentation_arc = self.create_presentation_arc_element(**arc_args)

        # generate mail element xml
        self.generate_elements_xml(
            role_data,
            presentation_links,
            presentation_link,
            line_item,
            dimension=True,
        )

    def check_role_is_dimension_or_not(self, role_data):
        # Flag variable to track if any Axis_Member has a value
        records: list[str] = []

        # Check if any Axis_Member has a value
        for item in role_data:
            if item["Axis_Member"]:
                records.append(item)

        return records

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
            record: dict = role_data[0] | {}
            if role_name:
                _root_level_abstract: str = record.get("RootLevelAbstract")
                root_level_abstract = _root_level_abstract.replace("--", "_")

                role_name_without_spaces = re.sub(r"\s+", "", role_name)
                role = (
                    role_name_without_spaces.replace("(", "")
                    .replace(")", "")
                    .replace(",", "")
                    .replace("-", "")
                    .replace("'", "")
                )
                # Create roleRef element and append it to role_ref_elements list.
                role_uri = (
                    f"http://{self.company_website}/{self.filing_date}/role/{role}"
                )
                role_ref_element = self.create_role_ref_element(
                    linkbase_element,
                    role_uri=role_uri,
                    xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{role}",
                )

                _line_item: str = record.get("LineItem")
                line_item = _line_item.replace("--", "_")

                role_ref_elements.append(role_ref_element)

                # Create presentationLink element and append it to presentation_links list.
                presentation_link = ET.SubElement(
                    linkbase_element,
                    "link:presentationLink",
                    attrib={
                        "xlink:role": role_uri,
                        "xlink:type": "extended",
                    },
                )

                # Create presentation loc elements for root_level_abstract and element.
                root_level_abstract_href = self.get_href_url(root_level_abstract)
                root_level_abstract_loc = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{root_level_abstract}",
                    xlink_href=f"{root_level_abstract_href}#{root_level_abstract}",
                )

                # check role is dimension or not
                dimension_records = self.check_role_is_dimension_or_not(role_data)

                # if role is dimension
                if dimension_records:
                    self.generate_dimension_xml(
                        role_data,
                        dimension_records,
                        presentation_link,
                        presentation_links,
                        root_level_abstract,
                    )
                else:
                    # if role is not dimension
                    self.generate_elements_xml(
                        role_data,
                        presentation_links,
                        presentation_link,
                        root_level_abstract,
                    )

                # add elements data into pre.xml next to the main elements
                if role == "Cover":
                    for element in self.elements_data:
                        element_xlink_href = self.get_href_url(f"dei--{element}")
                        pre_element_parent_loc = self.create_presentation_loc_element(
                            parent_tag=presentation_link,
                            label=f"loc_dei_{element}",
                            xlink_href=f"{element_xlink_href}#dei_{element}",
                        )
                        # Add definition arc elements
                        presentation_arc = self.create_presentation_arc_element(
                            parent_tag=presentation_link,
                            order="1",
                            arc_role="http://xbrl.org/int/dim/arcrole/parent-child",
                            xlink_from=f"loc_{root_level_abstract}",
                            xlink_to=f"loc_dei_{element}",
                        )

        # XML declaration and comments.
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            "<!-- Creation Date : -->",
            "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
        ]

        # Concatenate XML data and save it into the pre.xml file.
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


# # Example usage:
# ticker = "msft"
# filing_date = "20230630"
# data = html_elements_data
# company_website = "http://www.microsoft.com"

# # Initialize the PreXMLGenerator and generate the pre.xml file.
# generator = PreXMLGenerator(data, filing_date, ticker, company_website)
# generator.generate_pre_xml()
