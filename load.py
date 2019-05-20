import json
import sys
import zipfile

from IPython import embed
from tqdm import tqdm

from fetch import get_project_slug


def load_events(issue_id):
    events = []
    project_slug = get_project_slug(issue_id)
    with zipfile.ZipFile('{}-{}.zip'.format(project_slug, issue_id), 'r') as zip_file:
        for f in tqdm(zip_file.filelist):
            events.append(json.loads(zip_file.read(f)))
    return events


if __name__ == '__main__':
    events = load_events(sys.argv[1])
    embed()
