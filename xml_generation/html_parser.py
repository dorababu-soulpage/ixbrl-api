import re
import json


class HtmlTagParser:
    def __init__(self, html_tags):
        # Initialize the class with a list of HTML tags
        self.html_tags = html_tags

    def extract_field(self, data, prefix):
        # Extract a specific field from the data based on the provided prefix
        for item in data[1:]:
            if item.startswith(prefix):
                return item.lstrip(prefix)
        return ""

    def get_formatted_data(self, html_tag):
        # Process a single HTML tag and return formatted data
        data = re.findall(r"[^_]+(?:__[^_]+)*|__", html_tag)
        return {
            "Type": "90F",
            "Element": self.extract_field(data, "e"),
            "Unit": self.extract_field(data, "u"),
            "PreElementParent": self.extract_field(data, "p"),
            "Indenting": self.extract_field(data, "i"),
            "Precision": self.extract_field(data, "d"),
            "CountedAs": self.extract_field(data, "s"),
            "CalculationParent": self.extract_field(data, "ma"),
            "Period": self.extract_field(data, "c"),
            "Axis_Member": self.extract_field(data, "h"),
            "PreferredLabel": self.extract_field(data, "n"),
            "PreferredLabelType": self.extract_field(data, "y"),
            "Table": self.extract_field(data, "t"),
            "LineItem": self.extract_field(data, "l"),
            "RootLevelAbstract": self.extract_field(data, "a"),
            "RoleName": self.extract_field(data, "r"),
            "UniqueId": data[-1],
        }

    def process_tags(self):
        # Process all HTML tags in the list
        formatted_tags = []
        for tag in self.html_tags:
            formatted_data = self.get_formatted_data(tag)
            formatted_tags.append(formatted_data)
        return formatted_tags


# Example usage:
html_tags_list = [
    "apex_ynegatedTotal_90F_eus-gaap--Land_uCanadianDollar_pus-gaap:AssetsAbstract_i01_dn3_sn6_ma7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross_c2024022_hsrt--StatementScenarioAxis__srt--ConsolidatedEntityMember__srt--RestatementAxis__us-gaap--OtherOperatingIncomeExpenseMember_tus-gaap--StatementTable_lTable_aus-gaap--LandAndLandImprovementsAbstract_rStatement_0efb6deb824c493da1b6e03669691c36",
    "apex_ynegatedTotal_90F_eus-gaap--Land_uCanadianDollar_pus-gaap:AssetsAbstract_i01_dn3_sn6_ma7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross_c2024022_hsrt--StatementScenarioAxis__srt--ConsolidatedEntityMember__srt--RestatementAxis__us-gaap--OtherOperatingIncomeExpenseMember_tus-gaap--StatementTable_lTable_aus-gaap--LandAndLandImprovementsAbstract_rStatement_0efb6deb824c493da1b6e03669691c36",
    # Add more HTML tags here
]

# Create an instance of HtmlTagParser
parser = HtmlTagParser(html_tags_list)

# Get the formatted data for all tags
formatted_tags = parser.process_tags()

# Print the formatted data
print(json.dumps(formatted_tags, indent=4))
