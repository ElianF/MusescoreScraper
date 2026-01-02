# Musescore Scraper to PDF

A CLI utility designed to scrape sheet music from musescore and compile them into a PDF document.

### Features
- **Multi-Source**: Supports multiple URLs in a single execution.
- **Dynamic Scraper**: Uses Selenium to handle lazy-loading scrollers via auto-scroll.
- **SVG Sanitizer**: Automatically cleans and converts SVGs to high-resolution PNGs (2480px width) to prevent `CairoSVG` dash-array crashes.
- **Standardized Layout**: Enforces a fixed PDF page width (595pt) for consistent viewing.
- **Auto-Cleanup**: Automatically removes temporary files and directories after conversion.

---

### Prerequisites

1. **Python Packages**: Requirements installable with ```pip install -r ./requirements```
2. **Tools**: Installation of Cairo e.g. via `https://cairographics.org/`
3. **Chrome Browser**: Ensure Google Chrome is installed (Selenium 4+ manages drivers automatically).
4. **SVG Support (Windows)**: Install the [GTK for Windows Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) to provide the necessary C libraries for `cairosvg`.

---

### Usage

Run the script from your terminal providing the target URLs, title, and composer:

```bash
python main.py --urls "MusescoreURL1" "MusescoreURL2" --title "Concerto" --composer "Beethoven"
```

**Arguments:**

* `--urls`: One or more space-separated source URLs.
* `--title`: The title of the work (used for filename).
* `--composer`: The name of the composer (used for filename).

---

### Technical Workflow

1. **Selenium Crawl**: Launches a maximized Chrome instance, iterates through the `--urls`, and identifies image elements in the `#jmuse-scroller-component`.
2. **Dynamic Scrolling**: Calculates element height to scroll the container precisely, triggering lazy-loading.
3. **Sanitization**: Reads SVG source code and uses Regex to strip `stroke-dash` attributes that cause rendering errors in Cairo.
4. **Rasterization**: Converts SVGs to PNGs at high density (300 DPI equivalent) for sharpness.
5. **PDF Assembly**: Uses `img2pdf` to bundle images into a final PDF named `Composer - Title.pdf`.
6. **Cleanup**: Deletes all images in the `./tmp` folder and removes the directory.
