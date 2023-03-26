from graphql import DocumentNode
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from os import environ
import json
import pandas as pd
from datetime import datetime
from typing import Any, Dict

URL: str = 'https://api.linear.app/graphql'


class LinearClient:
    def __init__(self, token: str):
        self.token: str = token
        self.transport: RequestsHTTPTransport = RequestsHTTPTransport(
            url=URL,
            verify=True,
            retries=3,
            headers={
                'Authorization': self.token,
            }
        )
        self.client: Client = Client(transport=self.transport,
                                     fetch_schema_from_transport=True)

    def execute(self, query: DocumentNode, variable_values: Dict[str, Any] = None) -> Dict[str, Any]:
        return self.client.execute(query, variable_values=variable_values)


TOKEN: str = environ.get('LINEAR_API_KEY')
client: LinearClient = LinearClient(TOKEN)


states_query: DocumentNode = gql("""
query Query($filter: WorkflowStateFilter) {
  workflowStates(filter: $filter) {
    nodes {
      name
    }
  }
}
""")

variable_values: Dict[str, Any] = {
    'filter': {
        'team': {
            'name': {
                'eq': 'Juristat'
            }
        },
    }
}

states_result: Dict[str, Any] = client.execute(
    states_query, variable_values=variable_values)

with open('states.json', 'w') as f:
    json.dump(states_result, f)

exit(0)

query = gql("""
query ExampleQuery($filter: IssueFilter) {
  issues(filter: $filter) {
    nodes {
      id
      number
      identifier
      history {
        nodes {
          toState {
            name
          }
          fromState {
            name
          }
          createdAt
        }
      }
      state {
        name
      }
      title
      createdAt
      assignee {
        displayName
      }
    }
  }
}
""")

# variable_values = {
#     'filter': {
#         'team': {
#             'name': {
#                 'eq': 'Juristat'
#             }
#         },
#         'createdAt': {
#             'gt': '2023-03-01'
#         }
#     }
# }


# issues_result = client.execute(query, variable_values=variable_values)

# with open('data.json', 'w') as f:
#     json.dump(issues_result, f)

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

oldest_created_date = pd.to_datetime(
    datetime.utcnow().strftime("%d/%m/%Y %H:%M:%SZ"))
for issue in issues_result['issues']['nodes']:
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
    oldest_state_date = pd.to_datetime(
        datetime.utcnow().strftime("%d/%m/%Y %H:%M:%SZ"))
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

pd.set_option('display.max_columns', None)

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

print(state_counts)
