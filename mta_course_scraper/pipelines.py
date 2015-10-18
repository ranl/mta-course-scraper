# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class AddTypePipeline(object):

    """
    Add the type of the item (class name)
    to the item
    """

    def process_item(self, item, spider):
        item['item_type'] = type(item).__name__
        return item
