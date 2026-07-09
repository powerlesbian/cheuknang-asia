# Chinese /zh/ build tooling

Translation memory + builder for the Traditional-Chinese (HK) mirror.

Run from repo root:
    PYTHONPATH=_tools python3 _tools/build_zh.py

- `zh_content.py` — per-page EN→ZH content maps (keyed by exact EN source strings).
- `build_zh.py`   — copies each EN page, translates nav + content, writes
  /zh/<slug>/index.html, then `relink_all()` cross-links zh pages that exist
  and wires the EN↔中文 nav switcher (no 404s to unbuilt pages).

To add a page: extract its visible strings, add a MAP dict in zh_content.py,
add it to the `pages` list in build_zh.py `__main__`, run, screenshot-verify,
commit. Pages still to do: portfolio, new-villa-cecil, news, reports.
