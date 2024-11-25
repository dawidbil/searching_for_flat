import contextlib
import csv
import json
import time

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
from seleniumwire.utils import decode

offset = 0


def start_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(options=options)


def find_response(driver):
    global offset
    for request in driver.iter_requests():
        if request.path == '/api/v1/offers/' and request.params['offset'] == str(offset):
            offset += 40
            return request.response
    raise RuntimeError('No request found')


def parse_text_from_article(article) -> str:
    text = article['title'] + '\n'
    text += article['description'] + '\n'
    text += 'Extra metadata: ' + json.dumps(article['params']) + '\n'
    return text


def get_articles(driver):
    response = find_response(driver)
    body = decode(response.body, response.headers.get('Content-Encoding', 'identity'))
    data = json.loads(body)
    for article in data['data']:
        text = parse_text_from_article(article)
        yield article['url'], article['created_time'], text


def update_articles(driver, articles):
    for link, when, text in get_articles(driver):
        if link not in articles:
            print('=' * 30)
            line, _, _ = text.partition('\n')
            print(f'Article from: {when}\n{line}')
        articles[link] = (when, text.replace('\n', ' '))


def next_page(driver) -> bool:
    try:
        button = driver.find_element(By.XPATH, f"//a[@data-cy='pagination-forward']")
        button.click()
        return True
    except NoSuchElementException:
        return False


def main():
    articles = {}
    driver = start_driver()
    driver.get('https://www.olx.pl')
    input('Search for what you want & press Enter ')
    with contextlib.suppress(KeyboardInterrupt):
        while True:
            update_articles(driver, articles)
            del driver.requests
            if not next_page(driver):
                break
            print('Next page')
            time.sleep(12)
    with open('feed.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, ['link', 'when', 'text'])
        writer.writeheader()
        for link, data in articles.items():
            when, text = data
            writer.writerow(dict(link=link, when=when, text=text))


if __name__ == '__main__':
    main()
