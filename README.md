# Info More

Info More는 네이버 쇼핑 데이터를 정형화된 구조로 수집·저장하기 위한 Scrapy 기반 크롤링 프로젝트입니다.
카테고리(대/중/소) 계층 구조부터 상품 정보, 가격·평점·리뷰·랭킹 스냅샷까지 수집하여
분석 및 모니터링에 적합한 데이터베이스 구조로 적재하는 것을 목표로 합니다.

본 프로젝트는 단순 수집이 아닌, 데이터 엔지니어링 관점에서의 크롤링 파이프라인 설계에 중점을 두고 개발되었습니다.

---

## 주요 기능

* 네이버 쇼핑 카테고리 전체 수집

  * 대분류 / 중분류 / 소분류 계층 구조
* 카테고리별 상품 목록 크롤링
* 상품 정보 정규화 및 타입 검증
* MySQL 기반 데이터 저장

  * 카테고리 테이블
  * 상품 테이블
  * 상품 스냅샷 테이블
* 동일 상품 중복 수집 방지 (ON DUPLICATE KEY UPDATE)
* 실행 시점 기준 가격/평점/랭킹 스냅샷 저장
* 스케줄 기반 자동 실행 지원

---

## 수집 데이터

### 카테고리(Category)

* 네이버 카테고리 ID
* 카테고리명
* 카테고리 레벨 (대 / 중 / 소)
* 부모 카테고리 관계

### 상품(Product)

* 네이버 상품 ID
* 상품명
* 쇼핑몰명
* 가격 / 원가 / 할인율
* 배송비
* 평점 / 리뷰 수
* 랭킹
* 상세 페이지 URL
* 소속 카테고리 (FK)

### 상품 스냅샷(Product Snapshot)

* 상품 ID (FK)
* 스냅샷 시간
* 가격 / 할인율
* 배송비
* 평점 / 리뷰 수
* 랭킹

---

## 기술 스택

| 구분           | 사용 기술              |
| ------------ | ------------------ |
| Language     | Python 3           |
| Crawling     | Scrapy             |
| Parsing      | CSS Selector, JSON |
| Database     | MySQL              |
| Driver       | PyMySQL            |
| Scheduling   | schedule           |
| Architecture | Pipeline 기반 ETL 구조 |

---

## 프로젝트 구조

```text
info_more/
├─ spiders/
│  ├─ init.py
│  ├─ naver.py
│  └─ constant.py   # 요청 관련 상수 및 설정 모듈
├─ init.py
├─ items.py
├─ pipelines.py
├─ settings.py
├─ constant.py
├─ main.py
├─ middlewares.py
└─ scrapy.cfg
```

---

## 동작 흐름

1. 스케줄 또는 수동 실행으로 Spider 시작
2. 네이버 쇼핑 카테고리 API 호출
3. 대 → 중 → 소 카테고리 계층 순회
4. 각 카테고리별 상품 목록 크롤링
5. 데이터 정제 및 타입 검증
6. MySQL Pipeline을 통해 데이터 저장
7. 동일 상품은 업데이트, 가격 정보는 스냅샷으로 누적

---

## 실행 방법

### 1. 필수 패키지 설치

pip install scrapy pymysql schedule

---

### 2. MySQL 설정

settings.py에서 MySQL 접속 정보를 설정합니다.

MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = '비밀번호'
MYSQL_DB = 'naver_store'
MYSQL_CHARSET = 'utf8mb4'

---

### 3. 크롤러 실행

scrapy crawl naver

---

### 4. 스케줄 실행

python main.py

기본 설정

* 하루 4회 자동 실행 (00:00 / 06:00 / 12:00 / 18:00)

---

## 설계 특징

* 계층형 카테고리 모델링
  self-referencing 구조로 부모-자식 관계 관리
* FK 기반 데이터 무결성 유지
* 캐시 기반 ID 조회 최적화
* 스냅샷 테이블 분리
  시계열 분석 및 가격 추적 가능
* Pipeline 분리 구조
  카테고리 / 상품 / 스냅샷 독립 처리

---

## 라이선스

본 프로젝트는 개인 학습 및 기말고사 프로젝트 목적으로 제작되었습니다.
크롤링에 필요한 요청값(constant.py)은 보안상의 이유로 포함되어 있지 않아, 현재 상태에서는 실제 크롤링 기능이 동작하지 않습니다.
