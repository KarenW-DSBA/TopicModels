from __future__ import unicode_literals
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
import PyPDF2
from PyPDF2 import PdfFileReader
from PyPDF2 import utils
import requests
from requests.auth import HTTPBasicAuth
import datetime
import scrapy
import sys
import urllib
import pdfquery
import pandas
import sqlite3
from sqlite3 import Error

PATH = ''
LOGIN_URL = ''
USER = ''
PASSWORD = ''
DOMAIN = ''

sys.path.insert(0, PATH)


from scrapy import FormRequest
from loginform import fill_login_form

class MySpider(scrapy.Spider):

    def __init__(self, *args, **kwargs):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        super(MySpider, self).__init__(*args, **kwargs)

    name = 'to_db_spider'
    custom_settings = {
        'FEED_URI': 'OUTPUT.csv',
        'LOG_ENABLED': True,
    }
    login_url = LOGIN_URL  # authentication for some websites
    userid = USER
    password = PASSWORD

    def create_connection(self, db_file):
        try:
            conn = sqlite3.connect(db_file)
            conn.text_factory = str  # necessary to prevent UTF-8 encoding errors
            print(sqlite3.version)
        except Error as e:
            print(e)
        return conn

    def get_unscraped_urls(self, c):
        c.execute("SELECT * FROM urls where scraped = 0;")
        return c.fetchall()

    def connect_to_db(self):
        conn = self.create_connection("C:/sqlite/db/pythonsqlite.db")
        self.conn = conn
        return conn.cursor()

    def set_db_entry(self, c, item, row):
        print("Setting database entry for this scrape...")

        try:
            c.execute("""   UPDATE urls 
                            SET scraped = 1,
                                scraped_title = ?,
                                scraped_content = ?,
                                scrape_date = ?
                            WHERE row_id = ?;   """, [item['scraped_title'], item['scraped_content'], item['scrape_date'], row[19]])
            self.conn.commit()
        except Error as e:
            print(e)

    def start_requests(self):
        '''call parse_login function to authenticate & call parse function to start scraping'''
        yield scrapy.Request(self.login_url, self.parse_login)

    def parse_login(self, response):
        '''perform authentication for urls that require it'''
        data, url, method = fill_login_form(response.url, response.body, self.userid, self.password)
        return FormRequest(url, formdata = dict(data), method = method, callback = self.start_crawl)

    def start_crawl(self, response):
        c = self.connect_to_db()
        to_scrape = self.get_unscraped_urls(c)
        for row in to_scrape:
            url = row[0]
            yield scrapy.Request(url, callback = self.parse, meta = {'current_scrape':row, 'c':c})

    def spider_closed(self):
        '''
        Whence the spider has finished all of its scrapes, we:
        1: Commit our changes to the database
        2: Close the connection
        '''
        self.conn.close()
        print("All scrapes finished, commit changes to database")

    def download_pdf(self, path, content):
        f = open(path, 'wb')
        f.write(content)
        f.close()

    def parse(self, response):
        date = (datetime.datetime.today()).strftime('%m/%d/%Y')
        if '.pptx' in response.url:
            pass
        if '.pdf' in response.url:
            path = (filepath).encode('utf-8')
            self.download_pdf(path, response.body)
            try:
                pdf = PdfFileReader(path)
            except utils.PdfReadError("EOF marker not found"):
                raise
            text = ''
            for i in range(pdf.numPages):
                text += pdf.getPage(i).extractText() + " "
        elif DOMAIN in response.url:
            title = response.xpath("//h1/text()|//h2/text()|//h3/text()|//h4/text()|//h5/text()|//h6/text()").extract()
            text = response.xpath('//p/text()|//p[@class]/text()').extract()
        else:
            title = response.xpath("//h1/text()|//h2/text()|//h3/text()|//h4/text()|//h5/text()|//h6/text()").extract()
            text = response.xpath('//div[@class]/text()').extract()
        try:
            title
        except NameError:
            print("No title for this request, creating empty...")
            title = []
        try:
            text
        except NameError:
            print("No text for this request, creating empty...")
            text = []
        try:
            date
        except NameError:
            print('No date for this request, creating empty...')
            date = (datetime.datetime.today()).strftime('%m/%d/%Y')

        # check for redirect in url
        if 'redirect_urls' in response.meta:
            url = response.meta['redirect_urls'][-1]
        else:
            url = response.request.url

        current_scrape = response.meta['current_scrape']

        item = {
            'scraped_web_page_url': url,
            'scraped_title': ''.join(title).encode('utf-8'),
            'scraped_content': ''.join(text).encode('utf-8'),
            'scrape_date': date,
        }

        yield self.set_db_entry(response.meta['c'], item, current_scrape)