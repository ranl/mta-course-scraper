# -*- coding: utf-8 -*-

"""
MTA Course information scraper

from scrapy.shell import inspect_response
inspect_response(response, self)
"""

import scrapy
import json
import re
import traceback
from collections import defaultdict

from mta_course_scraper.items import (
    Faculty,
    Track,
    Program,
    Course,
    Group,
)


class SpiderErrorDetector(object):

    def __init__(self):
        def _entry():
            return {'error': 0, 'total': 0}
        self._stats = defaultdict(_entry)

    def add_error(self, key):
        self._stats[key]['error'] += 1
        self._stats[key]['total'] += 1

    def add_success(self, key):
        self._stats[key]['total'] += 1

    def calc_ratio(self):
        for key, stats in self._stats.iteritems():
            if stats['total'] == 0:
                stats['error_ratio'] = float(0)
            else:
                stats['error_ratio'] = stats['error'] / float(stats['total'])

    def __repr__(self):
        return json.dumps(self._stats, indent=4)


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
        '-N\s*(\d+),\s*-N\s*(\d+),\s*-N\s*(\d+),\s*-N\s*(\d+)')

    # Group Tables
    dependencies_table = u'\u05ea\u05e0\u05d0\u05d9 \u05e7\u05d3\u05dd \u05dc\u05e0\u05d5\u05e9\u05d0'
    schedule_table = u'\u05de\u05e2\u05e8\u05db\u05ea \u05e9\u05e2\u05d5\u05ea'

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
        self.stats = SpiderErrorDetector()

    def closed(self, reason):
        """
        Print out the stats dict
        """
        self.stats.calc_ratio()
        self.logger.info(self.stats)

    def parse(self, response):
        """
        Parse the first menu to get all the Misgarot

        curl -F 'PRGNAME=S_MASLUL' -F 'ARGUMENTS=R1C9' -F 'R1C9=11' -F 'APPNAME='
        'https://rishum.mta.ac.il/yedion/fireflyweb.aspx
        """

        options = response.xpath('//select[@name="{0}"]//option'.format(
            self.faculty_arg
        ))
        for opt in options:
            faculty = Faculty()
            try:
                faculty['id'] = int(opt.xpath('@value').extract()[0])
                faculty['name'] = opt.xpath('text()').extract()[0]
            except Exception:
                self.stats.add_error(Faculty.__name__)
                self.logger.error(traceback.format_exc())
                continue
            else:
                self.stats.add_success(Faculty.__name__)

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

        json_response = json.loads(response.body)['Answer']
        for trk in json_response:
            track = Track()
            try:
                track['id'] = int(trk['Code'])
                track['name'] = trk['Name']
            except Exception:
                self.stats.add_error(Track.__name__)
                self.logger.error(traceback.format_exc())
                continue
            else:
                self.stats.add_success(Track.__name__)

            track['faculty_id'] = response.meta['faculty']['id']
            track['year'] = self.year

            if self.track and track['id'] != self.track:
                continue

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
            prog = Program()
            try:
                name, search, comment = tr.xpath('.//td')
                query_string = search.xpath('./a/@href').extract()[0].split('?', 1)[1]
                args = self.extract_course_view_args.match(query_string)
                prog['name'] = name.xpath('text()').extract()[0].strip()
                prog['id'] = args.groupdict()['prog']
                try:
                    prog['comment'] = comment.xpath('text()').extract()[0].strip()
                except IndexError:
                    prog['comment'] = ''
            except Exception:
                self.stats.add_error(Program.__name__)
                self.logger.error(traceback.format_exc())
                continue
            else:
                self.stats.add_success(Program.__name__)

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
            course = Course()
            try:
                course_id, course_name, _, button, comment = tr.xpath('.//td')
                course['id'] = course_id.xpath('text()').extract()[0].strip()
                course['name'] = course_name.xpath('text()').extract()[0].strip()
                try:
                    course['comment'] = comment.xpath('text()').extract()[0].strip()
                except IndexError:
                    course['comment'] = ''
            except Exception:
                self.stats.add_error(Course.__name__)
                self.logger.error(traceback.format_exc())
                continue
            else:
                self.stats.add_success(Course.__name__)

            course['year'] = response.meta['program']['year']
            course['faculty_id'] = response.meta['program']['faculty_id']
            course['track_id'] = response.meta['program']['track_id']
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
            try:
                js_func = button.xpath('@onclick').extract()[0]
                js_args = js_func.split('\'')[5]
                args = ','.join(map(
                    lambda x: '-N' + x,
                    self.extract_group_args.match(js_args).groups()))
            except Exception:
                self.stats.add_error('CourseIter')
                self.logger.error(traceback.format_exc())
                continue
            else:
                self.stats.add_success('CourseIter')

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

        def get_float(td, miss_value=0):
            try:
                return float(td.xpath('text()').extract()[0].split(':', 1)[1])
            except ValueError:
                return float(miss_value)

        def parse_schedule(table):
            trs = table.xpath('.//tr')
            trs.pop(0)
            group['classes'] = []
            for tr in trs:
                semester, day, start_time, end_time, _, _ = tr.xpath('.//td')
                group['classes'].append({
                    'semester': semester.xpath('text()').extract()[0].strip(),
                    'day': day.xpath('text()').extract()[0].strip(),
                    'start_time': start_time.xpath('text()').extract()[0].strip(),
                    'end_time': end_time.xpath('text()').extract()[0].strip(),
                })

        def parse_dependencies(table):
            trs = table.xpath('.//tr')
            trs.pop(0)
            group['dependencies'] = []
            for tr in trs:
                dep_type, affected_students, course, _ = tr.xpath('.//td')
                group['dependencies'].append({
                    'dep_type': dep_type.xpath('text()').extract()[0].strip(),
                    'affected_students': affected_students.xpath('text()').extract()[0].strip(),
                    'course': course.xpath('text()').extract()[0].strip(),
                })

        def parse_sibling_courses(table):
            trs = table.xpath('.//tr')
            trs.pop(0)
            group['siblings'] = []
            for tr in trs:
                course_id, course_name, course_type, schedule, lecturer, link = tr.xpath('.//td')
                group['siblings'].append({
                    'course_id': course_id.xpath('text()').extract()[0].strip(),
                    'course_name': course_name.xpath('text()').extract()[0].strip(),
                    'course_type': course_type.xpath('text()').extract()[0].strip(),
                    'schedule': schedule.xpath('text()').extract()[0].strip(),
                    'lecturer': lecturer.xpath('text()').extract()[0].strip(),
                    'link': link.xpath('./a/@href').extract()[0].strip(),
                })

        try:
            tds = response.xpath('//table[@class="text"]/tr/td')
            group['points'] = get_float(tds[4])
            group['hours'] = get_float(tds[5])
            group['lecturer'] = tds[6].xpath('text()').extract()[0].split(':', 1)[1].strip()
            group['id'] = int(tds[7].xpath('text()').extract()[0].split(':', 1)[1])

            # If we have the <b> tag then we have exams dates
            # some groups can have zero exams
            i = 8
            if tds[8].xpath('./b'):
                i += 1
                group['exams'] = []
                for date in tds[i].xpath('text()').extract()[2:]:
                    dmy, t = date.split()[4:6]
                    group['exams'].append({
                        'date': dmy,
                        'time': t,
                    })

            for table in response.xpath('//table[contains(@id, "myTable")]'):
                table_name = table.xpath('../div/h2/text()').extract()[0].strip()
                if table_name == self.schedule_table:
                    parse_schedule(table)
                elif table_name == self.dependencies_table:
                    parse_dependencies(table)
                else:
                    parse_sibling_courses(table)
        except Exception:
            self.stats.add_error(Group.__name__)
            self.logger.error(traceback.format_exc())
            return
        else:
            self.stats.add_success(Group.__name__)

        yield group
