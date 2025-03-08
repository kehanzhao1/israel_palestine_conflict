
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from google.cloud import bigquery
import plotly.express as px
import plotly.graph_objects as go

#%%
client = bigquery.Client()

query = """
SELECT Country_Name, Fiscal_Year, Current_Dollar_Amount, Activity_Name, Activity_Description,
Funding_Agency_Name, Foreign_Assistance_Objective_Name, International_Purpose_Name
, International_Category_Name, International_Sector_Name
FROM `data342.israel.trunc3`
WHERE Transaction_Type_Name = "Disbursements"
--GROUP BY Country_Name, Fiscal_Year
ORDER BY Fiscal_Year DESC
"""

query_political = """
SELECT *
FROM `data342.israel.violence_combined`
order by Year
"""

query_civilian = """
SELECT *
FROM `data342.israel.civilian_combined`
order by Year
"""

query_healthcare = """
SELECT Country,  sum(`Number of Attacks on Health Facilities Reporting Damaged`) as healthcare_facilities_damanged,
 sum(`Occupation of Health Facility`) as healthcare_facilities_occupied, 
 sum(`Health Transportation Damaged`) as health_transportation_damanged, 
 sum(`Looting of Health Supplies`) as health_supplies_looted, 
 SUM(SAFE_CAST(`Health Workers Killed` AS INT64)) AS health_workers_killed, 
 sum(safe_cast(`Health Workers Injured` as int64)) as health_workers_injured, 
 count(distinct `Weapon Used` ) as weapons_used
FROM `data342.israel.health` 
group by 1 
"""
query_weapons = """
SELECT 
    Country, 
    `Weapon Used` AS weapon_used, 
    COUNT(*) AS weapon_usage_count, 
    `Location of Incident` AS incident_location, 
    COUNT(*) AS attack_count
FROM `data342.israel.health`
GROUP BY Country, `Weapon Used`, `Location of Incident`
ORDER BY Country, weapon_usage_count DESC, attack_count DESC;
"""
@st.cache_data  # Caches results to improve performance
def load_data1():
    return client.query(query).to_dataframe()
df = load_data1()

@st.cache_data 
def load_data2():
    return client.query(query_political).to_dataframe()
df_political = load_data2()

@st.cache_data 
def load_data3():
    return client.query(query_civilian).to_dataframe()
df_civilian = load_data3()

@st.cache_data 
def load_data4():
    return client.query(query_healthcare).to_dataframe()
df_health = load_data4()

@st.cache_data 
def load_data5():
    return client.query(query_weapons).to_dataframe()
df_weapons = load_data5()

df["Country_Name"] = df["Country_Name"].replace("West Bank and Gaza", "Palestine")
st.title("Israel Palestine Conflict Dashboard 🌍")
st.write("This dashboard displays US foreign aid trends related to Israel, Palestine and ")

col1, col2, col3, col4 = st.columns(4)
with col1:
    country = st.selectbox("Select a Country", ["All"] + sorted(df["Country_Name"].unique()))

with col2:
    year = st.selectbox("Select a Year", ["All"] + sorted(df["Fiscal_Year"].unique(), reverse=True))

with col3:
    category = st.selectbox("Select a Funding Agency", ["All"] + sorted(df["Funding_Agency_Name"].unique()))

filtered_df = df.copy()
if country != "All":
    filtered_df = filtered_df[filtered_df["Country_Name"] == country]
if year != "All":
    filtered_df = filtered_df[filtered_df["Fiscal_Year"] == year]
if category != "All":
    filtered_df = filtered_df[filtered_df["Funding_Agency_Name"] == category]

total_aid_current = filtered_df["Current_Dollar_Amount"].sum()

def format_large_number(value):
    if value >= 1_000_000_000:  # 
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:  # 
        return f"${value / 1_000_000:.2f}M"
    else:  # 
        return f"${value:,.2f}"
    
###########========================================================
st.markdown("### 1. Key US Foreign Aid Figures ")
kpi_col1, kpi_col2 = st.columns(2)

