import json

import requests
from jsonschema import validate

URL = 'https://jsonplaceholder.typicode.com'


def test_get_users():
    # Step 1
    response = requests.get(f'{URL}/users')
    # Step 2
    # a
    assert response.status_code == 200
    # b
    negative_case = requests.get(f'{URL}/user')
    assert not negative_case.status_code == 200
    # c
    data = response.json()
    with open('test2.json') as schema_file:
        schema = json.loads(schema_file.read())
    assert all(validate(x, schema) is None for x in data)
    # d
    assert len(data) == 10
    # bonus
    response = requests.get(f'{URL}/users?username=Antonette')
    data = response.json()
    assert len(data) > 0
    assert data[0]['username'] == 'Antonette'
