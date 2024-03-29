import json
import os
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

N_PAGES = 326
N_REVIEWS = 4792

url = "https://www.theramenrater.com/page/{page}/"

placeholder_img = "https://media.istockphoto.com/id/1409329028/vector/no-picture-available-placeholder-thumbnail-icon-illustration-design.jpg?s=612x612&w=0&k=20&c=_zOuJu755g2eEUioiOUdz_mHKJQJn-tDgIAhQzyeKUQ="

pattern = re.compile(r"#(\d+): (.+)")


@dataclass
class Review:
    title: str
    id: int
    img_url: str


def scrape() -> None:
    os.makedirs("results", exist_ok=True)
    stats = {"ids_on_pages": {}}
    reviews = []
    for i in range(1, N_PAGES + 1):
        try:
            soup = get_page_data(i)
            parsed = parse_page(soup)
            reviews.extend(parsed)
            stats["ids_on_pages"][i] = [review.id for review in parsed]
        except Exception as e:
            print(f"Failed to scrape page {i}")
            print(e)
    print(len(reviews))
    for review in reviews:
        save_review_image(review, "results")

    # check which ids are missing
    ids = [review.id for review in reviews]
    missing = [i for i in range(1, N_REVIEWS + 1) if i not in ids]
    stats["missing_ids"] = missing
    print(missing)

    with open("results/stats.json", "w") as f:
        json.dump(stats, f, indent=4)


def get_page_data(page: int):
    response = requests.get(url.format(page=page))
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def parse_page(soup: BeautifulSoup) -> list[Review]:
    reviews = soup.find_all("article")
    parsed_reviews = []
    for review in reviews:
        match = pattern.match(review.find("h2").text)
        if match is None:
            continue
        img = review.find("img")
        url = img["src"] if img else ""
        parsed_reviews.append(
            Review(
                title=match.group(2),
                id=int(match.group(1)),
                img_url=url,
            )
        )
    return parsed_reviews


def save_review_image(review: Review, dst_dir: str) -> None:
    url = review.img_url if review.img_url else placeholder_img
    img = requests.get(url)
    img_path = os.path.join(dst_dir, f"{review.id}.jpg")
    with open(img_path, "wb") as f:
        f.write(img.content)


if __name__ == "__main__":
    scrape()
