# info_more/pipelines.py

import pymysql
from itemadapter import ItemAdapter
from info_more.items import CategoryItem, ProductItem

class MySQLCategoryPipeline:
    def __init__(self, host, user, password, db, port, charset):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db
        self.port = port
        self.charset = charset
        self.conn = None
        self.cursor = None
        # naver_category_id → category.id 캐시
        self.id_cache = {}

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            host=settings.get('MYSQL_HOST'),
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWORD'),
            db=settings.get('MYSQL_DB'),
            port=settings.getint('MYSQL_PORT'),
            charset=settings.get('MYSQL_CHARSET'),
        )

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db_name,
            port=self.port,
            charset=self.charset,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,   # 트랜잭션 단순화
        )
        self.cursor = self.conn.cursor()
        spider.logger.info("MySQLCategoryPipeline: DB 연결 완료")

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        spider.logger.info("MySQLCategoryPipeline: DB 연결 종료")

    def _get_level_int(self, level_str):
        if level_str == "major":
            return 1
        elif level_str == "medium":
            return 2
        elif level_str == "sub":
            return 3
        else:
            return 0  # 예외 케이스

    def _get_parent_id(self, parent_naver_id):
        if parent_naver_id is None:
            return None

        parent_naver_id = str(parent_naver_id)

        # 캐시 먼저 확인
        if parent_naver_id in self.id_cache:
            return self.id_cache[parent_naver_id]

        # DB에서 조회
        sql = "SELECT id FROM category WHERE naver_category_id = %s"
        self.cursor.execute(sql, (parent_naver_id,))
        row = self.cursor.fetchone()
        if row:
            self.id_cache[parent_naver_id] = row['id']
            return row['id']
        return None

    def _save_and_cache_id(self, naver_category_id: str):
        """INSERT 후 해당 naver_category_id의 id를 캐시에 넣기 위한 헬퍼."""
        naver_category_id = str(naver_category_id)
        sql = "SELECT id FROM category WHERE naver_category_id = %s"
        self.cursor.execute(sql, (naver_category_id,))
        row = self.cursor.fetchone()
        if row:
            self.id_cache[naver_category_id] = row['id']

    def process_item(self, item, spider):
        if not isinstance(item, CategoryItem):
            return item
                
        adapter = ItemAdapter(item)

        level_str = adapter.get("level")
        level = self._get_level_int(level_str)

        if level == 0:
            spider.logger.warning(f"알 수 없는 level 값: {level_str}")
            return item

        # level에 따라 naver_category_id / name / parent_naver_id 결정
        if level_str == "major":
            naver_category_id = adapter.get("major_id")
            name = adapter.get("major_name")
            parent_naver_id = None
        elif level_str == "medium":
            naver_category_id = adapter.get("medium_id")
            name = adapter.get("medium_name")
            parent_naver_id = adapter.get("major_id")
        elif level_str == "sub":
            naver_category_id = adapter.get("sub_id")
            name = adapter.get("sub_name")
            parent_naver_id = adapter.get("medium_id")

        # parent_id 조회
        parent_id = self._get_parent_id(parent_naver_id)

        # INSERT ... ON DUPLICATE KEY UPDATE
        sql = """
        INSERT INTO category (naver_category_id, name, level, parent_id)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            level = VALUES(level),
            parent_id = VALUES(parent_id)
        """

        self.cursor.execute(
            sql,
            (str(naver_category_id), name, level, parent_id)
        )

        # 캐시 업데이트 (부모로 쓰일 수 있는 major / medium은 특히 중요)
        self._save_and_cache_id(naver_category_id)

        return item    
    

    
