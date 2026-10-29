"""Transactional local storage. Dates are assigned/validated on the server."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from catalog import catalogue, DEFAULT_TAGS

NOTE_FIELDS = ('idea', 'key_points', 'precautions', 'boundaries', 'reference_code')


class ValidationError(ValueError):
    pass


def today():
    return datetime.now(timezone(timedelta(hours=8))).date().isoformat()


def text(data, key, limit=200_000, required=False):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValidationError(f'{key} 内容为空、过长或格式不正确')
    return value


class Store:
    def __init__(self, path, content_path=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY, number INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL, slug TEXT NOT NULL, url TEXT NOT NULL,
                    category TEXT NOT NULL, collection TEXT NOT NULL,
                    difficulty TEXT NOT NULL DEFAULT '', done INTEGER NOT NULL DEFAULT 0,
                    description TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS records (
                    problem_id INTEGER NOT NULL REFERENCES problems(id), day TEXT NOT NULL,
                    result TEXT NOT NULL CHECK(result IN ('pass','fail')), code TEXT NOT NULL,
                    tags TEXT NOT NULL, note TEXT NOT NULL, updated TEXT NOT NULL,
                    PRIMARY KEY(problem_id, day)
                );
                CREATE TABLE IF NOT EXISTS drafts (
                    problem_id INTEGER NOT NULL REFERENCES problems(id), day TEXT NOT NULL,
                    code TEXT NOT NULL, PRIMARY KEY(problem_id, day)
                );
                CREATE TABLE IF NOT EXISTS notes (
                    problem_id INTEGER PRIMARY KEY REFERENCES problems(id),
                    idea TEXT NOT NULL DEFAULT '', key_points TEXT NOT NULL DEFAULT '',
                    precautions TEXT NOT NULL DEFAULT '', boundaries TEXT NOT NULL DEFAULT '',
                    reference_code TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS tags (name TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY,problem_id INTEGER NOT NULL REFERENCES problems(id),
                    created TEXT NOT NULL,day TEXT NOT NULL,code TEXT NOT NULL,code_hash TEXT NOT NULL,
                    mode TEXT NOT NULL,status TEXT NOT NULL,passed INTEGER NOT NULL,total INTEGER NOT NULL,
                    completed INTEGER NOT NULL,version TEXT NOT NULL,seed INTEGER,
                    milliseconds INTEGER NOT NULL,memory_kb INTEGER NOT NULL,
                    detail TEXT NOT NULL DEFAULT '{}',revealed INTEGER NOT NULL DEFAULT 0
                );
            ''')
            if 'submission_id' not in {r['name'] for r in db.execute('PRAGMA table_info(records)')}:
                db.execute('ALTER TABLE records ADD COLUMN submission_id TEXT')
            db.executemany('INSERT OR IGNORE INTO tags VALUES (?)', [(t,) for t in DEFAULT_TAGS])
            for p in catalogue():
                db.execute('''INSERT OR IGNORE INTO problems
                    (number,title,slug,url,category,collection) VALUES
                    (:number,:title,:slug,:url,:category,:collection)''', p)
        # Cached statement imports never overwrite user edits or personal records.
        if content_path and Path(content_path).exists():
            content = json.loads(Path(content_path).read_text(encoding='utf-8-sig'))
            with self.db() as db:
                for item in content:
                    db.execute('''UPDATE problems SET description=?,source=?,difficulty=?
                        WHERE number=? AND description='' ''',
                        (item['description'], item['source'], item.get('difficulty', ''), item['number']))

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def state(self):
        with self.db() as db:
            problems = [dict(r) for r in db.execute('''SELECT id,number,title,url,category,
                collection,difficulty,done FROM problems WHERE collection='Hot 100' ORDER BY id''')]
            records = [dict(r) for r in db.execute("SELECT r.problem_id,r.day,r.result,r.tags FROM records r JOIN problems p ON p.id=r.problem_id WHERE p.collection='Hot 100'")]
            tags = [r[0] for r in db.execute('SELECT name FROM tags ORDER BY rowid')]
        for r in records:
            r['tags'] = json.loads(r['tags'])
        return dict(today=today(), problems=problems, records=records, tags=tags)

    def problem(self, pid):
        with self.db() as db:
            row = db.execute("SELECT * FROM problems WHERE id=? AND collection='Hot 100'", (pid,)).fetchone()
            if row is None:
                raise LookupError('题目不存在')
            p = dict(row)
            draft = db.execute('SELECT code FROM drafts WHERE problem_id=? AND day=?', (pid, today())).fetchone()
            record = db.execute('SELECT * FROM records WHERE problem_id=? AND day=?', (pid, today())).fetchone()
            note = db.execute('SELECT * FROM notes WHERE problem_id=?', (pid,)).fetchone()
            p.update(day=today(), draft=draft[0] if draft else (record['code'] if record else ''),
                     record=self.decode_record(record), notes=dict(note) if note else {f: '' for f in NOTE_FIELDS})
            return p

    def decode_record(self,row):
        if not row:
            return None
        result = dict(row)
        result['tags'] = json.loads(result['tags'])
        result['judgment']=None
        if result.get('submission_id'):
            with self.db() as db:
                judgment=db.execute('SELECT id,status,passed,total,version,created FROM submissions WHERE id=?',(result['submission_id'],)).fetchone()
            result['judgment']=dict(judgment) if judgment else None
        return result

    def history(self, pid):
        self.problem(pid)
        with self.db() as db:
            return [self.decode_record(r) for r in db.execute(
                'SELECT * FROM records WHERE problem_id=? ORDER BY day DESC', (pid,))]

    @staticmethod
    def check_day(data):
        if data.get('day') != today():
            raise ValidationError('日期已变化或不是今天；请保留代码并返回首页重新打开题目。不能补录历史日期。')

    def save_draft(self, pid, data):
        self.check_day(data)
        self.problem(pid)
        code = text(data, 'code')
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO drafts VALUES (?,?,?)', (pid, today(), code))

    def save_record(self, pid, data):
        self.check_day(data)
        self.problem(pid)
        if data.get('result') not in ('pass', 'fail'):
            raise ValidationError('请选择 ✅ 或 ❌')
        tags = data.get('tags', []) if data['result'] == 'fail' else []
        if not isinstance(tags, list) or len(tags) > 30 or any(
                not isinstance(t, str) or not t.strip() or len(t) > 50 for t in tags):
            raise ValidationError('错误标签格式不正确')
        tags = list(dict.fromkeys(tags))
        code, note = text(data, 'code'), text(data, 'note', 10_000) if data['result'] == 'fail' else ''
        with self.db() as db:
            submission=db.execute("""SELECT id FROM submissions WHERE problem_id=? AND day=? AND code=?
                AND status IN ('AC','WA','CE','RE','TLE','MLE','OLE') ORDER BY created DESC LIMIT 1""",(pid,today(),code)).fetchone()
            db.execute('INSERT OR REPLACE INTO records (problem_id,day,result,code,tags,note,updated,submission_id) VALUES (?,?,?,?,?,?,?,?)',
                       (pid, today(), data['result'], code, json.dumps(tags, ensure_ascii=False), note,
                        datetime.now(timezone.utc).isoformat(),submission['id'] if submission else None))
            db.execute('INSERT OR REPLACE INTO drafts VALUES (?,?,?)', (pid, today(), code))
            db.execute('UPDATE problems SET done=1 WHERE id=?', (pid,))
            db.executemany('INSERT OR IGNORE INTO tags VALUES (?)', [(t,) for t in tags])

    def save_notes(self, pid, data):
        self.problem(pid)
        values = [text(data, f) for f in NOTE_FIELDS]
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO notes VALUES (?,?,?,?,?,?)', [pid, *values])

    def mark_done(self, data):
        ids = data.get('ids')
        if not isinstance(ids, list) or not ids or len(ids) > 5000 or any(type(i) is not int for i in ids):
            raise ValidationError('请选择需要标记的题目')
        with self.db() as db:
            for pid in set(ids):
                if not db.execute("SELECT 1 FROM problems WHERE id=? AND collection='Hot 100'", (pid,)).fetchone():
                    raise LookupError('选中的题目不存在')
                db.execute('UPDATE problems SET done=1 WHERE id=?', (pid,))

    def save_description(self, pid, data):
        self.problem(pid)
        description = text(data, 'description', required=True)
        with self.db() as db:
            db.execute("UPDATE problems SET description=?, source='用户录入' WHERE id=?", (description, pid))

    def add_tag(self, data):
        name = text(data, 'name', 50, True).strip()
        with self.db() as db:
            db.execute('INSERT OR IGNORE INTO tags VALUES (?)', (name,))
