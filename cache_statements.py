"""Download only statement sections, never solutions, into ignored local data.

Source: doocs/leetcode (CC BY-SA 4.0). Each cached item retains attribution.
Run manually when online; startup and daily practice do not require downloads.
"""
import concurrent.futures
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from catalog import catalogue

ROOT = Path(__file__).resolve().parent


def read_url(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'LeetCode-Review-Local/1.0'})
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def main():
    api = 'https://api.github.com/repos/doocs/leetcode'
    revision = json.loads(read_url(api + '/git/ref/heads/main'))['object']['sha']
    def get_tree(sha):
        return json.loads(read_url(api + '/git/trees/' + sha))['tree']
    root_tree = get_tree(revision)
    solution_sha = next(i['sha'] for i in root_tree if i['path'] == 'solution')
    ranges = get_tree(solution_sha)
    wanted = {p['number'] for p in catalogue()}
    paths = {}
    for group in ranges:
        match = re.fullmatch(r'(\d{4})-(\d{4})', group['path'])
        if not match or not any(int(match[1]) <= n <= int(match[2]) for n in wanted):
            continue
        for item in get_tree(group['sha']):
            prefix = re.match(r'^(\d{4})\.', item['path'])
            if prefix and int(prefix[1]) in wanted:
                paths[int(prefix[1])] = f'solution/{group["path"]}/{item["path"]}/README.md'
    if wanted - paths.keys():
        raise RuntimeError(f'Catalogue entries missing upstream: {wanted - paths.keys()}')
    target = ROOT / 'data/statements.json'
    existing = json.loads(target.read_text('utf-8')) if target.exists() else []
    cached = {item['number']: item for item in existing}

    def download(p):
        number = p['number']
        if number in cached:
            return cached[number]
        path = urllib.parse.quote(paths[number], safe='/')
        url = f'https://raw.githubusercontent.com/doocs/leetcode/{revision}/{path}'
        for attempt in range(3):
            try:
                source = read_url(url)
                match = re.search(r'<!-- description:start -->(.*?)<!-- description:end -->', source, re.S)
                if not match or not match[1].strip():
                    raise ValueError(f'No statement markers for {number}')
                difficulty = re.search(r'^difficulty: (.+)$', source, re.M)
                return dict(number=number, description=match[1].strip(),
                            source=f'https://github.com/doocs/leetcode/blob/{revision}/{path}',
                            difficulty=difficulty[1] if difficulty else '')
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)

    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        tasks = {pool.submit(download, p): p for p in catalogue()}
        for task in concurrent.futures.as_completed(tasks):
            p = tasks[task]
            try:
                cached[p['number']] = task.result()
            except Exception as error:
                errors.append(f'{p["number"]}: {error}')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(list(cached.values()), ensure_ascii=False, indent=2), 'utf-8')
    print(f'Cached {len(cached)}/100 statements. Solutions excluded. Source: doocs/leetcode, CC BY-SA 4.0.')
    if errors:
        raise RuntimeError('\n'.join(errors))


if __name__ == '__main__':
    main()
