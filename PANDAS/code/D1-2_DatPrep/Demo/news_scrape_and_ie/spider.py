import os
from datetime import datetime, timedelta
import re
import scrapy

URL = 'https://news.mthai.com/economy-news/page/{}'


class NewsSpider(scrapy.Spider):
    name = 'news_spider'

    def __init__(self, first_page=1, last_page=None, out_dir='output', *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)

        try:
            self.first_page = int(first_page)
        except ValueError:
            self.first_page = 1
        try:
            self.last_page = int(last_page or 'raise error')
        except ValueError:
            self.last_page = float('inf')

        self.out_dir = out_dir

        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

    def start_requests(self):
        yield scrapy.Request(url=URL.format(self.first_page), callback=self.parse_page)

    def parse_page(self, response):
        try:
            page = int(response.url.split('/')[-1])
        except ValueError:
            page = 1

        if response.status != 200 or page > self.last_page:
            return

        sel = response.selector
        for box in sel.xpath('//*[@id="main"]/div[1]/div'):
            item_url = box.xpath('.//h3/a/@href').extract_first()
            yield scrapy.Request(url=item_url, callback=self.parse_item)

        yield scrapy.Request(url=URL.format(page+1), callback=self.parse_page)

    def parse_item(self, response):
        id_ = response.url.split('/')[-1].split('.')[0]
        out_file = os.path.join(self.out_dir, id_+'.txt')

        sel = response.selector
        with open(out_file, 'w', encoding='utf-8') as f:
            for p in sel.xpath('//*[@id="content-inner-{}"]/p'.format(id_)):
                print(' '.join(p.xpath('.//text()').extract()).strip(), file=f)

        item = dict()
        item['path'] = out_file
        item['id'] = id_
#         item['author'] = sel.xpath('//*[@itemprop="author"]/a/text()').extract_first().strip()
        item['author'] = sel.xpath('//*[@class="author-name"]/text()').extract_first().strip()
        item['title'] = sel.xpath('//*[@id="post-{}"]/header/h1/text()'.format(id_)).extract_first().strip()
        item['date'] = sel.xpath('//*[@id="post-{}"]//time/@datetime'.format(id_)) \
            .extract_first().split('T')[0].strip()

        yield item

