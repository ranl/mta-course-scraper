# mta-course-scraper
Scrap course information from MTA Meida-Net website
 
# Work in progress
This is not done, but has a good starting point if you want to have the ability to get data from Meida Net

# Requirements
* python
* python-pip
* scrapy (tested with 1.0.3)

# Installation
scrapy installation - http://doc.scrapy.org/en/latest/intro/install.html
```
sudo apt-get install python-pip python-lxml libffi-dev
sudo pip install scrapy==1.0.3
```

# Examples
get all the courses from Computer Science - Internet and Networking Specialty  
```
time scrapy crawl -o /tmp/data_from_crawler.json -t jsonlines -a faculty=11 -a track=1141 --loglevel=ERROR course_spider
```