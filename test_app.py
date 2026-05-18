import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_alive(client):
    """Перевірка ендпоінту /health/alive"""
    rv = client.get('/health/alive')
    assert rv.status_code == 200
    assert b'OK' in rv.data


@patch('app.get_db_connection')
def test_health_ready_success(mock_get_db, client):
    """Перевірка /health/ready при успішному підключенні до БД"""
    mock_conn = MagicMock()
    mock_get_db.return_value = mock_conn

    rv = client.get('/health/ready')
    assert rv.status_code == 200
    mock_conn.close.assert_called_once()


@patch('app.get_db_connection')
def test_health_ready_fail(mock_get_db, client):
    """Перевірка /health/ready при падінні БД"""
    mock_get_db.return_value = None
    rv = client.get('/health/ready')
    assert rv.status_code == 500


def test_root(client):
    """Перевірка головної сторінки"""
    rv = client.get('/')
    assert rv.status_code == 200


@patch('app.get_db_connection')
def test_get_tasks(mock_get_db, client):
    """Перевірка отримання списку задач"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{'id': 1, 'title': 'Test Task', 'status': 'pending'}]
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    rv = client.get('/tasks')
    assert rv.status_code == 404
    assert b'Test Task' in rv.data


@patch('app.get_db_connection')
def test_create_task(mock_get_db, client):
    """Перевірка створення задачі"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    rv = client.post('/tasks', json={'title': 'New Task'})
    assert rv.status_code == 201


@patch('app.get_db_connection')
def test_mark_task_done(mock_get_db, client):
    """Перевірка оновлення статусу задачі"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    rv = client.post('/tasks/1/done')
    assert rv.status_code == 200
