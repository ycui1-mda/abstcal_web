import streamlit as st
import abstcal as ac
import sys
import datetime


sys.tracebacklimit = 0

duplicate_options_mapped = {
    "Keep the minimal only": "min",
    "Keep the maximal only": "max",
    "Keep the mean (calculated) only": "mean",
    "Remove all duplicates": False
}
duplicate_options = list(duplicate_options_mapped)

outlier_options_mapped = {
    "Remove the outliers": True,
    "Impute the outliers with the bounding values (min and max, please specify)": False
}
outlier_options = list(outlier_options_mapped)

# tlfb_filepath = "/Users/ycui1/PycharmProjects/abstcal/tests/test_tlfb.csv"
tlfb_data_params = dict.fromkeys([
    "filepath",
    "cutoff",
    "subjects",
    "duplicate_mode",
    "imputation_last_record",
    "imputation_mode",
    "imputation_gap_limit",
    "outliers_mode",
    "allowed_min",
    "allowed_max"
])
tlfb_imputation_options = [
    "None (no imputations)",
    "Linear (a linear interpolation in the gap)",
    "Uniform (the same value in the gap)",
    "Specified Value"
]

visit_data_params = dict.fromkeys([
    "filepath",
    "file_format",
    "subjects",
    "visits",
    "expected_visits",
    "duplicate_mode",
    "imputation_mode",
    "anchor_visit",
    "allowed_min",
    "allowed_max",
    "outliers_mode"
])
visit_file_formats = [
    "Long",
    "Wide"
]
visit_imputation_options = [
    "None (no imputations)",
    "The most frequent interval since the anchor",
    "The mean interval since the anchor"
]

bio_data_params = dict.fromkeys([
    "filepath",
    "cutoff",
    "duplicate_mode",
    "imputation_mode",
    "allowed_min",
    "allowed_max",
    "outliers_mode"
])

abst_target_dir = None
abst_options = [
    "Point-Prevalence",
    "Prolonged",
    "Continuous"
]
abst_pp_params = dict()
abst_con_params = dict()
abst_prol_params = dict()
abst_prol_lapse_params = dict()
calculation_assumptions = ["Intent-to-Treat (ITT)",
                           "Responders-Only (RO)"]


def _load_elements():
    st.title("Abstinence Calculator")
    st.markdown("This web app calculates abstinence using the Timeline-Followback data in addiction research. No data "
                "will be saved or shared.")
    st.markdown("For advanced use cases and detailed API references, please refer to the package's "
                "[GitHub](https://github.com/ycui1-mda/abstcal) page for more information.")
    _load_tlfb_elements()
    _load_visit_elements()
    _load_bio_elements()
    _load_cal_elements()


def _load_tlfb_elements():
    st.header("TLFB Data")
    st.markdown("""The dataset should have three columns: __*id*__, 
    __*date*__, and __*amount*__. The id column stores the subject ids, each of which should 
    uniquely identify a study subject. The date column stores the dates when daily substance 
    uses are collected. The amount column stores substance uses for each day. Supported file 
    formats include comma-separated (.csv), tab-delimited (.txt), and Excel spreadsheets (.xls, .xlsx).  \n\n
      \n\nid | date | amount 
    ------------ | ------------- | -------------
    1000 | 02/03/2019 | 10
    1000 | 02/04/2019 | 8
    1000 | 02/05/2019 | 12
      \n\n
    """)
    tlfb_data_params['filepath'] = st.text_input("Specify the file path to the TLFB data on your computer.")
    tlfb_subjects = list()
    if tlfb_data_params['filepath']:
        tlfb_data = ac.TLFBData(tlfb_data_params['filepath'])
        tlfb_subjects = sorted(tlfb_data.subject_ids)


    with st.beta_expander("TLFB Data Processing Advanced Configurations"):
        tlfb_data_params["cutoff"] = st.number_input(
            "1. Specify the cutoff value for abstinence (default: 0)",
            step=None
        )
        tlfb_data_params["subjects"] = st.multiselect(
            "2. Choose the subjects of the TLFB data whose abstinence will be calculated.",
            tlfb_subjects,
            default=tlfb_subjects
        )
        st.write("3. TLFB Missing Data Imputation")
        imputation_mode_col, imputation_gap_col, imputation_last_record_col = st.beta_columns(3)
        tlfb_data_params["imputation_mode"] = imputation_mode_col.selectbox(
            "TLFB Missing Data Imputation",
            tlfb_imputation_options,
            index=1
        )
        tlfb_data_params["imputation_gap_limit"] = imputation_gap_col.number_input(
            "Maximal Gap for Imputation (days)",
            value=30,
            step=1
        )
        tlfb_data_params["imputation_last_record"] = imputation_last_record_col.text_input(
            "Last Record Imputation (fill foreword or a number value)",
            value="ffill"
        )
        tlfb_data_params["duplicate_mode"] = duplicate_options_mapped[st.selectbox(
            "4. TLFB Duplicate Records Action",
            duplicate_options,
            index=len(duplicate_options) - 1
        )]
        st.write("5. TLFB Outliers Actions")
        tlfb_data_params["outlier_mode"] = outlier_options_mapped[st.selectbox(
            "TLFB Outliers (i.e., lower than the min or higher than the max) Action",
            outlier_options
        )]
        left_col, right_col = st.beta_columns(2)
        tlfb_data_params["allowed_min"] = left_col.number_input("Allowed Minimal Daily Value", step=None)
        tlfb_data_params["allowed_max"] = right_col.number_input("Allowed Maximal Daily Value", step=None)


