import os

import markdown
import requests
from dotenv import load_dotenv


load_dotenv()


class ConfluenceClient:
    def __init__(self):
        self.base_url = os.environ["CONFLUENCE_BASE_URL"].rstrip("/")
        self.email = os.environ["CONFLUENCE_EMAIL"]
        self.api_token = os.environ["CONFLUENCE_API_TOKEN"]
        self.page_id = os.environ["CONFLUENCE_PAGE_ID"]

        self.auth = (self.email, self.api_token)

    def get_page(self) -> dict:
        url = f"{self.base_url}/rest/api/content/{self.page_id}"

        response = requests.get(
            url,
            params={"expand": "body.storage,version,title"},
            auth=self.auth,
            headers={"Accept": "application/json"},
            timeout=20,
        )

        response.raise_for_status()
        return response.json()

    def update_page_from_markdown(self, markdown_content: str) -> dict:
        page = self.get_page()

        title = page["title"]
        current_version = page["version"]["number"]
        next_version = current_version + 1

        html_content = markdown.markdown(
            markdown_content,
            extensions=["extra"],
        )

        url = f"{self.base_url}/rest/api/content/{self.page_id}"

        payload = {
            "id": self.page_id,
            "type": "page",
            "title": title,
            "version": {
                "number": next_version,
                "minorEdit": True,
            },
            "body": {
                "storage": {
                    "value": html_content,
                    "representation": "storage",
                }
            },
        }

        response = requests.put(
            url,
            json=payload,
            auth=self.auth,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=20,
        )

        response.raise_for_status()
        return response.json()