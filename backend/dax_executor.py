
import os
import requests
import msal
import pandas as pd

# =====================================================
# POWER BI CONFIGURATION
# =====================================================

TENANT_ID = "36627a7a-9acb-42a2-a6f9-a65cc894def7"
CLIENT_ID = "f60b754c-c95f-4bb7-87b2-12e8d5d131db"

WORKSPACE_ID = "1531ea24-0b16-452f-8ef1-a5c518c1ac10"
DATASET_ID = "31841f98-7507-4f21-8c1d-28415421cbc6"

# =====================================================
# POWER BI CONFIGURATION
# =====================================================

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

SCOPES = [
    "https://analysis.windows.net/powerbi/api/Dataset.Read.All"
]

EXECUTE_URL = (
    f"https://api.powerbi.com/v1.0/myorg/groups/"
    f"{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
)

# =====================================================
# AUTHENTICATION
# =====================================================

_msal_app = None
_access_token = None


def get_access_token():

    global _msal_app, _access_token

    if _msal_app is None:
        _msal_app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY
        )

    # Try silent authentication first
    accounts = _msal_app.get_accounts()

    if accounts:
        result = _msal_app.acquire_token_silent(
            SCOPES,
            account=accounts[0]
        )

        if result and "access_token" in result:
            _access_token = result["access_token"]
            return _access_token

    # Interactive login if no valid cached token exists
    result = _msal_app.acquire_token_interactive(
        scopes=SCOPES
    )

    if "access_token" not in result:
        raise Exception(
            "Power BI authentication failed: "
            + result.get("error_description", str(result))
        )

    _access_token = result["access_token"]

    return _access_token


# =====================================================
# EXECUTE DAX
# =====================================================

def execute_dax(query):

    global _access_token

    if not query or not query.strip():
        raise ValueError("DAX query cannot be empty.")

    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "queries": [
            {
                "query": query
            }
        ],
        "serializerSettings": {
            "includeNulls": True
        }
    }

    response = requests.post(
        EXECUTE_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    # Retry once if the token has expired or been rejected
    if response.status_code == 401:

        _access_token = None
        token = get_access_token()

        headers["Authorization"] = f"Bearer {token}"

        response = requests.post(
            EXECUTE_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

    if not response.ok:
        raise Exception(
            f"Power BI API Error: {response.status_code}\n"
            f"{response.text}"
        )

    data = response.json()

    try:
        rows = data["results"][0]["tables"][0]["rows"]

        return pd.DataFrame(rows)

    except (KeyError, IndexError, TypeError) as e:
        raise Exception(
            f"Unable to parse Power BI response: {data}"
        ) from e
