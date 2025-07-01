import re

def test_patterns():
    queries = ['which are these?', 'what are these?', 'list them', 'show them']
    patterns = [
        r'^which are these\??$',
        r'^what are these\??$', 
        r'^which ones\??$',
        r'^what ones\??$',
        r'^list them$',
        r'^name them$',
        r'^show them$'
    ]

    for query in queries:
        query_lower = query.lower().strip()
        matches = [re.match(pattern, query_lower) for pattern in patterns]
        print(f'Query: "{query}" -> Matches: {any(matches)}')
        for i, pattern in enumerate(patterns):
            if re.match(pattern, query_lower):
                print(f'  Matched pattern {i}: {pattern}')

if __name__ == "__main__":
    test_patterns() 