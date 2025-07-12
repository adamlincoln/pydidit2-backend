"""Utils."""

from contextlib import suppress
from urllib.parse import urlparse

with suppress(ImportError):
    import boto3

if "boto3" in globals():
    def build_rds_db_url(db_url: str) -> str:
        """Use the boto3 library to construct a short lived IAM auth token."""
        if "amazonaws" in db_url:
            url_parts = urlparse(db_url)
            client = boto3.Session(profile_name="pydidit").client("rds")
            netloc, port = url_parts.netloc.split(":", maxsplit=1)

            token = client.generate_db_auth_token(
                DBHostname=netloc,
                Port=port,
                DBUsername="pydidit_db_user",
                Region="us-east-1",
            )

            db_url = f"{url_parts.scheme}://pydidit_db_user:{token}@{netloc}:{port}/postgres?sslmode=require"

        return db_url
