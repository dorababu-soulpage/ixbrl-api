import re
from itertools import groupby
import xml.etree.ElementTree as ET
from xml_generation.labels import labels_dict


class CalXMLGenerator:
    def __init__(self, data, filing_date, ticker, company_website):
        # Initialize the CalXMLGenerator with data, filing_date, ticker, and company_website.
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

    def group_data_by_cal_parent(self, data):
        cal_parent_grouped_data = {}
        # Group the data by RoleName using itertools groupby and store it in grouped_data.
        for key, group in groupby(data, key=lambda x: x["CalculationParent"]):
            cal_parent_grouped_data[key] = [
                dict(t) for t in {tuple(d.items()) for d in list(group)}
            ]
        return cal_parent_grouped_data

    def create_role_ref_element(self, parent=None, role_uri=None, xlink_href=None):
        return ET.SubElement(
            parent,
            "link:roleRef",
            attrib={
                "roleURI": f"http://{role_uri}",
                "xlink:href": xlink_href,
                "xlink:type": "simple",
            },
        )

    def create_calculation_loc_element(
        self, parent_tag=None, label=None, xlink_href=None
    ):
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

    def create_calculation_arc_element(
        self,
        parent_tag=None,
        order=None,
        weight=None,
        arc_role=None,
        xlink_from=None,
        xlink_to=None,
    ):
        return ET.SubElement(
            parent_tag,
            "link:calculationArc",
            attrib={
                "order": order,
                "weight": weight,
                "xlink:arcrole": arc_role,
                "xlink:from": xlink_from,
                "xlink:to": xlink_to,
                "xlink:type": "arc",
            },
        )

    def add_role_ref_element(self, parent, role_uri, xlink_href):
        role_ref_element = self.create_role_ref_element(parent, role_uri, xlink_href)
        self.role_ref_elements.append(role_ref_element)

        # Function to check if all Axis_Member are empty

    def are_all_cal_parents_empty(self, json_data):
        for item in json_data:
            if item["CalculationParent"] != "":
                return False
        return True

    def generate_cal_xml(self):
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
        calculation_links = []  # List to store calculationLink elements.

        # Iterate through grouped data and create roleRef and presentationLink elements.
        for role_index, (role_name, role_data) in enumerate(
            self.grouped_data.items(), start=1
        ):
            # Check if all cal parents are empty
            all_empty = self.are_all_cal_parents_empty(role_data)
            if all_empty:
                pass
            else:
                if role_name:
                    role_without_spaces = re.sub(r"\s+", "", role_name)

                    # Create roleRef element and append it to role_ref_elements list.
                    role_ref_element = self.create_role_ref_element(
                        parent=linkbase_element,
                        role_uri=f"{self.company_website}/{self.filing_date}/role/{role_without_spaces}",
                        xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{role_without_spaces}",
                    )
                    role_ref_elements.append(role_ref_element)

                    calculation_link = ET.SubElement(
                        linkbase_element,
                        "link:calculationLink",
                        attrib={
                            "xlink:role": f"http://{self.company_website}/role/{role_without_spaces}",
                            "xlink:type": "extended",
                        },
                    )

                    # group the by role data based on the calculation parent
                    data = self.group_data_by_cal_parent(role_data)

                    calculation_parents = []
                    cal_parent_Children = []

                    parent_index = 1
                    for cp_index, (cal_parent, children) in enumerate(
                        data.items(), start=1
                    ):
                        # if calculation is exits create entry in cal XML
                        if cal_parent:

                            _calculation_parent = cal_parent
                            calculation_parent = _calculation_parent.replace("--", "_")

                            # calculation parent
                            calculation_parent_href = self.get_href_url(
                                calculation_parent
                            )
                            calculation_parent_loc = self.create_calculation_loc_element(
                                parent_tag=calculation_link,
                                label=f"loc_{calculation_parent}_{role_index}",
                                xlink_href=f"{calculation_parent_href}#{calculation_parent}",
                            )
                            # loop all cal parent children and create loc, and arc elements
                            children_index = 1
                            for index, record in enumerate(children, start=1):

                                _element = record.get("Element")
                                element = _element.replace("--", "_")

                                if element not in cal_parent_Children:

                                    if element in calculation_parents:
                                        element_label = f"loc_{element}_{index+1}"
                                    else:
                                        element_label = f"loc_{element}"

                                    # element
                                    element_href = self.get_href_url(element)
                                    element_loc = self.create_calculation_loc_element(
                                        parent_tag=calculation_link,
                                        label=element_label,
                                        xlink_href=f"{element_href}#{element}",
                                    )

                                    # Add calculation arc elements
                                    calculation_arc = self.create_calculation_arc_element(
                                        parent_tag=calculation_link,
                                        order=str(index),
                                        weight="1",
                                        arc_role="http://www.xbrl.org/2003/arcrole/summation-item",
                                        xlink_from=f"loc_{calculation_parent}_{children_index}",
                                        xlink_to=element_label,
                                    )
                                    calculation_parents.append(calculation_parent)
                                    cal_parent_Children.append(element)
                                    # increment the children index
                                    children_index += 1

                            calculation_links.append(calculation_link)

                        # increment the parent index
                        parent_index += 1

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
        # Save the XML data into the pre.xml file.
        filename = f"{self.ticker}-{self.filing_date}_cal.xml"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(xml_data)


# # Usage example:
# ticker = "msft"
# filing_date = "20230630"
# data = html_elements_data
# company_website = "http://www.microsoft.com"

# # Example usage
# generator = CalXMLGenerator(data, filing_date, ticker, company_website)
# xml_data = generator.generate_cal_xml()
