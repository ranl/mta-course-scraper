# -*- coding: utf-8 -*-
import scrapy
import re

from mta_course_scraper.items import (
    Misgeret,
    Maslul,
    Prog,
)


class CourseSpiderSpider(scrapy.Spider):
    name = "course_spider"
    allowed_domains = ["rishum.mta.ac.il"]
    media_net_endpoint = 'https://rishum.mta.ac.il/yedion/fireflyweb.aspx'
    start_urls = ('{0}?prgname=Enter_Search'.format(media_net_endpoint),)

    # Form Arguments
    year_arg = 'R1C1'
    maslul_arg = 'R1C2'
    misgeret_arg = 'R1C9'
    hug_arg = 'HUG'

    # RE
    extract_maslul_info = re.compile(
        '^\s*(?P<id>\d+)[- ]+(?P<name>.+)'
    )
    extract_year_info = re.compile(
        '^\s*(?P<year>\d+)[- ]+(?P<heb_year>.+)'
    )
    extract_course_view_args = re.compile(
        'fireflyweb\.aspx\?prgname=S_SHOW_PROGS&arguments=(?P<left>-N\d+),(?P<right>-N\d+)'
    )

    def parse(self, response):
        """
        Parse the first menu to get all the Misgarot

        curl -F 'PRGNAME=S_MASLUL' -F 'ARGUMENTS=R1C9' -F 'R1C9=11' -F 'APPNAME='
        'https://rishum.mta.ac.il/yedion/fireflyweb.aspx
        """

        options = response.xpath('//select[@name="{0}"]//option'.format(
            self.misgeret_arg
        ))
        for opt in options:
            # Create the misgeret Item
            misgeret = Misgeret()
            misgeret['id'] = int(opt.xpath('@value').extract()[0])
            misgeret['name'] = opt.xpath('text()').extract()[0]

            # Create the crawl misgeret request
            request = scrapy.FormRequest(
                self.media_net_endpoint,
                callback=self.parse_misgeret,
                method='POST',
                formdata={
                    'PRGNAME': 'S_MASLUL',
                    'ARGUMENTS': self.misgeret_arg,
                    self.misgeret_arg: str(misgeret['id']),
                },
            )
            request.meta['misgeret'] = misgeret

            # Yield results
            yield misgeret
            yield request

    def parse_misgeret(self, response):
        """
        Get all the maslolim for the specific misgeret

        curl -F 'PRGNAME=S_PROG' -F 'ARGUMENTS=HUG,R1C1,R1C2' -F 'R1C1=2015' -F 'HUG=11' -F 'R1C2=1146'
        'https://rishum.mta.ac.il/yedion/fireflyweb.aspx' |less
        """

        # Get the latest year
        years = []
        for opt in response.xpath('//select[@name="{0}"]//option'.format(self.year_arg)):
            match = self.extract_year_info.match(
                opt.xpath('text()').extract()[0]
            )
            if match:
                years.insert(0, int(match.groupdict()['year']))
        years.sort()

        options = response.xpath('//select[@name="{0}"]//option'.format(self.maslul_arg))
        for opt in options:
            match = self.extract_maslul_info.match(
                opt.xpath('text()').extract()[0]
            )
            if match:
                # Create the maslul Item
                maslul = Maslul()
                maslul['id'] = int(match.groupdict()['id'])
                maslul['name'] = match.groupdict()['name']
                maslul['misgeret_id'] = response.meta['misgeret']['id']
                maslul['year'] = years[-1]

                # Create a request to crawl this maslul
                request = scrapy.FormRequest(
                    self.media_net_endpoint,
                    callback=self.parse_prog,
                    method='POST',
                    formdata={
                        'PRGNAME': 'S_PROG',
                        'ARGUMENTS': ','.join([
                            self.hug_arg,
                            self.year_arg,
                            self.maslul_arg,
                        ]),
                        self.maslul_arg: str(maslul['id']),
                        self.year_arg: str(maslul['year']),
                        self.hug_arg: str(maslul['misgeret_id']),
                    },
                )
                request.meta['maslul'] = maslul

                # Yield results
                yield maslul
                yield request

    def parse_prog(self, response):
        """
        Get all the programs for the specific maslul

        curl -F 'PRGNAME=' -F 'ARGUMENTS=' -F 'R1C1=' -F 'HUG=' -F 'R1C2='
        'https://rishum.mta.ac.il/yedion/fireflyweb.aspx' |less
        <a href="fireflyweb.aspx?prgname=S_SHOW_PROGS&amp;arguments=-N2015,-N115600101">הצג קורסים </a>
        """

        trs = response.xpath('//table[@id="myTable0"]/tr')
        trs.pop(0)
        for tr in trs:
            # Create the Prog
            name, search, comment = tr.xpath('.//td')
            prog = Prog()
            prog['misgeret_id'] = response.meta['maslul']['misgeret_id']
            prog['maslul_id'] = response.meta['maslul']['id']
            prog['id'] = -1  # ???
            prog['name'] = name.xpath('text()').extract()[0]
            prog['year'] = response.meta['maslul']['year']
            args = self.extract_course_view_args.match(
                search.xpath('./a/@href').extract()[0]
            )

            # Create the request for the list of courses
            request = scrapy.FormRequest(
                self.media_net_endpoint,
                callback=self.parse_courses,
                method='GET',
                formdata={
                    'PRGNAME': 'S_SHOW_PROGS',
                    'ARGUMENTS': ','.join(
                        args.groups()
                    ),
                },
            )
            request.meta['prog'] = prog

            # Yield results
            yield prog
            yield request

    def parse_courses(self, response):
        """
        Get all the courses for the specific prog
        """

        for tr in response.xpath('//table[@id="myTable0"]/tbody//tr'):
            pass
