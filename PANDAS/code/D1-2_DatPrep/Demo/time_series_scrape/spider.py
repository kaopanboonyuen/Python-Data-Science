from datetime import datetime, timedelta
import re
import scrapy

URL = 'http://www.thaiwater.net/DATA/REPORT/php/rid_bigcm.php?sdate={}'
columns = [
    ('name', 1), ('capacity', 2), ('volume_total', 4),
    ('volume_usable', 6), ('volume_gain', 9), ('volume_drain', 12),
]

map_reg = {
    'ภาคเหนือ':'N',
    'ภาคตะวันออกเฉียงเหนือ':'NE',
    'ภาคกลาง':'C',
    'ภาคตะวันตก':'W',
    'ภาคตะวันออก':'E',
    'ภาคใต้':'S',
}

date2str = lambda d: d.strftime('%Y-%m-%d')
str2date = lambda d: datetime.strptime(d, '%Y-%m-%d').date()
tomorrow = lambda d: d + timedelta(days=1)

date_pat = re.compile(r'.*sdate=(\d{4}-\d{2}-\d{2})', re.I)


class DamSpider(scrapy.Spider):
    name = 'dam_spider'

    def __init__(self, start_date='2010-01-01', end_date=None, *args, **kwargs):
        super(DamSpider, self).__init__(*args, **kwargs)

        if end_date:
            self.end_date = str2date(end_date)
        else:
            self.end_date = datetime.now().date()

        self.start_date = str2date(start_date)

    def start_requests(self):
        d = self.start_date
        while d <= self.end_date:
            yield scrapy.Request(
                url=URL.format(date2str(d)),
                callback=self.parse,
            )
            d = tomorrow(d)

    def parse(self, response):
        sel = response.selector
        date = date_pat.match(response.url).group(1)

        for row in sel.xpath('/html/body/div/center/table/tbody/tr'):
            if row.xpath('td[1][@bgcolor]'):  # skip
                continue

            if row.xpath('td[1]/b'):
                region = map_reg[row.xpath('td[1]/b//text()').extract_first().strip()]
                continue

            item = dict()

            item['date'] = date
            item['region'] = region
            for col, i in columns:
                t = row.xpath('string(td[$i])', i=i).extract_first()
                if '*' in t:
                    continue
                t = re.sub(',', '', t)
                item[col] = t.strip()

            yield item
