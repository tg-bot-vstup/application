import asyncio
import datetime
import errno
import os
import socket

import aiohttp
from bs4 import BeautifulSoup
from db_models import (Coefficient, Knowledge_area, Region, Speciality,
                       University, Zno)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

region_coefficient_dict = {
    "м. Київ": 1.00,
    "Донецька область": 1.04,
    "Луганська область": 1.04,
    "Кіровоградська область": 1.04,
    "Миколаївська область": 1.04,
    "Рівненська область": 1.04,
    "Сумська область": 1.04,
    "Херсонська область": 1.04,
    "Житомирська область": 1.04,
    "Черкаська область": 1.04,
    "Чернігівська область": 1.04,
    "Івано-Франківська область": 1.02,
    "Вінницька область": 1.02,
    "Волинська область": 1.02,
    "Дніпропетровська область": 1.02,
    "Закарпатська область": 1.02,
    "Запорізька область": 1.02,
    "Київська область": 1.00,
    "Львівська область": 1.02,
    "Одеська область": 1.02,
    "Полтавська область": 1.02,
    "Тернопільська область": 1.02,
    "Харківська область": 1.02,
    "Хмельницька область": 1.02,
    "Чернівецька область": 1.02,
}

specialities_coefficient_dict = {
    "012": 1.02,
    "013": 1.02,
    "014": 1.02,
    "015": 1.02,
    "091": 1.02,
    "101": 1.02,
    "102": 1.02,
    "103": 1.02,
    "104": 1.02,
    "105": 1.02,
    "106": 1.02,
    "111": 1.02,
    "112": 1.02,
    "124": 1.02,
    "131": 1.02,
    "132": 1.02,
    "133": 1.02,
    "134": 1.02,
    "135": 1.02,
    "136": 1.02,
    "141": 1.02,
    "142": 1.02,
    "143": 1.02,
    "144": 1.02,
    "145": 1.02,
    "151": 1.02,
    "152": 1.02,
    "153": 1.02,
    "161": 1.02,
    "171": 1.02,
    "172": 1.02,
    "173": 1.02,
    "181": 1.02,
    "182": 1.02,
    "183": 1.02,
    "184": 1.02,
    "185": 1.02,
    "186": 1.02,
    "187": 1.02,
    "192": 1.02,
    "193": 1.02,
    "194": 1.02,
    "201": 1.02,
    "202": 1.02,
    "203": 1.02,
    "204": 1.02,
    "205": 1.02,
    "206": 1.02,
    "207": 1.02,
    "208": 1.02,
    "251": 1.02,
    "252": 1.02,
    "253": 1.02,
    "254": 1.02,
    "255": 1.02,
    "261": 1.02,
    "263": 1.02,
    "271": 1.02,
    "272": 1.02,
    "273": 1.02,
    "274": 1.02,
    "275": 1.02,
}

db_link = "postgresql+asyncpg:" + os.environ.get("DATABASE_URL")
async_engine = create_async_engine(db_link, pool_size=30, pool_timeout=300)
async_session = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/97.0.4692.71 Safari/537.36"
}


async def get_region(region_name: str):
    """
    function used to get region id from db or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            region = await session.execute(
                select(Region.id).filter(Region.name == region_name)
            )
            region = region.scalars().first()
            if not region:
                return None
            return region


async def create_region(region_name: str):
    """
    function used to create region object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            region = Region(
                name=region_name,
                region_coefficient=region_coefficient_dict[region_name],
            )
            session.add(region)
            await session.commit()
            return region.id


