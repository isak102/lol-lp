import asyncio
import logging

import aiohttp
import requests

__all__ = ["get_lphistory", "get_apex_cutoffs"]

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API-related errors."""

    pass


async def async_get_page(
    session, summoner_name: str, region, page_index
) -> dict | None:
    """
    Asynchronously fetches a page of a player's League Points (LP) history from Mobalytics.
    """
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

    game_name, tag_line = summoner_name.split("#")

    json_data = {
        "operationName": "LolProfilePageLpGainsQuery",
        "variables": {
            "cLpPerPage": 150,
            "cLpPageIndex": page_index,
            "gameName": game_name,
            "tagLine": tag_line,
            "region": region,
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "bade8e2e917de67ec76c0e30e82d2bc38c40fa0af1ed61a7dbe0a795cd49857f",
            },
        },
    }

    try:
        logger.info(f"Fetching page {page_index} for {summoner_name}...")
        async with session.post(
            "https://mobalytics.gg/api/lol/graphql/v1/query",
            headers=headers,
            json=json_data,
        ) as response:
            if response.status != 200:
                content = await response.text()
                logger.error(f"Non-200 HTTP status code: {response.status}")
                logger.error(f"Response content: {content}")
                response.raise_for_status()

            res = await response.json()
            if "errors" in res:
                raise APIError(f"{res['errors']}")
            return res["data"]["lol"]["player"]["lpHistory"]

    except aiohttp.ClientError as e:
        logger.error(f"Client error fetching page {page_index}: {e}")
    except asyncio.TimeoutError as e:
        logger.error(f"Timeout error fetching page {page_index}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching page {page_index}: {e}")

    return None


async def get_lphistory(
    summoner_name, region, page_limit=None, batch_size=4
) -> list[dict]:
    """
    Asynchronously fetches a player's League of Legends LP history from the Mobalytics API,
    using batched requests to manage load. Throws an exception if any page fails to fetch. If
    the first page has no data (e.g no games played), an empty list is returned.
    """
    async with aiohttp.ClientSession() as session:
        try:
            first_page = await async_get_page(
                session, summoner_name, region, page_index=1
            )
            if first_page is None:
                raise Exception("Failed to fetch the first page.")

            total_pages = first_page.get("pageInfo", {}).get("totalPages", 0)
            logger.info(f"Total pages: {total_pages}")
            if total_pages == 0:
                logger.warning(f"First page has no data.")
                return []

            if page_limit is not None:
                total_pages = min(total_pages, page_limit)

            all_pages = [first_page]
            for i in range(2, total_pages + 1, batch_size):
                end = min(i + batch_size, total_pages + 1)
                tasks = [
                    async_get_page(session, summoner_name, region, j)
                    for j in range(i, end)
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, dict):
                        all_pages.append(result)
                    else:
                        raise Exception(
                            f"Error fetching a page in batch starting at {i}: {result}"
                        )

            return all_pages

        except Exception as e:
            logger.error(f"Error when fetching pages for: {summoner_name}: {e}")
            raise


def get_apex_cutoffs(
    region: str,
) -> dict[str, int]:  # TODO: handle the case where no cutoffs exist
    # TODO: only fetch cutoffs once per day
    """
    Returns a dictionary mapping each apex tier to its cutoff value. Gets the cutoffs from
    deeplol.gg. Will throw an exception if the request fails.
    """
    REGION_TO_CODE = {
        "NA": "NA1",
        "EUW": "EUW1",
        "EUNE": "EUN1",
        "BR": "BR1",
        "JP": "JP1",
        "KR": "KR",
        "LAN": "LA1",
        "LAS": "LA2",
        "OCE": "OC1",
        "TR": "TR1",
    }

    try:
        headers = {
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.deeplol.gg/",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": '"Linux"',
        }
        response = requests.get(
            "https://b2c-api-cdn.deeplol.gg/common/tier-boundary", headers=headers
        )
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()["tier_boundary_solo"][REGION_TO_CODE[region.upper()]]
    except Exception as e:
        raise Exception(f"Error fetching apex cutoffs: {e}")
