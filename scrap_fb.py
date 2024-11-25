import contextlib
import csv
import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

TAG_WITH_POST = 'x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z'
TAG_WITH_HREF = ('x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 '
                 'x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 '
                 'x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xzsf02u x1s688f')
TAG_WITH_TEXT = ('x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty '
                 'x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h')
TAG_WITH_TIME = ('x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk '
                 'xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg '
                 'xggy1nq x1a2a7pz x1sur9pj xkrqix3 xi81zsa xo1l8bm')
TAG_WITH_TIME2 = 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs'
SHOW_MORE = 'Wyświetl więcej'


def start_driver():
    return uc.Chrome()


def update_articles(driver, articles):
    for link, when, text in scrap_articles(driver.page_source):
        if SHOW_MORE in text:
            continue
        if link not in articles:
            print('=' * 30)
            print(f'Article from: {when}\n{text}')
        articles[link] = (when, text)


def expand_posts(driver):
    tags = driver.find_elements(By.XPATH, f"//*[text()='{SHOW_MORE}']")
    for tag in tags:
        if not tag.is_displayed():
            continue
        tag.click()


def scrap_link(tag):
    for a_tag in tag.find_all('a', attrs={'role': 'link'}):
        if a_tag['href'].startswith('/groups'):
            return a_tag['href']
    return ''


def scrap_when(tag):
    when = ''
    try:
        when = tag.find('a', attrs={'class': TAG_WITH_TIME}).text
    except AttributeError:
        pass
    try:
        when = tag.find('span', attrs={'class': TAG_WITH_TIME2}).text
    except AttributeError:
        pass
    return when


def scrap_articles(source):
    soup = BeautifulSoup(source, features='html.parser')
    post_tags = soup.find_all('div', attrs={'class': TAG_WITH_POST})
    for post_tag in post_tags:
        try:
            link = scrap_link(post_tag)
            if not link:
                continue
            text = post_tag.find('span', attrs={'class': TAG_WITH_TEXT}).text
            when = scrap_when(post_tag)
            yield 'https://www.facebook.com' + link, when, text
        except (TypeError, AttributeError):
            pass


def main():
    articles = {}
    scroll_pos = 0
    driver = start_driver()
    driver.get('https://www.facebook.com')
    input('Login on facebook, go to group feed & press Enter ')
    with contextlib.suppress(KeyboardInterrupt):
        for _ in range(1_000):
            expand_posts(driver)
            driver.execute_script(f'scroll(0, {scroll_pos})')
            scroll_pos += 500
            time.sleep(3)
            update_articles(driver, articles)
    with open('feed.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, ['link', 'when', 'text'])
        writer.writeheader()
        for link, data in articles.items():
            when, text = data
            writer.writerow(dict(link=link, when=when, text=text))


if __name__ == '__main__':
    main()