async def start_parsing():
    """
    function for parsing all regions and region urls from vstup.osvita.ua
    and add region if it does not exist
    """
    url = "https://vstup.osvita.ua"
    connector = aiohttp.TCPConnector(limit=50, force_close=True)
    request = aiohttp.ClientSession(connector=connector)
    async with request.get(url, headers=headers) as response:
        soup = BeautifulSoup(await response.text(), "lxml")

        select_list_regions = soup.find("select", class_="region-select")
        if select_list_regions:
            select_list_regions = select_list_regions.find_all("option")
        if select_list_regions:
            # tasks = []
            for option in select_list_regions:
                option_text = option.text
                option_value = option.get("value")
                if option_value:
                    region_id = await get_region(option_text)
                    if not region_id:
                        region_id = await create_region(option_text)
                    region_url = f"{url}{option_value}"
                    print(option_text)
                    # tasks.append(
                    #     asyncio.ensure_future(
                    #         get_region_universities(
                    #             request=request,
                    #             region_url=region_url,
                    #             region_id=region_id
                    #         )
                    #     )
                    # )
                    await get_region_universities(
                        request=request,
                        region_url=region_url,
                        region_id=region_id
                    )
            # await asyncio.wait(tasks)
    await request.close()


async def get_university(university: str, region_id: int):
    """
    function used to get university id from db
    or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            university_id = await session.execute(
                select(University.id).filter(
                    University.name == university,
                    University.region_id == region_id
                )
            )
            university_id = university_id.scalars().first()
            return university_id


async def create_university(university: str, region_id: int):
    """
    function used to create university object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            university_object = University(
                name=university,
                region_id=region_id
            )
            session.add_all([university_object])
            await session.commit()
            return university_object.id


async def get_region_universities(
    request: aiohttp.ClientSession, region_url: str, region_id: int
):
    """
    Method that get all universities and university urls for one region
    and add them to db if they are not in there already
    """
    if region_url:
        while True:
            soup = await get_soup(request, url=region_url)
            all_uni = soup.find("ul", class_="section-search-result-list")
            if all_uni:
                all_uni = all_uni.find_all("a")
                tasks = []
                if all_uni:
                    for uni in all_uni:
                        uni_text = uni.text
                        uni_url = f"{uni.get('href')}"
                        uni_url_sized = f"{uni_url.split('/')[2]}/"
                        university_id = await get_university(
                            uni_text, region_id=region_id
                        )
                        if not university_id:
                            university_id = await create_university(
                                university=uni_text, region_id=region_id
                            )
                        university_url = f"{region_url}{uni_url_sized}"
                        print(uni_text)
                        await get_university_department(
                            request=request,
                            university_url=university_url,
                            university_id=university_id,
                        )
                    #     tasks.append(
                    #         asyncio.ensure_future(
                    #             get_university_department(
                    #                 request=request,
                    #                 university_url=university_url,
                    #                 university_id=university_id
                    #             )
                    #         )
                    #     )
                    # await asyncio.wait(tasks)
                    break


async def get_grades(avg_grades: BeautifulSoup):
    """
    function used to get minimal rating for budget
    and average rating for contract if they are exists
    """
    if avg_grades:
        avg_grades = avg_grades.select("tr")
        if avg_grades:
            min_budget = None
            avg_contract = None
            for row in avg_grades:
                info_list = row.select("td")
                if (
                    info_list[0].text == "Мінімальний рейтинговий бал"
                    " серед зарахованих на бюджет"
                ):
                    min_budget = info_list[1].text
                if (
                    info_list[0].text
                    == "Середній рейтинговий бал зарахованих на контракт"
                ):
                    avg_contract = info_list[1].text
            return min_budget, avg_contract
    return None, None


async def get_soup(request: aiohttp.ClientSession, url: str):
    while True:
        try:
            async with request.get(
                    url,
                    headers=headers
            ) as response:
                return BeautifulSoup(await response.text(), "lxml")
        except socket.error as e:
            if e.errno != errno.ECONNRESET:
                raise e


async def parse_speciality_grades(
        request: aiohttp.ClientSession,
        speciality_url: str
):
    """
    function used to get grades for speciality from past years
    """
    speciality_2021 = await get_soup(request, speciality_url)
    avg_grades = speciality_2021.find("table", class_="stats-vnz-table")
    min_budget, avg_contract = await get_grades(avg_grades)
    if min_budget or avg_contract:
        return min_budget, avg_contract
    link_2020 = speciality_2021.find("table", class_="stats-vnz-table")
    if link_2020:
        if link_2020.find("a"):
            url = link_2020.find("a")
            if url:
                url = url.get("href")
                if url:
                    url = "https://vstup.osvita.ua" + url
                    speciality_2020 = await get_soup(request, url)
                    avg_grades = speciality_2020.find(
                        "table", class_="stats-vnz-table"
                    )
                    min_budget, avg_contract = await get_grades(
                        avg_grades
                    )
                    return min_budget, avg_contract
    return None, None


