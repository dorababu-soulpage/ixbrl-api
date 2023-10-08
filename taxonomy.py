TAXONOMY_IDS = [
    "xdx_980_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--CommercialRealEstateMember_zyRZaioytjQ1",
    "xdx_986_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20230101__20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--CommercialRealEstateMember_z4FQ1c6FDD04",
    "xdx_985_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--CommercialRealEstateMember_zGaeSDgqg7Oh",
    "xdx_986_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20220101__20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--CommercialRealEstateMember_zYH77sKR5fpd",
    "xdx_912_eus-gaap--CommercialRealEstateMember_z0FxegXDAfi3",
    "xdx_98F_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--ResidentialRealEstateMember_zQGL3jxy0Xx3",
    "xdx_988_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20230101__20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--ResidentialRealEstateMember_zBdfZoBbZJg5",
    "xdx_98E_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--ResidentialRealEstateMember_z3hB5jS7iZW",
    "xdx_98C_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20220101__20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--CollateralAxis__us-gaap--ResidentialRealEstateMember_zuSA48DHbZH9",
    "xdx_914_eus-gaap--ConstructionLoansMember_zUdUUGs5uZga",
    "xdx_98C_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__us-gaap--ConstructionLoansMember_zPj5UavOAvyf",
    "xdx_989_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20230101__20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__us-gaap--ConstructionLoansMember_zqNp0UXa9Xbe",
    "xdx_987_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__us-gaap--ConstructionLoansMember_z7rAsgu7gDff",
    "xdx_984_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20220101__20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__us-gaap--ConstructionLoansMember_zFMmDLD8lLUb",
    "xdx_91C_ecustom--BusinessLoanMember_zZlMwW4YpNJk",
    "xdx_987_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__custom--BusinessLoanMember_zbbkNKipCt35",
    "xdx_98D_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20230101__20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__custom--BusinessLoanMember_zGMKrD5jg7m5",
    "xdx_985_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__custom--BusinessLoanMember_zbRauCvd2S44",
    "xdx_986_ecustom--CommercialLoansReceivablePercentage_pip0_dp_c20220101__20221231__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember__us-gaap--FinancingReceivableRecordedInvestmentByClassOfFinancingReceivableAxis__custom--BusinessLoanMember_z83HSLS4Tzsc",
    "xdx_919_eus-gaap--ConsumerLoanMember_zcpL5nW8tS1d",
    "xdx_983_ecustom--CommercialLoansReceivableCarryingAmount_iI_pn3n3_c20230630__us-gaap--FinancialInstrumentAxis__us-gaap--CommercialLoanMember_zfuuzXCKYLzb",


]

unique_contexts = {taxonomy for taxonomy in TAXONOMY_IDS if any(element.startswith("c") for element in taxonomy.split("_"))}


from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

def date_formate(input_date):
    from datetime import datetime

    # Convert the input date to the "YYYY-MM-DD" format
    formatted_date = datetime.strptime(input_date, "%Y%m%d").strftime("%Y-%m-%d")
    return formatted_date

def check_first_two_numbers_or_not(filtered_list):
    # Attempt to convert the first two values to integers
    try:
        first_value = int(filtered_list[0].replace("c", ""))
        second_value = int(filtered_list[1])
        return True
    except ValueError:
        return False
    