def _load_visit_elements():
    st.header("Visit Data")
    st.markdown("""It needs to be in one of the following two formats.  \n\n**The long format.** 
    The dataset should have three columns: __*id*__, __*visit*__, 
    and __*date*__. The id column stores the subject ids, each of which should uniquely 
    identify a study subject. The visit column stores the visits. The date column stores 
    the dates for the visits.  \n\nid | visit | date 
    ------------ | ------------- | -------------
    1000 | 0 | 02/03/2019
    1000 | 1 | 02/10/2019
    1000 | 2 | 02/17/2019  \n\n\n\n---
      \n**The wide format.** 
    The dataset should have the id column and additional columns 
    with each representing a visit.  \n\nid | v0 | v1 | v2 | v3 | v4 | v5
    ----- | ----- | ----- | ----- | ----- | ----- | ----- |
    1000 | 02/03/2019 | 02/10/2019 | 02/17/2019 | 03/09/2019 | 04/07/2019 | 05/06/2019
    1001 | 02/05/2019 | 02/13/2019 | 02/20/2019 | 03/11/2019 | 04/06/2019 | 05/09/2019""")
    visit_data_params['filepath'] = st.text_input("Specify the file path to the Visit data on your computer.")
    visit_data_params['file_format'] = st.selectbox("Specify the file format", visit_file_formats)
    visit_data_params['visits'] = list()
    visit_subjects = list()
    if visit_data_params['filepath']:
        visit_data = ac.VisitData(visit_data_params['filepath'])
        visit_subjects = sorted(visit_data.subject_ids)
        visit_data_params['visits'] = sorted(visit_data.visits)

    with st.beta_expander("Visit Data Processing Advanced Configurations"):
        visit_data_params['expected_visits'] = st.multiselect(
            "1. Set the expected order of the visits (for data normality check)",
            visit_data_params['visits'],
            default=visit_data_params['visits']
        )
        st.write("2. Visit Missing Dates Imputation")
        left_col0, right_col0 = st.beta_columns(2)
        visit_data_params["imputation_mode"] = left_col0.selectbox(
            "Imputation Mode",
            visit_imputation_options,
            index=1
        )
        visit_data_params["anchor_visit"] = right_col0.selectbox(
            "Anchor Visit for Imputation",
            visit_data_params['expected_visits'],
            index=0
        )
        visit_data_params["subjects"] = st.multiselect(
            "3. Choose the subjects of the visit data whose abstinence will be calculated.",
            visit_subjects,
            default=visit_subjects
        )
        visit_data_params["duplicate_mode"] = st.selectbox(
            "4. Visit Duplicate Records Action",
            duplicate_options,
            index=2
        )
        st.write("5. Visit Date Range")
        visit_data_params["outlier_mode"] = st.selectbox(
            "Visit Date Outliers (i.e., lower than the min or higher than the max) Action",
            outlier_options
        )
        left_col, right_col = st.beta_columns(2)
        visit_data_params["allowed_min"] = left_col.date_input(
            "Allowed Minimal Visit Date",
            value=datetime.datetime.today() - datetime.timedelta(days=365*10)
        )
        visit_data_params["allowed_max"] = right_col.date_input(
            "Allowed Maximal Visit Date",
            value=None
        )


