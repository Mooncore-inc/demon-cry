import asyncio
import aiodns
from modules.base_modules import OSINTModule

NAME_SERVERS = [
    "1.1.1.1",
    "8.8.8.8",
    "9.9.9.9",
    "77.88.8.8",
    "208.67.220.220"
]

RECORD_FIELDS = {
    "A": ["addr"],
    "AAAA": ["addr"],
    "MX": ["priority", "exchange"],
    "NS": ["nsdname"],
    "TXT": ["data"],
    "CNAME": ["cname"],
    "SOA": ["mname", "rname", "serial", "refresh", "retry", "expire", "minimum"],
    "PTR": ["dname"],
}

class DnsLookup(OSINTModule):
    name = "dns_lookup"
    description = "finds DNS records"
    parameters = {
        "type": "object",
        "properties": {
            "domain": {"type": "string", "description": "Domain to lookup"},
            "record_type": {
                "type": "string",
                "enum": list(RECORD_FIELDS.keys()),
                "default": "A",
                "description": "Record type(s), comma-separated for multiple (e.g. A,MX,NS)"
            }
        },
        "required": ["domain"]
    }

    async def execute(self, domain: str, record_type: str = "A") -> dict:
        resolver = aiodns.DNSResolver(nameservers=NAME_SERVERS)
        types = [t.strip().upper() for t in record_type.split(",")]

        async def query_one(qtype: str):
            try:
                result = await resolver.query_dns(host=domain, qtype=qtype)
                return (qtype, result.answer if result.answer else None)
            except Exception:
                return (qtype, None)

        results = await asyncio.gather(*(query_one(t) for t in types))

        lines = []
        for qtype, records in results:
            fields = RECORD_FIELDS.get(qtype, [])
            if records:
                for rec in records:
                    values = [str(getattr(rec.data, f, "")) for f in fields]
                    lines.append(f"| {qtype} | {', '.join(values)} |")
            else:
                lines.append(f"| {qtype} | Нет записей |")

        table = f"| Тип | Значение |\n|---|---|\n" + "\n".join(lines)

        return {"result": table}
