import re
from itertools import groupby
import xml.etree.ElementTree as ET


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

    def create_role_ref_element(self, parent=None, role_uri=None, xlink_href=None):
        # Create a roleRef element with specified attributes
        return ET.SubElement(
            parent,
            "link:roleRef",
            attrib={
                "roleURI": f"http://{role_uri}",
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

    def get_href_url(self, element: str):
        if element.startswith("us-gaap"):
            return "https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd"
        if element.startswith("dei"):
            return "https://xbrl.sec.gov/dei/2023/dei-2023.xsd"
        if element.startswith("srt"):
            return "https://xbrl.fasb.org/srt/2023/elts/srt-2023.xsd"
        if element.startswith(self.ticker):
            return f"{self.ticker}-{self.filing_date}.xsd"

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

    def get_arcrole_refs_xml(self, parent):
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
            arcrole_ref = ET.SubElement(
                parent,
                "link:arcroleRef",
                arcroleURI=arcrole_ref_data["arcroleURI"],
                **{
                    "xlink:type": "simple",
                    "xlink:href": arcrole_ref_data["xlink:href"],
                },
            )
            arcrole_ref_elements.append(arcrole_ref)

        arcrole_ref_elements_xml = "\n".join(
            [ET.tostring(e, encoding="utf-8").decode() for e in arcrole_ref_elements]
        )
        return arcrole_ref_elements_xml

    # Function to check if all Axis_Member are empty
    def are_all_axis_member_empty(self, json_data):
        for item in json_data:
            if item["Axis_Member"] != "":
                return False
        return True

    def generate_def_xml(self):

        role_ref_elements = []
        definition_links = []  # List to store presentationLink elements.

        tables_list = []
        line_items_list = []
        dimension_records_list = []
        pre_element_parent_created = False

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

        self.get_arcrole_refs_xml(linkbase_element)

        # Iterate through grouped data and create roleRef and presentationLink elements
        for role_name, role_data in self.grouped_data.items():

            # Check if all Axis_Member are empty
            all_empty = self.are_all_axis_member_empty(role_data)
            if all_empty:
                pass
            else:
                role_without_spaces = re.sub(r"\s+", "", role_name)
                # Create roleRef element and append it to role_ref_elements list.
                role_ref_element = self.create_role_ref_element(
                    parent=linkbase_element,
                    role_uri=f"{self.company_website}/{self.filing_date}/role/{role_without_spaces}",
                    xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{role_without_spaces}",
                )

                role_ref_elements.append(role_ref_element)

                # Create definitionLink root element
                definition_link = ET.SubElement(
                    linkbase_element,
                    "link:definitionLink",
                    attrib={
                        "xlink:role": f"http://{self.company_website}/role/{role_without_spaces}",
                        "xlink:type": "extended",
                    },
                )

                for index, record in enumerate(role_data, start=1):
                    role = record.get("RoleName")

                    _table = record.get("Table")
                    table = _table.replace("--", "_")

                    _element = record.get("Element")
                    element = _element.replace("--", "_")

                    label = record.get("PreferredLabel")
                    order = record.get("Indenting")

                    _root_level_abstract = record.get("RootLevelAbstract")
                    root_level_abstract = _root_level_abstract.replace("--", "_")

                    _line_item: str = record.get("LineItem")
                    line_item = _line_item.replace("--", "_")

                    _pre_element_parent: str = record.get("PreElementParent")
                    pre_element_parent = _pre_element_parent.replace("--", "_")

                    axis_members: str = record.get("Axis_Member")

                    # if Axis_Member exists create entry in def XML
                    if axis_members:
                        if line_item not in line_items_list:
                            # line item location
                            line_item_xlink_href = self.get_href_url(line_item)
                            line_item_loc = self.create_definition_loc_element(
                                parent_tag=definition_link,
                                label=f"loc_{line_item}",
                                xlink_href=f"{line_item_xlink_href}#{line_item}",
                            )
                            line_items_list.append(line_item)

                        if table not in tables_list:
                            # table
                            table_xlink_href = self.get_href_url(table)
                            table_loc = self.create_definition_loc_element(
                                parent_tag=definition_link,
                                label=f"loc_{table}",
                                xlink_href=f"{table_xlink_href}#{table}",
                            )

                            # Common arguments for create_presentation_arc_element
                            arc_args = {
                                "parent_tag": definition_link,
                                "arc_role": "http://xbrl.org/int/dim/arcrole/all",
                                "xlink_from": f"loc_{line_item}",
                                "xlink_to": f"loc_{table}",
                                "order": order,
                            }

                            # Add definition arc elements
                            definition_arc = self.create_definition_arc_element(
                                **arc_args
                            )
                            tables_list.append(table)

                            splitted = axis_members.split("__")

                            # Group by 3
                            groups = [
                                splitted[i : i + 3] for i in range(0, len(splitted), 3)
                            ]
                            for group in groups:
                                _axis, _domain, _member = group
                                axis = _axis.replace("--", "_")
                                domain = _domain.replace("--", "_")
                                member = _member.replace("--", "_")

                                dimension_record = (axis, domain, member)
                                if dimension_record not in dimension_records_list:

                                    # axis
                                    axis_xlink_href = self.get_href_url(axis)
                                    axis_loc = self.create_definition_loc_element(
                                        parent_tag=definition_link,
                                        label=f"loc_{axis}",
                                        xlink_href=f"{axis_xlink_href}#{axis}",
                                    )

                                    # Common arguments for create_presentation_arc_element
                                    arc_args = {
                                        "parent_tag": definition_link,
                                        "arc_role": "http://xbrl.org/int/dim/arcrole/hypercube-dimension",
                                        "xlink_from": f"loc_{line_item}",
                                        "xlink_to": f"loc_{axis}",
                                        "order": order,
                                    }

                                    # Add definition arc elements
                                    definition_arc = self.create_definition_arc_element(
                                        **arc_args
                                    )

                                    # domain dimension-default
                                    domain_xlink_href = self.get_href_url(domain)
                                    domain_loc = self.create_definition_loc_element(
                                        parent_tag=definition_link,
                                        label=f"loc_{domain}_1",
                                        xlink_href=f"{domain_xlink_href}#{domain}",
                                    )

                                    # Common arguments for create_presentation_arc_element
                                    arc_args = {
                                        "parent_tag": definition_link,
                                        "arc_role": "http://xbrl.org/int/dim/arcrole/dimension-default",
                                        "xlink_from": f"loc_{axis}",
                                        "xlink_to": f"loc_{domain}",
                                        "order": order,
                                    }

                                    # Add definition arc elements
                                    definition_arc = self.create_definition_arc_element(
                                        **arc_args
                                    )

                                    # domain dimension-domain
                                    domain_xlink_href = self.get_href_url(domain)
                                    domain_loc = self.create_definition_loc_element(
                                        parent_tag=definition_link,
                                        label=f"loc_{domain}",
                                        xlink_href=f"{domain_xlink_href}#{domain}",
                                    )

                                    # Common arguments for create_presentation_arc_element
                                    arc_args = {
                                        "parent_tag": definition_link,
                                        "arc_role": "http://xbrl.org/int/dim/arcrole/dimension-domain",
                                        "xlink_from": f"loc_{axis}",
                                        "xlink_to": f"loc_{domain}",
                                        "order": order,
                                    }

                                    # Add definition arc elements
                                    definition_arc = self.create_definition_arc_element(
                                        **arc_args
                                    )

                                    # member
                                    member_xlink_href = self.get_href_url(member)
                                    member_loc = self.create_definition_loc_element(
                                        parent_tag=definition_link,
                                        label=f"loc_{member}",
                                        xlink_href=f"{member_xlink_href}#{member}",
                                    )

                                    # Common arguments for create_presentation_arc_element
                                    arc_args = {
                                        "parent_tag": definition_link,
                                        "arc_role": "http://xbrl.org/int/dim/arcrole/domain-member",
                                        "xlink_from": f"loc_{domain}",
                                        "xlink_to": f"loc_{member}",
                                        "order": order,
                                    }

                                    # Add definition arc elements
                                    definition_arc = self.create_definition_arc_element(
                                        **arc_args
                                    )

                                    dimension_records_list.append(dimension_record)

                        # check pre element parent is created or not
                        if pre_element_parent_created is False:
                            # pre parent element
                            pre_element_parent_xlink_href = self.get_href_url(
                                pre_element_parent
                            )
                            pre_element_parent_loc = self.create_definition_loc_element(
                                parent_tag=definition_link,
                                label=f"loc_{pre_element_parent}",
                                xlink_href=f"{pre_element_parent_xlink_href}#{pre_element_parent}",
                            )

                            # Add definition arc elements
                            definition_arc = self.create_definition_arc_element(
                                parent_tag=definition_link,
                                order=str(index),
                                arc_role="http://xbrl.org/int/dim/arcrole/domain-member",
                                xlink_from=f"loc_{line_item}",
                                xlink_to=f"loc_{pre_element_parent}",
                            )

                            pre_element_parent_created = True

                        # main elements
                        element_xlink_href = self.get_href_url(element)
                        element_loc = self.create_definition_loc_element(
                            parent_tag=definition_link,
                            label=f"loc_{element}",
                            xlink_href=f"{element_xlink_href}#{element}",
                        )

                        # Add definition arc elements
                        definition_arc = self.create_definition_arc_element(
                            parent_tag=definition_link,
                            order=str(index),
                            arc_role="http://xbrl.org/int/dim/arcrole/domain-member",
                            xlink_from=f"loc_{pre_element_parent}",
                            xlink_to=f"loc_{element}",
                        )

                    definition_links.append(definition_link)

        # Create an XML declaration
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'

        # Comments after the XML declaration
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            "<!-- Creation Date : -->",
            "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
        ]

        # Concatenate XML declaration, comments, and linkbase element
        xml_data = (
            xml_declaration
            + "\n".join(comments_after_declaration)
            + "\n"
            + ET.tostring(linkbase_element, encoding="utf-8").decode()
        )

        self.save_xml_data(xml_data)

    def save_xml_data(self, xml_data):
        # Save the XML data into the pre.xml file.
        filename = f"{self.ticker}-{self.filing_date}_def.xml"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(xml_data)


# ticker = "msft"
# filing_date = "20230630"
# data = html_elements_data
# company_website = "http://www.microsoft.com"

# # Example usage
# data = html_elements_data  # Assuming html_elements_data is defined
# generator = DefXMLGenerator(data, ticker, filing_date, company_website)
# generator.generate_def_xml()
