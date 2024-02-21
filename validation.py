import re
import json


class EDGARValidations:
    def __init__(self, filename):
        self.errors = {}
        self.filename = filename

    def validate_filename(self):

        # Check length
        if len(self.filename) > 32:
            self.errors["length"] = "File name must be no longer than 32 characters."

        # Check if the name starts with a letter or number
        if not re.match("^[a-zA-Z0-9]", self.filename):
            self.errors["start"] = (
                "File name must start with a letter (a-z) or a number (0-9)."
            )

        # Check for spaces
        if " " in self.filename:
            self.errors["spaces"] = "File name may not contain spaces."

        # Check for valid characters
        if not re.match("^[a-zA-Z0-9\.\-\_]+$", self.filename):
            self.errors["characters"] = (
                "File name may only contain letters, numbers, periods, hyphens, and underscores."
            )

        # Check for valid extensions
        valid_extensions = [
            ".htm",
            ".txt",
            ".pdf",
            ".fil",
            ".jpg",
            ".gif",
            ".xsd",
            ".xml",
        ]
        if not any(self.filename.lower().endswith(ext) for ext in valid_extensions):
            self.errors["extensions"] = (
                "File name must end with a valid extension: *.htm, *.txt, *.pdf, *.fil, *.jpg, *.gif, *.xsd, or *.xml."
            )

        return True

    def open_file(self):
        filename = self.filename
        try:
            with open(filename, "r", encoding="utf-8") as file:
                html_contents = file.read()
                return html_contents

        except FileNotFoundError:
            self.errors["file"] = f"File not found: {filename}"
        except Exception as e:
            self.errors["file"] = f"An error occurred: {e}"

    def validate_html_file(self):
        html_contents = self.open_file()

        characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz`~!@#$%&*().-+ {}[]|\\:;\"'<>,_?/="
        allowed_characters = set(characters)

        for char in html_contents:
            if char not in allowed_characters:
                self.errors[char] = f"Invalid character: {char}"
        return True

    def validate_html_tags(self):
        # List of unsupported HTML tags
        unsupported_tags = [
            r"<ACRONYM>",
            r"<APPLET>",
            r"<AREA>",
            r"<BASE>",
            r"<BASEFONT>",
            r"<BDO>",
            r"<BUTTON>",
            r"<COL>",
            r"<COLGROUP>",
            r"<DEL>",
            r"<EMBED>",
            r"<FIELDSET>",
            r"<FORM>",
            r"<FRAME>",
            r"<FRAMESET>",
            r"<IFRAME>",
            r"<INPUT>",
            r"<INS>",
            r"<LABEL>",
            r"<LEGEND>",
            r"<MAP>",
            r"<META HTTP_EQUIV…>",
            r"<NOFRAMES>",
            r"<NOSCRIPT>",
            r"<OBJECT>",
            r"<OPTION>",
            r"<PARAM>",
            r"<Q>",
            r"<S>",
            r"<C>",
            r"<FN>",
            r"<F1>",
            r"<F2>",
            r"<SUP>",
            r"<SUB>",
            r"<SCRIPT>",
            r"<SELECT>",
            r"<SPAN>",
            r"<TBODY>",
            r"<TEXTAREA>",
            r"<TFOOT>",
            r"<THEAD>",
            r"<!DOCTYPE>",
            r"<!ELEMENT>",
            r"<!ENTITY>",
        ]

        # Check for unsupported tags in the HTML content
        html_content = self.open_file()
        for tag in unsupported_tags:
            if re.search(tag, html_content, re.IGNORECASE):
                self.errors[tag] = "Unsupported tag found."

        return True

    def validate(self):
        self.validate_filename()
        self.validate_html_file()
        self.validate_html_tags()
        return True if not self.errors else self.errors


# Example usage:
# file_name = "r10q-630.htm"
file_name = "fult4200081_8k.htm"
validator = EDGARValidations(file_name)
validation_result = validator.validate()

if validation_result is True:
    print(f"{file_name} is a valid file.")
else:
    print(
        f"{file_name} is not a valid file.\nErrors: \n{json.dumps(validation_result , indent=4)}"
    )
