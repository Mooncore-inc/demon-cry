from modules.dns_lookup import DnsLookup
import asyncio
import json

#Тестовый клиент

async def main():
    ser = DnsLookup()
    for type in ['A', 'AAAA']:
        result = await ser.execute(domain="google.com",record_type=type)
        print(json.dumps(result, ensure_ascii=False))

asyncio.run(main=main())