async def get_knowledge_area(university_id: int, knowledge_area: str):
    """
    function used to get knowledge area id from db
    or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            knowledge_area = await session.execute(
                select(Knowledge_area.id).filter(
                    Knowledge_area.university_id == university_id,
                    Knowledge_area.name == knowledge_area,
                )
            )
            knowledge_area = knowledge_area.scalars().first()
            return knowledge_area


async def create_knowledge_area(university_id, knowledge_area):
    """
    function used to create knowledge area object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            knowledge_area = Knowledge_area(
                university_id=university_id, name=knowledge_area
            )
            session.add_all([knowledge_area])
            await session.commit()
            return knowledge_area.id


async def get_university_department(
    request: aiohttp.ClientSession, university_url: str, university_id: int
):
    """
    Method that parse every speciality for one university
    and add knowledge areas if they are not exists
    """
    soup = await get_soup(request=request, url=university_url)
    year_urls = soup.find_all("span", class_="year")
    if year_urls:
        url_2021 = year_urls[1]
        if url_2021:
            url = url_2021.find("a")
            if url:
                url = "https://vstup.osvita.ua" + url.get("href")
                soup = await get_soup(request, url)
                deps_all = soup.find("div", class_="panel den")
                if deps_all:
                    deps_all = deps_all.select(
                        'div[class*="row no-gutters'
                        ' table-of-specs-item-row qual1 base40"]'
                    )
                if deps_all:
                    tasks = []
                    for dep in deps_all:
                        # await parse_ode_department(
                        #     request,
                        #     dep,
                        #     university_id
                        # )
                        tasks.append(
                            asyncio.ensure_future(
                                parse_ode_speciality(
                                    request,
                                    dep,
                                    university_id
                                )
                            )
                        )
                    await asyncio.wait(tasks)


async def get_speciality(speciality_url: str):
    """
    function used to get speciality object from db
    or None if there is no such object
    """
    async with async_session() as session:
        async with session.begin():
            speciality_object = await session.execute(
                select(Speciality).filter_by(speciality_url=speciality_url)
            )
            speciality_object = speciality_object.scalars().first()
            if speciality_object:
                session.expunge(speciality_object)
            return speciality_object


async def create_speciality(speciality_url: str):
    """
    function used to create speciality object,
    add it to db and get it
    """
    async with async_session() as session:
        async with session.begin():
            speciality_object = Speciality(speciality_url=speciality_url)
            session.add_all([speciality_object])
            await session.commit()
            session.expunge(speciality_object)
            return speciality_object


async def edit_speciality(
    speciality_name: str,
    speciality_object: Speciality,
    min_budget: str,
    avg_contract: str,
    department: str,
    program: str,
    knowledge_area_id: int,
):
    """
    function used to edit speciality object,
    add commit changes
    """
    async with async_session() as session:
        async with session.begin():
            session.add(speciality_object)
            speciality_index = speciality_name.split(" ")[0]
            speciality_coefficient = specialities_coefficient_dict.get(
                speciality_index
            )
            if not speciality_coefficient:
                speciality_coefficient = 1
            speciality_object.program = program
            if min_budget:
                speciality_object.min_rate_budget = float(min_budget)
            if avg_contract:
                speciality_object.average_rate_contract = float(avg_contract)
            speciality_object.name = speciality_name
            speciality_object.area_id = knowledge_area_id
            speciality_object.faculty = department
            speciality_object.speciality_coefficient = speciality_coefficient
            await session.commit()


async def get_zno(subject: str):
    """
    function used to get zno id from db,
    or None if there are no such object
    """
    async with async_session() as session:
        async with session.begin():
            zno = await session.execute(
                select(
                    Zno.id
                ).filter(
                    Zno.name == subject
                )
            )
            zno = zno.scalars().first()
            return zno


