import requests, json; r = requests.post('http://localhost:8000/conversation/chat', json={'message': 'What types of access points are used in Building A?', 'session_id': 'test'}); result = r.json(); print(f'Sources: {len(result.get(\
sources\, []))}'); print(f'Response: {result.get(\response\, \\)[:100]}...')
