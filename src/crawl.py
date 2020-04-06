from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
import json
import os
import re
import time
import traceback

THIS_PATH = os.path.dirname(os.path.abspath(__file__))

options = ChromeOptions()
options.add_argument('--headless')
selenium_driver = Chrome(THIS_PATH + '/../chromedriver', options=options)

doc_index_src = ''

DOC_HOST = 'https://docs.aws.amazon.com'
DOC_URL = DOC_HOST + '/index.html'
SELECTOR_CATEGORY_SECTION = '#awsdocs-focus-element > main-landing-page-sections > div > div:nth-child(2) > service-category-tiles > div > awsui-cards > div > ol > li.awsui-cards-card-container'
SELECTOR_CATEGORY_TITLE = 'div.awsui-cards-card-header span.awsui-cards-card-header-inner h4'
SELECTOR_AWS_SERVICE = 'awsdocs-service-link'
SELECTOR_AWS_SERVICE_PREFIX = 'a > div > span.awsdocs-service-prefix'
SELECTOR_AWS_SERVICE_NAME = 'a > div > span.awsdocs-service-name'
SELECTOR_AWS_DOC = '#awsdocs-focus-element > landing-page-sections li.awsui-cards-card-container span.awsui-cards-card-header-inner awsdocs-link'
SELECTOR_AWS_DOC_NAV = 'nav.awsui-app-layout__navigation-landmark div.awsui-side-navigation > .awsui-side-navigation__list > li > span > a'


def get_soup(url, delay=1.5):
    # type: (url, int) -> BeautifulSoup
    """ Get bs4 instance with url"""

    selenium_driver.get(url)
    time.sleep(delay)
    html_src = selenium_driver.page_source.encode('utf-8')
    return BeautifulSoup(html_src, 'html.parser')


def get_categories():
    # type: () -> list[BeautifulSoup]
    """ Get category elements of AWS.
        e.g.)
        * Compute
        * Storage
        * Database
    """
    docs_index = get_soup(DOC_URL)
    return docs_index.select(SELECTOR_CATEGORY_SECTION)


def get_services(category_soup):
    # type: (BeautifulSoup) -> list[BeautifulSoup]
    """ Get services of each AWS category.
        e.g.)
        * Compute
            * Amazon EC2
            * AWS Batch
            * Amazon ECR
            * Amazon ECS
            * Amazon EKS
            * AWS Elastic Beanstalk
            * Amazon EC2 Image Builder
            * AWS Lambda
            * AWS Launch Wizard
            * Amazon Lightsail
            * AWS Outposts
            * AWS ParallelCluster
            * AWS Serverless Application Model (AWS SAM)
            * AWS Serverless Application Repository
    """
    return category_soup.select(SELECTOR_AWS_SERVICE)


def get_docs(service_index_url):
    # type: (BeautifulSoup) -> list(BeautifulSoup)
    """ Get docs of each AWS service.
        e.g.)
        * Storage
            * Amazon S3
                * Getting Started Guide
                * Developer Guide
                * API Reference
                * Console User Guide
    """
    service_index = get_soup(service_index_url)
    return service_index.select(SELECTOR_AWS_DOC)


def get_category_item(category_soup):
    # type: (BeautifulSoup) -> dict
    """ Get a category item of AWS
        e.g.
        {
            "title": "",
            "services": []
        }
    """
    category_item = {
        'title': '',
        'services': list()
    }

    try:
        category_name = category_soup.select(SELECTOR_CATEGORY_TITLE)[0].string
        print(category_name)

        category_item['title'] = category_name

        services = get_services(category_soup)
        for s_idx, s in enumerate(services):
            service_item = get_service_item(s)
            category_item['services'].append(service_item)
    except Exception:
        print(traceback.format_exc())
    finally:
        return category_item


