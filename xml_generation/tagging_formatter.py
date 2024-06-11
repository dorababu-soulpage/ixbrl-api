import re
import json


class FormatValueRetriever:
    def __init__(self, input_text=None):
        self.input_text = input_text
        self.format_file_path = "assets/format.json"

    def get_format_value(self, element, data_type):
        if element.endswith("DocumentPeriodEndDate"):
            return "ixt:datemonthdayyearen"

        if data_type in [
            "xbrli:monetaryItemType",
            "xbrli:sharesItemType",
            "xbrli:integerItemType",
            "srt-types:perUnitItemType",
        ]:
            # Patterns to match each format
            numcommadecdimal_pattern = re.compile(r"^\d{1,3}(?:[\.\s]?\d{3})*,\d{2}$")
            numdotdecimal_pattern = re.compile(r"^\d{1,3}(?:[,\s]?\d{3})*(?:\.\d{2})?$")
            numdotdecimalin_pattern = re.compile(
                r"^\d{1,2}(?:[,\s]?\d{2})*(?:\.\d{2})?$"
            )

            if numcommadecdimal_pattern.match(self.input_text):
                return "ixt:numcommadecdimal"
            elif numdotdecimal_pattern.match(self.input_text):
                return "ixt:numdotdecimal"
            elif numdotdecimalin_pattern.match(self.input_text):
                return "ixt:numdotdecimalin"
        else:
            return self._retrieve_format_from_file(data_type)

    def _retrieve_format_from_file(self, data_type):

        with open(self.format_file_path, "r") as json_file:
            data = json.load(json_file)

            for record in data:
                if (
                    record.get("Datatype 1") == data_type
                    or record.get("Datatype 2") == data_type
                    or record.get("Datatype 3") == data_type
                    or record.get("Datatype 4") == data_type
                ):
                    return record.get("Format Code", "")
            return ""


# Usage:
# retriever = FormatValueRetriever()
# format_value = retriever.get_format_value(element, data_type, input_text)
