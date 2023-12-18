import requests


def get(summoner_name: str, region: str = "EUW") -> dict | None:
    headers = {
        "authority": "mobalytics.gg",
        "accept": "*/*",
        "accept-language": "en_us",
        "content-type": "application/json",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-moba-client": "mobalytics-web",
        "x-moba-proxy-gql-ops-name": "LolProfilePageLpGainsQuery",
    }

    json_data = {
        "operationName": "LolProfilePageLpGainsQuery",
        "variables": {
            "cLpPerPage": 150,
            "summonerName": summoner_name,
            "region": region,
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "75a0cdde5122fb16124634512f4cdc44551272d7e82ab827818c3b37bd72e97b",
            },
        },
    }

    try:
        response = requests.post(
            "https://mobalytics.gg/api/lol/graphql/v1/query",
            headers=headers,
            json=json_data,
        )
        if response.status_code == 200:
            res = response.json()["data"]["lol"]["player"]["lpHistory"]
            return res
        else:
            response.raise_for_status()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
