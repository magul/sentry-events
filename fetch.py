import io
import os
import sys
import zipfile

import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
ORGANIZATION_SLUG = os.getenv('ORGANIZATION_SLUG')

ISSUE_URL = 'https://sentry.io/api/0/issues/{}/'
EVENT_URL = 'https://sentry.io/api/0/projects/{}/{}/events/{}/'
EVENTS_LIST_URL = 'https://sentry.io/api/0/issues/{}/events/'


def get_project_slug(issue_id):
    return requests.get(ISSUE_URL.format(issue_id), headers={
        'Authorization': f'Bearer {API_TOKEN}'
    }).json()['project']['slug']


def fetch_events(issue_id):
    response = requests.get(EVENTS_LIST_URL.format(issue_id), headers={
        'Authorization': f'Bearer {API_TOKEN}'
    })
    data = response.json()
    print('{} => {}'.format(EVENTS_LIST_URL.format(issue_id), len(data)))
    events = data

    while True:
        page_url = response.links['next']['url']
        response = requests.get(page_url, headers={
            'Authorization': f'Bearer {API_TOKEN}'
        })

        data = response.json()
        if len(data) == 0:
            break

        print('{} => {}'.format(page_url, len(data)))
        events.extend(data)

    project_slug = get_project_slug(issue_id)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for event in tqdm(events):
            zip_file.writestr(
                '{}.json'.format(event['eventID']),
                io.BytesIO(requests.get(
                    EVENT_URL.format(
                        ORGANIZATION_SLUG,
                        project_slug,
                        event['eventID'],
                    ),
                    headers={
                        'Authorization': f'Bearer {API_TOKEN}'
                    },
                ).content).getvalue(),
            )

    with open('{}-{}.zip'.format(project_slug, issue_id), 'wb') as f:
        f.write(zip_buffer.getvalue())


if __name__ == '__main__':
    fetch_events(sys.argv[1])
