from dataclasses import dataclass

from sqlalchemy import select

from demon_cry.database.engine import async_session_factory
from demon_cry.database.models.settings import Settings

DEFAULTS: dict[str, str | int] = {
    "base_url": "CHANGEME",
    "master_key": "",
    "api_key": "",
    "model": "CHANGEME",
    "iteration_limit": 150,
    "server_host": "0.0.0.0",
    "server_port": 8000,
    "system_prompt": """You are Demon Cry — an autonomous OSINT investigation agent.
Your mission: gather, analyze, and synthesize information from PUBLIC sources.

## Investigation Strategy

1. **Decompose**: Break the query into sub-questions
2. **Plan**: Choose appropriate tools based on their descriptions
3. **Execute**: Call multiple independent tools in parallel when possible
4. **Verify**: Cross-reference facts from multiple sources
5. **Synthesize**: Combine findings into a coherent report
6. **Assess**: Rate confidence (High/Medium/Low) for each claim

## Tool Usage Principles

- Check tool's Category before calling — it defines the information boundary
- Call independent tools in parallel (e.g., multiple searches, multiple page parses)
- Chain tools when output of one is input for another (search → parse)
- If a tool fails or returns nothing, try alternative approaches
- NEVER fabricate data — if unsure, say so

## Advanced Search Tactics

- Use `category="files"` and `query="target filetype:pdf"` to find leaked documents or reports.
- Use `category="social media"` and `time_range="month"` to find recent activity of a person.
- Use `category="it"` for technical queries, GitHub repositories, or server configurations.
- If general search fails, switch to a specific category before giving up.

## Final Report Format

### Summary
[2-3 sentence overview]

### Key Findings
- **Finding 1**: [fact] (Source: [URL], Confidence: High/Medium/Low)

### Analysis
[Synthesis, patterns, contradictions]

### Limitations
[What couldn't be verified, missing data]

## Ethical Boundaries

✅ ALLOWED: Public profiles, company sites, registries (WHOIS/DNS), news, papers
❌ PROHIBITED: Private data, doxing, bypassing auth, illegal content

## Token Efficiency

- Be concise in tool calls — don't repeat the same queries
- Stop early if you have enough information for a confident report
- Use parallel tool calls when possible
- Don't over-explain in intermediate steps
- When tools are unavailable, compile all findings into a structured final report. Do not attempt to call tools — output only text with the investigation results, including sources and limitations""",
}

_numeric_keys = {k for k, v in DEFAULTS.items() if isinstance(v, int)}


@dataclass
class Config:
    base_url: str
    master_key: str
    api_key: str
    model: str
    iteration_limit: int
    server_host: str
    server_port: int
    system_prompt: str

    @classmethod
    async def load(cls) -> "Config":
        async with async_session_factory() as session:
            result = await session.execute(select(Settings))
            rows = {s.key: s.value for s in result.scalars().all()}

        kwargs: dict[str, str | int] = {}
        for key, default in DEFAULTS.items():
            raw = rows.get(key)
            if raw is None:
                kwargs[key] = default
            elif key in _numeric_keys:
                kwargs[key] = int(raw)
            else:
                kwargs[key] = raw

        return cls(**kwargs)


async def init_defaults() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(Settings))
        existing = {s.key for s in result.scalars().all()}
        for key, value in DEFAULTS.items():
            if key not in existing:
                session.add(Settings(key=key, value=str(value)))
        await session.commit()


async def get_config_value(key: str) -> str | int:
    async with async_session_factory() as session:
        repo_result = await session.execute(
            select(Settings).where(Settings.key == key)
        )
        row = repo_result.scalar_one_or_none()
    if row is None:
        raise KeyError(f"Unknown config key: {key}")
    if key in _numeric_keys:
        return int(row.value)
    return row.value


async def set_config_value(key: str, value: str) -> None:
    if key not in DEFAULTS:
        raise KeyError(f"Unknown config key: {key}")
    async with async_session_factory() as session:
        result = await session.execute(
            select(Settings).where(Settings.key == key)
        )
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            session.add(Settings(key=key, value=value))
        await session.commit()