if country == "Israel":
    country_color = "steelblue" 
elif country == "West Bank and Gaza":
    country_color = "salmon"  
else:
    country_color = "white" 

with kpi_col1:
    st.markdown(f"<h2 style='color:{country_color};'>{country if country != 'All' else 'All Countries'}</h2>", unsafe_allow_html=True)

with kpi_col2:
    st.metric(
        label="Total Aid (USD)",
        value=format_large_number(total_aid_current)
    )

st.dataframe(filtered_df.drop(columns=["Country_Name"]))
graph_df = df.copy() 
if country != "All":
    graph_df = graph_df[graph_df["Country_Name"] == country]
if category != "All":
    graph_df = graph_df[graph_df["Funding_Agency_Name"] == category]
color_map = {
    "Israel": "steelblue",  
    "Gaza": "salmon", 
}
graph_df["color"] = graph_df["Country_Name"].map(color_map).fillna("gray")  # Default Gray for others

graph_df = graph_df.groupby(["Country_Name", "Fiscal_Year"], as_index=False).agg(
    {"Current_Dollar_Amount": "sum"}
)


fig = px.line(
    graph_df, 
    x="Fiscal_Year", 
    y="Current_Dollar_Amount", 
    color="Country_Name",
    title=f"Foreign Aid Over Time ({country if country != 'All' else 'All Countries'})",
    markers=True,
    color_discrete_map=color_map 
)


st.plotly_chart(fig)
###########========================================================
st.markdown("### Funding Objectives breakdown 📊")
col3, col4, col5 = st.columns(3)

with col3:
    selected_country_bar = st.selectbox("Select a Country for Bar Chart", ["All"] + sorted(df["Country_Name"].unique()), key="country_bar")

with col4:
    selected_year_bar = st.selectbox("Select a Year for Bar Chart", ["All"] + sorted(df["Fiscal_Year"].unique(), reverse=True), key="year_bar")

with col5:
    sort_variable = st.selectbox(
        "Sort by",
        ["Foreign_Assistance_Objective_Name", "International_Purpose_Name"],
        key="sort_by_bar"
    )

filtered_df_bar = df.copy()
if selected_country_bar != "All":
    filtered_df_bar = filtered_df_bar[filtered_df_bar["Country_Name"] == selected_country_bar]
if selected_year_bar != "All":
    filtered_df_bar = filtered_df_bar[filtered_df_bar["Fiscal_Year"] == selected_year_bar]


bar_chart_df = filtered_df_bar.groupby(sort_variable, as_index=False).agg(
    {"Current_Dollar_Amount": "sum"}
).sort_values(by="Current_Dollar_Amount", ascending=True)
color_arg = "Foreign_Assistance_Objective_Name" if sort_variable == "Foreign_Assistance_Objective_Name" else None
color_map = {
    "Economic": "#FFD700",  
    "Military": "#008000",  
}


fig_bar = px.bar(
    bar_chart_df,
    x="Current_Dollar_Amount",
    y=sort_variable,
    orientation="h",
    title=f"Total Foreign Aid by {sort_variable} ({selected_country_bar if selected_country_bar != 'All' else 'All Countries'}, {selected_year_bar if selected_year_bar != 'All' else 'All Years'})",
    labels={"Current_Dollar_Amount": "Total Aid (USD)", sort_variable: sort_variable},
    height=700,
    color=color_arg,
    color_discrete_map=color_map if color_arg else None
)


st.plotly_chart(fig_bar)


st.markdown(f"### Top 10 Funding Activities ({selected_country_bar if selected_country_bar != 'All' else 'All Countries'}, {selected_year_bar if selected_year_bar != 'All' else 'All Years'})")

funding_activity_df = filtered_df_bar.groupby(["Activity_Name", "Activity_Description"], as_index=False).agg(
    {"Current_Dollar_Amount": "sum"}
).sort_values(by="Current_Dollar_Amount", ascending=False).head(10)  # Get Top 10