def _load_bio_elements():
    st.header("Biochemical Data (Optional)")
    st.markdown("""
    If your study has collected biochemical verification data, such as carbon monoxide for smoking or breath alcohol 
    concentration for alcohol intervention, these biochemical data can be integrated into the TLFB data. 
    In this way, non-honest reporting can be identified (e.g., self-reported of no use, but biochemically un-verified), 
    the self-reported value will be overridden, and the updated record will be used in later abstinence calculation.
    
    Please note that the biochemical measures dataset should have the same data structure as you TLFB dataset. 
    In other words, it should have three columns: id, date, and amount.
    
    id | date | amount 
    ------------ | ------------- | -------------
    1000 | 02/03/2019 | 4
    1000 | 02/11/2019 | 6
    1000 | 03/04/2019 | 10
    ***
    """)
    bio_data_params['filepath'] = st.text_input("Specify the file path to the Biochemical data on your computer.")
    with st.beta_expander("Biochemical Data Processing Advanced Configurations"):
        bio_data_params["cutoff"] = st.number_input(
            "1. Specify the cutoff value for biochemically-verified abstinence (default: 0.0)",
            value=0.0,
            step=None)
        st.write("2. Biochemical Data Imputation. The calculator will estimate the biochemical levels based on the "
                 "current measures in the preceding days.")
        left_col, right_col = st.beta_columns(2)
        left_col.number_input("Half Life of the Biochemical Measure in Hours")
        right_col.number_input("The Number of Days of Imputation", value=1, step=1)


def _load_cal_elements():
    global abst_target_dir
    st.header("Calculate Abstinence")
    abst_target_dir = st.text_input("Specify the directory where your data will be saved.")
    pp_col, prol_col, con_col = columns = st.beta_columns(3)
    for i, (abst_option, col) in enumerate(zip(abst_options, columns)):
        col.write(abst_option)
        col.multiselect("Visits for Abstinence Calculation", visit_data_params['visits'], key=abst_option)
        col.text_input("Abstinence Variable Names (They'll be inferred by default).", key=abst_option + "_name")
    pp_col.number_input("The number of days preceding the visit dates", value=0, step=1)
    prol_col.selectbox("Specify the quit visit", visit_data_params['visits'])
    prol_col.text_input("Specify lapse definitions (e.g., False, 5 cigs, 3 days). See GitHub page for more details.")
    con_col.selectbox("Specify the start visit", visit_data_params['visits'])

    with st.beta_expander("Calculator Advanced Configurations"):
        st.selectbox("Abstinence Assumption", calculation_assumptions)
        st.checkbox("Include each of the visit dates in the calculation (default: No)")

    if st.button("Get Abstinence Results"):
        _run_analysis()


def _run_analysis():
    print("Calculate abstinence")
    tlfb_data = ac.TLFBData(
        tlfb_data_params["filepath"],
        tlfb_data_params["cutoff"],
        tlfb_data_params["subjects"]
    )
    # tlfb_data.profile_data(tlfb_data_params["allowed_min"], tlfb_data_params["allowed_max"])
    tlfb_na_number = tlfb_data.drop_na_records()
    st.write(f"Removed Records With N/A Values: {tlfb_na_number}")
    tlfb_duplicates = tlfb_data.check_duplicates(tlfb_data_params["duplicate_mode"])
    st.write(f"Duplicate Records: {tlfb_duplicates}")
    st.write(tlfb_data.recode_outliers(
        tlfb_data_params["allowed_min"],
        tlfb_data_params["allowed_max"],
        tlfb_data_params["outlier_mode"])
    )
    st.write(tlfb_data.impute_data(
        tlfb_data_params["imputation_mode"],
    ))
    tlfb_data.impute_data()


def _max_width_():
    max_width_str = f"max-width: 1200px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    _max_width_()
    _load_elements()
