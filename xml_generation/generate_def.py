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


def create_arc_role_ref_element(arc_role_uri=None, xlink_href=None):
    return ET.Element(
        "link:arcroleRef",
        attrib={
            "arcroleURI": arc_role_uri,
            "xlink:href": xlink_href,
            "xlink:type": "simple",
        },
    )


def create_definition_loc_element(parent_tag=None, label=None, xlink_href=None):
    return ET.SubElement(
        parent_tag,
        "link:loc",
        attrib={
            "xlink:type": "locator",
            "xlink:label": label,
            "xlink:href": xlink_href,
        },
    )


def create_definition_arc_element(
    parent_tag=None, order=None, arc_role=None, xlink_from=None, xlink_to=None
):
    return ET.SubElement(
        parent_tag,
        "link:definitionArc",
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
        "xmlns:xbrldt": "http://xbrl.org/2005/xbrldt",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    },
)


ticker = "msft"
filing_date = "20230630"
company_website = "http://www.microsoft.com"

# need to loop all the arc roles
# create arcRole element
arc_role_ref_element1 = create_arc_role_ref_element(
    arc_role_uri="http://xbrl.org/int/dim/arcrole/all",
    xlink_href="http://www.xbrl.org/2005/xbrldt-2005.xsd#all",
)

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

role_ref_elements = [arc_role_ref_element1, role_ref_element1, role_ref_element2]

# Create definition root element
definition_link = ET.Element(
    "link:definitionLink",
    attrib={
        "xlink:role": f"{company_website}/role/DOCUMENTANDENTITYINFORMATION",
        "xlink:type": "extended",
    },
)

# Add definition loc elements
loc_cover_abstract = create_definition_loc_element(
    parent_tag=definition_link,
    label="loc_dei_CoverAbstract_78b692da-072f-46a4-a033-5240eccee245",
    xlink_href="https://xbrl.sec.gov/dei/2023/dei-2023.xsd#dei_CoverAbstract",
)

loc_entities_table = create_definition_loc_element(
    parent_tag=definition_link,
    label="loc_dei_EntitiesTable_67ac2dcd-9ad2-412b-b1f5-329d0c812ae0",
    xlink_href="https://xbrl.sec.gov/dei/2023/dei-2023.xsd#dei_EntitiesTable",
)

# Add definition arc elements
definition_arc = create_definition_arc_element(
    parent_tag=definition_link,
    order="1",
    arc_role="http://www.xbrl.org/2003/arcrole/parent-child",
    xlink_from="loc_dei_CoverAbstract_78b692da-072f-46a4-a033-5240eccee245",
    xlink_to="loc_dei_EntitiesTable_67ac2dcd-9ad2-412b-b1f5-329d0c812ae0",
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
    + ET.tostring(definition_link, encoding="utf-8").decode()
)

# Print or use xml_data as needed

# Optionally, write the XML to a file
with open("def.xml", "w", encoding="utf-8") as file:
    file.write(xml_data)
