import sqlite3
from datetime import datetime


def connect_get_cursor(db):
    conn = None
    cursor = None
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as e:
        print(f"[connect_get_cursor] Ошибка подключения к БД: {e}")
        if conn:
            conn.close()
        return None, None


def create_news_table(cursor, conn):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news( 
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                published_date TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                university_id INTEGER NOT NULL,
                content TEXT,
                added_at TEXT DEFAULT (datetime('now'))
            ); 
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"[create_news_table] Ошибка: {e}")
        conn.rollback()


def create_categories_table(cursor, conn):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_categories (
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL
            );
        ''')

        num = cursor.execute('''
            SELECT COUNT(*) FROM news_categories;
        ''').fetchone()

        if num[0] == 0:
            cursor.execute('''
                INSERT INTO news_categories (category_id, name) VALUES
                (1, 'Наука и инновации'),
                (2, 'Образование'),
                (3, 'Студенческая жизнь'),
                (4, 'Спорт'),
                (5, 'Культура и творчество'),
                (6, 'Международная деятельность'),
                (7, 'Сотрудничество и партнёрство'),
                (8, 'Объявления и события'),
                (9, 'Абитуриентам'),
                (10, 'Без категории')
            ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"[create_categories_table] Ошибка: {e}")
        conn.rollback()


def create_university_tables(cursor, conn):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS universities (
                university_id INTEGER NOT NULL,
                name TEXT NOT NULL
            );
        ''')

        num = cursor.execute('''
            SELECT COUNT(*) FROM universities;
        ''').fetchone()
        if num[0] == 0:
            cursor.execute('''
                INSERT INTO universities (university_id, name) VALUES 
                (1, 'МАИ'),
                (2, 'РЭУ'),
                (3, 'МИФИ'),
                (4, 'ВШЭ'),
                (5, 'МИРЭА'),
                (6, 'КФУ')
            ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"[create_university_tables] Ошибка: {e}")
        conn.rollback()


def get_university_id(cursor, name):
    try:
        uni_id = cursor.execute('''
            SELECT university_id FROM universities
            WHERE name = ?;
        ''', (name,)).fetchone()
        return uni_id[0] if uni_id else None
    except sqlite3.Error as e:
        print(f"[get_university_id] Ошибка: {e}")
        return None
    finally:
        pass


def get_category_id(cursor, cat):
    try:
        cat_id = cursor.execute('''
            SELECT category_id FROM news_categories
            WHERE name = ?;
        ''', (cat,)).fetchone()
        return cat_id[0] if cat_id else None
    except sqlite3.Error as e:
        print(f"[get_category_id] Ошибка: {e}")
        return None


def get_last_link(cursor):
    try:
        row = cursor.execute('''
            SELECT link FROM news n
            JOIN universities u ON u.university_id = n.university_id
            WHERE u.name = 'МИРЭА'
            ORDER BY published_date DESC
            LIMIT 1;
        ''').fetchone()

        link = row[0] if row else None
        return link
    except sqlite3.Error as e:
        print(f"[get_last_link] Ошибка: {e}")
        return None


def print_all_rows(cursor):
    try:
        cursor.execute('''
            SELECT * 
            FROM news
        ''')
        print(cursor.fetchall())
    except sqlite3.Error as e:
        print(f"[print_all_rows] Ошибка: {e}")