def get_service_item(service_soup):
    # type: (BeautifulSoup) -> dict
    """ Get a service item of an AWS service.
        e.g.)
        {
            "title": "",
            "docs": [

            ]
        }
    """
    service_item = {
        'title': '',
        'index_url': '',
        'docs': list()
    }

    try:
        s_prefix = service_soup.select(
            SELECTOR_AWS_SERVICE_PREFIX)[0].string
        s_name = re.sub(r'^<span class="awsdocs-service-name ng-binding">(.+?)<!-- ngIf: \$ctrl\.external -->.*', r'\1', str(
            service_soup.select(SELECTOR_AWS_SERVICE_NAME)[0]))
        s_full_name = f'{s_prefix} {s_name}' if s_prefix is not None else s_name

        exists_docs = True
        if re.match(r'^\/.+', service_soup['href']):
            s_link = DOC_HOST + service_soup['href']
        else:
            s_link = service_soup['href']
            exists_docs = False

        print(f'  {s_full_name}')
        service_item['title'] = s_full_name
        service_item['index_url'] = s_link

        if exists_docs is True:
            service_docs = get_docs(s_link)
            for doc in service_docs:
                doc_item = get_service_doc_item(doc)
                service_item['docs'].append(doc_item)
    except Exception:
        print(traceback.format_exc())
    finally:
        return service_item


def get_service_doc_item(doc_soup):
    # type: (BeautifulSoup) -> dict
    """ Get a document item of an AWS Service.
        e.g.)
        {
            "title": ,
            "html_url": "",
            "rss_url": ""
        }
    """
    doc_name = doc_soup['label']
    doc_link = DOC_HOST + doc_soup['href']
    doc_index = get_soup(doc_link, 1)
    rss_url = get_doc_rss_url_from_doc_index_page(doc_index, doc_link)
    if rss_url == '':
        rss_url = get_doc_rss_url_from_doc_history_page(doc_index, doc_link)
    print(f'    {doc_name} : {rss_url}')
    return {
        'menu_title': doc_name,
        'html_url': doc_link,
        'rss_url': rss_url
    }


def get_doc_rss_url_from_doc_index_page(doc_index_soup, doc_index_url):
    # type: (BeautifulSoup, str) -> str
    return get_doc_rss_url(doc_index_soup, doc_index_url)


def get_doc_rss_url_from_doc_history_page(doc_index_soup, doc_index_url):
    # type: (BeautifulSoup, str) -> str
    """ Get RSS feed URL from doc index page.
        If rss feed link exists, return it. Else, return empty string.
    """
    rss_url = ''
    doc_history_url = get_document_history_url(doc_index_soup, doc_index_url)
    if doc_history_url != '':
        doc_history_soup = get_soup(doc_history_url, 0)
        rss_url = get_doc_rss_url(doc_history_soup, doc_index_url)

    return rss_url


def get_doc_rss_url(doc_soup, doc_url):
    # type: (BeautifulSoup, str) -> str
    rss_url = ''
    rss_elem = doc_soup.select('awsdocs-link[label="RSS"] a')
    if rss_elem is not None and len(rss_elem) > 0:
        if re.match(r'^http', rss_elem[0]['href']):
            rss_url = rss_elem[0]['href']
        else:
            rss_url = re.sub(r'\/[^\/]+$', '/' + rss_elem[0]
                             ['href'], doc_url)

    return rss_url


def get_document_history_url(doc_index_soup, doc_index_url):
    # type: (BeautifulSoup, str) -> str
    """ Get document history url from doc index page. """

    doc_history_url = ''
    try:
        doc_nav = doc_index_soup.select(SELECTOR_AWS_DOC_NAV)
        doc_nav.reverse()
        for nav in doc_nav:
            if nav.string == 'Document History':
                doc_history_url = re.sub(
                    r'\/[^/]+$', '/' + nav['href'], doc_index_url)
                break
    except Exception:
        print(traceback.format_exc())
    finally:
        return doc_history_url


def save_as_json(data, path):
    # type: (dict, str) -> ()
    with open(path, mode='w') as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    try:
        result = {
            'categories': list()
        }
        categories = get_categories()
        for c_idx, c in enumerate(categories):
            category_item = get_category_item(c)
            result['categories'].append(category_item)

        save_as_json(result, THIS_PATH + '/../data/result.json')
    except Exception:
        print(traceback.format_exc())
    finally:
        selenium_driver.close()
