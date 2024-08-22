import re
import json
from xml_generation.constants import (
    states_sort_list,
    county_sort_list,
    state_country_sort_list,
)


class FormatValueRetriever:
    def __init__(self, input_text: str = None):
        self.input_text = input_text.replace("(", "").strip()
        self.format_file_path = "assets/format.json"

    def get_format_value(self, element: str, data_type: str):
        if element.endswith("DocumentPeriodEndDate"):
            return "ixt:date-monthname-day-year-en"

        if self.input_text in ["no", "None"]:
            return "ixt-sec:numwordsen"

        if self.input_text == "-":
            return "ixt:fixed-zero"

        check_boxes = ["☐", "☑", "☒"]

        if data_type == "dei:yesNoItemType" and self.input_text in check_boxes:
            return "ixt-sec:yesnoballotbox"

        if data_type == "xbrli:booleanItemType" and self.input_text in check_boxes:
            return "ixt-sec:boolballotbox"

        if data_type in [
            "xbrli:monetaryItemType",
            "xbrli:sharesItemType",
            "xbrli:integerItemType",
            "srt-types:perUnitItemType",
            "dtr-types:areaItemType",
            "dtr-types:energyItemType",
            "dtr-types:massItemType",
            "dtr-types:flowItemType",
        ]:
            # Patterns to match each format
            numcommadecdimal_pattern = re.compile(r"^\d{1,3}(?:[\.\s]?\d{3})*,\d{1,2}$")
            numdotdecimal_pattern = re.compile(
                r"^\d{1,3}(?:[,\s]?\d{3})*(?:\.\d{1,2})?$"
            )
            numdotdecimalin_pattern = re.compile(
                r"^\d{1,2}(?:[,\s]?\d{2})*(?:\.\d{1,2})?$"
            )
            no_none = re.compile(r"^[A-Za-z\s]+$|^(no|None)$")

            if numcommadecdimal_pattern.match(self.input_text):
                return "ixt:num-comma-decimal"
            elif numdotdecimal_pattern.match(self.input_text):
                return "ixt:num-dot-decimal"
            elif numdotdecimalin_pattern.match(self.input_text):
                return "ixt:num-unit-decimal"

            elif re.match(r".*", self.input_text):  # This regex matches any string
                return "ixt:fixed-zero"

        if data_type in ["xbrli:dateItemType", "xbrli:gMonthDayItemType"]:
            # Patterns to match each format
            datedaymonthyear_pattern = re.compile(r"^\d{1,2}[./]\d{1,2}[./]\d{4}$")
            datemonthdayyear_pattern = re.compile(r"^\d{2}[./]\d{2}[./]\d{4}$")
            # Corrected pattern
            datemonthdayyearen_pattern = re.compile(r"^[A-Za-z]+\s\d{1,2},\s\d{4}$")
            datedaymonthyearen_pattern = re.compile(r"^\d{2}-[A-Za-z]{3}-\d{2}$")
            dateyearmonthday_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

            if datedaymonthyear_pattern.match(self.input_text):
                return "ixt:date-day-month-year"
            elif datedaymonthyearen_pattern.match(self.input_text):
                return "ixt:date-day-month-year-en"

            elif datemonthdayyear_pattern.match(self.input_text):
                return "ixt:date-month-day-year"
            elif datemonthdayyearen_pattern.match(self.input_text):
                return "ixt:date-monthname-day-year-en"
            elif dateyearmonthday_pattern.match(self.input_text):
                return "ixt:date-year-month-day"

        if data_type == "dei:edgarExchangeCodeItemType":
            return "ixt-sec:exchnameen"

        if data_type == "dei:stateOrProvinceItemType":
            if self.input_text not in states_sort_list:
                return "ixt-sec:stateprovnameen"

        if data_type == "dei:countryCodeItemType":
            if self.input_text not in county_sort_list:
                return "ixt-sec:countrynameen"

        category_list = [
            "Large accelerated filer",
            "accelerated filer",
            "Non-Accelerated Filer",
        ]
        if data_type == "dei:filerCategoryItemType" and category_list:
            return "ixt-sec:entityfilercategoryen"

        if data_type == "dei:edgarStateCountryItemType":
            if self.input_text not in state_country_sort_list:
                return "ixt-sec:stateprovnameen"

        if data_type == "xbrli:durationItemType":
            # Patterns to match each input format
            patterns = {
                # Matches -5.67, 5.67, -22.3456, 22.3456
                "ixt-sec:duryear": re.compile(r"^-?\d+\.\d+$"),
                "ixt-sec:durmonth": re.compile(r"^\d+\.\d+$"),  # Matches 5.67, 22.3456
                "ixt-sec:durweek": re.compile(r"^\d+$"),  # Matches 0
                "ixt-sec:durday": re.compile(r"^\d+\.\d+$"),  # Matches 0.000001
                "ixt-sec:durhour": re.compile(r"^\d+$"),  # Matches 1000
                "ixt-sec:durwordsen": re.compile(
                    r"^\d+\syears?,\s\d+\smonths?$|^[A-Za-z]+\syears?,\s[A-Za-z]+\smonths?$"
                ),  # Matches durations in words or numbers
                # "ixt-sec:numwordsen": re.compile(
                #     r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)(?:[\s-](?:and[\s-])?(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)?)*\b.*$"
                # ),  # Matches
            }

            # Check each pattern
            for format_code, pattern in patterns.items():
                if pattern.match(self.input_text, re.IGNORECASE):
                    return format_code

        if data_type == "xbrli:durationItemType":
            # Define the regex pattern
            pattern = r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)(?:[\s-](?:and[\s-])?(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)?)*\b.*$"
            if re.search(pattern, self.input_text, re.IGNORECASE):
                return "ixt-sec:numwordsen"


# # Usage:
# input_text = "FORTY TWO milestones"
# data_type = "xbrli:durationItemType"
# element = "usgap:Cash"
# retriever = FormatValueRetriever(input_text)
# format_value = retriever.get_format_value(element, data_type)
# print(format_value)
