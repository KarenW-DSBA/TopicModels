
# coding: utf-8

# In[1]:

from scrapy.conf import settings
#from scrapy.crawler import Crawler
from scrapy.exporters import CsvItemExporter

class ProjectCsvItemExporter(CsvItemExporter):
    '''
    item pipeline to export the scraping output to a csv file 
    '''
    
    def __init__(self, *args, **kwargs):
        delimiter = settings.get('CSV_DELIMITER', '|')
        kwargs['delimiter'] = delimiter
        
        fields_to_export = settings.get('FIELDS_TO_EXPORT', [])
        if fields_to_export:
            kwargs['fields_to_export'] = fields_to_export 
            
        super(ProjectCsvItemExporter, self).__init__(*args, **kwargs)