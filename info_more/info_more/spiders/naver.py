import scrapy
import json
import re
from urllib.parse import urlencode
from . import constant as ENV
from ..items import CategoryItem, ProductItem
from datetime import datetime


class NaverStoreSpider(scrapy.Spider):
    name = 'naver'


    ### 인스턴스 변수
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_list_url = ENV.CATEGORY_LIST_URL
        self.base_url = ENV.BASE_URL
        self.snapshot_time = datetime.now().replace(minute=0, second=0, microsecond=0)



    ### 카테고리 탐색 
    def start_requests(self):
        # 카테고리 문서는 GET 요청 기반이며 scrapy에서 직접 params를 주입할 수 없기 때문에 URL에 직접 날려서 보냄
        params = ENV.MAJOR_CATEGORY_PARAMS.copy()
        query = urlencode(params, doseq=True)
        url = f'{ENV.CATEGORY_LIST_URL}?{query}'

        yield scrapy.Request(
            url,
            callback=self.parse_major_category,
            headers=ENV.MAJOR_CATEGORY_HEADERS,
            cookies=ENV.MAJOR_CATEGORY_COOKIES,
        )



    ### 대분류 카테고리 탐색
    def parse_major_category(self, response):
        major_data = json.loads(response.text)

        for major in major_data.get('categories', []):
            major_id = major.get('id')
            major_name = major.get('name')
            
            # major
            yield CategoryItem(
                level=ENV.LEVEL_MAJOR,
                major_id=major_id,
                major_name=major_name,
            )

            url = f'{ENV.BASE_URL}/{major_id}'
            cb_kwargs = {
                "major_id": major_id,
                "major_name": major_name,
            }

            yield scrapy.Request(
                url,
                callback=self.parse_page,
                headers=ENV.MAJOR_HEADERS,
                cookies=ENV.MAJOR_COOKIES,        
                cb_kwargs=cb_kwargs  
            )

            yield from self.parse_medium_category(major_id, major_name, major)



    ### 중분류 카테고리 탐색
    def parse_medium_category(self, major_id, major_name, major):
        for medium in major.get("children", []):
            medium_id = medium.get('id')
            medium_name = medium.get('name')
            medium_leaf = medium.get('isLeaf')
        
            yield CategoryItem(
                level=ENV.LEVEL_MEDIUM,
                major_id=major_id,
                major_name=major_name,
                medium_id=medium_id,
                medium_name=medium_name,
                is_leaf=medium_leaf,
            )

            cb_kwargs={
                "major_id": major_id,
                "major_name": major_name,
                "medium_id": medium_id,
                "medium_name": medium_name,
            }    

            url = f'{ENV.BASE_URL}/{medium_id}'

            yield scrapy.Request(
                url,
                callback=self.parse_page,
                headers=ENV.MEDIUM_HEADERS,
                cookies=ENV.MEDIUM_COOKIES,        
                cb_kwargs=cb_kwargs  
            )

            if not medium_leaf:
                url = f'{ENV.CATEGORY_LIST_URL}/{medium_id}'
                callback=self.parse_sub_category
                headers=ENV.MEDIUM_CATEGORY_HEADERS
                cookies=ENV.MEDIUM_CATEGORY_COOKIES
                
                yield scrapy.Request(
                    url,
                    callback=callback,
                    headers=headers,
                    cookies=cookies,        
                    cb_kwargs=cb_kwargs  
                )                



    ### 소분류 카테고리 탐색
    def parse_sub_category(self, response, major_id, major_name, medium_id, medium_name):
        sub_data = json.loads(response.text)

        for sub in sub_data.get('children', []):
            sub_id = sub.get('id')
            sub_name = sub.get('name')
            
            yield CategoryItem(
                level=ENV.LEVEL_SUB,
                major_id=major_id,
                major_name=major_name,
                medium_id=medium_id,
                medium_name=medium_name,
                sub_id=sub_id,
                sub_name=sub_name,
            )

            url = f'{ENV.BASE_URL}/{sub_id}'
            headers = ENV.SUB_HEADERS.copy()
            headers['referer'] = response.url

            yield scrapy.Request(
                url,
                callback=self.parse_page,
                headers=headers,
                cookies=ENV.SUB_COOKIES,        
                cb_kwargs={
                    "major_id": major_id,
                    "major_name": major_name,
                    "medium_id": medium_id,
                    "medium_name": medium_name,
                    'sub_id': sub_id,
                    'sub_name': sub_name,
                }
            )



    ### 헬퍼 함수(정수 변환)
    def _to_int(self, val_str):        
        cleaned = re.sub(r'\D', '', val_str)

        if not cleaned:
            print(f'{val_str}는 유요한 정수값이 아닙니다.')
            return None
        
        return int(cleaned)
        


    ### 헬퍼 함수(소수 변환)        
    def _to_float(self, val_str):
        cleaned = re.sub(r'[^\d.]', '', val_str)

        if not cleaned:
            print(f'{val_str}는 유요한 소수값이 아닙니다.')
            return None
        
        return float(cleaned)
    


    ### 헬퍼 함수(유효성 검사)
    def _validation(self, validation_target, validation_type):
        # 값이 없으면 바로 None
        if not validation_target:
            return None

        if validation_type == 'int':
            return self._to_int(validation_target)
        elif validation_type == 'float':
            return self._to_float(validation_target)
        else:
            # 지원하지 않는 타입에 대한 방어 코드
            raise ValueError(f"지원하지 않는 validation_type 입니다: {validation_type}")



    ### 상품 탐색
    def parse_page(self, response, major_id, major_name, medium_id=None, medium_name=None, sub_id=None, sub_name=None):
        for product in response.css('ul div.basicProductCard_view_type_grid2__vKr1n'):
        
            # meta 데이터
            head_meta = product.css('a.basicProductCard_link__urzND')
            head_data = head_meta.attrib.get('data-shp-contents-dtl')
            head = json.loads(head_data)

            lookup = {d['key']: d['value'] for d in head}

            # 문자 타입
            name = lookup['prod_nm']
            naver_product_id = lookup['chnl_prod_no']
            detail_url = head_meta.attrib.get('href')
            body_id = head_meta.attrib.get('aria-labelledby')

            # 정수 타입
            price = self._validation(lookup['price'], ENV.VALIDATION_INT_TYPE)
            ranking = self._validation(head_meta.attrib.get('data-shp-contents-rank'), ENV.VALIDATION_INT_TYPE)            

            if sub_id:
                category_id = sub_id
            else:
                category_id = medium_id

            # 본문
            body_meta = product.css(f'#{body_id}')
            mall_name = body_meta.css('div span.productCardMallLink_mall_name__5oWPw::text').get()

            # original_price_str = body_meta.css('span.priceTag_original_price__jyZRY::text').get()
            original_price_span = body_meta.css('span.priceTag_original_price__jyZRY')
            original_price_str = original_price_span.xpath("string()").get()            
            original_price = self._validation(original_price_str, ENV.VALIDATION_INT_TYPE)
            if original_price is None:
                original_price = price
            
            discount_rate_str = body_meta.css('span.priceTag_discount_ratio__VE866::text').get()
            discount_rate = self._validation(discount_rate_str, ENV.VALIDATION_INT_TYPE)
            if discount_rate is None:
                discount_rate = 0

            delivery_fee_str = body_meta.css('span.productCardDeliveryFeeInfo_delivery_text__54pei::text').get()
            delivery_fee = self._validation(delivery_fee_str, ENV.VALIDATION_INT_TYPE)
            if delivery_fee is None:
                delivery_fee = 0

            rating_str = body_meta.css('span.productCardReview_text__A9N9N::text').get()
            rating = self._validation(rating_str, ENV.VALIDATION_FLOAT_TYPE)
            if rating is None:
                rating = 0.00

            review_span = body_meta.css('span.productCardReview_text__A9N9N:not(.productCardReview_star__7iHNO)')
            review_count_str = review_span.xpath("string()").get()
            review_count = self._validation(review_count_str, ENV.VALIDATION_INT_TYPE)
            if review_count is None:
                review_count = 0
                
            yield ProductItem(
                major_id=major_id,
                major_name=major_name,
                medium_id=medium_id,
                medium_name=medium_name,
                sub_id=sub_id,
                sub_name=sub_name,

                name = name,
                price = price,
                naver_product_id = naver_product_id,
                category_id = category_id,
                detail_url = detail_url,
                ranking = ranking,
                mall_name = mall_name,
                original_price = original_price,
                discount_rate = discount_rate,
                delivery_fee = delivery_fee,
                rating = rating,
                review_count = review_count,
            )            