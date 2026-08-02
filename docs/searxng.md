# SearXNG

Demon Cry использует [SearXNG](https://docs.searxng.org/) — метапоисковик, агрегирующий результаты из нескольких поисковых систем.

## Зачем нужен

Модуль `web_search` обращается к SearXNG для поиска в интернете. SearXNG объединяет результаты Google, DuckDuckGo, Bing, Qwant, Yandex и других — это повышает покрытие и снижает зависимость от одного поисковика.

## Настройка поисковиков

Конфигурация SearXNG хранится в `searxng/settings.yml`. По умолчанию включены:

| Движок | Вес |
|--------|-----|
| DuckDuckGo | 1.5 |
| Google | 1.5 |
| Bing | 1.5 |
| Qwant | 1.2 |
| Yandex | 1.0 |
| Wikipedia | 0.8 |

Startpage отключён.

## Категории поиска

Модуль `web_search` поддерживает категории: `general`, `images`, `files`, `it`, `social media`, `news`. Категория указывается в параметрах запроса.
