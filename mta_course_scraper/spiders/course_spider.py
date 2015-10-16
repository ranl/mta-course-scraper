# -*- coding: utf-8 -*-

"""
MTA Course information scraper

from scrapy.shell import inspect_response
inspect_response(response, self)
"""

import scrapy
import json
import re

from mta_course_scraper.items import (
    Faculty,
    Track,
    Program,
    Course,
    Group,
)

# TODO: Add try/catch when parsing new object to not fail the entire loop


class CourseSpiderSpider(scrapy.Spider):

    name = "course_spider"
    allowed_domains = ["rishum.mta.ac.il"]
    media_net_endpoint = 'https://rishum.mta.ac.il/yedion/fireflyweb.aspx'
    start_urls = ('{0}?prgname=Enter_Search'.format(media_net_endpoint),)

    # Form Arguments
    year_arg = 'R1C1'
    maslul_arg = 'R1C2'
    faculty_arg = 'R1C9'
    hug_arg = 'HUG'

    # RE
    extract_course_view_args = re.compile(
        'prgname=S_SHOW_PROGS&arguments=-N(?P<year>\d+),-N(?P<prog>\d+)')
    extract_group_args = re.compile(
        '.+?,\'-N\s*(\d+),\s*-N\s*(\d+),\s*-N\s*(\d+),\s*-N\s*(\d+)')

    def __init__(self, faculty=None, track=None, year=2016, *args, **kwargs):
        """
        Init function
        """
        super(CourseSpiderSpider, self).__init__(*args, **kwargs)
        if faculty is not None:
            self.faculty = int(faculty)
        else:
            self.faculty = None
        if track is not None:
            self.track = int(track)
        else:
            self.track = None
        if year is not None:
            self.year = int(year)
        else:
            self.year = None

    def parse(self, response):
        """
        Parse the first menu to get all the Misgarot

        curl -F 'PRGNAME=S_MASLUL' -F 'ARGUMENTS=R1C9' -F 'R1C9=11' -F 'APPNAME='
        'https://rishum.mta.ac.il/yedion/fireflyweb.aspx
        """

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)

        options = response.xpath('//select[@name="{0}"]//option'.format(
            self.faculty_arg
        ))
        for opt in options:
            faculty = Faculty()
            faculty['id'] = int(opt.xpath('@value').extract()[0])
            faculty['name'] = opt.xpath('text()').extract()[0]
            self.logger.info('Faculty: id={}, name={}'.format(
                faculty['id'], faculty['name'].encode('utf8')))

            if faculty and faculty['id'] != self.faculty:
                continue

            request = scrapy.FormRequest(
                self.media_net_endpoint,
                callback=self.parse_faculty,
                method='POST',
                formdata={
                    'PRGNAME': 'JSON',
                    'Faculty': str(faculty['id']),
                    'Action': '700',
                },
            )
            request.meta['faculty'] = faculty
            yield request
            yield faculty

    def parse_faculty(self, response):
        """
        Parse the JSON Faculty iteration
        """

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)

        json_response = json.loads(response.body)['Answer']
        for trk in json_response:
            track = Track()
            track['id'] = int(trk['Code'])
            track['name'] = trk['Name']
            track['faculty_id'] = response.meta['faculty']['id']
            track['year'] = self.year

            request = scrapy.FormRequest(
                self.media_net_endpoint,
                callback=self.parse_track,
                method='POST',
                formdata={
                    'PRGNAME': 'S_PROG',
                    'ARGUMENTS': ','.join([
                        self.hug_arg,
                        self.year_arg,
                        self.maslul_arg,
                    ]),
                    self.maslul_arg: str(track['id']),
                    self.year_arg: str(track['year']),
                    self.hug_arg: str(track['faculty_id']),
                },
            )
            request.meta['track'] = track

            yield track
            yield request

    def parse_track(self, response):
        """
        Get all the programs for the specific track

        curl -F 'PRGNAME=' -F 'ARGUMENTS=' -F 'R1C1=' -F 'HUG=' -F 'R1C2='
        'https://rishum.mta.ac.il/yedion/fireflyweb.aspx' |less
        <a href="fireflyweb.aspx?prgname=S_SHOW_PROGS&amp;arguments=-N2015,-N115600101">הצג קורסים </a>
        """

        trs = response.xpath('//table[@id="myTable0"]/tr')
        trs.pop(0)
        for tr in trs:
            name, search, comment = tr.xpath('.//td')
            query_string = search.xpath('./a/@href').extract()[0].split('?', 1)[1]
            args = self.extract_course_view_args.match(query_string)
            prog = Program()
            prog['name'] = name.xpath('text()').extract()[0].strip()
            prog['id'] = args.groupdict()['prog']
            try:
                prog['comment'] = comment.xpath('text()').extract()[0].strip()
            except IndexError:
                pass
            prog['year'] = response.meta['track']['year']
            prog['faculty_id'] = response.meta['track']['faculty_id']
            prog['track_id'] = response.meta['track']['id']

            # https://rishum.mta.ac.il/yedion/fireflyweb.aspx?prgname=S_SHOW_PROGS&arguments=-N2016,-N114100101
            request = scrapy.FormRequest(
                '{}?{}'.format(self.media_net_endpoint, query_string),
                callback=self.parse_program,
                method='GET',
            )
            request.meta['program'] = prog

            # Yield results
            yield prog
            yield request

    def parse_program(self, response):
        """
        Get all the courses for the specific program
        """

        for tr in response.xpath('//table[@id="myTable0"]/tbody//tr'):
            course_id, course_name, _, button, comment = tr.xpath('.//td')
            course = Course()
            course['id'] = course_id.xpath('text()').extract()[0].strip()
            course['name'] = course_name.xpath('text()').extract()[0].strip()
            try:
                course['comment'] = comment.xpath('text()').extract()[0].strip()
            except IndexError:
                pass
            course['year'] = response.meta['track']['year']
            course['faculty_id'] = response.meta['track']['faculty_id']
            course['track_id'] = response.meta['track']['id']
            course['program_id'] = response.meta['program']['id']

            request = scrapy.FormRequest(
                self.media_net_endpoint,
                callback=self.parse_course,
                method='POST',
                formdata={
                    'PRGNAME': 'S_LOOK_FOR_NOSE',
                    'ARGUMENTS': '-N{}'.format(course['id']),
                },
            )
            request.meta['course'] = course

            yield course
            yield request

    def parse_course(self, response):
        """
        Parse the request for each group for this specific group

        S_YPratem
        -N+111111,-N1,-N+++1,-N+11111101,-N
        POST
        """

        for button in response.xpath('//input[@name="B2"]'):
            js_func = button.xpath('@onclick').extract()[0]
            js_args = js_func.split('\'')[5]
            args = ','.join(map(
                lambda x: '-N' + x,
                self.extract_group_args.match(js_args).groups()))
            request = scrapy.FormRequest(
                self.media_net_endpoint,
                callback=self.parse_course_iter,
                method='POST',
                formdata={
                    'PRGNAME': 'S_YPratem',
                    'ARGUMENTS': args,
                },
            )
            request.meta['course'] = response.meta['course']
            yield request

    def parse_course_iter(self, response):
        """
        Parse the group for a given course
        """

        group = Group()
        tds = response.xpath('//table[@class="text"]/tr/td')
        group['points'] = float(tds[4].xpath('text()').extract()[0].split(':', 1)[1])
        group['hours'] = float(tds[5].xpath('text()').extract()[0].split(':', 1)[1])
        group['lecturer'] = tds[6].xpath('text()').extract()[0].split(':', 1)[1].strip()
        group['id'] = int(tds[7].xpath('text()').extract()[0].split(':', 1)[1])

        # If we have the <b> tag then we have exams dates
        # some groups can have zero exams
        i = 8
        if tds[8].xpath('./b'):
            i += 1
            group['exams'] = []
            for date in tds[8].xpath('text()').extract()[2:]:
                dmy, t = date.split()[4:6]
                group['exams'].push({
                    'date': dmy,
                    'time': t,
                })
