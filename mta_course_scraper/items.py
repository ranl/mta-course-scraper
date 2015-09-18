# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MtaCourseScraperItem(scrapy.Item):
    pass


class Misgeret(MtaCourseScraperItem):

    """
    A "Misgeret"
    for example:
        - Computer Science 1st Degree
        - Certificate Studies
        - etc ...
    """

    id = scrapy.Field()
    name = scrapy.Field()


class Maslul(MtaCourseScraperItem):

    """
    A "Maslul"
    for example:
        - Computer Science - Internet and Network
        - Computer Science - General
        - etc ...
    """

    misgeret_id = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()


class Prog(MtaCourseScraperItem):

    """
    A "Program"
    for example:
        - Mandatory Courses A
        - Mandatory Courses B
        - etc ...
    """

    misgeret_id = scrapy.Field()
    maslul_id = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()
