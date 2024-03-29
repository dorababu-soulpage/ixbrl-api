import re
import json


class HtmlTagParser:
    def __init__(self, html_tag):
        self.html_tag = html_tag
        self.data = re.findall(r"[^_]+(?:__[^_]+)*|__", html_tag)

    def extract_field(self, prefix):
        for item in self.data[1:]:
            if item.startswith(prefix):
                return item.lstrip(prefix)
        return ""

    def get_formatted_data(self):
        return {
            "Type": "90F",
            "Element": self.extract_field("e"),
            "Unit": self.extract_field("u"),
            "PreElementParent": self.extract_field("p"),
            "Indenting": self.extract_field("i"),
            "Precision": self.extract_field("d"),
            "CountedAs": self.extract_field("s"),
            "CalculationParent": self.extract_field("ma"),
            "Period": self.extract_field("c"),
            "Axis_Member": self.extract_field("h"),
            "PreferredLabel": self.extract_field("n"),
            "PreferredLabelType": self.extract_field("y"),
            "Table": self.extract_field("t"),
            "LineItem": self.extract_field("l"),
            "RootLevelAbstract": self.extract_field("a"),
            "RoleName": self.extract_field("r"),
            "UniqueId": self.data[-1],
        }


# Example usage:
html_tag = "apex_ynegatedTotal_90F_eus-gaap--Land_uCanadianDollar_pus-gaap:AssetsAbstract_i01_dn3_sn6_ma7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross_c2024022_hsrt--StatementScenarioAxis__srt--ConsolidatedEntityMember__srt--RestatementAxis__us-gaap--OtherOperatingIncomeExpenseMember_tus-gaap--StatementTable_lTable_aus-gaap--LandAndLandImprovementsAbstract_rStatement_0efb6deb824c493da1b6e03669691c36"

parser = HtmlTagParser(html_tag)
formatted_data = parser.get_formatted_data()
print(json.dumps(formatted_data, indent=4))
