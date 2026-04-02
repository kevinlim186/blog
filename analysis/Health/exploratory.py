import sys
import os

# Get the absolute path to the 'blog' directory
# Since you are in analysis/Health/, we go up two levels
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if root_path not in sys.path:
    sys.path.insert(0, root_path)

import pandas as pd
import xml.etree.ElementTree as ET
from utils.utility import build_mi_distance_matrix, featImpMDA_Repeated_Clustered
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import BaggingRegressor
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import importlib
import utils.utility

# # 1. Reload the entire module
# importlib.reload(utils.utility)

# # 2. Re-import the specific functions into your current namespace
# from utils.utility import build_mi_distance_matrix, featImpMDA_Clustered_Regression

# # 1. Setup path to your unzipped export
path = '/Users/KevinLim/Downloads/apple_health_export/export.xml'

def parse_health_data(file_path):
    data = []
    
    # Use iterparse to handle large files without filling up RAM
    # We only care about the 'end' of a tag
    context = ET.iterparse(file_path, events=('end',))
    
    for event, elem in context:
        if elem.tag == 'Record':
            # Extract all attributes (type, sourceName, unit, value, dates, etc.)
            data.append(elem.attrib)
            
            # Critical: Clear the element from memory after processing
            elem.clear()
            
    return pd.DataFrame(data)

# 2. Run the parser
df = parse_health_data(path)

# 3. Clean and Format
# Convert dates to datetime objects
for col in ['creationDate', 'startDate', 'endDate']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col])


df['value'] = pd.to_numeric(df['value'], errors='coerce')

# Clean up the 'type' column strings
df['type'] = df['type'].str.replace('HKQuantityTypeIdentifier', '', regex=False)
df['type'] = df['type'].str.replace('HKCategoryTypeIdentifier', '', regex=False)



df['date'] = pd.to_datetime(df['startDate']).dt.date

filtered_sleep =  df[(df['type']=='SleepAnalysis')&(df['sourceName']=='Zepp')]
def get_true_sleep_duration(df_subset):
    # 1. Create a list of every single minute covered by every row
    # This effectively "flattens" all overlaps (Total vs Stages vs Connect vs Zepp)
    minutes_list = []
    for _, row in df_subset.iterrows():
        # Generate a range of minutes for this row
        m = pd.date_range(start=row['startDate'], end=row['endDate'], freq='min')
        minutes_list.extend(m)
    
    # 2. Remove duplicates by converting to a 'set'
    unique_minutes = pd.Series(list(set(minutes_list)))
    
    # 3. Use the 'Sleep Day' trick (Subtract 12 hours) 
    # This keeps the night of the 20th-21st as one single date
    sleep_day = (unique_minutes - pd.Timedelta(hours=12)).dt.date
    
    # 4. Count the minutes and convert to hours
    return unique_minutes.groupby(sleep_day).count() / 60

# Apply to your filtered Zepp data
true_sleep = get_true_sleep_duration(filtered_sleep)

sleep_data = pd.DataFrame(true_sleep).reset_index()
sleep_data.columns = ['date', 'sleep']

weight = df[df['type']=='BodyMass'][['date', 'value']]
weight.columns = ['date', 'weight']


step_count = df[(df['type']=='StepCount')&(df['sourceName']=='Zepp')]
step_count = step_count.groupby('date')['value'].sum().reset_index()
step_count.columns = ['date', 'steps']

insulin_delivery = df[(df['type']=='InsulinDelivery')]
insulin_delivery = insulin_delivery.groupby('date')['value'].sum().reset_index()
insulin_delivery.columns = ['date', 'insulin']

calories_burn = df[(df['type']=='ActiveEnergyBurned')&(df['sourceName']=='Zepp')]
calories_burn = calories_burn.groupby('date')['value'].sum().reset_index()
calories_burn.columns = ['date', 'calories_burn']

# List of your dataframes
dfs = [sleep_data, weight, step_count, insulin_delivery, calories_burn]

for d in dfs:
    # Ensure date is datetime and create a Period column (e.g., '2026-03')
    d['month'] = pd.to_datetime(d['date']).dt.to_period('M')

# 2. Aggregate to Monthly Averages
# We group by the month and take the mean of the numeric columns
monthly_sleep    = sleep_data.groupby('month')['sleep'].mean().reset_index()
monthly_weight   = weight.groupby('month')['weight'].mean().reset_index()
monthly_steps    = step_count.groupby('month')['steps'].mean().reset_index()
monthly_insulin  = insulin_delivery.groupby('month')['insulin'].mean().reset_index()
monthly_calories = calories_burn.groupby('month')['calories_burn'].mean().reset_index()

# Start with Weight as the lead table
final_df = monthly_weight

