import os
import re
import json
from bs4 import BeautifulSoup


class EDGARValidations:
    def __init__(self, filename):
        self.errors = {}
        self.filename = filename

    def validate_filename(self):
        file_name = os.path.basename(self.filename)
        # Check length
        if len(file_name) > 32:
            self.errors["length"] = "File name must be no longer than 32 characters."

        # Check if the name starts with a letter or number
        if not re.match("^[a-zA-Z0-9]", file_name):
            self.errors["start"] = (
                "File name must start with a letter (a-z) or a number (0-9)."
            )

        # Check for spaces
        if " " in file_name:
            self.errors["spaces"] = "File name may not contain spaces."

        # Check for valid characters
        if not re.match("^[a-zA-Z0-9\.\-\_]+$", file_name):
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

    def read_html(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                html_content = file.read()
                return html_content
        except FileNotFoundError:
            self.errors["file"] = f"File not found: {self.filename}"
        except Exception as e:
            self.errors["file"] = f"An error occurred: {e}"

    def initialize_soup(self):
        html_content = self.read_html()

        if html_content is not None:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup
        else:
            print("HTML content is not loaded. Call read_html_file first.")

    def validate_html_file(self):
        html_content = self.read_html()

        characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz`~!@#$%&*().-+ {}[]|\\:;\"'<>,_?/="
        allowed_characters = set(characters)

        if html_content:
            for char in html_content:
                if char not in allowed_characters:
                    self.errors[char] = f"Invalid character: {char}"
            return True

    def validate_html_tags(self):
        html_content = self.read_html()

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
        if html_content:
            for tag in unsupported_tags:
                if re.search(tag, html_content, re.IGNORECASE):
                    self.errors[tag] = "Unsupported tag found."

            return True

    def validate_href(self):
        soup = self.initialize_soup()
        if soup:
            # Find all 'a' tags
            all_a_tags = soup.find_all("a")

            for a_tag in all_a_tags:
                # Get the 'href' attribute from the 'a' tag
                href = a_tag.get("href", "")

                if href.startswith(("http://", "https://")):

                    # Validation function with error messages
                    self.errors[f"Error in <a> tag"] = {
                        "error": "Invalid HREF format",
                        "href": href,
                    }
                return None

    def validate_img_attributes(self):
        soup = self.initialize_soup()
        if soup:
            # Find all image tags in the HTML
            img_tags = soup.find_all("img")

        # Extract attributes from each image tag
        attributes_list = []
        forbidden_attributes = ["DYNSRC", "LOOP", "LOOPDELAY", "START", "CONTROLS"]
        for img_tag in img_tags:
            attributes = img_tag.attrs
            attributes_list.append(attributes)

        # Check if any attribute is forbidden
        for attribute in attributes_list:
            if attribute in forbidden_attributes:
                self.errors["Image tag"] = f"Attribute '{attribute}' is forbidden."

    def validate_char(self):
        html_content = self.read_html()
        if html_content:
            # Mapping dictionary
            char_mapping = {
                # "f": "&#131;",
                "...": "&#133;",
                # "t": "&#134;",
                "‡": "&#135;",
                "1": "",
                "%0": "&#137;",
                "Š": "&#138;",
                "<": "&#139;",
                "Œ": "&#140;",
                "•": "&#149;",
                "™": "&#153;",
                "š": "&#154;",
                ">": "&#155;",
                "œ": "&#156;",
                "Ÿ": "&#159;",
                " ": "&#160;",
                # "¡": "&#161;",
                "¢": "&#162;",
                "£": "&#163;",
                "¤": "&#164;",
                "¥": "&#165;",
                "§": "&#167;",
                "¨": "&#168;",
                "©": "&#169;",
                "ª": "&#170;",
                "«": "&#171;",
                "®": "&#174;",
                "¯": "&#175;",
                "°": "&#176;",
                "±": "&#177;",
                "²": "&#178;",
                "³": "&#179;",
                "'": "&#180;",
                "µ": "&#181;",
                "·": "&#183;",
                "¸": "&#184;",
                "¹": "&#185;",
                "º": "&#186;",
                "»": "&#187;",
                "¼": "&#188;",
                "½": "&#189;",
                "¾": "&#190;",
                "¿": "&#191;",
            }
            for key, value in char_mapping.items():
                html_content = html_content.replace(key, value)

    def validate(self):
        self.validate_filename()
        self.validate_html_file()
        self.validate_html_tags()
        self.validate_href()
        self.validate_img_attributes()
        # self.validate_char()
        return True if not self.errors else self.errors


# Example usage:
# file_name = "r10q-630.htm"
file_name = "data/fult4200081_8k.htm"
validator = EDGARValidations(file_name)
validation_result = validator.validate()

if validation_result is True:
    print(f"{file_name} is a valid file.")
else:
    print(
        f"{file_name} is not a valid file.\nErrors: \n{json.dumps(validation_result , indent=4)}"
    )
