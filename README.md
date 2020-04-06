aws-docs-crawler
---

This is a simple script that crawling AWS documents pages.

# Features

- Crawl all of AWS documents pages to get page link and rss feed url (if it exists) .
- Output the result as a JSON file.
- Output the result as a OPML file (next feature) .

# Usage

This script has been tested on Python 3.x only. Please create virtual environment of Python 3.x if you need.

0. Get ChromeDriver.

    Please get ChromeDriver from following page, and place it directly under this project directory.

    - [Downloads - ChromeDriver - WebDriver for Chrome](https://chromedriver.chromium.org/downloads)

1. Clone this repository.

    ```
    git clone https://github.com/michimani/aws-docs-crawler.git
    ```

2. Install python modules.

    ```
    pip3 install -r requirements.txt
    ```

3. Run the script.

    ```
    python3 src/crawl.py
    ```

    Running this script takes about 25 - 30 minutes.
