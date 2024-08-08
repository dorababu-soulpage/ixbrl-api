import re
import json


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

        # if data_type == "dei:yesNoItemType" and self.input_text in ["☐", "☑", "☒"]:
        if data_type == "dei:yesNoItemType":
            return "ixt-sec:yesnoballotbox"

        # if data_type == "xbrli:booleanItemType" and self.input_text in ["☐", "☑", "☒"]:
        if data_type == "xbrli:booleanItemType":
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

            elif no_none.match(self.input_text):
                return "ixt-sec:numwordsen"

            elif re.match(r".*", self.input_text):  # This regex matches any string
                return "ixt:fixed-zero"

        if data_type in ["xbrli:dateItemType", "xbrli:gMonthDayItemType"]:
            # Patterns to match each format
            datedaymonthyear_pattern = re.compile(r"^\d{1,2}[./]\d{1,2}[./]\d{4}$")
            datemonthdayyear_pattern = re.compile(r"^\d{2}[./]\d{2}[./]\d{4}$")
            datemonthdayyearen_pattern = re.compile(r"^[A-Za-z]+\s\d{2},\s\d{4}$")
            datedaymonthyearen_pattern = re.compile(r"^\d{2}-[A-Za-z]{3}-\d{2}$")
            dateyearmonthday_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

            if datedaymonthyear_pattern.match(self.input_text):
                return "ixt:datedaymonthyear"
            elif datemonthdayyear_pattern.match(self.input_text):
                return "ixt:datemonthdayyear"
            elif datemonthdayyearen_pattern.match(self.input_text):
                return "ixt:datemonthdayyearen"
            elif datedaymonthyearen_pattern.match(self.input_text):
                return "ixt:datedaymonthyearen"
            elif dateyearmonthday_pattern.match(self.input_text):
                return "ixt:dateyearmonthday"

        if data_type == "dei:edgarExchangeCodeItemType":
            return "ixt-sec:exchnameen"

        if data_type == "dei:stateOrProvinceItemType":
            return "ixt-sec:stateprovnameen"

        if data_type == "dei:countryCodeItemType":
            return "ixt-sec:edgarprovcountryen"

        if data_type == "dei:countryCodeItemType":
            return "ixt-sec:countrynameen"

        category_list = [
            "Large accelerated filer",
            "accelerated filer",
            "Non-Accelerated Filer",
        ]
        if data_type == "dei:filerCategoryItemType" and category_list:
            return "ixt-sec:entityfilercategoryen"

        if data_type == "dei:edgarStateCountryItemType":
            return "ixt-sec:edgarprovcountryen"

        if data_type == ["xbrli:durationItemType", "xbrli:stringItemType"]:
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
                "ixt-sec:numwordsen": re.compile(
                    r"^[A-Za-z\s]+$|^(no|None)$"
                ),  # Matches any string of words including specific "no" and "None"
            }

            # Check each pattern
            for format_code, pattern in patterns.items():
                if pattern.match(self.input_text):
                    return format_code

    #     else:
    #         return self._retrieve_format_from_file(data_type)

    # def _retrieve_format_from_file(self, data_type):

    #     with open(self.format_file_path, "r") as json_file:
    #         data = json.load(json_file)

    #         for record in data:
    #             if (
    #                 record.get("Datatype 1") == data_type
    #                 or record.get("Datatype 2") == data_type
    #                 or record.get("Datatype 3") == data_type
    #                 or record.get("Datatype 4") == data_type
    #             ):
    #                 return record.get("Format Code", "")
    #         return ""


# Usage:
# input_text = "Property and Equipment-at cost"
# data_type = "xbrli:stringItemType"
# element = "usgap:Cash"
# retriever = FormatValueRetriever(input_text)
# format_value = retriever.get_format_value(element, data_type)
# print(format_value)