class MySQLProductPipeline:
    def __init__(self, host, user, password, db, port, charset):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db
        self.port = port
        self.charset = charset
        self.conn = None
        self.cursor = None
        # naver_category_id → category.id 캐시
        self.category_id_cache = {}

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            host=settings.get('MYSQL_HOST'),
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWORD'),
            db=settings.get('MYSQL_DB'),
            port=settings.getint('MYSQL_PORT'),
            charset=settings.get('MYSQL_CHARSET'),
        )

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db_name,
            port=self.port,
            charset=self.charset,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        self.cursor = self.conn.cursor()
        spider.logger.info("MySQLProductPipeline: DB 연결 완료")

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        spider.logger.info("MySQLProductPipeline: DB 연결 종료")

    def _get_category_id_by_naver_id(self, naver_category_id):
        """네이버 카테고리 ID → category.id (FK)"""
        if not naver_category_id:
            return None

        key = str(naver_category_id)

        # 캐시 확인
        if key in self.category_id_cache:
            return self.category_id_cache[key]

        sql = "SELECT id FROM category WHERE naver_category_id = %s LIMIT 1"
        self.cursor.execute(sql, (key,))
        row = self.cursor.fetchone()
        if row:
            self.category_id_cache[key] = row['id']
            return row['id']
        return None

    def process_item(self, item, spider):
        # ProductItem만 처리
        if not isinstance(item, ProductItem):
            return item

        adapter = ItemAdapter(item)

        naver_product_id = adapter.get('naver_product_id')

        # 어떤 카테고리를 FK로 쓸지: sub → medium → major 우선
        naver_category_id = (
            adapter.get('sub_id')
            or adapter.get('medium_id')
            or adapter.get('major_id')
        )

        category_id = self._get_category_id_by_naver_id(naver_category_id)
        if not category_id:
            spider.logger.warning(
                f"[PRODUCT] category not found for naver_category_id={naver_category_id}, "
                f"naver_product_id={naver_product_id}"
            )
            # FK 에러를 막기 위해 그냥 스킵
            return item

        mall_name = adapter.get('mall_name')
        name = adapter.get('name')
        detail_url = adapter.get('detail_url')

        # 숫자 필드 변환 (DB 타입에 맞춤)
        price = adapter.get('price')  # NOT NULL이라 0 기본
        original_price = adapter.get('original_price')
        discount_rate = adapter.get('discount_rate')
        delivery_fee = adapter.get('delivery_fee')
        rating = adapter.get('rating')
        review_count = adapter.get('review_count')
        ranking = adapter.get('ranking')

        sql = """
        INSERT INTO product (
            naver_product_id,
            category_id,
            mall_name,
            name,
            original_price,
            discount_rate,
            price,
            delivery_fee,
            rating,
            review_count,
            ranking,
            detail_url
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            category_id    = VALUES(category_id),
            mall_name      = VALUES(mall_name),
            name           = VALUES(name),
            original_price = VALUES(original_price),
            discount_rate  = VALUES(discount_rate),
            price          = VALUES(price),
            delivery_fee   = VALUES(delivery_fee),
            rating         = VALUES(rating),
            review_count   = VALUES(review_count),
            ranking        = VALUES(ranking),
            detail_url     = VALUES(detail_url),
            updated_at     = CURRENT_TIMESTAMP
        """

        try:
            self.cursor.execute(
                sql,
                (
                    naver_product_id,
                    category_id,
                    mall_name,
                    name,
                    original_price,
                    discount_rate,
                    price,
                    delivery_fee,
                    rating,
                    review_count,
                    ranking,
                    detail_url,
                )
            )
        except Exception as e:
            spider.logger.error(f"[PRODUCT] DB error: {e}")

        return item
    


class MySQLProductSnapshotPipeline:
    def __init__(self, host, user, password, db, port, charset):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db
        self.port = port
        self.charset = charset
        self.conn = None
        self.cursor = None
        # naver_product_id -> product.id 캐시
        self.product_id_cache = {}

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            host=settings.get('MYSQL_HOST'),
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWORD'),
            db=settings.get('MYSQL_DB'),
            port=settings.getint('MYSQL_PORT'),
            charset=settings.get('MYSQL_CHARSET'),
        )

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db_name,
            port=self.port,
            charset=self.charset,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        self.cursor = self.conn.cursor()
        spider.logger.info("MySQLProductSnapshotPipeline: DB 연결 완료")

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        spider.logger.info("MySQLProductSnapshotPipeline: DB 연결 종료")

    def _get_product_id_by_naver_product_id(self, naver_product_id):
        """네이버 상품 ID -> product.id 조회 (FK). 캐시 사용."""
        if not naver_product_id:
            return None

        key = str(naver_product_id)

        # 캐시 확인
        if key in self.product_id_cache:
            return self.product_id_cache[key]

        sql = "SELECT id FROM product WHERE naver_product_id = %s LIMIT 1"
        self.cursor.execute(sql, (key,))
        row = self.cursor.fetchone()
        if row:
            product_id = row['id']
            self.product_id_cache[key] = product_id
            return product_id
        return None

    def process_item(self, item, spider):
        # ProductItem만 처리
        if not isinstance(item, ProductItem):
            return item

        adapter = ItemAdapter(item)

        naver_product_id = adapter.get('naver_product_id')
        product_id = self._get_product_id_by_naver_product_id(naver_product_id)

        if not product_id:
            spider.logger.warning(
                f"[PRODUCT_SNAPSHOT] product not found for naver_product_id={naver_product_id}"
            )
            # product 테이블에 없는 상품은 스냅샷 스킵(FK 에러 방지)
            return item

        # 숫자 필드 (스파이더에서 이미 정제했다고 가정)
        original_price = adapter.get('original_price')
        discount_rate = adapter.get('discount_rate')
        price = adapter.get('price')
        delivery_fee = adapter.get('delivery_fee')
        rating = adapter.get('rating')
        review_count = adapter.get('review_count')
        ranking = adapter.get('ranking')

        sql = """
        INSERT INTO product_snapshot (
            product_id,
            snapshot_time,
            original_price,
            discount_rate,
            price,
            delivery_fee,
            rating,
            review_count,
            ranking
        )
        VALUES (
            %s,
            %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        """

        try:
            self.cursor.execute(
                sql,
                (
                    product_id,
                    spider.snapshot_time,   # ← 여기서 실행 고정 시간 사용
                    original_price,
                    discount_rate,
                    price,
                    delivery_fee,
                    rating,
                    review_count,
                    ranking,
                )
            )

        except Exception as e:
            # spider.logger.error(f"[PRODUCT_SNAPSHOT] DB error: {e}")
            pass

        return item