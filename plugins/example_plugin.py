"""Example plugin. Copy this file, rename it, and write your own analysis.

Rules:
  NAME            -> name shown in the app
  analyze(df, st) -> df is the loaded data (pandas DataFrame), st is streamlit
"""
NAME = "Example: basic statistics"


def analyze(df, st):
    st.write("Summary statistics of the loaded data:")
    st.dataframe(df.describe(include="all"))