funding_activity_df["Current_Dollar_Amount"] = funding_activity_df["Current_Dollar_Amount"].apply(format_large_number)
funding_activity_df.index = range(1, len(funding_activity_df) + 1)
st.dataframe(funding_activity_df)

###########========================================================
st.markdown("### 2. Political events and fatalities timeline")  

df_political["date"] = pd.to_datetime(df_political["Year"].astype(str) + "-" + df_political["Month"], errors="coerce", format="%Y-%B")
df_political = df_political.dropna(subset=["date"])
df_political = df_political.sort_values("date")
available_years = sorted(df_political["Year"].dropna().unique(), reverse=True)
selected_year = st.selectbox("Select Year", ["All"] + list(available_years), key="year_selector")

filtered_df2 = df_political.copy()
if selected_year != "All":
    filtered_df2 = filtered_df2[filtered_df2["Year"] == selected_year]


total_pse_fatalities = filtered_df2["pse_fatalities"].sum()
total_israel_fatalities = filtered_df2["israel_fatalities"].sum()

st.markdown("### Total Fatalities Summary")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Palestine Fatalities", value=f"{total_pse_fatalities:,}")
with col2:
    st.metric(label="Israel Fatalities", value=f"{total_israel_fatalities:,}")



y_axis_option = st.selectbox("Select Metric", ["Events", "Fatalities"], key="y_axis_toggle")


y_variable_map = {
    "Events": ["pse_events", "israel_events"],
    "Fatalities": ["pse_fatalities", "israel_fatalities"]
}
y_columns = y_variable_map[y_axis_option]


df_melted = df_political.melt(id_vars=["date"], value_vars=y_columns, var_name="Group", value_name="Count")

group_labels = {
    "pse_events": "Palestine Events",
    "israel_events": "Israel Events",
    "pse_fatalities": "Palestine Fatalities",
    "israel_fatalities": "Israel Fatalities"
}
df_melted["Group"] = df_melted["Group"].map(group_labels)


fig2 = px.line(
    df_melted,
    x="date",
    y="Count",
    color="Group",
    title=f"Political {y_axis_option} Over Time",
    labels={"date": "Date", "Count": y_axis_option},
    markers=True
)

st.plotly_chart(fig2)
###########========================================================

st.markdown("### Civilian targeting events and fatalities Summary")  

df_civilian["date"] = pd.to_datetime(df_civilian["Year"].astype(str) + "-" + df_civilian["Month"], errors="coerce", format="%Y-%B")
df_civilian = df_civilian.dropna(subset=["date"])
df_civilian = df_civilian.sort_values("date")
available_years2 = sorted(df_civilian["Year"].dropna().unique(), reverse=True)
selected_year2 = st.selectbox("Select Year", ["All"] + list(available_years), key="year")


filtered_df3 = df_civilian.copy()
if selected_year2 != "All":
    filtered_df3 = filtered_df3[filtered_df3["Year"] == selected_year2]


total_pse_fatalities2 = filtered_df3["pse_fatalities"].sum()
total_israel_fatalities2 = filtered_df3["israel_fatalities"].sum()

if selected_year2 != "All":
    total_pse = df_political[df_political["Year"] == selected_year2]["pse_fatalities"].sum()
    total_israel = df_political[df_political["Year"] == selected_year2]["israel_fatalities"].sum()
else :
    total_pse = df_political["pse_fatalities"].sum()
    total_israel = df_political['israel_fatalities'].sum()

israel_percentage = total_israel_fatalities2/total_israel
pse_percentage = total_pse_fatalities2/total_pse

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Palestine Fatalities", value=f"{total_pse_fatalities2:,}")
with col2:
    st.metric(label = "Percentage", value = f"{pse_percentage:.2%}")    
with col3:
    st.metric(label="Israel Fatalities", value=f"{total_israel_fatalities2:,}")
with col4:
    st.metric(label = "Percentage", value = f"{israel_percentage:.2%}")


y_axis_option2 = st.selectbox("Select Metric", ["Events", "Fatalities"], key="y_axis_toggle2")

