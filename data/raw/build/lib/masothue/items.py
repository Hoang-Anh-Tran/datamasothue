import scrapy

class CompanyLinkItem(scrapy.Item):
    href = scrapy.Field()

class CompanyDetailItem(scrapy.Item):
    tax_code = scrapy.Field()
    company_name = scrapy.Field()
    address = scrapy.Field()
    status = scrapy.Field()
    representative = scrapy.Field()
    phone = scrapy.Field()
    start_date = scrapy.Field()
    managed_by = scrapy.Field()
    last_updated = scrapy.Field()