# AGENTS.md

## What This Is

A course search tool for Rikkyo University (立教大学) that reverse-engineers the official syllabus system at `https://sy.rikkyo.ac.jp/web/show.php` and provides a better UI for searching and filtering courses.

## How to Run

```
python3 app.py
```

Starts Flask dev server on `http://localhost:5050`. Dependencies: `flask`, `requests`, `beautifulsoup4`.

## Architecture

### scraper.py — Upstream API Client & HTML Parser

- Sends POST to `https://sy.rikkyo.ac.jp/web/web_search_show.php` for page 1, GET with query params for subsequent pages
- The upstream site returns full HTML pages (not JSON). All responses are parsed with BeautifulSoup.
- Search results live in `table.searchShow`. Each `<tr>` has a `data-href` attribute pointing to the detail page (`preview.php?no_id=...`).
- Japanese text is inside `<span class="jp">` elements; English in `<span class="en">`. The `_jp_text()` helper extracts Japanese only.
- Registration method is encoded as icon images (`ri_icon01.jpg` through `ri_icon06.jpg`), mapped via `ICON_MAP`.
- Pagination links are in `ul.pagenav`.
- Detail pages have two key sections: `table.attribute` (metadata key-value pairs in paired `<td>` cells) and `div.subjectContents` (syllabus body with `<h3>` headings wrapped in 【】brackets).
- All `*_MAP` dicts map upstream form values (numeric IDs) to Japanese display names; these are passed to the template for select dropdowns.

### app.py — Flask Backend

- `GET /` — renders the single-page search UI, passing all MAP dicts to Jinja2
- `GET /api/search?page=&kamokumei=&gakubu=&...` — proxies search to upstream, returns JSON
- `GET /api/detail?url=<syllabus_url>` — fetches and parses a single course syllabus, returns JSON

### templates/index.html — Single-Page Frontend

- Vanilla JS, no build step. All search/detail requests are `fetch()` to the Flask API.
- Client-side filtering: time-slot grid (曜日時限) and semester checkboxes filter the already-fetched page of results locally without re-querying upstream.
- Syllabus detail opens in a modal overlay.

## Upstream API Notes

- The search endpoint does NOT require authentication.
- Page 1 must be POST; pages 2+ use GET with the same params plus `page=N`.
- The `keyword` field must be set to `"key"` (hardcoded upstream behavior).
- The `-find` field value is the literal submit button text: `" 検　索 "`.
- Results are 20 per page. Total count is in the `<h2>` text as `（N件）`.
