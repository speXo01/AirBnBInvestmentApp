import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

# Data loading
df = pd.read_csv('data/StreamlitData.csv')

# Streamlit App Title
st.title("Airbnb Investment Decision Tool")

# City Inputs
cities = st.multiselect('Select City/Cities', df['city'].unique())

# Profit Margin Input
profit_type = st.radio('Profit Margin Type', ['Percentage', 'Fixed Amount'])
if profit_type == 'Percentage':
    profit_margin = st.number_input('Enter Desired Profit Margin (%)', min_value=0.0, max_value=100.0, value=10.0) / 100
else:
    profit_margin = st.number_input('Enter Desired Profit Margin (Fixed Amount)', min_value=0.0)

# Maintenance Margin Input
maintenance_type = st.radio('Maintenance Margin Type', ['Percentage', 'Fixed Amount'])
if maintenance_type == 'Percentage':
    maintenance_margin = st.number_input('Enter Maintenance Margin (%)', min_value=0.0, max_value=100.0,
                                         value=5.0) / 100
else:
    maintenance_margin = st.number_input('Enter Maintenance Margin (Fixed Amount)', min_value=0.0)

# Select a range of beds
min_beds, max_beds = st.slider('Select Range of Beds', min_value=1, max_value=int(df['beds'].max()), value=(1, 5))

availability = st.selectbox('Choose Occupancy Rate', ['No Preference', 'Low', 'High'])

# Filter data based on user input
filtered_df = df[df['city'].isin(cities) & (df['beds'] >= min_beds) & (df['beds'] <= max_beds)]
mean_availability = df['availability_365'].mean()

if availability == 'Low':
    filtered_df = filtered_df[filtered_df['availability_365'] < mean_availability]
elif availability == 'High':
    filtered_df = filtered_df[filtered_df['availability_365'] > mean_availability]

# Calculate max monthly payment and profit left
if profit_type == 'Percentage':
    filtered_df['max_monthly_payment'] = (filtered_df['yearly_revenue'] * (1 - profit_margin)) / 12
else:
    filtered_df['max_monthly_payment'] = (filtered_df['yearly_revenue'] - profit_margin * 12) / 12

if maintenance_type == 'Percentage':
    filtered_df['max_monthly_payment'] = filtered_df['max_monthly_payment'] * (1 - maintenance_margin)
else:
    filtered_df['max_monthly_payment'] = filtered_df['max_monthly_payment'] - maintenance_margin

filtered_df['profit_left'] = filtered_df['yearly_revenue'] / 12 - filtered_df['max_monthly_payment']

# Currency formatter for Bar Plot
def currency_formatter(x, pos):
    return "${:,.2f}".format(x)


# Calculate and Display Average Profit by Number of Beds
avg_profit_by_beds = filtered_df.groupby('beds')['profit_left'].mean().reset_index()

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(avg_profit_by_beds['beds'].astype(str), avg_profit_by_beds['profit_left'])
ax.set_xlabel('Number of Beds')
ax.set_ylabel('Average Profit')
ax.set_title('Average Profit by Number of Beds')
plt.xticks(rotation=0)  # Ensure x-axis labels are horizontal
ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))

st.pyplot(fig)

# Rename columns for display
column_mapping = {
    'neighbourhood': 'District',
    'max_monthly_payment': 'Max Payment/Month',
    'profit_left': 'Remaining Profit'
}

# Display tables for each city side by side
for city in cities:
    city_data = filtered_df[filtered_df['city'] == city]
    top_districts = city_data.nlargest(5, 'max_monthly_payment')
    # Add a ranking column
    top_districts = top_districts.assign(Ranking=range(1, len(top_districts) + 1))

    st.write(f"### {city}")
    formatted_df = top_districts[['Ranking', 'neighbourhood', 'max_monthly_payment', 'profit_left']].rename(
        columns=column_mapping).set_index('Ranking').rename_axis("Rank")

    formatted_df['Max Payment/Month'] = formatted_df['Max Payment/Month'].apply(lambda x: "${:,.2f}".format(x))
    formatted_df['Remaining Profit'] = formatted_df['Remaining Profit'].apply(lambda x: "${:,.2f}".format(x))

    st.write(formatted_df)
