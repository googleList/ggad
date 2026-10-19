# Site Icon Subset

The site uses 27 glyphs from Tabler Icons 3.46.0. The generated local CSS and
WOFF2 font replace the full webfont download without changing existing icon
names or menu behavior. The upstream MIT license is in `assets/icons/LICENSE.txt`.

Rebuild after adding a name to `ICON_NAMES` in `build_icon_subset.py`:

```powershell
python -m pip install -r tools/requirements-icons.txt
python -B tools/build_icon_subset.py
python -B scripts/performance_budget_check.py
```

The generated manifest records upstream and subset hashes and glyph mappings.
Site runtime does not require Python or these build dependencies.

For browser verification, install Playwright in a tooling environment, serve the
repository locally, and run:

```powershell
node tools/check_site_icons.cjs http://127.0.0.1:8765/
```

`PLAYWRIGHT_MODULE` may point to an existing Playwright package;
`CHROME_PATH` may point to a local Chrome executable. The test checks all current
sitemap pages, mobile navigation states, nested article assets, local-file views,
font loading, and horizontal overflow. Screenshots and JSON results are written
to the temporary directory by default.
