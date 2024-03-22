html_elements_data: list[dict] = [
    # Def XML Elements
    {
        "Type": "90F",
        "Element": "us-gaap--Land",
        "Unit": "Canadian Dollar",
        "PreElementParent": "us-gaap:AssetsAbstract",
        "Indenting": "01",
        "Precision": "",
        "CountedAs": "",
        "Calculation": "",
        "Period": "",
        "Axis_Member": "",
        "Domain": "",
        "PreferredLabel": "Land",
        "PreferredLabelType": "terselabel",
        "Table": "us-gaap--StatementTable",
        "LineItem": "us-gaap_StatementLineItems",
        "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
        "RoleName": "StatementConsoildatedBalanceSheet",
        "UniqueId": "0efb6deb824c493da1b6e03669691c37",
    },
    # Pre XML Elements
    # {
    #     "Type": "90F",
    #     "Element": "us-gaap--AssetsAbstarct",
    #     "Unit": "Canadian Dollar",
    #     "PreElementParent": "dei:EntityInformationLineItems",
    #     "Indenting": "01",
    #     "Precision": "",
    #     "CountedAs": "",
    #     "Calculation": "",
    #     "Period": "",
    #     "Axis_Member": "",
    #     "Domain": "",
    #     "PreferredLabel": "Assets",
    #     "PreferredLabelType": "terselabel",
    #     "Table": "dei--EntitiesTable",
    #     "LineItem": "dei--EntityInformationLineItems",
    #     "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
    #     "RoleName": "StatementConsoildatedBalanceSheet",
    #     "UniqueId": "0efb6deb824c493da1b6e03669691c37",
    # },
    # {
    #     "Type": "90F",
    #     "Element": "us-gaap--AssetsNoncurrentAbstract",
    #     "Unit": "Canadian Dollar",
    #     "PreElementParent": "us-gaap:AssetsAbstarct",
    #     "Indenting": "01",
    #     "Precision": "",
    #     "CountedAs": "",
    #     "Calculation": "",
    #     "Period": "",
    #     "Axis_Member": "",
    #     "Domain": "",
    #     "PreferredLabel": "Non-Current Assets",
    #     "PreferredLabelType": "terselabel",
    #     "Table": "dei--EntitiesTable",
    #     "LineItem": "dei--EntityInformationLineItems",
    #     "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
    #     "RoleName": "StatementConsoildatedBalanceSheet",
    #     "UniqueId": "0efb6deb824c493da1b6e03669691c38",
    # },
    # {
    #     "Type": "90F",
    #     "Element": "us-gaap--Land",
    #     "Unit": "Canadian Dollar",
    #     "PreElementParent": "us-gaap:AssetsNoncurrentAbstract",
    #     "Indenting": "01",
    #     "Precision": "3",
    #     "CountedAs": "6",
    #     "Calculation": "a7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross",
    #     "Period": "20240223",
    #     "Axis_Member": "us-gaap--StatementClassOfStockAxis__us-gaap--CommonClassAMember",
    #     "Domain": "us-gaap_ClassOfStockDomain",
    #     "PreferredLabel": "Land",
    #     "PreferredLabelType": "terselabel",
    #     "Table": "dei--EntitiesTable",
    #     "LineItem": "dei--EntityInformationLineItems",
    #     "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
    #     "RoleName": "StatementConsoildatedBalanceSheet",
    #     "UniqueId": "0efb6deb824c493da1b6e03669691c39",
    # },
    # {
    #     "Type": "90F",
    #     "Element": "us-gaap--Land",
    #     "Unit": "Canadian Dollar",
    #     "PreElementParent": "us-gaap:AssetsNoncurrentAbstract",
    #     "Indenting": "01",
    #     "Precision": "3",
    #     "CountedAs": "6",
    #     "Calculation": "a7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross",
    #     "Period": "20230223",
    #     "Axis_Member": "us-gaap--StatementClassOfStockAxis__us-gaap--CommonClassAMember",
    #     "Domain": "us-gaap_ClassOfStockDomain",
    #     "PreferredLabel": "Land",
    #     "PreferredLabelType": "terselabel",
    #     "Table": "dei--EntitiesTable",
    #     "LineItem": "dei--EntityInformationLineItems",
    #     "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
    #     "RoleName": "StatementConsoildatedBalanceSheet",
    #     "UniqueId": "0efb6deb824c493da1b6e03669691c40",
    # },
    # {
    #     "Type": "90F",
    #     "Element": "us-gaap--OperatingLeaseRightOfUseAsset",
    #     "Unit": "Canadian Dollar",
    #     "PreElementParent": "us-gaap:AssetsNoncurrentAbstract",
    #     "Indenting": "02",
    #     "Precision": "3",
    #     "CountedAs": "6",
    #     "Calculation": "",
    #     "Period": "20240223",
    #     "Axis_Member": "",
    #     "Domain": "",
    #     "PreferredLabel": "Right of use assets",
    #     "PreferredLabelType": "verboselabel",
    #     "Table": "",
    #     "LineItem": "",
    #     "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
    #     "RoleName": "StatementConsoildatedBalanceSheet",
    #     "UniqueId": "0efb6deb824c493da1b6eAssetsNoncurrentAbstract03669691c41",
    # },
    # {
    #     "Type": "90F",
    #     "Element": "us-gaap--OperatingLeaseRightOfUseAsset",
    #     "Unit": "Canadian Dollar",
    #     "PreElementParent": "us-gaap:",
    #     "Indenting": "02",
    #     "Precision": "3",
    #     "CountedAs": "6",
    #     "Calculation": "",
    #     "Period": "20230223",
    #     "Axis_Member": "",
    #     "Domain": "",
    #     "PreferredLabel": "Right of use assets",
    #     "PreferredLabelType": "verboselabel",
    #     "Table": "",
    #     "LineItem": "",
    #     "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
    #     "RoleName": "StatementConsoildatedBalanceSheet",
    #     "UniqueId": "0efb6deb824c493da1b6e03669691c42",
    # },
    # {
    #     "Type": "90F",
    #     "Element": "msft--BankOverdraftsOfSBI",
    #     "Unit": "Canadian Dollar",
    #     "PreElementParent": "us-gaap:LiabilitiesCurrentAbstract",
    #     "Indenting": "01",
    #     "Precision": "3",
    #     "CountedAs": "6",
    #     "Calculation": "a7b4c79a89bfd48a48ac7b8d562c893b1__us-gaap--BuildingsAndImprovementsGross",
    #     "Period": "20240223",
    #     "Axis_Member": "srt--RestatementAxis__srt--ScenarioPreviouslyReportedMember",
    #     "Domain": "srt--RestatementDomain",
    #     "PreferredLabel": "Right of use assets",
    #     "PreferredLabelType": "verboselabel",
    #     "Table": "",
    #     "LineItem": "dei--EntityInformationLineItems",
    #     "RootLevelAbstract": "us-gaap--StatementOfFinancialPositionAbstract",
    #     "RoleName": "StatementConsoildatedBalanceSheet",
    #     "UniqueId": "0efb6deb824c493da1b6e03669691c42",
    # },
]
