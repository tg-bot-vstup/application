import datetime
import errno
from socket import error as SocketError

import aiohttp
import asyncio
from bs4 import BeautifulSoup

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
}


async def get_areas_dict() -> dict:
    """
    Method for parsing all areas and area urls from vstup.osvita.ua
    """
    url = "https://vstup.osvita.ua"
    async with aiohttp.ClientSession(trust_env=True) as request:
        async with request.get(url, headers=headers) as response:
            soup = BeautifulSoup(await response.text(), "lxml")

            areas_dict = None

            select_list_areas = soup.find("select", class_="region-select")
            if select_list_areas:
                select_list_areas = select_list_areas.find_all("option")
            if select_list_areas:
                areas_dict = {}
                for option in select_list_areas:
                    if option not in areas_dict:
                        option_text = option.text
                        option_value = option.get("value")
                        if option_value:
                            areas_dict[option_text] = f"{url}{option_value}"
            return areas_dict


async def get_area_universities(request, area_url: str) -> dict:
    """
    Method that get all universities and university urls for one area
    """
    if area_url:
        while True:
            try:
                async with request.get(area_url, headers=headers) as response:
                    soup = BeautifulSoup(await response.text(), "lxml")

                    uni_dict = {}

                    all_uni = soup.find("ul", class_="section-search-result-list")
                    if all_uni:
                        all_uni = all_uni.find_all("a")
                        for uni in all_uni:
                            uni_text = uni.text
                            uni_url = f"{uni.get('href')}"
                            uni_url_sized = f"{uni_url.split('/')[2]}/"
                            if uni_text not in uni_dict:
                                uni_dict[uni_text] = f"{area_url}{uni_url_sized}"
                        return uni_dict
            except SocketError as e:
                if e.errno != errno.ECONNRESET:
                    raise e
                pass


async def parse_speciality_grades(request, speciality_url):
    url = speciality_url
    while True:
        try:
            async with request.get(url, headers=headers) as response:
                speciality_2021 = BeautifulSoup(await response.text(), "lxml")
                link_2020 = speciality_2021.find("table", class_="stats-vnz-table")
                if link_2020:
                    if link_2020.find("a"):
                        url = link_2020.find("a").get("href")
                        if url:
                            url = "https://vstup.osvita.ua" + url
                            while True:
                                try:
                                    async with request.get(url, headers=headers) as response:
                                        speciality_2020 = BeautifulSoup(await response.text(), "lxml")
                                        avg_grades = speciality_2020.find("table", class_="stats-vnz-table")
                                        if avg_grades:
                                            avg_grades = avg_grades.select('tr')
                                        if avg_grades:
                                            min_budget = None
                                            avg_contract = None
                                            for row in avg_grades:
                                                info_list = row.select("td")
                                                if info_list[
                                                    0].text == "Мінімальний рейтинговий бал серед зарахованих на бюджет":
                                                    min_budget = info_list[1].text
                                                if info_list[0].text == 'Середній рейтинговий бал зарахованих на контракт':
                                                    avg_contract = info_list[1].text
                                            return min_budget, avg_contract
                                        break
                                except SocketError as e:
                                    if e.errno != errno.ECONNRESET:
                                        raise e
                                    pass
                break
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise e
            pass
    return None, None



async def parse_ode_department(request, dep):
    department_dict = {}
    try:
        department = dep.text.split("Факультет:")[1]
        department = department.split('Освітня')[0].strip()
    except IndexError:
        department = "-"
    knowledge_area = dep.text.split("Галузь:")[1].split('Спеціальність')[0].strip()
    speciality = dep.find("a").text
    program = dep.text.split("Освітня програма:")[1].split("\n")[0].strip()
    speciality_url = "https://vstup.osvita.ua" + dep.find("a", class_="green-button").get("href")
    grades_names = dep.select('div[class*="sub"]')
    grades_dict = {}
    for grade in range(0, len(grades_names), 2):
        name = grades_names[grade].text.split("(")[0].strip()
        coefficient = grades_names[grade].text.replace(" \n", "").replace(")", "").replace(", ",
                                                                                           "").replace(
            "балmin=", "k=").strip().split("k=")[1:3]
        if len(coefficient) > 1:
            grades_dict[name] = coefficient[1]
        else:
            grades_dict[name] = coefficient[0]
    department_dict[speciality] = {"zno": grades_dict}
    min_budget, avg_contract = await parse_speciality_grades(request, speciality_url)
    department_dict[speciality]["old_budget"] = min_budget
    department_dict[speciality]["old_contract"] = avg_contract
    department_dict[speciality]["department"] = department
    department_dict[speciality]["program"] = program
    department_dict[speciality]["speciality_url"] = speciality_url
    department_dict[speciality]["knowledge_area"] = knowledge_area
    return department_dict

