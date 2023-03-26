import json
import pandas as pd
from datetime import datetime

TIME_FORMAT = "%d/%m/%Y %H:%M:%SZ"
CURRENT_NOW = pd.to_datetime(datetime.utcnow().strftime(TIME_FORMAT))

with open('states.json') as f:
    states_result = json.load(f)

states = list()
for state in states_result['workflowStates']['nodes']:
    states.append(state['name'])

columns = ['ID']
for state in states:
    columns.append(f"{state} Start")
    columns.append(f"{state} End")
    columns.append(f"{state} Duration")

issue_state_dates = pd.DataFrame(columns=columns)

with open('data.json') as f:
    issues_result = json.load(f)

oldest_created_date = CURRENT_NOW
for issue in issues_result:
    issue_created_at = pd.to_datetime(issue['createdAt'])
    if issue_created_at < oldest_created_date:
        oldest_created_date = issue_created_at
    row = dict()
    row['ID'] = issue['identifier']
    for state in states:
        row[f"{state} Start"] = pd.NA
        row[f"{state} End"] = pd.NA
        row[f"{state} Duration"] = pd.NA
    oldest_state = 'For Grooming'
    oldest_state_date = CURRENT_NOW
    for history in issue['history']['nodes']:
        if history['fromState'] is None:
            continue
        row[f"{history['fromState']['name']} End"] = pd.to_datetime(
            history['createdAt'])
        row[f"{history['toState']['name']} Start"] = pd.to_datetime(
            history['createdAt'])
        if pd.to_datetime(history['createdAt']) < oldest_state_date:
            oldest_state = history['fromState']['name']
            oldest_state_date = pd.to_datetime(history['createdAt'])
    row[f"{oldest_state} Start"] = issue_created_at
    for state in states:
        if row[f"{state} Start"] is not pd.NA and row[f"{state} End"] is not pd.NA:
            row[f"{state} Duration"] = row[f"{state} End"] - \
                row[f"{state} Start"]
    issue_state_dates.loc[len(issue_state_dates)] = row

cycle_time_df = issue_state_dates[
    ~issue_state_dates['Done Start'].isna() &
    ~issue_state_dates['In Progress Start'].isna()
]
cycle_time_durations = cycle_time_df['Done Start'] - \
    cycle_time_df['In Progress Start']
throughput = len(cycle_time_durations)
cycle_time = {
    'mean': cycle_time_durations.mean(),
    'median': cycle_time_durations.median(),
    'min': cycle_time_durations.min(),
    'max': cycle_time_durations.max(),
}
committed_lead_time_df = issue_state_dates[
    ~issue_state_dates['Done Start'].isna() &
    (
        ~issue_state_dates['Todo Start'].isna() |
        ~issue_state_dates['Todo backlog Start'].isna()
    )
]
committed_lead_time_durations = pd.DataFrame(
    columns=['Start', 'End', 'Duration'])
committed_lead_time_durations['End'] = committed_lead_time_df['Done Start']
committed_lead_time_durations['Start'] = committed_lead_time_df['Todo Start']
for index, row in committed_lead_time_durations.iterrows():
    if pd.isna(row['Start']):
        row['Start'] = committed_lead_time_df['Todo backlog Start'][index]
committed_lead_time_durations['Duration'] = committed_lead_time_durations['End'] - \
    committed_lead_time_durations['Start']
committed_lead_time = {
    'mean': committed_lead_time_durations['Duration'].mean(),
    'median': committed_lead_time_durations['Duration'].median(),
    'min': committed_lead_time_durations['Duration'].min(),
    'max': committed_lead_time_durations['Duration'].max(),
}
suggested_lead_time_df = issue_state_dates[
    ~issue_state_dates['Done Start'].isna() & (
        ~issue_state_dates['Triage Start'].isna() |
        ~issue_state_dates['For Grooming Start'].isna()
    )
]
suggested_lead_time_durations = pd.DataFrame(
    columns=['Start', 'End', 'Duration'])
suggested_lead_time_durations['End'] = suggested_lead_time_df['Done Start']
suggested_lead_time_durations['Start'] = suggested_lead_time_df['Triage Start']
for index, row in suggested_lead_time_durations.iterrows():
    if pd.isna(row['Start']):
        row['Start'] = suggested_lead_time_df['For Grooming Start'][index]
suggested_lead_time_durations['Duration'] = suggested_lead_time_durations['End'] - \
    suggested_lead_time_durations['Start']
suggested_lead_time = {
    'mean': suggested_lead_time_durations['Duration'].mean(),
    'median': suggested_lead_time_durations['Duration'].median(),
    'min': suggested_lead_time_durations['Duration'].min(),
    'max': suggested_lead_time_durations['Duration'].max(),
}

state_counts = pd.DataFrame(columns=['Date'] + states + ['Total'])

for day in pd.date_range(start=oldest_created_date, end=pd.to_datetime(datetime.utcnow().strftime("%d/%m/%Y %H:%M:%SZ")), freq='D', normalize=True):
    next_day = day + pd.Timedelta(days=1)
    row = dict()
    row['Date'] = day
    row['Total'] = 0
    for state in states:
        row[state] = 0
    oldest_possible = oldest_created_date - pd.Timedelta(days=1)
    for index, issue in issue_state_dates.iterrows():
        latest_state = ''
        latest_state_date = oldest_possible
        for state in states:
            if issue[f"{state} Start"] is not pd.NA:
                state_start = pd.to_datetime(issue[f"{state} Start"])
                if state_start < next_day and state_start > latest_state_date:
                    latest_state = state
                    latest_state_date = state_start
        if '' != latest_state:
            row[latest_state] += 1
            row['Total'] += 1

    state_counts.loc[len(state_counts)] = row

print(throughput)
print(cycle_time)
print(committed_lead_time)
print(suggested_lead_time)
print(state_counts)