# Left Join the rest one by one
final_df = final_df.merge(monthly_sleep, on='month', how='left')
final_df = final_df.merge(monthly_steps, on='month', how='left')
final_df = final_df.merge(monthly_insulin, on='month', how='left')
final_df = final_df.merge(monthly_calories, on='month', how='left')

# Optional: Sort by month and convert period back to timestamp for plotting
final_df = final_df.sort_values('month')
final_df['month'] = final_df['month'].dt.to_timestamp()

final_df = final_df[final_df['month']>='2024-01-01'].reset_index(drop=True)

for i in range(1,7):
    final_df[f'weight_lag_{i}'] = final_df['weight'].shift(i)

x_interface = [ 'sleep', 'steps', 'insulin', 'calories_burn']
transposed_data = final_df[x_interface].T

distance_matrix = build_mi_distance_matrix(transposed_data)


base_tree = DecisionTreeRegressor(
    criterion='squared_error', 
    max_features=1,
    max_depth=10
)

regressor = BaggingRegressor(
    estimator=base_tree,    
    n_estimators=1000,
    max_features=1.0,
    max_samples=1.0,
    oob_score=True,  
    random_state=999,
    n_jobs=8
)

temp_data = pd.DataFrame()
temp_data.index=x_interface
for col in ['weight', 'weight_lag_1', 'weight_lag_2', 'weight_lag_3', 'weight_lag_4', 'weight_lag_5']:
    temp = final_df[x_interface+[col]].copy()
    temp=temp.dropna()
    X_input = temp[x_interface].copy()
    y_input = temp[col].copy()

    feature_clstrs = {i: [x] for i, x in enumerate(x_interface)}

    imp = featImpMDA_Repeated_Clustered(regressor, X=X_input, y= y_input, clstrs=feature_clstrs, n_splits=2, n_repeats=400)
    imp.index = x_interface
    temp_data[col] = imp['mean']
    print(temp_data)


print(temp_data)
temp_data = temp_data[['weight', 'weight_lag_1', 'weight_lag_2', 'weight_lag_3', 'weight_lag_4']]


THEME_COLORS = {
    "background": "#F5F7FA",
    "card": "#FFFFFF",
    "primary": "#005BBB",
    "text": "#1A1A1A",
    "textMuted": "#5A5A5A",
    "grid": "#D7DDE5",
    "accent": "#E63946" # For high-importance highlights
}

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Inter', 'Arial']

# 1. Setup Figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=THEME_COLORS["background"])
ax.set_facecolor(THEME_COLORS["card"])

# 2. Refined Heatmap
# Using a higher 'vmax' if your data is 0-1 to ensure the 'vlag' contrast is scientific
sns.heatmap(temp_data, 
            annot=True, 
            fmt=".1%", # Display as percentages for better readability
            cmap="vlag", 
            center=0, 
            linewidths=3, 
            linecolor=THEME_COLORS["background"], # Matches background for 'floating' effect
            cbar_kws={
                "shrink": .8, 
                "label": "Importance Score (% Error Increase)",
                "pad": 0.05
            },
            annot_kws={"size": 14, "weight": "bold"},
            ax=ax)

# 3. Aligned & Styled Header
ax.text(0, 1.25, 'The Hierarchy of Prediction: MDA Analysis', 
        transform=ax.transAxes, fontsize=28, fontweight='bold', color=THEME_COLORS['text'], ha='left')

ax.text(0, 1.10, 'Feature Importance measured by the percentage increase in Model Error when feature values are shuffled.\n'
                 'High values (Red) indicate variables the metabolism "relies" on for weight trajectory prediction.', 
        transform=ax.transAxes, fontsize=15, color=THEME_COLORS['textMuted'], ha='left', linespacing=1.6)

# 4. Axes Styling
# Dynamically ensure labels match the number of columns in your data
num_cols = temp_data.shape[1]
column_labels = [f'{i+1} Month Lag' for i in range(num_cols)]

ax.set_xticks(np.arange(num_cols) + 0.5) # Center the ticks
ax.set_xticklabels(column_labels, fontsize=12, color=THEME_COLORS['textMuted'])

ax.set_yticks(np.arange(len(x_interface)) + 0.5) # Center the ticks
ax.set_yticklabels([ 'Sleep', 'Steps', 'Insulin', 'Active Calories'], rotation=0, fontsize=14, fontweight='bold', color=THEME_COLORS['text'])


# Remove tick marks for a cleaner "DIB" look
ax.tick_params(left=False, bottom=False)

# 5. Footer / Source
ax.text(1, -0.15, 'Data: 24-Month T1D Longitudinal Study | yellowplanet.com', 
        transform=ax.transAxes, fontsize=11, color=THEME_COLORS['textMuted'], ha='right', style='italic')

# 6. Final Layout Spacing
plt.tight_layout(rect=[0, 0.05, 1, 0.92])
plt.show()

