import xml.etree.ElementTree as ET


def create_role_ref_element(role_uri=None, xlink_href=None):
    return ET.Element(
        "link:roleRef",
        attrib={
            "roleURI": role_uri,
            "xlink:href": xlink_href,
            "xlink:type": "simple",
        },
    )


def create_label_link_element(xlink_role=None, xlink_title=None):
    return ET.Element(
        "link:labelLink",
        attrib={
            "xlink:role": xlink_role,
            "xlink:title": xlink_title,
            "xlink:type": "extended",
        },
    )


def create_label_element(id=None, xlink_label=None):
    return ET.Element(
        "link:label",
        attrib={
            "id": id,
            "xlink:label": xlink_label,
            "xlink:role": "http://www.xbrl.org/2003/role/terseLabel",
            "xlink:type": "resource",
            "xmlns:xml": "http://www.w3.org/XML/1998/namespace",
            "xml:lang": "en-US",
        },
    )


def create_label_loc_element(label=None, xlink_href=None):
    return ET.Element(
        "link:loc",
        attrib={
            "xlink:type": "locator",
            "xlink:label": label,
            "xlink:href": xlink_href,
        },
    )


def create_label_arc_element(order=None, arc_role=None, xlink_from=None, xlink_to=None):
    return ET.Element(
        "link:labelArc",
        attrib={
            "order": order,
            "xlink:arcrole": arc_role,
            "xlink:from": xlink_from,
            "xlink:to": xlink_to,
            "xlink:type": "arc",
        },
    )


# Create an XML declaration
xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'

# Create comments after the XML declaration
comments_after_declaration = [
    "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
    "<!-- Creation Date : -->",
    "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
]

linkbase_element = ET.Element(
    "link:linkbase",
    attrib={
        "xsi:schemaLocation": "http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
        "xmlns:link": "http://www.xbrl.org/2003/linkbase",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    },
)


ticker = "msft"
filing_date = "20230630"
company_website = "http://www.microsoft.com"


# need to loop all the roles
# Create roleRef elements
role_ref_element1 = create_role_ref_element(
    role_uri="http://www.xbrl.org/2009/role/negatedLabel",
    xlink_href="http://www.xbrl.org/lrr/role/negated-2009-12-16.xsd#negatedLabel",
)

role_ref_element2 = create_role_ref_element(
    role_uri="http://www.xbrl.org/2009/role/negatedLabel",
    xlink_href="http://www.xbrl.org/lrr/role/negated-2009-12-16.xsd#negatedLabel",
)

label_link_element = create_label_link_element(
    xlink_role="http://www.xbrl.org/2003/role/link", xlink_title="labelLink"
)

label_element1 = create_label_element(
    id="lab_us-gaap_OtherShortTermInvestments_234723b2-7343-476f-b9a9-f832cb18bd36_terseLabel_en-US",
    xlink_label="lab_us-gaap_OtherShortTermInvestments",
)

label_element2 = create_label_element(
    id="lab_us-gaap_OtherShortTermInvestments_234723b2-7343-476f-b9a9-f832cb18bd36_terseLabel_en-US",
    xlink_label="lab_us-gaap_OtherShortTermInvestments",
)

label_loc_element1 = create_label_loc_element(
    label="loc_us-gaap_OtherShortTermInvestments",
    xlink_href="https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd#us-gaap_OtherShortTermInvestments",
)

label_arc_element1 = create_label_arc_element(
    order="1",
    arc_role="http://www.xbrl.org/2003/arcrole/concept-label",
    xlink_from="loc_us-gaap_OtherShortTermInvestments",
    xlink_to="lab_us-gaap_OtherShortTermInvestments",
)

role_ref_elements = [
    role_ref_element1,
    role_ref_element2,
    label_link_element,
    label_element1,
    label_element2,
    label_loc_element1,
    label_arc_element1,
]

# Convert each role_ref_element to XML string and concatenate
role_ref_elements_xml = "\n".join(
    [ET.tostring(e, encoding="utf-8").decode() for e in role_ref_elements]
)

# Concatenate XML declaration, comments, and linkbase element
xml_data = (
    xml_declaration
    + "\n".join(comments_after_declaration)
    + "\n"
    + ET.tostring(linkbase_element, encoding="utf-8").decode()
    + "\n"
    + role_ref_elements_xml  # Use the concatenated XML string
)

# Print or use xml_data as needed

# Optionally, write the XML to a file
with open("lab.xml", "w", encoding="utf-8") as file:
    file.write(xml_data)
