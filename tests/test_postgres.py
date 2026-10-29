import os,json,sys
from pathlib import Path
import pytest,psycopg
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from load_db import load
from pipeline import OUT

@pytest.mark.skipif(not os.environ.get('DATABASE_URL'),reason='Requires local PostgreSQL')
def test_real_postgres_roundtrip():
    load();load()
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        q=json.loads((OUT/'quality.json').read_text())
        assert conn.execute('SELECT count(*) FROM graveyard.startup').fetchone()[0]==q['unique_entities']
        assert conn.execute('SELECT count(*) FROM graveyard.verified_failures').fetchone()[0]==q['status_counts']['verified_failure']
        assert conn.execute("SELECT name FROM graveyard.search_failures('ingredients')").fetchone()[0]=='Dinnr'
        assert conn.execute('SELECT count(*) FROM graveyard.assertion a LEFT JOIN graveyard.startup s ON s.id=a.startup_id WHERE s.id IS NULL').fetchone()[0]==0
