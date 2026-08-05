import aiodns
from modules.base_modules import OSINTModule

NAME_SERVERS = [
    "1.1.1.1",
    "8.8.8.8",
    "9.9.9.9",
    "77.88.8.8",
    "208.67.220.220"
]

class DnsLookup(OSINTModule):
    name = "dns_lookup"
    description = "finds DNS records"
    parameters = {
        "type": "object",
        "properties": {
            "domain": {"type": "string", "description": "Domain to lookup"},
            "record_type": {
                "type": "sring",
                "enum":["A","AAAA"],
                "default":"A",
                "description":"Record type"
            }
        },
        "required": ["domain"]
    }

    async def execute(self, domain: str, record_type: str = "A") -> dict:

        resolver = aiodns.DNSResolver(nameservers=NAME_SERVERS)

        result = await resolver.query_dns(
            host=domain,
            qtype=record_type
        )

        records = f"{domain}:{record_type}\n\n"
        records += "\n".join([f"- **{rec.data.addr}**" for rec in result.answer])

        return {
            "result": records
            }
