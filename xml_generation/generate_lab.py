from itertools import groupby
from labels import labels_dict
import xml.etree.ElementTree as ET
from database import html_elements_data


class LabXMLGenerator:
    def __init__(self, data, filing_date, ticker, company_website):
        # Initialize the LabXMLGenerator with data, filing_date, ticker, and company_website.
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
        return ET.Element(
            "link:roleRef",
            attrib={
                "roleURI": role_uri,
                "xlink:type": "simple",
                "xlink:href": xlink_href,
            },
        )

    def create_label_element(
        self, parent_tag=None, id=None, xlink_label=None, xlink_role=None
    ):
        if xlink_role is None:
            xlink_role = "http://www.xbrl.org/2003/role/label"
        label_element = ET.SubElement(
            parent_tag,
            "link:label",
            attrib={
                "id": id,
                "xlink:label": xlink_label,
                "xlink:role": xlink_role,
                "xlink:type": "resource",
                "xml:lang": "en-US",
            },
        )
        label_element.text = xlink_label
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

    def add_role_ref_elements(self):
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
                role_uri=f"http://www.xbrl.org/2009/role/{label}",
                xlink_href=href,
            )
            role_ref_elements.append(role_ref_element)

        return role_ref_elements

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

        # Group data by RoleName.
        self.group_data_by_role()

        # add role ref elements
        role_ref_elements = self.add_role_ref_elements()

        elements: list[str] = []
        axis_members_list: list[str] = []
        pre_element_parents_list: list[str] = []
        calculation_parents_list: list[str] = []

        # Iterate through grouped data and create roleRef and presentationLink elements.
        for role_name, role_data in self.grouped_data.items():
            record: dict = role_data[0] | {}

            _root_level_abstract: str = record.get("RootLevelAbstract", "")
            root_level_abstract = _root_level_abstract.replace("--", "_")

            _table = record.get("Table", "")
            table = _table.replace("--", "_")

            _line_item: str = record.get("LineItem", "")
            line_item = _line_item.replace("--", "_")

            label_link = ET.Element(
                "link:labelLink",
                attrib={
                    "xlink:role": "http://www.xbrl.org/2003/role/link",
                    "xlink:type": "extended",
                },
            )
            # root level abstract

            # Create label loc elements for root_level_abstract and element.
            href_url = self.get_href_url(root_level_abstract)
            root_level_abstract_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{root_level_abstract}",
                xlink_href=f"{href_url}#{root_level_abstract}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{root_level_abstract}",
                "xlink_to": f"lab_{root_level_abstract}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_{root_level_abstract}_label_en-US",
                xlink_label=root_level_abstract,
            )

            # table
            href_url = self.get_href_url(table)
            table_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{table}",
                xlink_href=f"{href_url}#{table}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{table}",
                "xlink_to": f"lab_{table}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_{table}_label_en-US",
                xlink_label=table,
            )

            # line item
            href_url = self.get_href_url(line_item)
            line_item_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{line_item}",
                xlink_href=f"{href_url}#{line_item}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{line_item}",
                "xlink_to": f"lab_{line_item}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_{line_item}_label_en-US",
                xlink_label=line_item,
            )

            # loop through the main elements
            for record in role_data:
                _element = record.get("Element", "")
                element = _element.replace("--", "_")

                axis_ember = record.get("Axis_Member", "")
                preElement_parent = record.get("PreElementParent", "")
                calculation_parent = record.get("CalculationParent", "")

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

                # create label
                self.create_label_element(
                    parent_tag=label_link,
                    id=f"lab_{element}_1_label_en-US",
                    xlink_label=element,
                )

                # create terseLabel
                self.create_label_element(
                    parent_tag=label_link,
                    id=f"lab_{element}_2_label_en-US",
                    xlink_label=element,
                    xlink_role="http://www.xbrl.org/2003/role/terseLabel",
                )
                elements.append(element)
                axis_members_list.append(axis_ember)
                calculation_parents_list.append(calculation_parent)
                pre_element_parents_list.append(preElement_parent)

        # add calculation parents
        for calculation_parent in calculation_parents_list:

            cal_parent = calculation_parent.replace("--", "_")

            if cal_parent not in elements:
                href_url = self.get_href_url(cal_parent)
                element_loc = self.create_label_loc_element(
                    parent_tag=label_link,
                    label=f"loc_{cal_parent}",
                    xlink_href=f"{href_url}#{cal_parent}",
                )

                # Common arguments for create_label_arc_element
                arc_args = {
                    "parent_tag": label_link,
                    "order": "1",
                    "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                    "xlink_from": f"loc_{cal_parent}",
                    "xlink_to": f"lab_{cal_parent}",
                }

                # Create presentationArc element and append it to presentation_links list.
                label_arc = self.create_label_arc_element(**arc_args)

                # create label
                self.create_label_element(
                    parent_tag=label_link,
                    id=f"lab_{cal_parent}_1_label_en-US",
                    xlink_label=cal_parent,
                )

                # create terseLabel
                self.create_label_element(
                    parent_tag=label_link,
                    id=f"lab_{cal_parent}_2_label_en-US",
                    xlink_label=cal_parent,
                    xlink_role="http://www.xbrl.org/2003/role/terseLabel",
                )

        # add pre element parents
        for pre_element_parent in set(pre_element_parents_list):
            pre_element_parent = pre_element_parent.replace("--", "_")

            href_url = self.get_href_url(pre_element_parent)
            element_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{pre_element_parent}",
                xlink_href=f"{href_url}#{pre_element_parent}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{pre_element_parent}",
                "xlink_to": f"lab_{pre_element_parent}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_{pre_element_parent}_label_en-US",
                xlink_label=pre_element_parent,
            )

        # add axis, domain, member
        for axis_member in set(axis_members_list):
            _axis, _domain, _member = axis_member.split("__")
            axis = _axis.replace("--", "_")
            domain = _domain.replace("--", "_")
            member = _member.replace("--", "_")

            # axis
            href_url = self.get_href_url(axis)
            element_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{axis}",
                xlink_href=f"{href_url}#{axis}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{axis}",
                "xlink_to": f"lab_{axis}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_{axis}_label_en-US",
                xlink_label=axis,
            )

            # domain
            href_url = self.get_href_url(domain)
            element_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{domain}",
                xlink_href=f"{href_url}#{domain}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{domain}",
                "xlink_to": f"loc_{domain}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_{domain}_label_en-US",
                xlink_label=domain,
            )

            # member
            href_url = self.get_href_url(member)
            element_loc = self.create_label_loc_element(
                parent_tag=label_link,
                label=f"loc_{member}",
                xlink_href=f"{href_url}#{member}",
            )

            # Common arguments for create_label_arc_element
            arc_args = {
                "parent_tag": label_link,
                "order": "1",
                "arc_role": "http://www.xbrl.org/2003/arcrole/concept-label",
                "xlink_from": f"loc_{member}",
                "xlink_to": f"loc_{member}",
            }

            # Create presentationArc element and append it to presentation_links list.
            label_arc = self.create_label_arc_element(**arc_args)

            # create label
            self.create_label_element(
                parent_tag=label_link,
                id=f"lab_{member}_label_en-US",
                xlink_label=member,
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

        # Combine XML elements
        xml_data = (
            xml_declaration
            + "\n".join(comments_after_declaration)
            + "\n"
            + ET.tostring(linkbase_element, encoding="utf-8").decode()
            + "\n"
            + role_ref_elements_xml
            + "\n"
            + ET.tostring(label_link, encoding="utf-8").decode()
        )
        self.save_xml_data(xml_data)

    def save_xml_data(self, xml_data):
        # Save the XML data into the pre.xml file.
        filename = f"{self.ticker}-{self.filing_date}_lab.xml"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(xml_data)


# Usage example:
ticker = "msft"
filing_date = "20230630"
data = html_elements_data
company_website = "http://www.microsoft.com"

# Instantiate the class
generator = LabXMLGenerator(data, filing_date, ticker, company_website)
generator.generate_lab_xml()
