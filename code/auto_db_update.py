import asyncio
import datetime

import aiohttp
import pause
from bs4 import BeautifulSoup
from partroller import get_areas_dict


async def parse_next_update():
    async with aiohttp.ClientSession() as session:
        async with session.get(url="https://vstup.osvita.ua") as response:
            soup = BeautifulSoup(await response.text(), "lxml")
            last_update = soup.find("div", class_="last-update").text.split(
                "(наступне оновлення "
            )
            next = last_update[1].split(")")[0].split(".")
            next_update_date = datetime.datetime(
                year=int(next[2]),
                month=int(next[1]),
                day=int(next[0]),
                hour=23,
                minute=59,
            )
            return next_update_date


async def update_one_time_for_a_day():
    while True:
        print("Update started")
        next_update = await parse_next_update()
        await get_areas_dict()
        pause.until(next_update)


if __name__ == "__main__":
    # start = datetime.datetime.now()
    # asyncio.run(get_all_areas_to_db())
    # print(datetime.datetime.now() - start)
    asyncio.run(update_one_time_for_a_day())