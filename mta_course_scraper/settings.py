# -*- coding: utf-8 -*-

# Scrapy settings for mta_course_scraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'mta_course_scraper'

SPIDER_MODULES = ['mta_course_scraper.spiders']
NEWSPIDER_MODULE = 'mta_course_scraper.spiders'

ITEM_PIPELINES = {
    'mta_course_scraper.pipelines.AddTypePipeline': 500,
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'mta_course_scraper (+http://www.yourdomain.com)'
