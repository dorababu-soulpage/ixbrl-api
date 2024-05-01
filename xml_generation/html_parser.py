import re
import json
from utils import get_taxonomy_values


class HtmlTagParser:
    def __init__(self, html_tags):
        # Initialize the class with a list of HTML tags
        self.html_tags = html_tags

    def extract_field(self, data, prefix):
        # Extract a specific field from the data based on the provided prefix
        for item in data[1:-1]:
            if item.startswith(prefix):
                return item.lstrip(prefix)
        return ""

    def check_heading_or_not(self, data):
        # Extract a specific field from the data based on the provided prefix
        for item in data[1:-1]:
            if item.startswith("iB"):
                return True
        return False

    def get_indenting(self, data):
        for item in data[1:-1]:
            if item.startswith("i"):
                value = item.lstrip("iB").lstrip("i")
                return value
        return ""

    def get_precision_counted_as(self, data, prefix):
        result = {"Precision": "", "CountedAs": ""}
        for item in data[1:-1]:
            if item.startswith("p"):
                result["P"] = item[1:]
                result["Precision"] = item[1] if item[1] in ["d", "i"] else item[1:3]
                result["CountedAs"] = item.replace("p" + result["Precision"], "", 1)
        return result.get(prefix).lstrip("d")

    def get_calculation_parent(self, data):
        for item in data[1:-1]:
            if item.startswith("m"):
                _, cal_parent = item.split("__")
                return cal_parent
        return ""

    def get_formatted_data(self, html_tag):
        # Process a single HTML tag and return formatted data
        data = re.findall(r"[^_]+(?:__[^_]+)*|__", html_tag)
        return {
            "Type": data[1],
            "Element": self.extract_field(data, "e"),
            "Unit": self.extract_field(data, "u"),
            "PreElementParent": self.extract_field(data, "b"),
            "Heading": self.check_heading_or_not(data),
            "Indenting": self.get_indenting(data),
            "Precision": self.get_precision_counted_as(data, "Precision"),
            "CountedAs": self.get_precision_counted_as(data, "CountedAs"),
            "CalculationParent": self.get_calculation_parent(data),
            "Period": self.extract_field(data, "c"),
            "Axis_Member": self.extract_field(data, "h"),
            "PreferredLabelType": self.extract_field(data, "y"),
            "Table": self.extract_field(data, "t"),
            "LineItem": self.extract_field(data, "l"),
            "RootLevelAbstract": self.extract_field(data, "a"),
            "RoleType": self.extract_field(data, "r"),
            "UniqueId": data[-1],
        }

    def process_tags(self):
        # Process all HTML tags in the list
        formatted_tags = []
        for tag in self.html_tags:
            tag_id = tag.get("id")
            formatted_data = self.get_formatted_data(tag_id)
            formatted_data["RoleName"] = tag.get("role")
            formatted_data["PreferredLabel"] = tag.get("label")
            root_level_abstract: str = formatted_data.get("RootLevelAbstract")
            if root_level_abstract:
                _, name = root_level_abstract.split("--")
                element_value: dict = get_taxonomy_values(name)
                formatted_data["LabelText"] = element_value.get("label", "")
            formatted_tags.append(formatted_data)
        return formatted_tags


# # Example usage:
# html_tags_list = [
#     "apex_ynegatedTotal_90F_eus-gaap--Land_uCanadianDollar_pus-gaap:AssetsAbstract_i01_dn3_sn6_ma7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross_c2024022_hsrt--StatementScenarioAxis__srt--ConsolidatedEntityMember__srt--RestatementAxis__us-gaap--OtherOperatingIncomeExpenseMember_tus-gaap--StatementTable_lTable_aus-gaap--LandAndLandImprovementsAbstract_rStatement_0efb6deb824c493da1b6e03669691c36",
#     "apex_ynegatedTotal_90F_eus-gaap--Land_uCanadianDollar_pus-gaap:AssetsAbstract_i01_dn3_sn6_ma7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross_c2024022_hsrt--StatementScenarioAxis__srt--ConsolidatedEntityMember__srt--RestatementAxis__us-gaap--OtherOperatingIncomeExpenseMember_tus-gaap--StatementTable_lTable_aus-gaap--LandAndLandImprovementsAbstract_rStatement_0efb6deb824c493da1b6e03669691c36",
#     # Add more HTML tags here
# ]

# # Create an instance of HtmlTagParser
# parser = HtmlTagParser(html_tags_list)

# # Get the formatted data for all tags
# formatted_tags = parser.process_tags()

# # Print the formatted data
# print(json.dumps(formatted_tags, indent=4))