async def create_zno(subject: str):
    """
    function used to create zno object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            zno = Zno(name=subject)
            session.add_all([zno])
            await session.commit()
            return zno.id


async def get_coefficient(speciality_id: int, zno_id: int):
    """
    function used to get coefficient object from db,
    or None if there are no such object
    """
    async with async_session() as session:
        async with session.begin():
            coefficient_object = await session.execute(
                select(Coefficient).filter(
                    Coefficient.speciality_id == speciality_id,
                    Coefficient.zno_id == zno_id,
                )
            )
            coefficient_object = coefficient_object.scalars().first()
            if coefficient_object:
                session.expunge(coefficient_object)
            return coefficient_object


async def create_coefficient(speciality_id: int, zno_id: str):
    """
    function used to create coefficient object,
    add it to db and get id of it
    """
    async with async_session() as session:
        async with session.begin():
            coefficient_object = Coefficient(
                speciality_id=speciality_id,
                zno_id=zno_id
            )
            session.add_all([coefficient_object])

            session.expunge(coefficient_object)
            return coefficient_object


async def edit_coefficient(
    coefficient_object: Coefficient, coefficient: str, required: bool
):
    """
    function used to edit coefficient object,
    add commit changes to db
    """
    async with async_session() as session:
        async with session.begin():
            session.add(coefficient_object)
            coefficient_object.coefficient = float(coefficient)
            coefficient_object.required = required
            await session.commit()


async def parse_ode_speciality(
    request: aiohttp.ClientSession, dep: BeautifulSoup, university_id: int
):
    """
    function used to parse information about one speciality and add/modify it
    """
    try:
        department = dep.text.split("Факультет:")[1]
        department = department.split("Освітня")[0].strip()
    except IndexError:
        department = "-"
    knowledge_area = dep.text.split(
        "Галузь:"
    )[1].split(
        "Спеціальність"
    )[0].strip()
    knowledge_area_id = await get_knowledge_area(
        university_id,
        knowledge_area
    )
    if not knowledge_area_id:
        knowledge_area_id = await create_knowledge_area(
            university_id,
            knowledge_area
        )
    speciality = dep.find("a").text
    program = dep.text.split("Освітня програма:")[1].split("\n")[0].strip()
    url = dep.find("a", class_="green-button").get("href")
    if url:
        speciality_url = "https://vstup.osvita.ua" + url
        grades_names = dep.select('div[class*="sub"]')
        min_budget, avg_contract = await parse_speciality_grades(
            request,
            speciality_url
        )
        speciality_object = await get_speciality(speciality_url)
        if not speciality_object:
            speciality_object = await create_speciality(speciality_url)
        await edit_speciality(
            speciality_name=speciality,
            speciality_object=speciality_object,
            min_budget=min_budget,
            avg_contract=avg_contract,
            department=department,
            program=program,
            knowledge_area_id=knowledge_area_id,
        )
        for grade in range(0, len(grades_names), 2):
            name = grades_names[grade].text.split("(")[0].strip()
            coefficient = (
                grades_names[grade]
                .text.replace(" \n", "")
                .replace(")", "")
                .replace(", ", "")
                .replace("балmin=", "k=")
                .strip()
                .split("k=")[1:3]
            )
            correct_name = name
            if "*" in name:
                correct_name = name[:-1]
            try:
                zno_id = await create_zno(correct_name)
            except IntegrityError:
                zno_id = await get_zno(correct_name)
            coefficient_object = await get_coefficient(
                speciality_object.id,
                zno_id
            )
            if not coefficient_object:
                coefficient_object = await create_coefficient(
                    speciality_object.id, zno_id
                )
            required = True
            if "*" in name:
                required = False
            if len(coefficient) > 1:
                coefficient_value = coefficient[1]
            else:
                coefficient_value = coefficient[0]

            await edit_coefficient(
                coefficient_object,
                coefficient_value,
                required
            )


if __name__ == "__main__":
    start = datetime.datetime.now()
    asyncio.run(start_parsing())
    print(datetime.datetime.now() - start)