def duration_xml(resources, from_, to_):
    # Create the dutation_context element
    dutation_context = ET.SubElement(resources, "xbrli:context", id=f"From{from_}{to_}")
    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(dutation_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier")
    identifier.set("scheme", "http://www.sec.gov/CIK")
    identifier.text = "0000012345"

    # Create xbrli:period element and its child elements
    period = ET.SubElement(dutation_context, "xbrli:period")
    startdate = ET.SubElement(period, "xbrli:startdate")
    startdate.text = date_formate(from_)
    enddate = ET.SubElement(period, "xbrli:enddate")
    enddate.text = date_formate(to_)

def instance_xml(resources, from_):
     # Create the instance_context element
    instance_context = ET.SubElement(resources, "xbrli:context", id=f"AsOf{from_}")
    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(instance_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier")
    identifier.set("scheme", "http://www.sec.gov/CIK")
    identifier.text = "0000012345"

    # Create xbrli:period element and its child elements
    period = ET.SubElement(instance_context, "xbrli:period")
    instant = ET.SubElement(period, "xbrli:instant")
    instant.text = date_formate(from_)

def check_dimension(items):
    # Use a list comprehension to check if any item ends with "Member"
    has_member = any(item.endswith("Member") for item in items)

    if has_member:
        return True
    else:
       return False
    
def duration_dimension_xml(resources, from_, to_,items):
    dimensions = list()
    members = list()
    for item in items:
        if item.startswith("us-gaap") and not item.endswith("Member"):
            dimensions.append(item)
        if item.endswith("Member"):
            members.append(item)
    context_id = f"From{date_formate(from_)}{date_formate(to_)}"
    for member in members:
        context_id+= f"_{member}".replace("--", "_")
    # Create the root element
    duration_dimension_context = ET.SubElement(resources, "xbrli:context", id =context_id)

    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(duration_dimension_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier", scheme="http://www.sec.gov/CIK")
    identifier.text = "0000012345"

    # Create xbrli:segment element and its child elements
    segment = ET.SubElement(entity, "xbrli:segment")

    for dimension, member in zip(dimensions, members):
        explicit_member1 = ET.SubElement(segment, "xbrldi:explicitMember", dimension=f"{dimension}".replace("--",":"))
        explicit_member1.text = f"{member}".replace("--", ":")

    # Create xbrli:period element and its child elements
    period = ET.SubElement(duration_dimension_context, "xbrli:period")
    start_date = ET.SubElement(period, "xbrli:startDate")
    start_date.text = date_formate(from_)
    end_date = ET.SubElement(period, "xbrli:endDate")
    end_date.text = date_formate(to_)


def instance_dimension_xml(resources, from_, items):
    dimensions = list()
    members = list()
    for item in items:
        if item.startswith("us-gaap") and not item.endswith("Member"):
            dimensions.append(item)
        if item.endswith("Member"):
            members.append(item)
    context_id = f"AsOf{date_formate(from_)}"
    for member in members:
        context_id+= f"{member}".replace("--", ":")
    # Create the root element
    instance_dimension_context = ET.SubElement(resources, "xbrli:context", id =context_id)

    # Create xbrli:entity element and its child elements
    entity = ET.SubElement(instance_dimension_context, "xbrli:entity")
    identifier = ET.SubElement(entity, "xbrli:identifier", scheme="http://www.sec.gov/CIK")
    identifier.text = "0000012345"

    # Create xbrli:segment element and its child elements
    segment = ET.SubElement(entity, "xbrli:segment")

    explicit_member = ET.SubElement(segment, "xbrldi:explicitmember", dimension="us-gaap:AcceleratedShareRepurchasesDateAxis")
    explicit_member.text = "us-gaap:AboveMarketLeasesMember"

    for dimension, member in zip(dimensions, members):
        explicit_member1 = ET.SubElement(segment, "xbrldi:explicitMember", dimension=f"{dimension}".replace("--",":"))
        explicit_member1.text = f"{member}".replace("--", ":")

    # Create xbrli:period element and its child elements
    period = ET.SubElement(instance_dimension_context, "xbrli:period")
    instant = ET.SubElement(period, "xbrli:instant")
    instant.text = f"{date_formate(from_)}"



root = ET.Element("ix:header")
# create initial contenxt

# Create the 'ix:resources' element
resources = ET.SubElement(root, "ix:resources")
# Create the 'xbrli:context' element within 'ix:resources'
context = ET.SubElement(resources, "xbrli:context", id="context_id")
# Create the 'xbrli:entity' and 'xbrli:identifier' elements within 'xbrli:context'
entity = ET.SubElement(context, "xbrli:entity")
identifier = ET.SubElement(entity, "xbrli:identifier", scheme="http://www.sec.gov/CIK")
identifier.text = "identifier_text"

# Create the 'xbrli:period' element within 'xbrli:context'
period = ET.SubElement(context, "xbrli:period")
start_date = ET.SubElement(period, "xbrli:startDate")
start_date.text = "start_date_text"
end_date = ET.SubElement(period, "xbrli:endDate")
end_date.text = "end_date_text"

for context in unique_contexts:
    elements = context.split("_")
    for element in elements:
        if element.startswith("c"):
            req_list = elements[elements.index(element):-1]
            # Remove empty values (empty strings) from the list
            filtered_list = [item for item in req_list if item]
            if len(filtered_list) >= 2:
                result = check_first_two_numbers_or_not(filtered_list[:2])
                # if True duration else instance
                from_ = filtered_list[0].replace("c","")
                to_ = filtered_list[1]
                if result:
                    duration_dimension = check_dimension(filtered_list)
                    if duration_dimension:
                        duration_dimension_xml(resources, from_, to_,filtered_list)
                    duration_xml(resources, from_, to_)
                else:
                    instance_dimension = check_dimension(filtered_list)
                    if instance_dimension:
                        instance_dimension_xml(resources, from_,filtered_list)
                    instance_xml(resources, from_)
    # break
# Create an ElementTree object and serialize it to a string
xml_str = ET.tostring(root,encoding="utf-8").decode("utf-8")
soup = BeautifulSoup(xml_str, 'html.parser')
print(soup.prettify())

