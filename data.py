from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from os import environ


URL = 'https://api.linear.app/graphql'
TOKEN = environ.get('LINEAR_API_KEY')


transport = RequestsHTTPTransport(
    url="https://api.linear.app/graphql",
    verify=True,
    retries=3,
    headers={
        'Authorization': TOKEN,
    }
)

client = Client(transport=transport, fetch_schema_from_transport=True)


query = gql(
    """
query Teams {
  teams {
    nodes {
      id
      name
    }
  }
}
"""
)

result = client.execute(query)
print(result)
