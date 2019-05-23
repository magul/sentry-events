import io
import os
import sys
import zipfile
from pathlib import Path

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

    filename = '{}-{}.zip'.format(project_slug, issue_id)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as new_zip_file:

        old_events = {}
        if Path(filename).is_file():
            with zipfile.ZipFile(filename, 'r') as zip_file:
                for f in tqdm(zip_file.filelist):
                    old_events[f.filename[:-5]] = zip_file.read(f)

        for event in tqdm(events):
            if event['eventID'] in old_events:
                event_details = old_events[event['eventID']]
            else:
                event_details = requests.get(
                    EVENT_URL.format(
                        ORGANIZATION_SLUG,
                        project_slug,
                        event['eventID'],
                    ),
                    headers={
                        'Authorization': f'Bearer {API_TOKEN}'
                    },
                ).content

            new_zip_file.writestr(
                '{}.json'.format(event['eventID']),
                io.BytesIO(event_details).getvalue(),
            )

    with open(filename, 'wb') as f:
        f.write(zip_buffer.getvalue())


if __name__ == '__main__':
    fetch_events(sys.argv[1])
