# src/github_client.py
import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv



load_dotenv(override=True)
GQL_URL = "https://api.github.com/graphql"
TOKEN = os.getenv("GH_TOKEN")  # GitHub Actions token or local token

# Default headers
HEADERS = {
    "Authorization": f"bearer {TOKEN}" if TOKEN else "",
    "Accept": "application/vnd.github.v4+json"
}

# GraphQL query to search repositories (max 100 per page)
SEARCH_QUERY = """
query($queryString: String!, $first: Int, $after: String) {
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
  search(query: $queryString, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      ... on Repository {
        id
        name
        url
        stargazerCount
        createdAt
        updatedAt
        owner { login }
      }
    }
  }
}
"""

class GithubGraphQLClient:
    def __init__(self, token=None):
        self.token = token or TOKEN
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"bearer {self.token}"})
        self.session.headers.update({"Accept": "application/vnd.github.v4+json"})

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type((requests.exceptions.RequestException,))
    )
    def post(self, query, variables):
        """
        Send GraphQL POST request with retries.
        Handles transient network errors and rate-limit-related exceptions.
        """
        resp = self.session.post(GQL_URL, json={"query": query, "variables": variables}, timeout=30)
        
        if resp.status_code >= 500:
            resp.raise_for_status()  # retry on server errors
        if resp.status_code == 401:
            raise Exception("Unauthorized. Check GITHUB_TOKEN permissions.")
        if resp.status_code == 403:
            # Could be rate limit
            raise Exception(f"Forbidden: {resp.text}")
        
        data = resp.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data.get('errors')}")
        
        return data

    def search_repos_page(self, query_string, first=100, after=None):
        """
        Search a single page of repositories with the given query string.
        Returns JSON data including nodes, pageInfo, and rateLimit.
        """
        variables = {"queryString": query_string, "first": first, "after": after}
        return self.post(SEARCH_QUERY, variables)
