import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import plotly.express as px

stagingSheet = "C:\\Users\\james\\JMS Metaltec\\JMS Engineering Team - JMS Engineering Team SharePoint\\JMS Master Schedule\\testAutomation\\bundleStagingSheet.xlsx"

df = pd.read_excel(stagingSheet)

st.title("test dashboard")
st.dataframe(df)
st.text(df['Estimated Bundle Time (Hours)'])
st.text("TOTAL ESTIMATED BUNDLE HOURS - " + str(df["Estimated Bundle Time (Hours)"].sum()))

st.text("list of bundle titles and due dates")
for bundle in range(0,len(df)):
    st.text('title: ' + str(df.iloc[bundle,0]))
    st.text('Due Date: ' + str(df.iloc[bundle,2]))

# pie chart
type_counts = df["Type"].value_counts().reset_index()
type_counts.columns = ["Type", "Count"]
fig = px.pie(type_counts, names = "Type", values = "Count", title = "pie chart showing percentages of tube vs flat", hole=0.4)
fig.update_traces(textinfo="percent+label")
st.plotly_chart(fig)

# filter by Machine pie chart
Machine = st.selectbox("Select Machine", df["Machine"].dropna().unique())
filtered_df = df[df["Machine"] == Machine]
fig = px.pie(filtered_df, names = "Type", title = "pie chart showing percentages of tube vs flat - Only Showing: " + Machine, hole=0.2)
fig.update_traces(textinfo="percent+label")
st.plotly_chart(fig)

# CSS TESTING
st.markdown("""
            <style>
                body{ 
                    background-color: red;
                    width: 1000px;
            }
            </style>
            """, unsafe_allow_html=True)

st.markdown('<div style="float: right"><p style="color:blue">right blue</p></div>', unsafe_allow_html=True)

# TEST CHANGE API PRACTICE