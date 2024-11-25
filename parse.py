import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(
    format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def load_prompt(path: str) -> str:
    with open(path, encoding='utf-8') as file:
        return file.read()


PARSE_PROMPT = load_prompt('parse_prompt.txt')
VALIDATE_PROMPT = load_prompt('validate_prompt.txt')
VALIDATION_CORRECT = 'Poprawny'
VALIDATION_INCORRECT_JSON = 'JSON jest niepoprawny, proszę popraw go'
VALIDATION_FIELDS_MISSING = 'JSON nie zawiera wszystkich potrzebnych pól, proszę uzupełnij go'
VALIDATING_ATTEMPTS = 3
JSON_TAG_START = '```json'
JSON_TAG_END = '```'


def get_csv(path: str) -> Dict:
    logger.debug(f'Getting CSV: {path}')
    if not Path(path).exists():
        return dict()
    with open(path, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = [row for row in reader]
    return {row['link']: row for row in rows}  # noqa


def save_parsed(parsed: Dict) -> None:
    rows = list(parsed.values())
    logger.debug(f'Saving parsed, len(rows): {len(rows)}')
    with open('parsed.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_json(client: OpenAI, messages: List[Dict]) -> str:
    completion = client.chat.completions.create(
        messages=messages, model='gpt-4o', max_tokens=2048, response_format={'type': 'json_object'}, temperature=0.25)
    generated_json = completion.choices[0].message.content
    logger.debug(f'Generated json: {generated_json}')
    return generated_json


def check_if_all_fields_exist(parsed: Dict) -> str:
    keys = set(parsed.keys())
    required_keys = {'rodzaj ogłoszenia', 'co wynajmowane', 'jakie mieszkanie', 'cena', 'kaucja', 'czynsz', 'inne koszty', 'miejsce', 'internet', 'pośrednik', 'zwierzęta', 'preferowane osoby'}
    if keys == required_keys:
        return ''
    return ', '.join(required_keys - keys)


def validate_with_model(client: OpenAI, parsed: Dict) -> str:
    messages = [dict(role='system', content=VALIDATE_PROMPT), dict(role='system', content=json.dumps(parsed))]
    completion = client.chat.completions.create(messages=messages, model='gpt-4o', max_tokens=2048, temperature=0.25)
    validation = completion.choices[0].message.content
    logger.debug(f'Validation result: {validation}')
    return validation


def validate_json(client: OpenAI, parsed: str) -> str:
    if parsed.startswith(JSON_TAG_START):
        parsed = parsed[len(JSON_TAG_START):]
    if parsed.endswith(JSON_TAG_END):
        parsed = parsed[len(JSON_TAG_END):]
    try:
        parsed = json.loads(parsed)
    except ValueError:
        return VALIDATION_INCORRECT_JSON
    missing_fields = check_if_all_fields_exist(parsed)
    if missing_fields:
        return VALIDATION_FIELDS_MISSING + f'. Brakujące pola: {missing_fields}'
    return validate_with_model(client, parsed)


def parse_post(client: OpenAI, row: Dict) -> Dict:
    assert list(row.keys()) == ['link', 'when', 'text']
    validation_attempts = 0
    messages = [dict(role='system', content=PARSE_PROMPT), dict(role='user', content=row['text'])]
    parsed = generate_json(client, messages)
    validation_result = validate_json(client, parsed)
    while validation_result != VALIDATION_CORRECT:
        messages.extend([dict(role='assistant', content=parsed), dict(role='user', content=validation_result)])
        parsed = generate_json(client, messages)
        validation_result = validate_json(client, parsed)
        validation_attempts += 1
        if validation_attempts > VALIDATING_ATTEMPTS:
            raise RuntimeError(f'Validating more than {VALIDATING_ATTEMPTS}')
    return json.loads(parsed)


def main():
    load_dotenv()
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    parsed = get_csv('parsed.csv')
    for link, row in get_csv('feed.csv').items():
        if link in parsed:
            logger.info(f'Already in parsed: {link}')
            continue
        parsed_row = parse_post(client, row)
        parsed[link] = row | parsed_row
        save_parsed(parsed)


if __name__ == '__main__':
    main()