def insert_news(cursor, conn, title, link, dt, category_id, university_id, content):
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO news (title, link, published_date, category_id, university_id, content) VALUES (?, ?, ?, ?, ?, ?);
        ''', (title, link, dt, category_id, university_id, content))
        conn.commit()
    except sqlite3.Error as e:
        print(f"[insert_news] Ошибка: {e}")
        conn.rollback()


def create_users_table(cursor, conn):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT
            );
        ''')

        num = cursor.execute('''
                SELECT COUNT(*) FROM users;
            ''').fetchone()

        if num[0] == 0:
            cursor.execute('''
                INSERT INTO users (id, name) VALUES
                (1, 'John'),
                (2, 'Mark'),
                (3, 'Ivanka'),
                (4, 'Maynard'),
                (5, 'Mathew')
            ''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"[create_users_table] Ошибка: {e}")
        conn.rollback()


def create_user_cat_table(cursor, conn):
    try:
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS user_categories (
                   user_id INTEGER NOT NULL,
                   category_id INTEGER NOT NULL,
                   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
               );
           ''')

        num = cursor.execute('''
                   SELECT COUNT(*) FROM user_categories;
               ''').fetchone()

        if num[0] == 0:
            cursor.execute('''
                   INSERT INTO user_categories (user_id, category_id) VALUES
                   (1, 1),
                   (1, 2),
                   (2, 3),
                   (2, 4),
                   (3, 5),
                   (3, 6),
                   (4, 7),
                   (4, 8),
                   (5, 9),
                   (5, 1)
               ''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"[create_user_cat_table] Ошибка: {e}")
        conn.rollback()

def connect(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    return conn, cursor

def connect_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    return conn, cursor

def table_news(con, cursor):
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                published_date TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                university_id INTEGER NOT NULL,
                added_at TEXT DEFAULT (datetime('now')),
                content TEXT DEFAULT 'no text'
        );
    """)

    con.commit()

def table_categories(con, cursor):

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_categories(
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL
        );
    """)

    count = cursor.execute("""SELECT COUNT(*) FROM news_categories;""").fetchone()[0]

    if count == 0:

        cursor.execute("""
            INSERT INTO news_categories(category_id, name)
                VALUES
                    (1, "Наука"),
                    (2, "Спорт"),
                    (3, "Абитуриентам"),
                    (4, "Объявления"),
                    (5, "Студенчество"),
                    (6, "Международная деятельность"),
                    (7, "Сотрудничество"),
                    (8, "Культура"),
                    (9, "Образование"),
                    (10, "Без категории");
        """)


    con.commit()

def table_university(con, cursor):

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS universities(
            university_id INTEGER NOT NULL,
            name TEXT NOT NULL
        );
    """)
    count = cursor.execute("""SELECT COUNT(*) FROM universities;""").fetchone()[0]

    if count == 0:

        cursor.execute("""
                INSERT INTO universities(university_id, name)
                    VALUES
                        (1, "РЭУ"),
                        (2, "МИРЭА"),
                        (3, "ВШЭ"),
                        (4, "МИСИС"),
                        (5, "МФТИ"),
                        (6, "МАИ"),
                        (7, "КФУ"),
                        (8, "МГУ"),
                        (9, "unknown");
            """)

    con.commit()

def table_users(con, cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        );
    """)
    con.commit()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_categories (
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
    con.commit()


def insert_news_rea(con, cursor, title, date, link, category, university, content):
    cursor.execute("""
            INSERT OR IGNORE INTO news(title, published_date, link, added_at, category_id, university_id, content)
            VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (
        title.text.strip(),
        date.text.strip(),
        link,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        category,
        university,
        content
    ))

    if cursor.rowcount == 1:
        print("Detected fresh new!")
        print(title.text.strip())
    else:
        print("There is no fresh news!")

    con.commit()

    print("Новые новости загружены")

def view_data(cursor):
    data = cursor.execute("SELECT * FROM news")
    row_count = cursor.execute("SELECT COUNT(*) FROM news").fetchone()[0]

    return data, row_count

def truncate_table(con, cursor):
    cursor.execute("DELETE FROM news")
    con.commit()
    print(f"Таблица news очищена")

def get_last_news(cursor, uni : str):
    uni = uni.upper()
    cursor.execute("""
        SELECT title
        FROM news n
        JOIN universities u ON n.university_id = u.university_id
        WHERE u.name = ?
        ORDER BY published_date DESC, id DESC
        LIMIT 1
    """, (uni,))
    result = cursor.fetchone()

    if result:
        return result
    else:
        return f"В таблице нет записей для {uni}"


def truncate(con, cursor, table_name):
    cursor.execute("DELETE FROM ?", (table_name,))
    con.commit()
    print(f"Таблица {table_name} очищена")