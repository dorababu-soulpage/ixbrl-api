import re, os
from datetime import datetime
from itertools import groupby

from xml.dom import minidom
import xml.etree.ElementTree as ET


class DefXMLGenerator:
    def __init__(
        self,
        data,
        ticker,
        filing_date,
        company_website,
        client_id,
        elements_data,
        taxonomy_year,
    ):
        # Initialize the DefXMLGenerator with provided data and metadata
        self.data = data
        self.ticker = ticker
        self.filing_date = filing_date
        self.company_website = company_website
        self.client_id = client_id
        self.taxonomy_year = taxonomy_year
        self.output_file = f"data/{self.ticker}-{self.filing_date}/{self.ticker}-{self.filing_date}_def.xml"
        self.grouped_data = self.group_data_by_role()
        self.elements_data = elements_data

    def group_data_by_role(self):
        # Group data by RoleName using itertools.groupby
        grouped_data: dict[str, list] = {}
        for record in self.data:
            role_name = record["RoleName"]
            if role_name in grouped_data.keys():
                grouped_data[role_name].append(record)
            else:
                grouped_data[role_name] = [record]
        return grouped_data

    def create_role_ref_element(self, parent=None, role_uri=None, xlink_href=None):
        # Create a roleRef element with specified attributes
        return ET.SubElement(
            parent,
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

    def get_href_url(self, element: str):
        if element.startswith(self.ticker):
            return f"{self.ticker}-{self.filing_date}.xsd"

        if element.startswith("country"):
            return f"https://xbrl.sec.gov/country/{self.taxonomy_year}/country-{self.taxonomy_year}.xsd"

        if element.startswith("dei"):
            return f"https://xbrl.sec.gov/dei/{self.taxonomy_year}/dei-{self.taxonomy_year}.xsd"

        if element.startswith("sic"):
            return f"https://xbrl.sec.gov/sic/{self.taxonomy_year}/sic-{self.taxonomy_year}.xsd"

        if element.startswith("exch"):
            return f"https://xbrl.sec.gov/exch/{self.taxonomy_year}/exch-{self.taxonomy_year}.xsd"

        if element.startswith("stpr"):
            return f"https://xbrl.sec.gov/stpr/{self.taxonomy_year}/stpr-{self.taxonomy_year}.xsd"

        if element.startswith("naics"):
            return f"https://xbrl.sec.gov/naics/{self.taxonomy_year}/naics-{self.taxonomy_year}.xsd"

        if element.startswith("srt"):
            return f"https://xbrl.fasb.org/srt/{self.taxonomy_year}/elts/srt-{self.taxonomy_year}.xsd"

        if element.startswith("currency"):
            return f"https://xbrl.sec.gov/currency/{self.taxonomy_year}/currency-{self.taxonomy_year}.xsd"

        if element.startswith("us-gaap"):
            return f"https://xbrl.fasb.org/us-gaap/{self.taxonomy_year}/elts/us-gaap-{self.taxonomy_year}.xsd"

    def create_definition_arc_element(
        self, parent_tag=None, order=None, arc_role=None, xlink_from=None, xlink_to=None
    ):
        attributes = {
            "xlink:arcrole": arc_role,
            "xlink:from": xlink_from,
            "xlink:to": xlink_to,
            "xlink:type": "arc",
            "order": order,
        }

        if arc_role in [
            "http://xbrl.org/int/dim/arcrole/all",
            "http://xbrl.org/int/dim/arcrole/dimension-default",
        ]:
            attributes["xbrldt:contextElement"] = "segment"

        # Create a definitionArc element with specified attributes
        return ET.SubElement(
            parent_tag,
            "link:definitionArc",
            attrib=attributes,
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

    # # Function to check if all Axis_Member are empty
    # def are_all_axis_member_empty(self, json_data):
    #     for item in json_data:
    #         if item["Axis_Member"]:
    #             return False
    #     return True

    def check_role_is_dimension_or_not(self, role_data):
        # Flag variable to track if any Axis_Member has a value
        # Check if any Axis_Member has a value
        for item in role_data:
            if item["Axis_Member"]:
                # records.append(item)
                return True

    def generate_def_xml(self):

        role_ref_elements = []
        definition_links = []  # List to store presentationLink elements.

        tables_list = []
        line_items_list = []
        pre_element_parent_created = False
        # is_table_loc_created = False

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

            is_line_item_created = False
            is_table_loc_created = False
            dimension_records_list = []
            axis_list = []
            members_list = []
            member_order = 1
            main_element_list = []
            # main elements
            elements_list: list = []

            # Check if all Axis_Member are empty or not
            is_dimension_role = self.check_role_is_dimension_or_not(role_data)

            if is_dimension_role:
                role_without_spaces = re.sub(r"\s+", "", role_name)
                role = (
                    role_without_spaces.replace("(", "")
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
                # Create roleRef element and append it to role_ref_elements list.
                role_uri = (
                    f"http://{self.company_website}/{self.filing_date}/role/{role}"
                )
                role_ref_element = self.create_role_ref_element(
                    parent=linkbase_element,
                    role_uri=role_uri,
                    xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{role}",
                )

                role_ref_elements.append(role_ref_element)

                # Create definitionLink root element
                definition_link = ET.SubElement(
                    linkbase_element,
                    "link:definitionLink",
                    attrib={
                        "xlink:role": role_uri,
                        "xlink:type": "extended",
                    },
                )

                for record in role_data:
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

                    if line_item and is_line_item_created is False:
                        # line item location
                        line_item_xlink_href = self.get_href_url(line_item)
                        line_item_loc = self.create_definition_loc_element(
                            parent_tag=definition_link,
                            label=f"loc_{line_item}",
                            xlink_href=f"{line_item_xlink_href}#{line_item}",
                        )
                        line_items_list.append(line_item)
                        is_line_item_created = True

                    if table and is_table_loc_created is False:
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
                            "order": "1",
                        }

                        # Add definition arc elements
                        definition_arc = self.create_definition_arc_element(**arc_args)
                        tables_list.append(table)

                        is_table_loc_created = True

                    if axis_members:
                        splitted = axis_members.split("__")

                        # Group by 3
                        groups = [
                            splitted[i : i + 3] for i in range(0, len(splitted), 3)
                        ]
                        for group in groups:
                            _axis, _domain, _member = group
                            axis = _axis.replace("--", "_").replace(
                                "custom", self.ticker
                            )
                            domain = _domain.replace("--", "_").replace(
                                "custom", self.ticker
                            )
                            member = _member.replace("--", "_").replace(
                                "custom", self.ticker
                            )

                            dimension_record = (axis, domain)
                            if dimension_record not in dimension_records_list:
                                if axis not in axis_list:

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
                                        # "xlink_from": f"loc_{line_item}",
                                        "xlink_from": f"loc_{table}",
                                        "xlink_to": f"loc_{axis}",
                                        "order": "1",
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
                                        "xlink_to": f"loc_{domain}_1",
                                        "order": "1",
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
                                        "order": "1",
                                    }

                                    # Add definition arc elements
                                    definition_arc = self.create_definition_arc_element(
                                        **arc_args
                                    )
                                    axis_list.append(axis)

                                dimension_records_list.append(dimension_record)

                            if member not in members_list:
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
                                    "order": str(member_order),
                                }

                                # Add definition arc elements
                                definition_arc = self.create_definition_arc_element(
                                    **arc_args
                                )
                                members_list.append(member)
                                member_order += 1

                            # add dimension record
                            main_element_list.append(record)
                    else:
                        main_element_list.append(record)

                initial_record = None
                for record in role_data:

                    heading = record.get("Heading")
                    if heading:
                        continue
                    else:
                        initial_record = record
                        break

                root_level_abstract = initial_record.get("RootLevelAbstract")
                _pre_element_parent: str = initial_record.get("PreElementParent")

                # root level abstract and pre element parent is same don't create pre element parent
                # consider root level abstract as a pre element parent

                # pre parent element
                if root_level_abstract != _pre_element_parent:
                    pre_element_parent = _pre_element_parent.replace("--", "_")
                    if pre_element_parent and pre_element_parent_created is False:
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
                            order="1",
                            arc_role="http://xbrl.org/int/dim/arcrole/domain-member",
                            xlink_from=f"loc_{line_items_list[-1]}",
                            xlink_to=f"loc_{pre_element_parent}",
                        )

                        pre_element_parent_created = True

                element_occurrences = {}
                # add main element to def XML
                for index, record in enumerate(main_element_list, start=1):
                    _element = record.get("Element")
                    if _element and _element not in elements_list:
                        element = _element.replace("--", "_")

                        _pre_element_parent: str = record.get("PreElementParent")
                        pre_element_parent = _pre_element_parent.replace("--", "_")

                        if element.startswith("custom"):
                            element = element.replace("custom", self.ticker)
                            element_loc = self.create_definition_loc_element(
                                parent_tag=definition_link,
                                label=f"loc_{element}",
                                xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{element}",
                            )
                        else:
                            element_xlink_href = self.get_href_url(element)
                            element_loc = self.create_definition_loc_element(
                                parent_tag=definition_link,
                                label=f"loc_{element}",
                                xlink_href=f"{element_xlink_href}#{element}",
                            )

                        # xlink_from = pre_element_parent
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

                        # Add definition arc elements
                        definition_arc = self.create_definition_arc_element(
                            parent_tag=definition_link,
                            order=str(element_occurrences.get(xlink_from)),
                            arc_role="http://xbrl.org/int/dim/arcrole/domain-member",
                            xlink_from=f"loc_{line_item}",
                            xlink_to=f"loc_{element}",
                        )

                        elements_list.append(_element)

                    definition_links.append(definition_link)

                # hidden line items
                if role_without_spaces in ["Cover", "DocumentandEntityInformation"]:

                    # EntityCentralIndexKey
                    element_xlink_href = self.get_href_url(
                        f"dei--EntityCentralIndexKey"
                    )
                    def_element_parent_loc = self.create_definition_loc_element(
                        parent_tag=definition_link,
                        label=f"loc_dei_EntityCentralIndexKey",
                        xlink_href=f"{element_xlink_href}#dei_EntityCentralIndexKey",
                    )
                    # Add definition arc elements
                    definition_arc = self.create_definition_arc_element(
                        parent_tag=definition_link,
                        order=str(element_occurrences.get(root_level_abstract) + 1),
                        arc_role="http://xbrl.org/int/dim/arcrole/domain-member",
                        xlink_from=f"loc_{line_item}".replace("--", "_"),
                        xlink_to=f"loc_dei_EntityCentralIndexKey",
                    )
                    element_occurrences[xlink_from] = (
                        element_occurrences[root_level_abstract] + 1
                    )
                    if self.elements_data:
                        for element in self.elements_data:
                            # if element not in main elements list, add element
                            if f"dei_{element}" not in main_element_list:
                                element_xlink_href = self.get_href_url(
                                    f"dei--{element}"
                                )
                                def_element_parent_loc = self.create_definition_loc_element(
                                    parent_tag=definition_link,
                                    label=f"loc_dei_{element}",
                                    xlink_href=f"{element_xlink_href}#dei_{element}",
                                )
                                # Add definition arc elements
                                definition_arc = self.create_definition_arc_element(
                                    parent_tag=definition_link,
                                    order=str(
                                        element_occurrences.get(root_level_abstract) + 1
                                    ),
                                    arc_role="http://xbrl.org/int/dim/arcrole/domain-member",
                                    xlink_from=f"loc_{line_item}".replace("--", "_"),
                                    xlink_to=f"loc_dei_{element}",
                                )

                                element_occurrences[xlink_from] = (
                                    element_occurrences[root_level_abstract] + 1
                                )

        # Create an XML declaration
        xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'

        # Get current date and time with AM/PM
        current_datetime = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        # Comments after the XML declaration
        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            f"<!-- Creation Date : {current_datetime} -->",
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


# ticker = "msft"
# filing_date = "20230630"
# data = html_elements_data
# company_website = "http://www.microsoft.com"

# # Example usage
# data = html_elements_data  # Assuming html_elements_data is defined
# generator = DefXMLGenerator(data, ticker, filing_date, company_website)
# generator.generate_def_xml()
