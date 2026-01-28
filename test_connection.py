import httpx
import asyncio

async def test():
    try:
        client = httpx.AsyncClient(timeout=10.0)
        resp = await client.post(
            'http://host.docker.internal:9996',
            json={
                'jsonrpc': '2.0',
                'method': 'message/send',
                'params': {
                    'message': {
                        'role': 'user',
                        'parts': [{'text': 'weather in Paris'}],
                        'messageId': 'test789'
                    }
                },
                'id': 3
            }
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:300]}")
        await client.aclose()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
