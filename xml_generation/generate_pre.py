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

    def get_href_url(self, element: str):
        if element.startswith("us-gaap"):
            return "https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd"
        if element.startswith("dei"):
            return "https://xbrl.sec.gov/dei/2023/dei-2023.xsd"
        if element.startswith("srt"):
            return "https://xbrl.fasb.org/srt/2023/elts/srt-2023.xsd"
        if element.startswith(self.ticker):
            return f"{self.ticker}-{self.filing_date}.xsd"

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

    def generate_elements_xml(self, role_data, presentation_links, presentation_link):
        # main elements
        elements_list: list = []
        pre_element_parent_created = False

        for index, record in enumerate(role_data, start=1):
            order = record.get("Indenting")
            label = record.get("PreferredLabel")

            _element: str = record.get("Element")
            element = _element.replace("--", "_")

            label_type = record.get("PreferredLabelType")
            preferred_label = self.get_preferred_label(label_type)

            _pre_element_parent: str = record.get("PreElementParent")
            pre_element_parent = _pre_element_parent.replace(":", "_")

            _line_item: str = record.get("LineItem")
            line_item = _line_item.replace("--", "_")
            if pre_element_parent_created is False:
                # pre parent element
                pre_element_parent_xlink_href = self.get_href_url(pre_element_parent)
                pre_element_parent_loc = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{pre_element_parent}",
                    xlink_href=f"{pre_element_parent_xlink_href}#{pre_element_parent}",
                )

                # Add definition arc elements
                definition_arc = self.create_presentation_arc_element(
                    parent_tag=presentation_link,
                    order=str(index),
                    arc_role="http://xbrl.org/int/dim/arcrole/domain-member",
                    xlink_from=f"loc_{line_item}",
                    xlink_to=f"loc_{pre_element_parent}",
                )

                pre_element_parent_created = True

            if element not in elements_list:
                # main elements
                if element.startswith(self.ticker):
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

                # Common arguments for create_presentation_arc_element
                arc_args = {
                    "parent_tag": presentation_link,
                    "order": str(index),
                    "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                    "xlink_from": f"loc_{pre_element_parent}",
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
        # iterate through dimension records
        for index, record in enumerate(dimension_records):
            _table = record.get("Table")
            if _table:
                table = _table.replace("--", "_")

            order = record.get("Indenting")
            axis_members: str = record.get("Axis_Member")

            _line_item: str = record.get("LineItem")
            line_item = _line_item.replace("--", "_")

            label = record.get("PreferredLabel")
            label_type = record.get("PreferredLabelType")
            preferred_label = self.get_preferred_label(label_type)

            if is_table_loc_created is False:
                # table location
                table_xlink_href = href_url = self.get_href_url(table)
                table_loc = self.create_presentation_loc_element(
                    parent_tag=presentation_link,
                    label=f"loc_{table}",
                    xlink_href=f"{table_xlink_href}#{table}",
                )

                # Common arguments for create_presentation_arc_element
                arc_args = {
                    "parent_tag": presentation_link,
                    "order": order,
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
                axis = _axis.replace("--", "_")
                domain = _domain.replace("--", "_")
                member = _member.replace("--", "_")

                dimension_record = (axis, domain, member)
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
                        "order": order,
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
                        "order": order,
                        "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                        "xlink_from": f"loc_{axis}",
                        "xlink_to": f"loc_{domain}",
                    }

                    # Create presentationArc element and append it to presentation_links list.
                    presentation_arc = self.create_presentation_arc_element(**arc_args)

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
                        "order": order,
                        "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                        "xlink_from": f"loc_{domain}",
                        "xlink_to": f"loc_{member}",
                    }

                    # Create presentationArc element and append it to presentation_links list.
                    presentation_arc = self.create_presentation_arc_element(**arc_args)

                    dimension_records_list.append(dimension_record)

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
                    "order": order,
                    "arc_role": "http://www.xbrl.org/2003/arcrole/parent-child",
                    "xlink_from": f"loc_{table}",
                    "xlink_to": f"loc_{line_item}",
                }

                # Create presentationArc element and append it to presentation_links list.
                presentation_arc = self.create_presentation_arc_element(**arc_args)

        # generate mail element xml
        self.generate_elements_xml(role_data, presentation_links, presentation_link)

    def check_role_is_dimension_or_not(self, role_data):
        # Flag variable to track if any Axis_Member has a value
        records: list = []
        elements_list: list = []

        # Check if any Axis_Member has a value
        for item in role_data:
            if item["Axis_Member"]:
                element = item["Element"]
                if element not in elements_list:
                    elements_list.append(element)
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

            _root_level_abstract: str = record.get("RootLevelAbstract")
            root_level_abstract = _root_level_abstract.replace("--", "_")

            # Create roleRef element and append it to role_ref_elements list.
            role_ref_element = self.create_role_ref_element(
                role_uri=f"{self.company_website}/{self.filing_date}/role/{role_name}",
                xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{role_name}",
            )

            _line_item: str = record.get("LineItem")
            line_item = _line_item.replace("--", "_")

            role_ref_elements.append(role_ref_element)

            # Create presentationLink element and append it to presentation_links list.
            presentation_link = ET.Element(
                "link:presentationLink",
                attrib={
                    "xlink:role": f"{self.company_website}/role/{role_name}",
                    "xlink:type": "extended",
                },
            )
            # Create presentation loc elements for root_level_abstract and element.
            root_level_abstract_loc = self.create_presentation_loc_element(
                parent_tag=presentation_link,
                label=f"loc_{root_level_abstract}",
                xlink_href=f"https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd#{root_level_abstract}",
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
            # if role is not dimension
            else:
                self.generate_elements_xml(
                    role_data, presentation_links, presentation_link
                )

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
