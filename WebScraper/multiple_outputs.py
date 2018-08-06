from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from spiders.spider0 import Spider0
from spiders.spider1 import Spider1
from twisted.internet import defer
from twisted.internet import reactor

settings = get_project_settings()
runner = CrawlerRunner(settings)

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(Spider0)
    yield runner.crawl(Spider1)

crawl()
reactor.run()