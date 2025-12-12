# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class CategoryItem(scrapy.Item):
    level = scrapy.Field()          # major / medium / sub
    major_id = scrapy.Field()
    major_name = scrapy.Field()
    medium_id = scrapy.Field()
    medium_name = scrapy.Field()
    sub_id = scrapy.Field()
    sub_name = scrapy.Field()
    is_leaf = scrapy.Field()



class ProductItem(scrapy.Item):
    major_id = scrapy.Field()
    major_name = scrapy.Field()
    medium_id = scrapy.Field()
    medium_name = scrapy.Field()
    sub_id = scrapy.Field()
    sub_name = scrapy.Field()
    is_leaf = scrapy.Field()    

    name = scrapy.Field()    
    price = scrapy.Field()    
    naver_product_id = scrapy.Field()
    category_id = scrapy.Field()
    detail_url = scrapy.Field()
    ranking = scrapy.Field()
    mall_name = scrapy.Field()
    original_price = scrapy.Field()
    discount_rate = scrapy.Field()
    delivery_fee = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()





