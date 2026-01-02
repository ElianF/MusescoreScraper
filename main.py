import argparse
import re
import pathlib
import requests
import img2pdf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import cairosvg

def convert_svg_to_png(svg_path):
    """
    Converts a local SVG file to a PNG file in the same directory.
    Returns the Path object of the new PNG.
    """
    svg_path = pathlib.Path(svg_path)
    # Create new filename: image_001.svg -> image_001.png
    png_path = svg_path.with_suffix('.png')
    
    # 1. Read the SVG content
    with open(svg_path, 'r', encoding='utf-8', errors='ignore') as f:
        svg_data = f.read()

    # 2. Fix 'invalid dash' error by removing problematic dasharray attributes
    # This replaces dasharray settings that often cause the Cairo crash
    svg_data = re.sub(r'stroke-dasharray\s*[:=]\s*["\']?[^"\';]*["\']?', '', svg_data)
    svg_data = re.sub(r'stroke-dashoffset\s*[:=]\s*["\']?[^"\';]*["\']?', '', svg_data)
    
    # 3. Convert the sanitized string data instead of the file path
    try:
        cairosvg.svg2png(
            bytestring=svg_data.encode('utf-8'), 
            write_to=str(png_path),
            output_width=2480  # Maintain the high resolution for sharpness
        )
    except Exception as e:
        print(f"CairoSVG failed even after sanitization: {e}")
        # Fallback: if it still fails, you might need to skip this specific image
        return None
    
    return png_path

def validate_url(url_string):
    # Basic URL regex: starts with http/https and has a domain structure
    url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not re.match(url_regex, url_string):
        raise argparse.ArgumentTypeError(f"Invalid URL: '{url_string}'")
    return url_string

def download_images(image_urls, download_dir):
    """Downloads images to a pathlib directory."""
    downloaded_paths = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    
    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Create a filename (e.g., 001.jpg)
            file_extension = url.split('.')[-1].split('?')[0] or 'jpg'
            file_path = download_dir / f"{i:03d}.{file_extension}"
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            # If SVG, convert to PNG first
            if file_extension.lower() == 'svg':
                print(f"Converting {file_path} to PNG...")
                png_path = convert_svg_to_png(file_path)
                if png_path != None:
                    downloaded_paths.append(str(png_path))
            else:
                downloaded_paths.append(str(file_path))
            
            print(f"Downloaded: {file_path}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            
    return downloaded_paths

def main():
    parser = argparse.ArgumentParser(description="Web Crawler to PDF converter")
    
    # Arguments
    parser.add_argument("--urls", type=validate_url, nargs='+', required=True, help="List of URLs to crawl")
    parser.add_argument("--title", required=True)
    parser.add_argument("--composer", required=True)
    
    args = parser.parse_args()

    # 1. Setup Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Run without window
    chrome_options.add_argument("--start-maximized") # Run in full screen
    driver = webdriver.Chrome(options=chrome_options)

    image_urls = list()
    element_xpath = lambda page: f'//*[@id="jmuse-scroller-component"]/div[{page}]/img'

    for source_url in args.urls:
        driver.get(source_url)

        page = 1
        wrapper = driver.find_element(by=By.XPATH, value='//*[@id="jmuse-scroller-component"]')
        while True:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, element_xpath(page)))
                )
            except TimeoutException:
                break
            except NoSuchElementException:
                break

            time.sleep(2)
            image_url = element.get_attribute('src')
            print(image_url)
            image_urls.append(image_url)
            height = element.size["height"]
            driver.execute_script(f"arguments[0].scrollBy(0, {height+16});", wrapper)
            page += 1
    else:
        driver.quit()

    if image_urls:
        # 2. Setup Temporary Directory using pathlib
        tmp_dir = pathlib.Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        # 3. Download images
        image_paths = download_images(image_urls, tmp_dir)

        # 4. Convert to PDF
        target_width = 595
        layout_fun = img2pdf.get_layout_fun(pagesize=(target_width, None))
        output_filename = f"{args.composer} - {args.title}.pdf"
        with open(output_filename, "wb") as f:
            f.write(img2pdf.convert(image_paths, layout_fun=layout_fun))
        
        for file in tmp_dir.iterdir():
            file.unlink()
        tmp_dir.rmdir()
        
        print(f"Successfully created: {output_filename}")


if __name__ == '__main__':
    main()