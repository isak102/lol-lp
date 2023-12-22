import aiohttp
import asyncio

__all__ = ["get_lphistory"]


async def async_get(
    session, summoner_name: str, region="EUW", page_index=1
) -> dict | None:
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
            "cLpPageIndex": page_index,
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
        print(f"Fetching page {page_index} for {summoner_name}...")
        async with session.post(
            "https://mobalytics.gg/api/lol/graphql/v1/query",
            headers=headers,
            json=json_data,
        ) as response:
            if response.status == 200:
                res = await response.json()
                return res["data"]["lol"]["player"]["lpHistory"]
            else:
                response.raise_for_status()
    except Exception as e:
        print(f"Error fetching page {page_index}: {e}")


async def get_lphistory(
    summoner_name, region="EUW", page_limit=None, batch_size=4
) -> list[dict | None]:
    """
    Asynchronously fetches a player's League of Legends LP (League Points) history from the Mobalytics API,
    using batched requests to manage load.

    This function first fetches the first page to determine the total number of pages available. It then
    fetches the remaining pages in batches to avoid overwhelming the server and the network.
    """
    async with aiohttp.ClientSession() as session:
        first_page = await async_get(session, summoner_name, region, 1)
        total_pages = first_page["pageInfo"]["totalPages"]  # type: ignore
        print(f"Total pages: {total_pages}")

        if page_limit is not None:
            total_pages = min(total_pages, page_limit)

        all_pages = [first_page]
        for i in range(2, total_pages + 1, batch_size):
            end = min(i + batch_size, total_pages + 1)
            tasks = [
                async_get(session, summoner_name, region, j) for j in range(i, end)
            ]
            batch_results = await asyncio.gather(*tasks)
            all_pages.extend(batch_results)

        return all_pages
