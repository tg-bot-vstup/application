import datetime
import pause

import aiohttp
import asyncio

from bs4 import BeautifulSoup

from controller import get_all_areas_to_db


async def parse_next_update():
    async with aiohttp.ClientSession() as session:
        async with session.get(url="https://vstup.osvita.ua") as response:
            soup = BeautifulSoup(await response.text(), "lxml")
            last_update = soup.find("div", class_="last-update").text.split("(наступне оновлення ")
            previous = last_update[0].split(' ')[-2].split(".")
            previous_update_date = datetime.date(
                year=int(previous[2]),
                month=int(previous[1]),
                day=int(previous[0])
            )
            print(previous_update_date)
            next = last_update[1].split(")")[0].split(".")
            next_update_date = datetime.datetime(
                year=int(next[2]),
                month=int(next[1]),
                day=int(next[0]),
                hour=23,
                minute=59
            )
            return next_update_date, previous_update_date

async def update_one_time_for_a_day():
    while True:
        next_update, previous_update = await parse_next_update()
        current_time = datetime.date.today()
        if current_time > previous_update:
            """
            need to add something like table to db containing information about last update
            """
            # await get_all_areas_to_db()
            print("shiiieeeet")
            print(datetime.date.today())
        pause.until(next_update)


if __name__ == "__main__":
    # start = datetime.datetime.now()
    # asyncio.run(get_all_areas_to_db())
    # print(datetime.datetime.now() - start)
    asyncio.run(update_one_time_for_a_day())
