import json
import datetime
import pandas as pd


def find_value_in_nested_dict(input_dict, target_value):
    if isinstance(input_dict, list):
        for record in input_dict:
            result = find_value_in_nested_dict(record, target_value)
            if result:
                return result
    elif isinstance(input_dict, dict):
        for key, value in input_dict.items():
            if value == target_value:
                return input_dict
            if isinstance(value, (dict, list)):
                result = find_value_in_nested_dict(value, target_value)
                if result:
                    return result
    return None


def write_into_json_file(input_dict, output_file="output.json"):
    with open(output_file, "w") as file:
        json.dump(input_dict, file, indent=4)
        print(f"data successfully inserted in {output_file}")


def get_icon(element):
    icon_mapping = {
        "xbrli:item": "abstractItem" if element["abstract"] == True else "item",
        "xbrldt:hypercubeItem": "hypercube",
        "xbrldt:dimensionItem": "dimension",
    }

    substitution_group = element["substitutionGroup"]
    icon = icon_mapping.get(substitution_group, None)
    return icon


def create_node(row, cn):
    return {
        "na": f"{row['prefix']}:{row['name']}",
        "lb": row["label_x"],
        "ic": get_icon(row),
        "cn": cn,
        "nd": [],
    }


def merge_el_and_pr_sheets(excel_file, sheet1, sheet2):
    # Read Excel sheets into DataFrames
    elements_df = pd.read_excel(excel_file, sheet_name=sheet1)
    presentation_df = pd.read_excel(excel_file, sheet_name=sheet2)

    presentation_df["id"] = presentation_df.index + 1
    presentation_df["cn"] = ""

    presentation_df["deprecated"] = ""
    # Joining Elements on Presentation using both 'name' and 'prefix' columns
    merged_df = presentation_df.merge(
        elements_df, how="inner", on=["name", "prefix"]
    ).sort_values("id")
    # merged_df.to_excel(f"{sheet1}_{sheet2}.xlsx")
    merged_df.rename(columns={"type": "dataType", "periodType": "period"}, inplace=True)

    return merged_df


def main(xlsx_file, sheet1, sheet2, output_file):
    defs = []
    prefix = []
    period = []
    balance = []
    abstract = []
    dataType = []
    deprecated = []
    taxonomy_data = []

    df = merge_el_and_pr_sheets(xlsx_file, sheet1, sheet2)

    total_records = 0
    for _, row in df.iterrows():
        parent = str(row["parent"])
        dl = str(row["deprecatedLabel"])
        dd = str(row["deprecatedDate"])
        r_deprecated = "false" if dl == "nan" and dd == "nan" else "true"
        r_abstract = "true" if row["abstract"] == True else "false"

        df.loc[df["id"] == row["id"], "deprecated"] = r_deprecated

        df.loc[df["id"] == row["id"], "abstract"] = r_abstract

        if row["prefix"] not in prefix:
            prefix.append(row["prefix"])

        if row["period"] not in period:
            period.append(row["period"])

        if row["balance"] not in balance:
            balance.append(row["balance"])

        if r_abstract not in abstract:
            abstract.append(r_abstract)

        if row["dataType"] not in dataType:
            dataType.append(row["dataType"])

        if r_deprecated not in deprecated:
            deprecated.append(r_deprecated)

        if parent == "nan":
            if row["definition"] not in defs:
                cn = str(len(defs))
                # add csv value to df
                cn_val = cn + "-0"
                df.loc[df["id"] == row["id"], "cn"] = cn_val
                node = {
                    "lb": row["definition"],
                    "ic": "group",
                    "cn": cn,
                    "nd": [create_node(row, cn_val)],
                }
                taxonomy_data.append(node)
                defs.append(row["definition"])
            else:
                index = defs.index(row["definition"])
                nodes = taxonomy_data[index]["nd"]

                # update cn val in df
                cn_val = str(index) + "-" + str(len(nodes))
                df.loc[df["id"] == row["id"], "cn"] = cn_val

                node = create_node(row, cn_val)
                nodes.append(node)
        else:
            index = defs.index(row["definition"])
            target_dict = find_value_in_nested_dict(taxonomy_data[index], parent)
            nodes = target_dict["nd"]

            # update cn val in df
            cn_val = target_dict["cn"] + "-" + str(len(nodes))
            df.loc[df["id"] == row["id"], "cn"] = cn_val

            node = create_node(row, cn_val)
            nodes.append(node)
        total_records += 1

    df.to_excel(f"GAAP_Taxonomy_2023_{sheet1}_{sheet2}.xlsx")
    print(f"Total {total_records} records processed.")
    sorted_data = sorted(taxonomy_data, key=lambda x: (x["lb"]))
    # write data into json
    taxonomy_fields = {
        "prefix": prefix,
        "period": period,
        "balance": balance,
        "abstract": abstract,
        "dataType": dataType,
        "deprecated": deprecated,
    }
    write_into_json_file(sorted_data, output_file)
    write_into_json_file(taxonomy_fields, "GAAP_Taxonomy_2023_taxonomy_fields.json")


if __name__ == "__main__":
    xlsx_file = "GAAP_Taxonomy_2023.xlsx"
    sheet1 = "Elements"
    sheet2 = "Presentation"
    output_file = "GAAP_Taxonomy_2023_presentation.json"

    start_time = datetime.datetime.now()

    main(xlsx_file, sheet1, sheet2, output_file)

    end_time = datetime.datetime.now()
    time_diff = end_time - start_time
    print(f"Executed in : {time_diff}")
