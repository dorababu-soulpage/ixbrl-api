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


def create_calculation_loc_element(parent_tag=None, label=None, xlink_href=None):
    return ET.SubElement(
        parent_tag,
        "link:loc",
        attrib={
            "xlink:type": "locator",
            "xlink:label": label,
            "xlink:href": xlink_href,
        },
    )


def create_calculation_arc_element(
    parent_tag=None,
    order=None,
    weight=None,
    arc_role=None,
    xlink_from=None,
    xlink_to=None,
    preferred_label=None,
):
    return ET.SubElement(
        parent_tag,
        "link:calculationArc",
        attrib={
            "order": order,
            "weight": weight,
            "xlink:arcrole": arc_role,
            "xlink:from": xlink_from,
            "xlink:to": xlink_to,
            "xlink:type": "arc",
            "preferredLabel": preferred_label,
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
        "xmlns:link": "http://www.xbrl.org/2003/linkbase",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
    },
)

ticker = "msft"
filing_date = "20230630"
company_website = "http://www.microsoft.com"


# need to loop all the roles
# Create roleRef elements
role_ref_element1 = create_role_ref_element(
    role_uri=f"{company_website}/{filing_date}/taxonomy/role/Role_DocumentDocumentAndEntityInformation",
    xlink_href=f"{ticker}-{filing_date}.xsd#Role_DocumentDocumentAndEntityInformation",
)
role_ref_element2 = create_role_ref_element(
    role_uri=f"{company_website}/{filing_date}/taxonomy/role/Role_StatementINCOMESTATEMENTS",
    xlink_href=f"{ticker}-{filing_date}.xsd#Role_StatementINCOMESTATEMENTS",
)

role_ref_elements = [role_ref_element1, role_ref_element2]

# Create calculation root element
calculation_link = ET.Element(
    "link:calculationLink",
    attrib={
        "xlink:role": f"{company_website}/role/DOCUMENTANDENTITYINFORMATION",
        "xlink:type": "extended",
    },
)

# Add calculation loc elements
loc_cover_abstract = create_calculation_loc_element(
    parent_tag=calculation_link,
    label="loc_dei_CoverAbstract_78b692da-072f-46a4-a033-5240eccee245",
    xlink_href="https://xbrl.sec.gov/dei/2023/dei-2023.xsd#dei_CoverAbstract",
)

loc_entities_table = create_calculation_loc_element(
    parent_tag=calculation_link,
    label="loc_dei_EntitiesTable_67ac2dcd-9ad2-412b-b1f5-329d0c812ae0",
    xlink_href="https://xbrl.sec.gov/dei/2023/dei-2023.xsd#dei_EntitiesTable",
)

# Add calculation arc elements
calculation_arc = create_calculation_arc_element(
    parent_tag=calculation_link,
    order="1",
    weight="-1.0",
    arc_role="http://www.xbrl.org/2003/arcrole/parent-child",
    xlink_from="loc_dei_CoverAbstract_78b692da-072f-46a4-a033-5240eccee245",
    xlink_to="loc_dei_EntitiesTable_67ac2dcd-9ad2-412b-b1f5-329d0c812ae0",
    preferred_label="http://www.xbrl.org/2003/role/terseLabel",
)


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
    + "\n"
    + ET.tostring(calculation_link, encoding="utf-8").decode()
)

# Print or use xml_data as needed

# Optionally, write the XML to a file
with open("cal.xml", "w", encoding="utf-8") as file:
    file.write(xml_data)
