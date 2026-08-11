import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from app.main import app
from app.database.db import SessionLocal, engine, Base
from app.database.models import User, GamePlayer
from app.services.auth_service import hash_password, create_access_token
from app.services.game_service import game_service

client = TestClient(app)

@pytest.fixture
def game_setup():
    db = SessionLocal()
    u = User(id='u1', username='webtest2', nickname='webplayer2', password_hash=hash_password('pass'))
    db.add(u)
    db.commit()
    token = create_access_token('u1')

    r = client.post('/api/games/create', json={'timeout_duration': 30}, headers={'Authorization': f'Bearer {token}'})
    game_id = r.json()['id']
    join_code = r.json()['join_code']

    # Join another player (or same player for test simplicity, though real app prevents duplicate)
    u2 = User(id='u2', username='webtest3', nickname='webplayer3', password_hash=hash_password('pass'))
    db.add(u2)
    db.commit()
    token2 = create_access_token('u2')

    client.post('/api/games/join', json={'join_code': join_code}, headers={'Authorization': f'Bearer {token2}'})
    db.close()
    return game_id, token, token2

def test_full_game_flow(game_setup):
    game_id, token, token2 = game_setup

    # Check waiting state
    r = client.get(f'/api/games/{game_id}', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert r.json()['state'] in ('created', 'waiting')

    # Start game
    r = client.post(f'/api/games/{game_id}/start', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert r.json()['status'] == 'started'

    # Roll dice
    r = client.post(f'/api/games/{game_id}/roll', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert len(r.json()['dice']) == 5
    assert r.json()['rolls_left'] == 2

    # Select category
    r = client.post(f'/api/games/{game_id}/select-category', json={'category': 'chance'}, headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert 'score' in r.json()
    assert r.json()['category'] == 'chance'
