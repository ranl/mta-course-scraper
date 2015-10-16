# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MtaCourseScraperItem(scrapy.Item):
    pass


class Faculty(MtaCourseScraperItem):

    """
    A Faculty
    for example:
        - Computer Science 1st Degree
        - Certificate Studies
        - etc ...
    """

    id = scrapy.Field()
    name = scrapy.Field()


class Track(MtaCourseScraperItem):

    """
    A Track in a specific faculty
    for example:
        - Computer Science - Internet and Network
        - Computer Science - General
        - etc ...
    """

    faculty_id = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()


class Program(MtaCourseScraperItem):

    """
    A Program in a track
    for example:
        - Mandatory Courses A
        - Mandatory Courses B
        - etc ...
    """

    faculty_id = scrapy.Field()
    track_id = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()
    comment = scrapy.Field()


class Course(MtaCourseScraperItem):

    """
    A Course in a given program
    """

    faculty_id = scrapy.Field()
    track_id = scrapy.Field()
    program_id = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()


class Group(MtaCourseScraperItem):

    """
    A Group for a given course
    """

    faculty_id = scrapy.Field()
    track_id = scrapy.Field()
    program_id = scrapy.Field()
    course_id = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()
    type = scrapy.Field()
    points = scrapy.Field()
    hours = scrapy.Field()
    lecturer = scrapy.Field()
    exams = scrapy.Field()
    syllabus = scrapy.Field()