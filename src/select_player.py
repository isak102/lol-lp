import json
import subprocess
import urllib.parse as urllib

from src.config import BOOKMARKS_FILE

__all__ = ["select_player"]


def get_opgg_urls() -> list[tuple[str, str]]:
    """
    Get all op.gg urls from the bookmarks file with the bookmark name as the first element
    and the url as the second element
    """

    def strip_query_params(url):
        # Parse the URL into components
        parsed_url = urllib.urlparse(url)

        # Rebuild the URL without the query component
        new_url = urllib.urlunparse(parsed_url._replace(query=""))

        return new_url

    with open(BOOKMARKS_FILE, "r") as file:
        bookmarks = json.load(file)

    opgg_urls = []
    for root in bookmarks["roots"]["bookmark_bar"]["children"]:
        if root["name"] == "opgg":
            for child in root["children"]:
                opgg_urls.append((child["name"], strip_query_params(child["url"])))

    return [
        url
        for url in opgg_urls
        if "op.gg" in url[1]
        and "multi_old" not in url[1]
        and "multisearch" not in url[1]
    ]


def parse_url(url: str) -> tuple[str, str]:
    """
    Parse an op.gg url and return the riot ID and region
    """
    if "www.op.gg" in url and "userName=" not in url:
        # The url is the updated version
        parts = url.split("/")
        riot_id, region = parts[5], parts[4]
    else:
        # The url is the old version
        parts = url.split("/")
        region = parts[2].split(".")[0]
        if region == "www":
            region = "kr"

        if "userName=" in parts[-1]:
            riot_id = parts[-1].split("userName=")[1]
        else:
            riot_id = parts[-1]

    return (transform_riot_id(riot_id, region), region)


def transform_riot_id(riot_id: str, region: str) -> str:
    # TODO: append default tagline ?
    decoded = urllib.unquote(riot_id.replace("-", "#").replace("+", " "))
    return decoded


def select_player() -> tuple[str, str]:
    players = []
    urls = get_opgg_urls()
    for url in urls:
        bookmark_name = url[0]
        riot_id, region = parse_url(url[1])
        players.append({"title": bookmark_name, "riot_id": riot_id, "region": region})

    input_str = "\n".join(
        [
            "[{}]: {} ({})".format(player["title"], player["riot_id"], player["region"])
            for player in players
        ]
    )

    process = subprocess.Popen(
        [
            "dmenu",
            "-p",
            "Select player",
            "-ix",
            "-l",
            "25",
            "-g",
            "3",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    output, _ = process.communicate(input_str)
    index = output.strip()
    if index.isdigit():
        index = int(index)
    else:
        exit(1)

    return (players[index]["riot_id"], players[index]["region"])