async def get_university_department(request, university_url: str):
    """
    Method that parse every department for one university
    """
    url = university_url
    while True:
        try:
            async with request.get(url, headers=headers) as response:
                if response:
                    soup = BeautifulSoup(await response.text(), "lxml")
                    year_urls = soup.find_all("span", class_="year")
                    url_2021 = 0
                    for i in year_urls:
                        if "2021" in i.text:
                            url_2021 = i
                    while True:
                        try:
                            async with request.get("https://vstup.osvita.ua" + url_2021.find("a").get("href"), headers=headers) as response:
                                soup = BeautifulSoup(await response.text(), "lxml")
                                break
                        except SocketError as e:
                            if e.errno != errno.ECONNRESET:
                                raise e
                            pass
                    deps_all = soup.find("div", class_="panel den")
                    if deps_all:
                        deps_all = deps_all.select('div[class*="row no-gutters table-of-specs-item-row qual1 base40"]')
                    if deps_all:
                        return deps_all
                break
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise e
            continue
    return None, None



if __name__ == "__main__":
    print("da")
    start = datetime.datetime.now()
    loop = asyncio.get_event_loop()
    connector = aiohttp.TCPConnector(limit=10, force_close=True)
    request = aiohttp.ClientSession(connector=connector)
    print(loop.run_until_complete(
        parse_speciality_grades(request=request, speciality_url="https://vstup.osvita.ua/y2022/r27/183/990603/")))
    request.close()
    print(datetime.datetime.now() - start)

"""
result_example = {
                    "[Area]":
                        {"[University]":
                            {"[speciality_id]":
                                {"[Speciality]":
                                    {"zno":
                                        {"[subject]":"[coefficient]"},
                                    "old_contract": "[grade or none]",
                                    "old_budget": "[grade or none]",
                                    "knowledge_area": "[name of knowledge_area]",
                                    "program": "[program name]"
                                    }
                                }
                            }
                        }
                 }
"""


"""
                            try:
                                department = dep.text.split("Факультет:")[1]
                                department = department.split('Освітня')[0].strip()
                            except IndexError:
                                department = "-"
                            knowledge_area = dep.text.split("Галузь:")[1].split('Спеціальність')[0].strip()
                            print(knowledge_area)
                            speciality = dep.find("a").text
                            program = dep.text.split("Освітня програма:")[1].split("\n")[0].strip()
                            speciality_url = "https://vstup.osvita.ua" + dep.find("a", class_="green-button").get("href")
                            grades_names = dep.select('div[class*="sub"]')
                            counter += 1
                            grades_dict = {}
                            for grade in range(0, len(grades_names), 2):
                                name = grades_names[grade].text.split("(")[0].strip()
                                coefficient = grades_names[grade].text.replace(" \n", "").replace(")", "").replace(", ",
                                                                                                                   "").replace(
                                    "балmin=", "k=").strip().split("k=")[1:3]
                                if len(coefficient) > 1:
                                    grades_dict[name] = coefficient[1]
                                else:
                                    grades_dict[name] = coefficient[0]
                            if knowledge_area not in departments_dict.keys():
                                departments_dict[knowledge_area] = {}
                            if speciality not in departments_dict[knowledge_area]:
                                departments_dict[knowledge_area].setdefault(f"speciality{counter}", {})
                                departments_dict[knowledge_area][f"speciality{counter}"][speciality] = {"zno": grades_dict}
                            min_budget, avg_contract = await parse_speciality_grades(request, speciality_url)
                            departments_dict[knowledge_area][f"speciality{counter}"][speciality]["old_budget"] = min_budget
                            departments_dict[knowledge_area][f"speciality{counter}"][speciality]["old_contract"] = avg_contract
                            departments_dict[knowledge_area][f"speciality{counter}"][speciality][
                                "department"] = department
                            departments_dict[knowledge_area][f"speciality{counter}"][speciality]["program"] = program
                            departments_dict[knowledge_area][f"speciality{counter}"][speciality]["speciality_url"] = speciality_url
"""