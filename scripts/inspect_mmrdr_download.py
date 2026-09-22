import requests

ARTICLE_ID = 29423747

url = f"https://api.figshare.com/v2/articles/{ARTICLE_ID}"

print("\n=== FIGSHARE ARTICLE ===")

article = requests.get(
    url,
    timeout=30
)

article.raise_for_status()

data = article.json()

print("Title:", data.get("title"))
print("Version:", data.get("version"))
print("DOI:", data.get("doi"))

print("\n=== FILES ===")

files = data.get(
    "files",
    []
)

total = 0

for i, f in enumerate(
    files,
    start=1,
):

    size = int(
        f.get(
            "size",
            0
        )
    )

    total += size

    print(
        f"\n[{i}]"
    )

    print(
        "ID:",
        f.get("id")
    )

    print(
        "Name:",
        f.get("name")
    )

    print(
        "Size GB:",
        round(
            size
            /
            1024**3,
            3
        )
    )

    print(
        "Download:",
        f.get(
            "download_url"
        )
    )


print(
    "\nTOTAL GB:",
    round(
        total
        /
        1024**3,
        3
    )
)
