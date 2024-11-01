import re, os
from datetime import datetime

from typing import Dict
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml_generation.labels import labels_dict


class CalXMLGenerator:
    def __init__(
        self, data, filing_date, ticker, company_website, client_id, taxonomy_year
    ):
        # Initialize the CalXMLGenerator with data, filing_date, ticker, and company_website.
        self.data = data
        self.filing_date = filing_date
        self.ticker = ticker
        self.company_website = company_website
        self.client_id = client_id
        self.taxonomy_year = taxonomy_year
        self.output_file = f"data/{self.ticker}-{self.filing_date}/{self.ticker}-{self.filing_date}_cal.xml"
        # Dictionary to store grouped data by RoleName.
        self.grouped_data: dict[str, list] = {}

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

    def group_data_by_cal_parent(self, data):
        cal_parent_grouped_data: Dict[str, list] = {}

        for record in data:
            cal_parent = record.get("CalculationParent")
            if cal_parent:
                if cal_parent not in cal_parent_grouped_data.keys():
                    cal_parent_grouped_data[cal_parent] = []
                    cal_parent_grouped_data[cal_parent].append(record)
                else:
                    cal_parent_grouped_data[cal_parent].append(record)

        return cal_parent_grouped_data

    def create_role_ref_element(self, parent=None, role_uri=None, xlink_href=None):
        return ET.SubElement(
            parent,
            "link:roleRef",
            attrib={
                "roleURI": role_uri,
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
                    role_without_spaces = (
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
                    role_uri = f"http://{self.company_website}/{self.filing_date}/role/{role_without_spaces}"
                    role_ref_element = self.create_role_ref_element(
                        parent=linkbase_element,
                        role_uri=role_uri,
                        xlink_href=f"{self.ticker}-{self.filing_date}.xsd#{role_without_spaces}",
                    )
                    role_ref_elements.append(role_ref_element)

                    calculation_link = ET.SubElement(
                        linkbase_element,
                        "link:calculationLink",
                        attrib={
                            "xlink:role": role_uri,
                            "xlink:type": "extended",
                        },
                    )

                    # group the by role data based on the calculation parent
                    data = self.group_data_by_cal_parent(role_data)

                    calculation_parents = []
                    cal_parent_Children = []
                    element_occurrences = {}

                    parent_index = 1
                    for cp_index, (cal_parent, children) in enumerate(
                        data.items(), start=1
                    ):
                        # if calculation is exits create entry in cal XML
                        if cal_parent:

                            _calculation_parent = cal_parent
                            calculation_parent = _calculation_parent.replace(
                                "--", "_"
                            ).replace("custom", self.ticker)

                            # calculation parent
                            calculation_parent_href = self.get_href_url(
                                calculation_parent
                            )

                            if calculation_parent in cal_parent_Children:
                                calculation_parent_loc = self.create_calculation_loc_element(
                                    parent_tag=calculation_link,
                                    # label=f"loc_{calculation_parent}_{role_index}",
                                    label=f"loc_{calculation_parent}_1",
                                    xlink_href=f"{calculation_parent_href}#{calculation_parent}",
                                )
                            else:
                                calculation_parent_loc = self.create_calculation_loc_element(
                                    parent_tag=calculation_link,
                                    # label=f"loc_{calculation_parent}_{role_index}",
                                    label=f"loc_{calculation_parent}",
                                    xlink_href=f"{calculation_parent_href}#{calculation_parent}",
                                )

                            # loop all cal parent children and create loc, and arc elements
                            children_index = 1
                            for index, record in enumerate(children, start=1):

                                _element = record.get("Element")
                                calculation_weight = record.get("CalculationWeight")
                                element = _element.replace("--", "_").replace(
                                    "custom", self.ticker
                                )

                                if element not in cal_parent_Children:
                                    if element in calculation_parents:
                                        # element
                                        element_href = self.get_href_url(element)
                                        element_loc = (
                                            self.create_calculation_loc_element(
                                                parent_tag=calculation_link,
                                                label=f"loc_{element}_1",
                                                xlink_href=f"{element_href}#{element}",
                                            )
                                        )
                                    else:
                                        # element
                                        element_href = self.get_href_url(element)
                                        element_loc = self.create_calculation_loc_element(
                                            parent_tag=calculation_link,
                                            # label=f"loc_{element}_{index+1}",
                                            label=f"loc_{element}",
                                            xlink_href=f"{element_href}#{element}",
                                        )

                                    # xlink_from = f"{calculation_parent}_{parent_index}"
                                    if calculation_parent in cal_parent_Children:
                                        xlink_from = f"{calculation_parent}_1"
                                    else:
                                        xlink_from = f"{calculation_parent}"

                                    # calculate xlink from element element occurrence
                                    if xlink_from not in element_occurrences:
                                        element_occurrences[xlink_from] = 1
                                    else:
                                        element_occurrences[xlink_from] = (
                                            element_occurrences[xlink_from] + 1
                                        )

                                    if element in calculation_parents:
                                        xlink_to = f"loc_{element}_1"
                                    else:
                                        xlink_to = f"loc_{element}"

                                    # Add calculation arc elements
                                    calculation_arc = self.create_calculation_arc_element(
                                        parent_tag=calculation_link,
                                        order=str(element_occurrences.get(xlink_from)),
                                        weight=calculation_weight,
                                        arc_role="http://www.xbrl.org/2003/arcrole/summation-item",
                                        xlink_from=f"loc_{xlink_from}",
                                        # xlink_to=f"loc_{element}_{index+1}",
                                        xlink_to=xlink_to,
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

        # Get current date and time with AM/PM
        current_datetime = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        comments_after_declaration = [
            "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
            f"<!-- Creation Date : {current_datetime} -->",
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

# # Example usage
# generator = CalXMLGenerator(data, filing_date, ticker, company_website)
# xml_data = generator.generate_cal_xml()
