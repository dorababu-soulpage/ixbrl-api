import xml.etree.ElementTree as ET


def generate_xsd_schema(definitions, ticker, filing_date, company_website):
    # Create an XML declaration
    xml_declaration = '<?xml version="1.0" encoding="US-ASCII"?>\n'

    # Create comments after the XML declaration
    comments_after_declaration = [
        "<!-- APEX iXBRL XBRL Schema Document - https://apexcovantage.com -->",
        "<!-- Creation Date : -->",
        "<!-- Copyright (c) Apex CoVantage All Rights Reserved. -->",
    ]

    # Concatenate XML declaration and comments
    xml_data = xml_declaration + "\n".join(comments_after_declaration) + "\n"

    # Create the root element
    root = ET.Element(
        "xsd:schema",
        attrib={
            "targetNamespace": f"{company_website}/{filing_date}",
            "attributeFormDefault": "unqualified",
            "elementFormDefault": "qualified",
            "xmlns:dtr-types": "http://www.xbrl.org/dtr/type/2022-03-31",
            "xmlns:country": "http://xbrl.sec.gov/country/2023",
            "xmlns:ecd-sub": "http://xbrl.sec.gov/ecd-sub/2023",
            f"xmlns:{ticker}": f"{company_website}/{filing_date}",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
            "xmlns:link": "http://www.xbrl.org/2003/linkbase",
            "xmlns:dei": "http://xbrl.sec.gov/dei/2023",
            "xmlns:xbrldt": "http://xbrl.org/2005/xbrldt",
            "xmlns:xbrli": "http://www.xbrl.org/2003/instance",
            "xmlns:enum2": "http://xbrl.org/2020/extensible-enumerations-2.0",
            "xmlns:srt": "http://fasb.org/srt/2023",
            "xmlns:us-gaap": "http://fasb.org/us-gaap/2023",
            "xmlns:xlink": "http://www.w3.org/1999/xlink",
        },
    )

    # Create xsd:import elements
    xsd_imports = [
        {
            "schemaLocation": "http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd",
            "namespace": "http://www.xbrl.org/2003/instance",
        },
        {
            "schemaLocation": "http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
            "namespace": "http://www.xbrl.org/2003/linkbase",
        },
        {
            "schemaLocation": "http://www.xbrl.org/2005/xbrldt-2005.xsd",
            "namespace": "http://xbrl.org/2005/xbrldt",
        },
        {
            "schemaLocation": "https://xbrl.sec.gov/dei/2023/dei-2023.xsd",
            "namespace": "http://xbrl.sec.gov/dei/2023",
        },
        {
            "schemaLocation": "https://www.xbrl.org/2020/extensible-enumerations-2.0.xsd",
            "namespace": "http://xbrl.org/2020/extensible-enumerations-2.0",
        },
        {
            "schemaLocation": "https://xbrl.sec.gov/ecd/2023/ecd-sub-2023.xsd",
            "namespace": "http://xbrl.sec.gov/ecd-sub/2023",
        },
        {
            "schemaLocation": "https://www.xbrl.org/dtr/type/2022-03-31/types.xsd",
            "namespace": "http://www.xbrl.org/dtr/type/2022-03-31",
        },
        {
            "schemaLocation": "https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd",
            "namespace": "http://fasb.org/us-gaap/2023",
        },
        {
            "schemaLocation": "https://xbrl.sec.gov/country/2023/country-2023.xsd",
            "namespace": "http://xbrl.sec.gov/country/2023",
        },
        {
            "schemaLocation": "https://xbrl.fasb.org/srt/2023/elts/srt-2023.xsd",
            "namespace": "http://fasb.org/srt/2023",
        },
    ]

    for xsd_import in xsd_imports:
        xsd_import_element = ET.Element("xsd:import", attrib=xsd_import)
        root.append(xsd_import_element)

    # Create xsd:annotation and xsd:appinfo elements
    xsd_annotation = ET.Element("xsd:annotation")
    xsd_appinfo = ET.Element("xsd:appinfo")

    # Create link:linkbaseRef elements
    linkbase_refs = [
        {
            "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
            "xlink:href": f"{ticker}-{filing_date}_lab.xml",
            "xlink:role": "http://www.xbrl.org/2003/role/labelLinkbaseRef",
            "xlink:title": "Labels link",
            "xlink:type": "simple",
        },
        {
            "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
            "xlink:href": f"{ticker}-{filing_date}_pre.xml",
            "xlink:role": "http://www.xbrl.org/2003/role/presentationLinkbaseRef",
            "xlink:title": "Presentation link",
            "xlink:type": "simple",
        },
        {
            "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
            "xlink:href": f"{ticker}-{filing_date}_def.xml",
            "xlink:role": "http://www.xbrl.org/2003/role/definitionLinkbaseRef",
            "xlink:title": "Definition link",
            "xlink:type": "simple",
        },
        {
            "xlink:arcrole": "http://www.w3.org/1999/xlink/properties/linkbase",
            "xlink:href": f"{ticker}-{filing_date}_cal.xml",
            "xlink:role": "http://www.xbrl.org/2003/role/calculationLinkbaseRef",
            "xlink:title": "Calculation link",
            "xlink:type": "simple",
        },
    ]

    for linkbase_ref in linkbase_refs:
        linkbase_ref_element = ET.Element("link:linkbaseRef", attrib=linkbase_ref)
        xsd_appinfo.append(linkbase_ref_element)

    for record in definitions:
        # HTML attributes values start from here
        # Create link:roleType element
        role = record.get("role", "")
        definition = record.get("definition", "")
        link_role_type = ET.Element(
            "link:roleType",
            attrib={
                "roleURI": f"{company_website}/{filing_date}/role/{role}",
                "id": role,
            },
        )

        # Create child elements for link:roleType
        link_role_type_elements = [
            {
                "tag": "link:definition",
                "text": definition,
            },
            {"tag": "link:usedOn", "text": "link:presentationLink"},
            {"tag": "link:usedOn", "text": "link:calculationLink"},
            {"tag": "link:usedOn", "text": "link:definitionLink"},
        ]

        for element_info in link_role_type_elements:
            element = ET.Element(element_info["tag"])
            element.text = element_info["text"]
            link_role_type.append(element)

        # Append link:roleType to xsd:appinfo
        xsd_appinfo.append(link_role_type)

    # Append xsd:appinfo to xsd:annotation
    xsd_annotation.append(xsd_appinfo)

    # Append xsd:annotation to root
    root.append(xsd_annotation)

    # Serialize only the root element and its children
    xml_data += ET.tostring(root, encoding="US-ASCII").decode("utf-8")
    filename = f"{ticker}-{filing_date}.xsd"
    # Optionally, write the XML to a file
    with open(filename, "w", encoding="US-ASCII") as file:
        file.write(xml_data)


# ticker = "msft"
# filing_date = "20230630"
# company_website = "http://www.microsoft.com"
# generate_xml_schema(ticker, filing_date, company_website)