y_variable_map2 = {
    "Events": ["pse_events", "israel_events"],
    "Fatalities": ["pse_fatalities", "israel_fatalities"]
}
y_columns2 = y_variable_map2[y_axis_option2]

df_melted2 = df_civilian.melt(id_vars=["date"], value_vars=y_columns2, var_name="Group", value_name="Count")


group_labels2 = {
    "pse_events": "Palestine Events",
    "israel_events": "Israel Events",
    "pse_fatalities": "Palestine Fatalities",
    "israel_fatalities": "Israel Fatalities"
}
df_melted2["Group"] = df_melted2["Group"].map(group_labels2)

fig3 = px.line(
    df_melted2,
    x="date",
    y="Count",
    color="Group",
    title=f"Civilian {y_axis_option2} Over Time",
    labels={"date": "Date", "Count": y_axis_option2},
    markers=True
)

st.plotly_chart(fig3)


###########========================================================
st.markdown("### 3. Attack on healthcare facilities")

df_health["Country"] = df_health["Country"].replace("OPT", "Palestine")  


metric_options = {
    "Health Workers Killed": "health_workers_killed",
    "Health Workers Injured": "health_workers_injured",
    "Healthcare Facilities Damaged": "healthcare_facilities_damanged",
    "Healthcare Facilities Occupied": "healthcare_facilities_occupied",
    "Health Transportation Damaged": "health_transportation_damanged",
    "Health Supplies Looted": "health_supplies_looted"

}

selected_metric = st.selectbox("Select Metric to Display", list(metric_options.keys()), key="health_metric_toggle")


metric_column = metric_options[selected_metric]
df_pie = df_health.groupby("Country", as_index=False)[metric_column].sum()
st.write("Attack on healthcare facilities suffered by both sides from October 7th 2023 to September 2024") 


fig_pie = px.pie(
    df_pie,
    names="Country",
    values=metric_column,
    title=f"{selected_metric} by Country",
    color="Country",
    color_discrete_map={"Israel": "steelblue", "Palestine": "salmon"}  #
)
fig_pie.update_traces(textinfo="label+value", textfont_size=14)



###########========================================================
st.plotly_chart(fig_pie)
st.markdown("### Location of incident / weapon used by attacker")


df_weapons["Country"] = df_weapons["Country"].replace("OPT", "Palestine")  # 


category_options = {
    "Weapons Used by perpetrator": ("weapon_used", "weapon_usage_count"),
    "Location of Incident": ("incident_location", "attack_count")
}
selected_category = st.selectbox("Select Category to Compare", list(category_options.keys()), key="category_toggle")
selected_column, sum_column = category_options[selected_category]

df_agg = df_weapons.groupby(["Country", selected_column], as_index=False).agg({sum_column: "sum"})

df_israel = df_agg[df_agg["Country"] == "Israel"].sort_values(by=sum_column, ascending=False).head(5)
df_palestine = df_agg[df_agg["Country"] == "Palestine"].sort_values(by=sum_column, ascending=False).head(5)


col1, col2 = st.columns(2)
color_map_last = {"Israel": "steelblue", "Palestine": "salmon"}
with col1:
    fig_israel = px.bar(
        df_israel,
        y=sum_column,
        x=selected_column,
       # orientation="h",
        title=f"Israel - {selected_category}",
        labels={sum_column: "Occurrences", selected_column: selected_category},
        height=700,
        color_discrete_sequence=[color_map_last["Israel"]] 
    )
    st.plotly_chart(fig_israel)

with col2:
    fig_palestine = px.bar(
        df_palestine,
        y=sum_column,
        x=selected_column,
        #orientation="h",
        title=f"Palestine - {selected_category}",
        labels={sum_column: "Occurrences", selected_column: selected_category},
        height=700,
        color_discrete_sequence=[color_map_last["Palestine"]]
    )
    st.plotly_chart(fig_palestine)



'''
Created by Kehan Zhao, Mar 2025
@UChicago PSD 
'''