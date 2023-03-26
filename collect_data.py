from graphql import DocumentNode
from gql import gql
from os import environ, path
import json
from typing import Any, Dict
from linear_client import LinearClient

TEAM_NAME: str = 'Juristat'
AFTER_DATE: str = '2023-03-01'
BEFORE_DATE: str = '2023-03-31'

TOKEN: str = environ.get('LINEAR_API_KEY')
client: LinearClient = LinearClient(TOKEN)

with open(path.join('queries', 'states.gql'), 'r') as file_handle:
    states_query: DocumentNode = gql(file_handle.read())

variable_values: Dict[str, Any] = {
    'filter': {
        'team': {
            'name': {
                'eq': TEAM_NAME
            }
        },
    }
}

states_result: Dict[str, Any] = client.execute(
    states_query, variable_values=variable_values)

with open('states.json', 'w') as f:
    json.dump(states_result, f)

with open(path.join('queries', 'issues.gql'), 'r') as file_handle:
    issues_query: DocumentNode = gql(file_handle.read())

variable_values: Dict[str, Any] = {
    'filter': {
        'team': {
            'name': {
                'eq': TEAM_NAME
            }
        },
        'createdAt': {
            'gt': BEFORE_DATE,
            'lt': AFTER_DATE,
        },
    }
}

issues_result = client.drain(
    query=issues_query,
    desired_path=('issues', 'nodes'),
    page_info_path=('issues', 'pageInfo'),
    variable_values=variable_values,
)

with open('data.json', 'w') as f:
    json.dump(issues_result, f)
