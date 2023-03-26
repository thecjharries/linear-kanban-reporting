"""A convenience wrapper around gql for Linear's GraphQL API."""
from functools import reduce
from graphql import DocumentNode
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from typing import Any, Dict, List, Tuple


class LinearClient:
    """A convenience wrapper around gql for Linear's GraphQL API."""

    """The URL for the Linear GraphQL API."""
    URL: str = 'https://api.linear.app/graphql'

    def __init__(self, token: str):
        """
        Initialize the client.

        :param token: The API key for the Linear workspace.
        """
        self.token: str = token
        self.transport: RequestsHTTPTransport = RequestsHTTPTransport(
            url=self.URL,
            verify=True,
            retries=3,
            headers={
                'Authorization': self.token,
            }
        )
        self.client: Client = Client(transport=self.transport,
                                     fetch_schema_from_transport=True)

    def execute(self, query: DocumentNode, variable_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        :param query: The query to execute.
        :param variable_values: The variables to use in the query.
        :return: The result of the query.
        """
        return self.client.execute(query, variable_values=variable_values)

    def paginate(self, query: DocumentNode, path: Tuple[str], variable_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Paginate through a GraphQL query.

        :param query: The query to execute.
        :param path: The path to the page info in the result.
        :param variable_values: The variables to use in the query.
        :return: The result of the query.
        """
        page_info = {
            'hasNextPage': True,
            'endCursor': None
        }
        while page_info['hasNextPage']:
            variable_values['after'] = page_info['endCursor']
            result = self.execute(query, variable_values=variable_values)
            page_info = reduce(dict.get, path, result)
            yield result

    def drain(self, query: DocumentNode, desired_path: Tuple[str], page_info_path: Tuple[str], variable_values: Dict[str, Any] = None) -> List[Any]:
        """
        Drain a GraphQL query.

        :param query: The query to execute.
        :param desired_path: The path to the desired data in the result.
        :param page_info_path: The path to the page info in the result.
        :param variable_values: The variables to use in the query.
        :return: The desired data from the query.
        """
        result = list()
        for page in self.paginate(query, page_info_path, variable_values=variable_values):
            result.extend(reduce(dict.get, desired_path, page))
        return result
