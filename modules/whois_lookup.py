import asyncwhois

from modules.base_modules import OSINTModule


CLEAN_FIELDS = {
    "domain_name": "Domain",
    "created": "Created",
    "updated": "Updated",
    "expires": "Expires",
    "registrar": "Registrar",
    "registrar_url": "Registrar URL",
    "registrar_abuse_email": "Registrar Abuse Email",
    "registrar_abuse_phone": "Registrar Abuse Phone",
    "name_servers": "Name Servers",
    "status": "Status",
    "registrant_name": "Registrant Name",
    "registrant_organization": "Registrant Organization",
    "registrant_email": "Registrant Email",
    "registrant_phone": "Registrant Phone",
    "tech_name": "Tech Name",
    "tech_organization": "Tech Organization",
    "tech_email": "Tech Email",
    "tech_phone": "Tech Phone",
}


class WhoisLookup(OSINTModule):
    name = "whois"
    description = "RDAP/WHOIS lookup for domain registration data"
    category = "network"
    parameters = {
        "type": "object",
        "properties": {
            "domain": {"type": "string", "description": "Domain to lookup"}
        },
        "required": ["domain"]
    }

    async def execute(self, domain: str) -> dict:
        data = await self._fetch(domain)
        if data is None:
            return {"error": f"Failed to fetch data for {domain}"}

        lines = []
        for key, label in CLEAN_FIELDS.items():
            value = data.get(key)
            if value is None or value == "":
                continue
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"| {label} | {value} |")

        if not lines:
            return {"error": f"No data returned for {domain}"}

        table = "| Field | Value |\n|---|---|\n" + "\n".join(lines)
        return {"result": table}

    async def _fetch(self, domain: str) -> dict | None:
        try:
            result = await asyncwhois.aio_rdap_domain(domain)
            return result.parser_output
        except Exception:
            pass

        try:
            result = await asyncwhois.aio_whois_domain(domain)
            return result.parser_output
        except Exception:
            return None
