import requests as rq
from bs4 import BeautifulSoup
from datetime import datetime
import time
import db_func as db
import pandas as pd
from urllib.parse import urljoin, urlparse
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f'Программа заняла: {end - start} секунд; {(end - start) / 60:.2f} минут')
        print("=" * 100)
        return result
    return wrapper

categories = {
    "Наука": 'Наука и инновации',
    "Спорт": "Спорт",
    "Абитуриентам": "Абитуриентам",
    "В мире": "Объявления и события",
    "Образование": "Образование",
    "Студенчество": "Студенческая жизнь",
    "Международная деятельность": "Международная деятельность",
    "Проекты": "Сотрудничество и партнёрство",
    "Университет": "Культура и творчество"
}



urls = []

for i in range(1, 10): # всех новостей 516 страниц
    page = f"https://www.rea.ru/news?tree-content-path=news&page={i}&per-page=12"
    urls.append(page)


@timer
def parse(con, cur):
    print("=" * 100)

    print('Начинаем парсинг новостей категории')
    print("=" * 100)
    # dc = pd.read_sql("SELECT * FROM news_categories", con=con)

    data = {
        "title": [],
        "published_date": [],
        "link": [],
        "added_at": [],
        "category_id": [],
        "university_id": [],
        "content": []
    }

    for url in urls:
        response = rq.get(url, timeout=10)
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')

        if response.status_code == 200:
            items = soup.select('a.catalog__item-content')

            for item in items:
                title = item.select_one('.catalog__item-title')
                date = item.select_one('.catalog__item-date')
                link = urljoin("https://www.rea.ru", item.get("href"))
                link = link.split("?")[0]

                response_sub = rq.get(link, timeout=10)
                html_sub = response_sub.text
                soup_sub = BeautifulSoup(html_sub, 'html.parser')

                if response_sub.status_code == 200:
                    category_tag = soup_sub.select_one("li.catalog-detail__tag")

                    content_tag = soup_sub.select_one(".catalog-detail__text")

                    if content_tag:
                        short_content = content_tag.get_text(" ", strip=True)
                    else:
                        short_content = "no text"

                    data["content"].append(short_content)

                    if category_tag:
                        category = category_tag.get_text(strip=True)

                        if category in categories:
                            category_name = categories[category]

                            cat = cur.execute(
                                "SELECT category_id FROM news_categories WHERE name = ?",
                                (category_name,)
                            ).fetchone()[0]

                            data["category_id"].append(cat)
                        else:
                            cat = cur.execute("SELECT category_id FROM news_categories WHERE name = ?", ("Без категории",)).fetchone()[0]
                            data["category_id"].append(cat)
                    else:
                        cat = cur.execute("SELECT category_id FROM news_categories WHERE name = ?", ("Без категории",)).fetchone()[0]
                        data["category_id"].append(cat)

                date_text = date.get_text(strip=True)

                if date_text == "Сегодня":
                    date_text = datetime.now().strftime("%d %m %Y")

                data["title"].append(title.get_text(strip=True))
                data["published_date"].append(date_text)
                data["link"].append(link)
                data["added_at"].append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                uni = cur.execute(
                    "SELECT university_id FROM universities WHERE name = ?",
                    ("РЭУ",)
                ).fetchone()[0]

                data["university_id"].append(uni)
        # else:
        #     print(response.status_code)

    df = pd.DataFrame(data)

    months = {
        'января': '01',
        'февраля': '02',
        'марта': '03',
        'апреля': '04',
        'мая': '05',
        'июня': '06',
        'июля': '07',
        'августа': '08',
        'сентября': '09',
        'октября': '10',
        'ноября': '11',
        'декабря': '12'
    }

    df['published_date'] = df['published_date'].replace(months, regex=True)
    df['published_date'] = pd.to_datetime(
        df['published_date'],
        format='%d %m %Y'
    )
    df["category_id"] = df["category_id"].astype('int')

    before = len(df)

    df = df.drop_duplicates(subset=["link"])

    after = len(df)

    print(f"Удалено дубликатов: {before - after}")

    df.to_sql(name='news', con=con, if_exists='append', index=False)

    print('=' * 100)
    print(f'Парсинг закончился, в базу данных сохранено {len(df)} новостей!')


@timer
def check_news(cursor, con):
    print("Проверяем наличие новых новостей...")

    df_cat = pd.read_sql("SELECT * FROM news_categories", con=con)
    df_uni = pd.read_sql("SELECT * FROM universities", con=con)

    url = "https://www.rea.ru/news?tree-content-path=news&search=&date_from=&date_to=&sub%5B0%5D=57407&page=1&per-page=12"

    response = rq.get(url, timeout=10)

    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    item = soup.select_one("a.catalog__item-content")

    if not item:
        print("Новости не найдены")
        return

    title = item.select_one(".catalog__item-title")
    date = item.select_one(".catalog__item-date")
    link = urljoin("https://www.rea.ru", item.get("href"))
    link = link.split("?")[0]

    title_text = title.get_text(strip=True)

    print(f"Последняя новость на сайте: {title_text}")

    result = db.get_last_news(cursor, "РЭУ")

    if isinstance(result, str):
        print("База данных пустая. Запускаем первоначальный парсинг...")
        parse(con, cursor)

    else:
        print("База данных уже содержит новости")

    last_title = result[0]

    if title_text == last_title:
        print("Новых новостей нет")
        return


    news_response = rq.get(link, timeout=10)
    soup_sub = BeautifulSoup(news_response.text, "html.parser")

    category_tag = soup_sub.select_one("li.catalog-detail__tag")

    if category_tag:
        category = category_tag.get_text(strip=True)

        if category in categories:
            category_name = categories[category]
            category = df_cat.loc[
                df_cat["name"] == category_name,
                "category_id"
            ].iloc[0]
        else:
            category = df_cat.loc[
                df_cat["name"] == "Без категории",
                "category_id"
            ].iloc[0]

    else:
        category = df_cat.loc[
            df_cat["name"] == "Без категории",
            "category_id"
        ].iloc[0]

    content_tag = soup_sub.select_one(".catalog-detail__text")

    if content_tag:
        content = content_tag.get_text(" ", strip=True)
    else:
        content = "no text"

    university = df_uni.loc[df_uni["name"] == "РЭУ", "university_id"].iloc[0]

    if date == "Сегодня":
        date = datetime.now().strftime("%d %m %Y")

    db.insert_news_rea(con, cursor, title, date, link, category, university, content)


def rea_parse(path):
    con, cursor = db.connect(path)
    db.table_news(con, cursor)
    db.table_categories(con, cursor)
    db.table_university(con, cursor)

    result = db.get_last_news(cursor, 'РЭУ')

    if result is None:
        print("База данных пустая. Запускаем первоначальный парсинг...")
        parse(con, cursor)

    else:
        print("База данных уже содержит новости")

    check_news(cursor, con)
    con.close()