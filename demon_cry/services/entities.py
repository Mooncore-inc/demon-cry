"""Извлечение энтити из результатов плагинов и запись их на граф исследования.

Принципы (issue #85):
- каждое появление — отдельная инстанция, дедупа нет;
- родителями результата считаются энтити, от которых запущен инструмент;
- эхо-защита: совпадение (type, value) с контекстной энтити не создаёт дубль.
"""

import json
import logging
import re
from collections.abc import Sequence

from demon_cry.database.models.entities import InvestigateEntityModel
from demon_cry.database.uow import AppUnitOfWork

logger = logging.getLogger(__name__)

TYPE_KEYS = ("type", "entity_type", "kind")
VALUE_KEYS = ("value", "indicator", "identifier", "target", "data")
VALUE_MAX = 1024
TYPE_MAX = 64

_ECHO_RELATION = "derived_from"
_SOURCE_PLUGIN = "plugin"

_WHITESPACE_RE = re.compile(r"\s+")
_SLUG_BAD_RE = re.compile(r"[^a-z0-9_-]+")
_SLUG_COLLAPSE_RE = re.compile(r"_+")


def normalize_type(raw: object) -> str | None:
    """Привести метку типа к slug-виду: lowercase, ограниченный алфавит, <= 64."""
    if not isinstance(raw, str):
        return None
    slug = _SLUG_BAD_RE.sub("_", _WHITESPACE_RE.sub("_", raw.strip().lower()))
    slug = _SLUG_COLLAPSE_RE.sub("_", slug).strip("_-")
    return slug[:TYPE_MAX] or None


def canonical_json(data: object) -> str:
    """Стабильный JSON: sort_keys, без пробелов, юникод как есть."""
    return json.dumps(
        data, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
    )


def _scalar_item(item: object) -> dict | None:
    """Скаляр из списка энтити -> candidate {"value": ...}."""
    if isinstance(item, str):
        return {"value": item}
    if isinstance(item, (int, float, bool)):
        return {"value": str(item)}
    return None


def _map_items(mapping: dict) -> list[tuple[dict, bool]]:
    """Словарь key->value трактуем как набор пар type/value (легаси-формат).

    (item, expanded): expanded=True — значение было вложенным dict, данные
    мержатся в item, ставится маркер normalized=True.
    """
    items: list[tuple[dict, bool]] = []
    for key, val in mapping.items():
        if isinstance(val, str):
            items.append(({"type": key, "value": val}, False))
        elif isinstance(val, (int, float, bool)):
            items.append(({"type": key, "value": str(val)}, False))
        elif isinstance(val, dict):
            items.append(({"type": key, **val}, True))
        # None/list в качестве значения на граф не ложатся разумно - пропускаем
    return items


def _list_items(entries: list) -> list[tuple[dict, bool]]:
    items: list[tuple[dict, bool]] = []
    for entry in entries:
        if isinstance(entry, dict):
            items.append((entry, False))
        elif (scalar := _scalar_item(entry)) is not None:
            items.append((scalar, False))
    return items


def extract_entities(raw: object) -> list[dict]:
    """Извлечь кандидатов энтити из поля `entities` результата плагина.

    Поддерживает формы:
    - list[dict]; скаляры в списке -> {"value": <строка>};
    - легаси-обёртку `{"data": [...]}` (как хранит `_as_dict`);
    - dict-словарь `{"ip": "1.1.1.1"}` -> type=key, value=value (легаси);
    - одиночный dict с ключами-кандидатами -> одна энтити;
    - fallback без value: `value` = canonical JSON элемента (<= 1024),
      в `data` ставится `normalized: false`.
    """
    items: list[tuple[dict, bool]] = []
    if isinstance(raw, list):
        items = _list_items(raw)
    elif isinstance(raw, dict):
        if isinstance(raw.get("data"), list):
            items = _list_items(raw["data"])
        elif any(key in raw for key in (*TYPE_KEYS, *VALUE_KEYS)):
            items = [(raw, False)]
        else:
            items = _map_items(raw)

    drafts: list[dict] = []
    for item, expanded in items:
        used: set[str] = set()
        entity_type = None
        for key in TYPE_KEYS:
            if key in item and item[key] is not None:
                entity_type = normalize_type(item[key])
                used.add(key)
                break
        value = None
        for key in VALUE_KEYS:
            candidate = item.get(key)
            if isinstance(candidate, str):
                value = candidate.strip()[:VALUE_MAX]
                if value:
                    used.add(key)
                    break
                value = None
        data = {k: v for k, v in item.items() if k not in used}
        if value is None:
            value = canonical_json(item)[:VALUE_MAX]
            data["normalized"] = False
        elif expanded:
            data["normalized"] = True
        drafts.append({"type": entity_type, "value": value, "data": data})
    return drafts


async def create_entities_from_run(
    uow: AppUnitOfWork,
    investigate_id: int,
    run_id: int,
    entities_raw: object,
    parents: Sequence[InvestigateEntityModel],
) -> list[InvestigateEntityModel]:
    """Создать инстанции энтити из результата запуска + связи derived_from.

    Вызывается внутри транзакции после записи investigates_data.
    Эхо: если (type, value) кандидата совпали с любой контекстной энтити —
    ни ноду, ни связи не создаём (иначе каждый запуск дублировал бы вход).
    """
    created: list[InvestigateEntityModel] = []
    for draft in extract_entities(entities_raw):
        if any(
            draft["value"] == parent.value
            and (draft["type"] or None) == (parent.type or None)
            for parent in parents
        ):
            continue
        entity = await uow.entities.create(
            investigate_id=investigate_id,
            type=draft["type"],
            value=draft["value"],
            data=draft["data"],
            source=_SOURCE_PLUGIN,
            source_run_id=run_id,
        )
        for parent in parents:
            await uow.entity_links.create(
                investigate_id=investigate_id,
                source_id=parent.id,
                target_id=entity.id,
                relation=_ECHO_RELATION,
                origin="auto",
                source_run_id=run_id,
            )
        created.append(entity)
    return created
