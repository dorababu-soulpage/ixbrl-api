import random
import string
import json, os
import requests

import random, uuid
from datetime import datetime
from bs4 import BeautifulSoup, Comment

from utils import (
    get_db_record,
    get_split_file_record,
    extract_html_elements,
)

import html
from lxml import etree
from constants import namespace
from xml_generation.html_parser import HtmlTagParser
from xml_generation.tagging_formatter import FormatValueRetriever


class XHTMLGenerator:
    def __init__(
        self,
        data,
        filing_date,
        ticker,
        cik,
        file_id,
        html_file,
        filename,
        split_file,
        website,
        taxonomy_year,
    ):
        # Initialize class attributes
        self.cik = cik
        self.data = data
        self.ticker = ticker
        self.file_id = file_id
        self.html_file = html_file
        self.split_file = split_file
        self.company_website = website
        self.filing_date = filing_date
        self.taxonomy_year = taxonomy_year
        self.output_file = f"data/{ticker}-{filing_date}/{ticker}-{filing_date}.htm"
        self.output_html = filename
        self.context_list = []
        self.xsd_filename = f"{ticker}-{filing_date}.xsd"  # XSD file name
        # Extract HTML elements from the provided HTML file
        self.html_elements = extract_html_elements(html_file, only_id=True)

    def get_filename(self):
        return os.path.basename(self.html_file)

    def get_unit_value(self, unit):
        # Read the JSON file

        with open("assets/units.json", "r") as json_file:
            data = json.load(json_file)

        # Loop through each object in the JSON data
        for obj in data:
            # Access individual fields, for example:
            if unit == obj["unitId"]:
                return obj["baseStandard"], obj["nsUnit"]
        else:
            return None, None

    def add_html_attributes(self):
        # Create a BeautifulSoup object
        soup = BeautifulSoup("", "html.parser")

        # Create the html tag
        html_tag = soup.new_tag("html")

        # Add attributes to the html tag

        # common for every taxonomy
        html_tag["xml:lang"] = "en-US"
        html_tag["xmlns"] = "http://www.w3.org/1999/xhtml"
        html_tag["xmlns:utr"] = "http://www.xbrl.org/2009/utr"
        html_tag["xmlns:ref"] = "http://www.xbrl.org/2006/ref"
        html_tag["xmlns:xlink"] = "http://www.w3.org/1999/xlink"
        html_tag["xmlns:xbrldi"] = "http://xbrl.org/2006/xbrldi"
        html_tag["xmlns:xbrldt"] = "http://xbrl.org/2005/xbrldt"
        html_tag["xmlns:ix"] = "http://www.xbrl.org/2013/inlineXBRL"
        html_tag["xmlns:link"] = "http://www.xbrl.org/2003/linkbase"
        html_tag["xmlns:xbrli"] = "http://www.xbrl.org/2003/instance"
        html_tag["xmlns:iso4217"] = "http://www.xbrl.org/2003/iso4217"
        html_tag["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"

        ixt = "http://www.xbrl.org/inlineXBRL/transformation/2022-02-16"
        html_tag["xmlns:ixt"] = ixt

        ixt_sec = "http://www.sec.gov/inlineXBRL/transformation/2015-08-31"
        html_tag["xmlns:ixt-sec"] = ixt_sec

        # change based on the taxonomy year
        html_tag["xmlns:srt"] = f"http://fasb.org/srt/{self.taxonomy_year}"
        html_tag["xmlns:dei"] = f"http://xbrl.sec.gov/dei/{self.taxonomy_year}"
        html_tag["xmlns:ecd"] = f"http://xbrl.sec.gov/ecd/{self.taxonomy_year}"
        html_tag["xmlns:us-gaap"] = f"http://fasb.org/us-gaap/{self.taxonomy_year}"
        html_tag["xmlns:us-roles"] = f"http://fasb.org/us-roles/{self.taxonomy_year}"
        html_tag["xmlns:country"] = f"http://xbrl.sec.gov/country/{self.taxonomy_year}"

        company_name_filing_date = f"http://{self.company_website}/{self.filing_date}"
        html_tag[f"xmlns:{self.ticker}"] = company_name_filing_date

        return str(html_tag).replace("</html>", "")

    def get_period_axis_unique_records(slef, data):
        unique_entries = {}

        for entry in data:
            if entry["Period"]:  # Exclude entries where "Period" value is empty
                key = (entry["Period"], entry["Axis_Member"])
                if key not in unique_entries:
                    unique_entries[key] = entry
        unique_entries = list(unique_entries.values())
        return unique_entries

    def formatted_to_date(self, date_str):
        # Convert to datetime object
        date_obj = datetime.strptime(date_str, "%Y%m%d")

        # Format the datetime object as "YYYY-MM-DD"
        formatted_date_str = date_obj.strftime("%Y-%m-%d")

        return formatted_date_str

    def non_dimension_context(self, period_date, resources, record):
        if "__" in period_date:
            from_, to = period_date.split("__")

            from_date_str = self.formatted_to_date(from_)
            to_date_str = self.formatted_to_date(to)
            context_id = f"FROM{from_date_str}TO{to_date_str}"

            if context_id not in self.context_list:

                # Create the root element
                context_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}context"
                )

                context_root.set("id", context_id)

                # Create the entity element
                entity = etree.SubElement(
                    context_root, "{http://www.xbrl.org/2003/instance}entity"
                )
                identifier = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}identifier"
                )
                identifier.set("scheme", "http://www.sec.gov/CIK")
                identifier.text = self.cik

                # Create the period element
                period = etree.SubElement(
                    context_root, "{http://www.xbrl.org/2003/instance}period"
                )
                startDate = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}startDate"
                )
                startDate.text = from_date_str
                endDate = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}endDate"
                )
                endDate.text = to_date_str

            self.context_list.append(context_id)

        else:
            period: str = record.get("Period")
            period_date_str = self.formatted_to_date(period_date)
            context_id = f"AsOf{period_date_str}"

            if context_id not in self.context_list:

                # Create the root element
                context_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}context"
                )
                context_root.set("id", context_id)

                # Create the entity element
                entity = etree.SubElement(
                    context_root, "{http://www.xbrl.org/2003/instance}entity"
                )
                identifier = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}identifier"
                )
                identifier.set("scheme", "http://www.sec.gov/CIK")
                identifier.text = self.cik

                # Create the period element
                period = etree.SubElement(
                    context_root, "{http://www.xbrl.org/2003/instance}period"
                )
                instant = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}instant"
                )
                instant.text = period_date_str

            self.context_list.append(context_id)

    def single_dimension_context(self, group, period_date, resources, record):
        _axis, _domain, _member = group
        axis = _axis.replace("--", "_").replace("custom", self.ticker)
        domain = _domain.replace("--", "_").replace("custom", self.ticker)
        member = _member.replace("--", "_").replace("custom", self.ticker)

        if "__" in period_date:
            from_, to = period_date.split("__")

            from_date_str = self.formatted_to_date(from_)
            to_date_str = self.formatted_to_date(to)
            context_id = f"FROM{from_date_str}TO{to_date_str}_{member}"

            if context_id not in self.context_list:

                # Create the root element
                dimension_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}context"
                )
                dimension_root.set("id", context_id)

                # Create the entity element
                entity = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}entity"
                )
                identifier = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}identifier"
                )
                identifier.set("scheme", "http://www.sec.gov/CIK")
                identifier.text = self.cik

                # Add the segment element
                segment = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}segment"
                )
                explicitMember = etree.SubElement(
                    segment,
                    "{http://xbrl.org/2006/xbrldi}explicitMember",
                    nsmap={"xbrldi": namespace.get("xbrldi")},
                )
                explicitMember.set("dimension", axis.replace("_", ":"))
                explicitMember.text = member.replace("_", ":")

                # Create the period element
                period = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}period"
                )
                startDate = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}startDate"
                )
                startDate.text = from_date_str
                endDate = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}endDate"
                )
                endDate.text = to_date_str

            self.context_list.append(context_id)

        else:
            period: str = record.get("Period")
            period_date_str = self.formatted_to_date(period_date)
            context_id = f"AsOf{period_date_str}_{member}"

            if context_id not in self.context_list:

                # Create the root element
                dimension_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}context"
                )
                dimension_root.set("id", context_id)

                # Create the entity element
                entity = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}entity"
                )
                identifier = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}identifier"
                )
                identifier.set("scheme", "http://www.sec.gov/CIK")
                identifier.text = self.cik

                # Add the segment element
                segment = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}segment"
                )
                explicitMember = etree.SubElement(
                    segment,
                    "{http://xbrl.org/2006/xbrldi}explicitMember",
                    nsmap={"xbrldi": namespace.get("xbrldi")},
                )
                explicitMember.set("dimension", axis.replace("_", ":"))
                explicitMember.text = member.replace("_", ":")

                # Add the period element
                period = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}period"
                )
                instant = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}instant"
                )
                instant.text = period_date_str

            self.context_list.append(context_id)

    def multiple_dimension_context(self, groups, period_date, resources, record):
        axis_list: list = []
        member_list: list = []

        for group in groups:
            _axis, _domain, _member = group
            axis = _axis.replace("--", "_").replace("custom", self.ticker)
            domain = _domain.replace("--", "_").replace("custom", self.ticker)
            member = _member.replace("--", "_").replace("custom", self.ticker)

            axis_list.append(axis)
            if member not in member_list:
                member_list.append(member)

        member_str = "_".join(member_list)

        if "__" in period_date:
            from_, to = period_date.split("__")

            from_date_str = self.formatted_to_date(from_)
            to_date_str = self.formatted_to_date(to)
            context_id = f"FROM{from_date_str}TO{to_date_str}_{member_str}"

            if context_id not in self.context_list:

                # Create the root element
                dimension_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}context"
                )
                dimension_root.set("id", context_id)

                # Create the entity element
                entity = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}entity"
                )
                identifier = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}identifier"
                )
                identifier.set("scheme", "http://www.sec.gov/CIK")
                identifier.text = self.cik

                # Add the segment element
                segment = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}segment"
                )

                for axis, member in zip(axis_list, member_list):
                    explicitMember = etree.SubElement(
                        segment,
                        "{http://xbrl.org/2006/xbrldi}explicitMember",
                        nsmap={"xbrldi": namespace.get("xbrldi")},
                    )
                    explicitMember.set("dimension", axis.replace("_", ":"))
                    explicitMember.text = member.replace("_", ":")

                # Create the period element
                period = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}period"
                )
                startDate = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}startDate"
                )
                startDate.text = from_date_str
                endDate = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}endDate"
                )
                endDate.text = to_date_str

            self.context_list.append(context_id)

        else:
            period: str = record.get("Period")
            period_date_str = self.formatted_to_date(period_date)
            context_id = f"AsOf{period_date_str}_{member_str}"

            if context_id not in self.context_list:
                # Create the root element
                dimension_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}context"
                )
                dimension_root.set("id", context_id)

                # Create the entity element
                entity = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}entity"
                )
                identifier = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}identifier"
                )
                identifier.set("scheme", "http://www.sec.gov/CIK")
                identifier.text = self.cik

                # Add the segment element
                segment = etree.SubElement(
                    entity, "{http://www.xbrl.org/2003/instance}segment"
                )

                for axis, member in zip(axis_list, member_list):
                    explicitMember = etree.SubElement(
                        segment,
                        "{http://xbrl.org/2006/xbrldi}explicitMember",
                        nsmap={"xbrldi": namespace.get("xbrldi")},
                    )
                    explicitMember.set("dimension", axis.replace("_", ":"))
                    explicitMember.text = member.replace("_", ":")

                # Add the period element
                period = etree.SubElement(
                    dimension_root, "{http://www.xbrl.org/2003/instance}period"
                )
                instant = etree.SubElement(
                    period, "{http://www.xbrl.org/2003/instance}instant"
                )
                instant.text = period_date_str

            self.context_list.append(context_id)

    def created_context_ref(self, resources):
        unique_entries = self.get_period_axis_unique_records(self.data)
        for record in unique_entries:
            period_date: str = record.get("Period")
            axis_member: str = record.get("Axis_Member")

            if period_date and axis_member:
                splitted = axis_member.split("__")
                # Group by 3
                groups = [splitted[i : i + 3] for i in range(0, len(splitted), 3)]
                if len(groups) == 1:
                    self.single_dimension_context(
                        groups[0], period_date, resources, record
                    )
                else:
                    self.multiple_dimension_context(
                        groups, period_date, resources, record
                    )

            else:
                self.non_dimension_context(period_date, resources, record)

    def create_units(self, resources, units):
        for unit in units:
            # check custom unit or not
            name = unit.get("name")
            numerator: str = unit.get("numerator")
            denominator: str = unit.get("denominator")
            custom_unit = unit.get("customUnit")

            if custom_unit:
                custom_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}unit", id=name
                )

                # Create the measure element
                measure = etree.SubElement(
                    custom_root, "{http://www.xbrl.org/2003/instance}measure"
                )
                measure.text = f"{self.ticker}:{name}"

            if "denominator" not in unit.keys() and custom_unit is False:

                # Create the root element
                numerator_root = etree.SubElement(
                    resources,
                    "{http://www.xbrl.org/2003/instance}unit",
                    id=name,
                )

                # Create the measure element for unitNumerator
                measure_numerator = etree.SubElement(
                    numerator_root, "{http://www.xbrl.org/2003/instance}measure"
                )

                numerator_name = numerator.split()[0]
                baseStandard, nsUnit = self.get_unit_value(numerator_name)

                if baseStandard:
                    if nsUnit.endswith("instance"):
                        baseStandard = f"{baseStandard}i".lower()
                        measure_numerator.text = f"{baseStandard}:{numerator_name}"
                    if nsUnit.endswith("utr"):
                        measure_numerator.text = f"utr:{numerator_name}"
                    if nsUnit.endswith("iso4217"):
                        measure_numerator.text = f"iso4217:{numerator_name}"
                else:
                    measure_numerator.text = f"{self.ticker}:{numerator_name}"

            if (
                "numerator" in unit.keys()
                and "denominator" in unit.keys()
                and not custom_unit
            ):
                # Create the root element
                nd_root = etree.SubElement(
                    resources, "{http://www.xbrl.org/2003/instance}unit", id=name
                )

                # Create the divide element
                divide = etree.SubElement(
                    nd_root, "{http://www.xbrl.org/2003/instance}divide"
                )

                # Create the unitNumerator element
                unitNumerator = etree.SubElement(
                    divide, "{http://www.xbrl.org/2003/instance}unitNumerator"
                )

                # Create the measure element for unitNumerator
                measure_numerator = etree.SubElement(
                    unitNumerator, "{http://www.xbrl.org/2003/instance}measure"
                )

                numerator_name = numerator.split()[0]
                baseStandard, nsUnit = self.get_unit_value(numerator_name)

                if baseStandard:
                    if nsUnit.endswith("instance"):
                        baseStandard = f"{baseStandard}i".lower()
                        measure_numerator.text = f"{baseStandard}:{numerator_name}"
                    if nsUnit.endswith("utr"):
                        measure_numerator.text = f"utr:{numerator_name}"
                    if nsUnit.endswith("iso4217"):
                        measure_numerator.text = f"iso4217:{numerator_name}"
                else:
                    measure_numerator.text = f"{self.ticker}:{numerator_name}"

                # Create the unitDenominator element
                unitDenominator = etree.SubElement(
                    divide, "{http://www.xbrl.org/2003/instance}unitDenominator"
                )

                # Create the measure element for unitDenominator
                measure_denominator = etree.SubElement(
                    unitDenominator, "{http://www.xbrl.org/2003/instance}measure"
                )

                name = denominator.split()[0]
                baseStandard, nsUnit = self.get_unit_value(name)

                if baseStandard:
                    if nsUnit.endswith("instance"):
                        baseStandard = f"{baseStandard}i".lower()
                        measure_denominator.text = f"{baseStandard}:{name}"
                    if nsUnit.endswith("utr"):
                        measure_denominator.text = f"utr:{name}"
                    if nsUnit.endswith("iso4217"):
                        measure_denominator.text = f"iso4217:{name}"
                else:
                    measure_denominator.text = f"{self.ticker}:{name}"

    def remove_ix_namespaces(self, html_content: str):
        for key, value in namespace.items():
            namespace_format = f'xmlns:{key}="{value}"'
            html_content = html_content.replace(namespace_format, "")
        return html_content

    def remove_role_attribute(self, soup):
        # Find all elements with the 'role' attribute
        elements_with_role = soup.find_all(attrs={"role": True})

        # Remove 'role' attribute from all elements
        for element in elements_with_role:
            del element["role"]

        return soup

    def remove_left_over_apex_ids(self, soup):
        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))
        for tag in tags:
            # Remove the 'id' attribute
            del tag["id"]
        return soup

    def save_html_file(self, soup):
        # Extract the directory from the output file path
        directory = os.path.dirname(self.output_file)

        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        soup = self.remove_left_over_apex_ids(soup)
        soup = self.remove_role_attribute(soup)

        # Find all <a> tags and modify the name attribute to href
        for a_tag in soup.find_all("a"):
            if a_tag.has_attr("name") and not a_tag.has_attr("href"):
                a_tag["href"] = f"#{a_tag['name']}"
                del a_tag["name"]

        # Manage entities manually_
        parsed_html = html.unescape(str(soup))

        # output_html_file = self.get_filename()
        # Update the output file with the new soup data
        with open(self.output_file, "wb") as out_file:
            # html_content: str = soup.prettify()
            html_content: str = parsed_html

            # remove all the namespaces in the ix header
            html_content = self.remove_ix_namespaces(html_content)

            html_content = html_content.replace(
                '<link:schemaRef xlink:href="soulpage-20240603.xsd" xlink:type="simple">',
                '<link:schemaRef xlink:href="soulpage-20240603.xsd" xlink:type="simple" />',
            )

            html_content = html_content.replace(
                "<continuation />", "</ix:continuation >"
            )
            html_content = html_content.replace("<continuation", " <ix:continuation")
            html_content = html_content.replace("/>", ">")
            html_content = html_content.replace(
                "<ix:continuation>", "</ix:continuation>"
            )
            html_content = html_content.replace(
                '<meta content="text/html" http-equiv="Content-Type">',
                '<meta content="text/html" http-equiv="Content-Type"/>',
            )

            html_content = html_content.replace("unitref", "unitRef")
            html_content = html_content.replace("contextref", "contextRef")
            html_content = html_content.replace("nonfraction", "nonFraction")
            html_content = html_content.replace("nonnumeric", "nonNumeric")

            html_content = html_content.replace("<font", "<span")
            html_content = html_content.replace("</font", "</span")
            html_content = html_content.replace("<br>", "<br/>")

            # replace html entities
            html_content = html_content.replace("&", "&amp;")
            html_content = html_content.replace("☐", "&#9744;")
            html_content = html_content.replace("☑", "&#9745;")
            html_content = html_content.replace("☒", "&#9746;")
            html_content = html_content.replace("- ", "&#8211;")
            html_content = html_content.replace("–", "&#8211;")
            html_content = html_content.replace("—", "&#8212;")

            # Non-breaking space
            html_content = html_content.replace("\u00A0", "&#160;")
            # Right single quotation mark (’)
            html_content = html_content.replace("\u2019", "&#8217;")
            # Section sign (§)
            html_content = html_content.replace("\u00A7", "&#167;")
            # Right double quotation mark (”)
            html_content = html_content.replace("\u201D", "&#8221;")
            # Left double quotation mark (“)
            html_content = html_content.replace("\u201C", "&#8220;")
            # Bullet point (•)
            html_content = html_content.replace("\u25CF", "&#8226;")

            html_content = html_content.replace("<!DOCTYPE html>", "")

            # add HTML attributes in the html
            html_attributes = self.add_html_attributes()
            html_content = html_content.replace("<html>", html_attributes)

            # Get current date and time with AM/PM
            current_datetime = datetime.now().strftime("%Y-%m-%d %I:%M %p")

            # Create comments after the XML declaration
            comments_after_declaration = [
                '<?xml version="1.0" encoding="utf-8"?>',
                "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
                f"<!-- Creation Date : {current_datetime} -->",
                "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
            ]

            # Concatenate XML declaration and comments
            xml_declaration = "\n".join(comments_after_declaration) + "\n"

            # Encode XML declaration to bytes and write to file
            xml_declaration_bytes = xml_declaration.encode("utf-8")

            # Encode prettified HTML content to bytes and write to file
            html_content_bytes = html_content.encode("utf-8")

            final_content = xml_declaration_bytes + html_content_bytes
            # Write prettified HTML content to the output file
            out_file.write(final_content)

    def get_datatype_data(self, data_type):
        with open("assets/elements.json", "r") as json_file:
            data = json.load(json_file)
            for record in data:
                if record.get("datatype") == data_type:
                    return record

    def create_continuation_tags(self, soup, start_id, end_id):

        # Find the first <p> tag with the specified ID
        first_id_tag = soup.find("p", id=start_id)

        # Find the second <p> tag with the specified ID
        second_id_tag = soup.find("p", id=end_id)

        random_number = random.randint(100, 999)
        count = 1

        continuation_start_tag = f'<ix:continuation id="f-{random_number}-{count}" continuedAt="f-{random_number}-{count+1}">'
        count += 1

        output_html = ""

        if first_id_tag and second_id_tag:
            first_id_tag.insert_after(BeautifulSoup(continuation_start_tag, "xml"))
            second_id_tag.insert_after(BeautifulSoup("<ix:continuation>", "xml"))

            # Find all tags, comments, and strings between the first and second IDs
            current_tag = first_id_tag.next_sibling

            while current_tag and current_tag != second_id_tag:
                if isinstance(current_tag, Comment):
                    # Include comment in the output
                    output_html += f"<!--{current_tag}-->"
                    comment = str(current_tag).strip()
                    if comment.startswith("Field: /Page"):
                        continuation_start_tag = f'<ix:continuation id="f-{random_number}-{count}" continuedAt="f-{random_number}-{count+1}">'
                        count += 1

                        current_tag.insert_after(
                            BeautifulSoup(continuation_start_tag, "xml")
                        )

                    if comment.startswith("Field: Page; Sequence"):
                        current_tag.insert_before(
                            BeautifulSoup("<ix:continuation>", "xml")
                        )

                else:
                    output_html += str(current_tag)
                current_tag = current_tag.next_sibling

            parser = HtmlTagParser()
            data = parser.process_tag(start_id)
            # create new Numeric or nonNumeric tag
            datatype_tag = self.create_datatype_tag(
                soup, data, first_id_tag, note_section=True
            )

            if datatype_tag:
                if first_id_tag.find_all():
                    # Add all contents from the specific <p> tag to the new tag
                    for inner_tag in first_id_tag.find_all():
                        datatype_tag.append(inner_tag)

                datatype_tag["id"] = f"f-{random_number}"
                style = first_id_tag.get("style")
                datatype_tag["id"] = f"f-{random_number}"
                datatype_tag["style"] = style
                first_id_tag.replace_with(datatype_tag)

            return soup

        return soup

    def get_context_id(self, data):
        context_id = None
        # Extract Period and Axis_Member data from the input dictionary
        period_date: str = data.get("Period")
        axis_member: str = data.get("Axis_Member")

        # If both Period and Axis_Member are present
        if period_date and axis_member:
            # Split Axis_Member to extract the relevant member
            splitted = axis_member.split("__")

            member_list = []
            # Group by 3
            groups = [splitted[i : i + 3] for i in range(0, len(splitted), 3)]
            for group in groups:
                # axis, domain, member = group
                _, _, _member = group
                member = _member.replace("--", "_").replace("custom", self.ticker)
                if member not in member_list:
                    member_list.append(member)

            member_str = "_".join(member_list)

            if "__" in period_date:
                # If Period contains a range, split it into start and end dates
                from_, to = period_date.split("__")

                # Format start and end dates
                from_date_str = self.formatted_to_date(from_)
                to_date_str = self.formatted_to_date(to)

                # Create context_id based on date range
                context_id = f"FROM{from_date_str}TO{to_date_str}_{member_str}"
            else:
                # Format period_date to a specific date format
                period_date_str = self.formatted_to_date(period_date)

                # Create context_id based on Period date and Axis member
                context_id = f"AsOf{period_date_str}_{member_str}"
        else:
            if period_date:
                # If Period is present but Axis_Member is not
                if "__" in period_date:
                    # If Period contains a range, split it into start and end dates
                    from_, to = period_date.split("__")

                    # Format start and end dates
                    from_date_str = self.formatted_to_date(from_)
                    to_date_str = self.formatted_to_date(to)

                    # Create context_id based on date range
                    context_id = f"FROM{from_date_str}TO{to_date_str}"
                else:
                    # If Period is a single date
                    # Format period_date to a specific date format
                    period_date_str = self.formatted_to_date(period_date)

                    # Create context_id based on single date
                    context_id = f"AsOf{period_date_str}"

        return context_id

    def get_format_value(self, element, data_type, input_text):
        retriever = FormatValueRetriever(input_text)
        format_value = retriever.get_format_value(element, data_type)
        return format_value

    def is_number(self, value):
        # Remove parentheses and commas, and check if it can be converted to a float
        try:
            if value is not None:
                cleaned_value = value.replace("(", "").replace(")", "").replace(",", "")
                float(cleaned_value)
                return True
        except ValueError:
            return False

    def create_datatype_tag(self, soup, data, tag, note_section=None):

        # data_type = data.get("DataType")
        # data_type = self.get_datatype(data.get("Element"))
        data_type = data.get("DataType")
        element: str = data.get("Element", "")
        heading = data.get("Heading")
        precision = data.get("Precision")
        counted_as = data.get("CountedAs")

        if data_type == "xbrli:durationItemType":
            next_sibling = tag.next_sibling
            # If there's a next sibling and it's text, strip and print it
            if next_sibling:
                next_sibling_text = next_sibling.strip()
                if next_sibling_text:
                    input_text = f"{tag.text} {next_sibling_text}"
                    if "to" in input_text:
                        input_text = input_text.replace("to", "years")
                    if "-" in input_text:
                        input_text = input_text.replace("-", "years")
                    if "year" in input_text:
                        input_text = f"{tag.text} years"
                else:
                    input_text = f"{tag.text} years"

                format_value = self.get_format_value(element, data_type, input_text)
            else:
                input_text = f"{tag.text} years"
                format_value = self.get_format_value(element, data_type, input_text)
        else:
            format_value = self.get_format_value(element, data_type, tag.text)

        if data_type and heading is False and not element.endswith("Abstract"):
            data_type_record = self.get_datatype_data(data_type)
            if data_type_record:
                datatype_element = data_type_record.get("element", "")
                datatype_attributes = data_type_record.get("attributes", "")

                # Create new nonNumeric or Numeric tag
                non_numeric_tag = soup.new_tag(datatype_element)

                fact = data.get("Fact", "")
                if fact and "N" in fact and tag.text == "-":
                    # name attribute
                    non_numeric_tag["name"] = element.replace("--", ":").replace(
                        "custom", self.ticker
                    )

                    # contextRef attribute
                    context_id = self.get_context_id(data)
                    non_numeric_tag["contextRef"] = context_id

                    # id attribute
                    is_footnote = data.get("have_footnote")
                    if is_footnote:
                        foot_note_reference = tag.get("FR", "")
                        # uniq_id = is_footnote[0]
                        uniq_id = foot_note_reference
                        # Remove the 'FR' attribute after the usage
                        if "FR" in tag.attrs:
                            del tag["data-info"]

                    else:
                        uniq_id = data.get("UniqueId", "")
                    non_numeric_tag["id"] = uniq_id

                    # unitRef attribute
                    unit: str = data.get("Unit", "")
                    non_numeric_tag["unitRef"] = unit

                    # xs:nill attribute
                    non_numeric_tag["xs:nil"] = "true"
                    unit: str = data.get("Unit", "")
                    non_numeric_tag["unitRef"] = unit

                if fact and "Z" in fact and "N" not in fact and tag.text == "-":
                    # name attribute
                    non_numeric_tag["name"] = element.replace("--", ":").replace(
                        "custom", self.ticker
                    )

                    # contextRef attribute
                    context_id = self.get_context_id(data)
                    non_numeric_tag["contextRef"] = context_id

                    # id attribute
                    is_footnote = data.get("have_footnote")
                    if is_footnote:
                        foot_note_reference = tag.get("FR", "")
                        # uniq_id = is_footnote[0]
                        uniq_id = foot_note_reference
                        # Remove the 'FR' attribute after the usage
                        if "FR" in tag.attrs:
                            del tag["data-info"]

                    else:
                        uniq_id = data.get("UniqueId", "")
                    non_numeric_tag["id"] = uniq_id

                    # formate attribute
                    non_numeric_tag["format"] = "ixt:fixed-zero"

                    # decimals attribute
                    precision: str = data.get("Precision", "")
                    non_numeric_tag["decimals"] = precision

                    # scale attribute
                    counted_as: str = data.get("CountedAs", "")
                    non_numeric_tag["scale"] = counted_as

                    # unitRef attribute
                    unit: str = data.get("Unit", "")
                    non_numeric_tag["unitRef"] = unit

                else:
                    for attribute in datatype_attributes:
                        if attribute == "contextRef":
                            context_id = self.get_context_id(data)
                            non_numeric_tag["contextRef"] = context_id

                        if attribute == "unitRef":
                            unit: str = data.get("Unit", "")
                            non_numeric_tag["unitRef"] = unit

                        if attribute == "name":
                            non_numeric_tag["name"] = element.replace(
                                "--", ":"
                            ).replace("custom", self.ticker)

                        # add scale and decimals value
                        datatypes_list = [
                            "xbrli:monetaryItemType",
                            "dtr-types:percentItemType",
                            "xbrli:sharesItemType",
                            "xbrli:integerItemType",
                            "dtr-types:perShareItemType",
                            "srt-types:perUnitItemType",
                            "xbrli:decimalItemType",
                            "dtr-types:volumeItemType",
                            "dtr-types:areaItemType",
                            "xbrli:pureItemType",
                            "dtr-types:energyItemType",
                            "dtr-types:massItemType",
                            "dtr-types:flowItemType",
                        ]
                        if data_type in datatypes_list:
                            if precision == "0" and counted_as == "0":
                                if format_value == "ixt:fixed-zero":
                                    if data_type == "xbrli:monetaryItemType":
                                        non_numeric_tag["decimals"] = "0"
                                    else:
                                        non_numeric_tag["decimals"] = "INF"

                                if "N" not in fact:
                                    if data_type == "xbrli:monetaryItemType":
                                        non_numeric_tag["decimals"] = "0"
                                    else:
                                        non_numeric_tag["decimals"] = "INF"
                            else:
                                if "N" not in fact:
                                    non_numeric_tag["decimals"] = precision
                                    non_numeric_tag["scale"] = counted_as

                            if precision == "0":
                                if data_type == "dtr-types:percentItemType":
                                    non_numeric_tag["decimals"] = "INF"

                        else:
                            if attribute == "decimals" and "N" not in fact:
                                non_numeric_tag["decimals"] = precision

                            if attribute == "scale" and "N" not in fact:
                                non_numeric_tag["scale"] = counted_as

                        if attribute == "format" and tag.text != "-":
                            if format_value:
                                non_numeric_tag["format"] = format_value

                        if attribute == "id":
                            is_footnote = data.get("have_footnote")
                            if is_footnote:
                                foot_note_reference = tag.get("FR", "")
                                # uniq_id = is_footnote[0]
                                uniq_id = foot_note_reference
                                # Remove the 'FR' attribute after the usage
                                if "FR" in tag.attrs:
                                    del tag["data-info"]

                            else:
                                uniq_id = data.get("UniqueId", "")
                            non_numeric_tag["id"] = uniq_id

                        if "R" in fact:
                            non_numeric_tag["sign"] = "-"

                if format_value == "ixt-sec:numwordsen":
                    non_numeric_tag["decimals"] = "0"

                if format_value == "ixt:fixed-zero":
                    del non_numeric_tag["sign"]

                if non_numeric_tag.get("xs:nil") == "true":
                    del non_numeric_tag["sign"]

                # Check if the tag is specifically ix:nonNumeric
                if non_numeric_tag.name == "ix:nonNumeric":
                    del non_numeric_tag["decimals"]

                # Check if the tag has xs:nil="true" and the 'decimals' attribute
                if non_numeric_tag.get("xs:nil") == "true" and non_numeric_tag.has_attr(
                    "decimals"
                ):
                    # Remove the 'decimals' attribute
                    del non_numeric_tag["decimals"]

                style = tag.get("style")
                if style:
                    non_numeric_tag["style"] = style
                if note_section:
                    return non_numeric_tag
                else:
                    non_numeric_tag.string = tag.text
                    return non_numeric_tag

    def generate_datatypes_tags(self, soup):

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(
            lambda tag: tag.name in ["p", "font"]
            and tag.get("id", "").startswith("apex_")
        )

        parser = HtmlTagParser()
        for tag in tags:
            # Find all tags with an id attribute
            tag_ids = [tag["id"]] + [
                tag["id"]
                for tag in tag.find_all(id=True)
                if tag["id"].startswith("apex")
            ]
            # handle multiple tags
            if len(tag_ids) > 1:
                datatype_tag_list = []
                for index, tag_id in enumerate(tag_ids):
                    data = parser.process_tag(tag_id)
                    fact = data.get("Fact", "")
                    # create new Numeric or nonNumeric tag
                    datatype_tag = self.create_datatype_tag(soup, data, tag)
                    # Set string only if it's not the last tag
                    if index != len(tag_ids) - 1:
                        datatype_tag.string = ""

                    if index == len(tag_ids) - 1:
                        if "(" in tag.text:
                            datatype_tag.string = tag.text.replace("(", "")

                            # Create a new NavigableString for the parenthesis
                            parenthesis = soup.new_string("(")

                            # Insert the parenthesis before the non_numeric_tag tag
                            tag.insert_before(parenthesis)

                    datatype_tag_list.append(str(datatype_tag))

                # Parse the first element to initialize the base XML
                non_numeric_soup = BeautifulSoup(datatype_tag_list[0], "html.parser")

                # Start with the root element
                parent = non_numeric_soup.find()  # Find the root element

                # Ensure parent is valid
                if parent is None:
                    print("Parent is None", str(tag))

                # Iterate over the remaining elements, nesting each one inside the previous
                for data in datatype_tag_list[1:]:
                    new_element = BeautifulSoup(data, "html.parser").find()

                    # Ensure new_element is found
                    if new_element is None:
                        raise ValueError(f"Tag not found in {data}")

                    # Append the new element as a child of the parent
                    parent.append(new_element)
                    parent = new_element  # The new element becomes the parent for the next iteration

                tag.replace_with(non_numeric_soup)

            # handle single tag
            else:
                tag_id = tag.get("id", "")
                data = parser.process_tag(tag_id)
                data_type = data.get("DataType", "")

                # create new Numeric or nonNumeric tag
                datatype_tag = self.create_datatype_tag(soup, data, tag)

                if datatype_tag:

                    fact = data.get("Fact", "")

                    # # with reverse fact
                    # if "R" in fact and "(" in tag.text:
                    #     datatype_tag.string = tag.text.replace("(", "")

                    #     # Create a new NavigableString for the parenthesis
                    #     parenthesis = soup.new_string("(")

                    #     # Insert the parenthesis before the non_numeric_tag tag
                    #     tag.insert_before(parenthesis)

                    # without reverse fact
                    if "R" not in fact and "(" in tag.text:
                        is_number = self.is_number(tag.tex)
                        element = data.get("Element")
                        if is_number and element != "dei--CityAreaCode":
                            datatype_tag.string = tag.text.replace("(", "")
                            datatype_tag["sign"] = "-"

                            # Create a new NavigableString for the parenthesis
                            parenthesis = soup.new_string("(")

                            # Insert the parenthesis before the non_numeric_tag tag
                            tag.insert_before(parenthesis)

                    if "(" in tag.text:
                        datatype_tag.string = tag.text.replace("(", "")

                        # Create a new NavigableString for the parenthesis
                        parenthesis = soup.new_string("(")
                        datatype_tag["sign"] = "-"

                        # Insert the parenthesis before the non_numeric_tag tag
                        tag.insert_before(parenthesis)

                    # Replace original font tag with new Numeric or nonNumeric tag
                    # font_tag = soup.find("font", id=tag_id)
                    font_tag = soup.find(id=tag_id)

                    if "N" in fact and tag.text == "-":
                        datatype_tag.string = ""

                    if data_type == "xbrli:stringItemType":
                        del datatype_tag["sign"]

                    if font_tag:
                        styles = datatype_tag.get("style", None)

                        if styles is None:
                            font_tag.replace_with(datatype_tag)
                        else:
                            p_tag = soup.new_tag("p")
                            p_tag["style"] = styles
                            del datatype_tag["style"]
                            p_tag.append(datatype_tag)
                            font_tag.replace_with(p_tag)

        return soup

    def create_continuation_exclude_tags(self, soup, start_id, end_id):
        # Find the first <p> tag with the specified ID
        first_id_tag = soup.find("p", id=start_id)

        # Find the second <p> tag with the specified ID
        second_id_tag = soup.find("p", id=end_id)

        # Find all tags, comments, and strings between the first and second IDs
        current_tag = first_id_tag.next_sibling

        output_html = ""

        while current_tag and current_tag != second_id_tag:
            if isinstance(current_tag, Comment):
                # Include comment in the output
                output_html += f"<!--{current_tag}-->"
                comment = str(current_tag).strip()
                if comment.startswith("Field: Page; Sequence:"):
                    next_div_tag = current_tag.find_next("div")
                    if next_div_tag:
                        exclude_tag = soup.new_tag("ix:exclude")
                        # Add the comment as a string
                        exclude_tag.append(soup.new_string(f"<!--{comment}-->"))
                        # Insert the <ix:exclude> tag before the original <div>
                        next_div_tag.insert_before(exclude_tag)
                        # Move the content of the <div> to the <ix:exclude> tag
                        # This moves the entire tag, avoiding the circular issue
                        exclude_tag.append(next_div_tag)
                        current_tag.insert_after(exclude_tag)

            current_tag = current_tag.next_sibling

        return soup

    def ixt_continuation(self, soup: BeautifulSoup):

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

        start_tag_ids = []
        end_tag_ids = []
        for tag in tags:
            tag_id: str = tag.get("id", "")
            # notes start section
            if tag_id.startswith("apex_80"):
                start_tag_ids.append(tag_id)
            # notes end section
            if tag_id.startswith("apex_81"):
                end_tag_ids.append(tag_id)

        for start_id, end_id in zip(start_tag_ids, end_tag_ids):
            # soup = self.create_continuation_tags(soup, start_id, end_id)
            soup = self.create_continuation_exclude_tags(soup, start_id, end_id)

        return soup

    def add_footnote_ix_header(self, soup: BeautifulSoup, from_ref, to_ref):
        # Find the ix:resources element
        resources = soup.find("ix:resources")

        if resources:
            # Define the relationships
            relationship = soup.new_tag(
                "ix:relationship", fromRefs=from_ref, toRefs=to_ref
            )

            # Find the last xbrli:unit element if it exists
            last_unit = (
                resources.find_all("xbrli:unit")[-1]
                if resources.find_all("xbrli:unit")
                else None
            )

            # Find all xbrli:unit elements with namespace handling
            xbrli_units = resources.find_all("unit")

            # Find the last xbrli:unit element if it exists
            last_unit = xbrli_units[-1] if xbrli_units else None

            # Insert relationships after the last xbrli:unit element if it exists, otherwise append to resources
            if last_unit:
                if relationship not in resources:
                    last_unit.insert_after(relationship)
            else:
                if relationship not in resources:
                    resources.append(relationship)

    def alphanumeric_string(self, length=16):

        # Define character sets
        letters = string.ascii_letters
        alphanumeric = string.ascii_letters + string.digits

        # Generate the first character from letters and the rest from alphanumeric
        first_char = random.choice(letters)
        remaining_chars = "".join(
            random.choice(alphanumeric) for _ in range(length - 1)
        )

        return first_char + remaining_chars

    def foot_notes(self, soup: BeautifulSoup):

        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        tags = soup.find_all(lambda tag: tag.get("id", "").startswith("apex_"))

        foot_note_tag_ids: list = []
        footnote_id_dict: dict = {}
        # Find all foot note tags and crated ix:footnote tag for that"
        for index, tag in enumerate(tags, start=100):
            parser = HtmlTagParser()
            tag_id: str = tag.get("id", "")
            # notes start section
            if tag_id.startswith("apex_F0"):
                foot_note_tag_ids.append(tag_id)
                # Create new footnote tag
                footnote_id = f"Footnote{index}"
                ix_footnote_tag = soup.new_tag("ix:footnote")
                ix_footnote_tag["id"] = footnote_id
                ix_footnote_tag["xml:lang"] = "en-US"

                ix_footnote_tag.string = tag.text
                tag.replace_with(ix_footnote_tag)

                splitted = tag_id.split("_")
                footnote_id_dict[splitted[-1]] = footnote_id

        # add footnotes relationship to ix header
        for tag in tags:
            tag_id: str = tag.get("id", "")
            data = parser.process_tag(tag_id)
            is_footnote: list = data.get("have_footnote")
            if is_footnote:
                # add footnote reference to tag using FR attribute
                # foot_note_reference = uuid.uuid4().hex
                foot_note_reference = self.alphanumeric_string()
                tag["FR"] = foot_note_reference
                for footnote in is_footnote:
                    from_ref = footnote
                    to_ref = footnote_id_dict.get(from_ref)
                    # self.add_footnote_ix_header(soup, from_ref, to_ref)
                    self.add_footnote_ix_header(soup, foot_note_reference, to_ref)

        return soup

    def create_level_tags(self, soup: BeautifulSoup, start_id, end_id):
        # Find the starting and ending tags
        start_tag = soup.find(id=start_id)
        end_tag = soup.find(id=end_id)

        # Initialize an empty list to store the content between the tags
        content = []

        # Find all tags between the start and end tags
        current_tag = start_tag.find_next_sibling()
        while current_tag and current_tag != end_tag:
            content.append(current_tag)
            current_tag = current_tag.find_next_sibling()

        parser = HtmlTagParser()
        data = parser.process_tag(start_id)

        # create new Numeric or nonNumeric tag
        datatype_tag = self.create_datatype_tag(soup, data, start_tag)

        if datatype_tag:
            datatype_tag["escape"] = "true"

            datatype_tag_string = datatype_tag.text

            # keep the strong tag for the tagged element
            target_element = soup.find(string=start_tag.text)
            if target_element:
                # Check if the parent tag is <strong>
                parent_tag = target_element.parent
                if parent_tag.name == "strong":
                    strong_tag = soup.new_tag("strong")
                    strong_tag.string = datatype_tag.string
                    datatype_tag.string = ""

                    styles = datatype_tag.get("style", None)
                    if styles:
                        p_tag = soup.new_tag("p")
                        p_tag["style"] = styles
                        del datatype_tag["style"]
                        p_tag.append(strong_tag)
                        datatype_tag.append(p_tag)
                    else:
                        # If no styles, append strong_tag directly to datatype_tag
                        datatype_tag.append(strong_tag)
                else:
                    # datatype_tag.string = datatype_tag_string
                    datatype_tag.string = ""

                    styles = datatype_tag.get("style", None)
                    if styles:
                        p_tag = soup.new_tag("p")
                        p_tag.string = datatype_tag_string
                        p_tag["style"] = styles
                        del datatype_tag["style"]
                        datatype_tag.append(p_tag)
                    else:
                        datatype_tag.string = datatype_tag_string

            for tag in content:
                datatype_tag.append(tag)

            if "N" in data.get("Fact"):
                datatype_tag.string = ""

            start_tag.replace_with(datatype_tag)

            # styles = datatype_tag.get("style", None)
            # if styles is None:
            #     # Insert the new tag into the document
            #     start_tag.replace_with(datatype_tag)
            # else:
            #     p_tag = soup.new_tag("p")
            #     p_tag["style"] = styles
            #     del datatype_tag["style"]
            #     p_tag.append(datatype_tag)
            #     start_tag.replace_with(p_tag)

        return soup

    def level_tags(self, soup: BeautifulSoup):
        # Find all tags with attributes that start with "id" and have a value starting with "apex_"
        level1 = soup.find_all(
            lambda tag: tag.get("id", "").startswith(("apex_80", "apex_81"))
        )
        level2 = soup.find_all(
            lambda tag: tag.get("id", "").startswith(("apex_84", "apex_85"))
        )
        level3 = soup.find_all(
            lambda tag: tag.get("id", "").startswith(("apex_89", "apex_8A"))
        )

        level1_tags = [tag["id"] for tag in level1]
        level2_tags = [tag["id"] for tag in level2]
        level3_tags = [tag["id"] for tag in level3]

        level1_groups = [level1_tags[i : i + 2] for i in range(0, len(level1_tags), 2)]
        level2_groups = [level2_tags[i : i + 2] for i in range(0, len(level2_tags), 2)]
        level3_groups = [level3_tags[i : i + 2] for i in range(0, len(level3_tags), 2)]

        for group in level1_groups:
            if len(group) == 2:
                start_id, end_id = group
                soup = self.create_level_tags(soup, start_id, end_id)

        for group in level2_groups:
            if len(group) == 2:
                start_id, end_id = group
                soup = self.create_level_tags(soup, start_id, end_id)

        for group in level3_groups:
            if len(group) == 2:
                start_id, end_id = group
                soup = self.create_level_tags(soup, start_id, end_id)

        return soup

    def generate_ix_header(self):
        if self.split_file:
            split_file_record = get_split_file_record(file_id=self.file_id)
            file_id = split_file_record.get("fileId")
            record = get_db_record(file_id=file_id)
        else:

            record = get_db_record(file_id=self.file_id)

        period_from_ = record.get("periodFrom", None)
        period_to_ = record.get("periodTo", None)
        period_from = period_from_.strftime("%Y-%m-%d")
        period_to = period_to_.strftime("%Y-%m-%d")

        units = record.get("unit", [])
        elements_data: dict = record.get("elementsData", {})

        schema_ref_xlink_href = self.xsd_filename

        # Create the root element
        root = etree.Element(
            "{http://www.xbrl.org/2013/inlineXBRL}header",
            nsmap={"ix": namespace.get("ix")},
        )

        non_numeric_contextRef = f"FROM{period_from}TO{period_to}"
        non_numeric_text = self.cik

        # Create the 'ix:hidden' element
        hidden = etree.SubElement(root, "{http://www.xbrl.org/2013/inlineXBRL}hidden")

        # Create the 'ix:nonNumeric' elements within 'ix:hidden'
        # CIK Entry
        non_numeric_cik = etree.SubElement(
            hidden,
            "{http://www.xbrl.org/2013/inlineXBRL}nonNumeric",
            contextRef=non_numeric_contextRef,
            name="dei:EntityCentralIndexKey",
        )
        non_numeric_cik.text = non_numeric_text

        if elements_data:
            # Create the 'ix:hidden' element

            # Create the 'ix:nonNumeric' elements within 'ix:hidden'
            for key, value in elements_data.items():
                if key == "CurrentFiscalYearEndDate":
                    # Extract the month and day parts
                    month_day = value[5:]  # Slicing from the 6th character to the end
                    # Prefix with "--" and return
                    value = f"--{month_day}"

                if key == "AmendmentFlag":
                    value = value.lower()

                non_numeric = etree.SubElement(
                    hidden,
                    "{http://www.xbrl.org/2013/inlineXBRL}nonNumeric",
                    contextRef=non_numeric_contextRef,
                    name=f"dei:{key}",
                )
                non_numeric.text = value

        # Create the 'ix:references' element
        references = etree.SubElement(
            root, "{http://www.xbrl.org/2013/inlineXBRL}references"
        )

        # Create the root element with the namespace map
        references = etree.SubElement(
            references,
            "{http://www.xbrl.org/2013/inlineXBRL}references",
            nsmap={
                "ix": namespace.get("ix"),
                "link": namespace.get("link"),
                "xlink": namespace.get("xlink"),
            },
        )
        references.set("{http://www.w3.org/XML/1998/namespace}lang", "en-US")

        # Create the schemaRef element
        schema_ref = etree.SubElement(
            references,
            "{http://www.xbrl.org/2003/linkbase}schemaRef",
            {
                "{http://www.w3.org/1999/xlink}href": schema_ref_xlink_href,
                "{http://www.w3.org/1999/xlink}type": "simple",
            },
        )

        # Create the 'ix:resources' element
        resources = etree.SubElement(
            root,
            "{http://www.xbrl.org/2013/inlineXBRL}resources",
            nsmap={"ix": namespace.get("ix"), "xbrli": namespace.get("xbrli")},
        )

        self.created_context_ref(resources)
        self.create_units(resources, units)

        # # Create an ElementTree object and serialize it to a string
        xml_str = etree.tostring(root).decode()
        return xml_str

    def generate_xhtml_file(self):
        # Retrieve HTML content from the provided URL
        response = requests.get(self.html_file)
        if response.status_code == 200:
            # html_content = response.text
            html_content = response.content

            # Parse HTML using Beautiful Soup
            soup = BeautifulSoup(html_content, "html.parser")

            # Check if body tag exists
            body_tag = soup.body

            # If body tag doesn't exist, create one and add the content inside
            if not body_tag:
                # Create a basic HTML structure
                basic_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title></title>
                </head>
                <body>
                </body>
                </html>"""

                # Parse the basic HTML structure
                basic_soup = BeautifulSoup(basic_html, "html.parser")

                # Insert provided content inside the body tag of the basic HTML structure
                body_tag = basic_soup.body
                body_tag.append(BeautifulSoup(html_content, "html.parser"))

                # Update the soup variable with the modified basic_soup
                soup = basic_soup

            # # Parse HTML content to BeautifulSoup object and add datatype tags
            # soup = add_datatype_tags(str(soup), self.html_elements)

            # Create a hidden div element to store XBRL header information
            div_element = soup.new_tag("div", style="display: none")

            # Generate XBRL header and append it to the div element
            ix_header = self.generate_ix_header()

            div_element.append(BeautifulSoup(ix_header, "xml"))

            try:
                # Try to locate body and head tags within the HTML structure
                body = soup.body
                head_tag = soup.head

                if not head_tag:
                    head_tag = soup.new_tag("head")
                    soup.html.insert(0, head_tag)

                # Insert meta tag specifying content type within head tag
                meta_tag = soup.new_tag("meta")
                meta_tag.attrs["http-equiv"] = "Content-Type"
                meta_tag.attrs["content"] = "text/html"
                head_tag.insert(0, meta_tag)
                # Insert the hidden div element at the beginning of the body tag
                body.insert(0, div_element)
            except Exception as e:
                print("Body Element Not found")

            # Find the link:schemaRef tag
            schema_ref_tag = soup.find("link:schemaRef")

            if schema_ref_tag:
                # Convert self-closing tag to a standard tag with a closing tag
                schema_ref_tag.string = ""

            soup = self.ixt_continuation(soup)
            # update the footnote to soup object
            soup = self.foot_notes(soup)
            # created level1, level2, level3 tags
            soup = self.level_tags(soup)
            soup = self.generate_datatypes_tags(soup)

            # finally save the html file
            self.save_html_file(soup)
