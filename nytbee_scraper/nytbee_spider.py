"""
Scrapy spider to download all NYT Spelling Bee puzzle pages from nytbee.com
Date range: 2018-06-23 to 2025-10-01
URL pattern: https://nytbee.com/Bee_YYYYMMDD.html
"""

import scrapy
from datetime import datetime, timedelta
from pathlib import Path


class NYTBeeSpider(scrapy.Spider):
    name = 'nytbee'
    allowed_domains = ['nytbee.com']

    # Custom settings for polite scraping
    custom_settings = {
        'DOWNLOAD_DELAY': 1,  # 1 second between requests
        'CONCURRENT_REQUESTS': 1,  # One request at a time
        'USER_AGENT': 'Mozilla/5.0 (compatible; SpellingBeeSolver/1.0)',
        'ROBOTSTXT_OBEY': True,
    }

    def __init__(self, *args, **kwargs):
        super(NYTBeeSpider, self).__init__(*args, **kwargs)
        self.output_dir = Path('/home/tom/spelling_bee_solver_project/nytbee_data')
        self.output_dir.mkdir(exist_ok=True)

    def start_requests(self):
        """Generate requests for all dates from 2018-06-23 to 2025-10-01"""
        start_date = datetime(2018, 6, 23)
        end_date = datetime(2025, 10, 1)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            url = f'https://nytbee.com/Bee_{date_str}.html'

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'date': date_str},
                errback=self.errback_httpbin,
                dont_filter=True
            )

            current_date += timedelta(days=1)

    def parse(self, response):
        """Save the HTML page"""
        date_str = response.meta['date']
        filename = self.output_dir / f'Bee_{date_str}.html'

        filename.write_bytes(response.body)
        self.logger.info(f'Saved: {filename}')

        yield {
            'date': date_str,
            'url': response.url,
            'status': response.status,
            'size': len(response.body)
        }

    def errback_httpbin(self, failure):
        """Handle errors (like 404s for missing pages)"""
        self.logger.error(f'Error: {failure.value}')
