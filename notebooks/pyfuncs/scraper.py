import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from collections import defaultdict
from time import sleep
import traceback
import math
import re

class Google_Shopping_Scraper:
    """Main scrapper for google shopping product reviews
    :params:
    product_name: query to search for
    n_reviews: number of reviews per product to include
    n_pages: number of pages to search

    :attribs:
    all_reviews: dictionary of search, link, price, listing, review arrays
    """

    def load_shopping(self):
        """Loads Google Shopping webpage on Google Chromium driver."""
        option = webdriver.ChromeOptions()
        chrome_prefs = {}
        #Disabling Images for faster script speeds
        option.experimental_options["prefs"] = chrome_prefs
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
        driver = webdriver.Chrome(chrome_options=option)
        driver.get('https://shopping.google.com/?nord=1')
        self.driver = driver
        self.driver.implicitly_wait(.05)
        if 'not found' in driver.page_source:
            self.driver.quit()
            sleep(1)
            self.load_shopping()

    def __init__(self, product_name, n_reviews=10, n_pages=3):
        self.n_reviews = n_reviews
        self.page_is_empty = False
        self.n_pages = n_pages
        self.load_shopping()
        self.product_name = product_name
        sleep(1)
        self.prod_search()
        self.get_results()

    def prod_search(self):
        """Searches for product on Google Shopping"""
        search_form = self.driver.find_element_by_css_selector('body > gx-app > div > gx-navigation-bar-ce > header > div > div:nth-of-type(2) > gx-search-bar > div > form')
        search_button = search_form.find_element_by_css_selector('div > button > span > gx-icon > svg')
        actions = ActionChains(self.driver)
        actions.click(search_form).send_keys(self.product_name).perform()
        sleep(1)
        search_button.click()
        sleep(1)
        try:
            list_or_grid = self.driver.find_element_by_css_selector('div#taw > div > div > div > div > a')
            if list_or_grid.get_attribute('title') == 'List':
                #click list view of results
                list_or_grid.click()
        except:
            pass
    def get_results(self):
        """Fetches list of results that have product reviews on the page"""
        results = self.driver.find_elements_by_class_name('sh-dlr__list-result')
        results_with_reviews = []
        for result in results:
            if 'product reviews' in result.text:
                results_with_reviews.append(result)
        self.results = results_with_reviews


    def get_product_reviews(self, result):
        """Scrapes product reviews of of the first page.
        Will implement scraping on multiple pages later."""
        try:
            result.find_element_by_css_selector('a > span:nth-of-type(2)').click()
            sleep(1)
        except:
            return None
        #click on all reviews
        try:
            self.driver.find_element_by_xpath("//*[text() = 'All Reviews']").click()

        except:
            print('could not find all reviews button')
        sleep(.5)
        for _ in range(math.floor(self.n_reviews/10 + 2)):
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(1)
                self.driver.find_element_by_xpath("//*[text() = 'More reviews']").find_element_by_xpath('..').click()
                # self.driver.find_element_by_css_selector("div.F9zmi").find_element_by_xpath('..').click()
            except:
                continue
                # print('no more review page buttons')
        review_ratings = []
        reviews = []
        # try:
        #     review_table = self.driver.find_element_by_css_selector('div#sh-rol__reviews-cont')
        # except:
        #     print('couldn"t find review table')
        review_list = self.driver.find_elements_by_xpath('//*[contains(@class, "fade-in-animate")]')
        for i in range(self.n_reviews):
            review_rating = None
            translated = False
            #checks if there are more reviews
            try:
                # review = review_table.find_element_by_css_selector(f'div#sh-rol__reviews-cont > div:nth-of-type({i+1})')
                review = review_list[i]
                actions = ActionChains(self.driver)
                actions.move_to_element(review).perform()
                sleep(.01)
            except:
                # print('couldnt find review')
                continue
            #     try:
            #         review = self.driver.find_elements_by_css_selector('div#_-jw fade-in-animate')[i+1 - 10]
            #     except:
            #         print('could not find review.')
            review_rating = review.find_element_by_css_selector("[aria-label]").get_attribute('aria-label')[0]
            # try:
            #     review_rating = review.find_element_by_css_selector('div .UzThIf').get_attribute('aria-label')[0]
            # except:
            #     try:
            #         review_rating = review.find_element_by_css_selector('div ._-mp').get_attribute('aria-label')[0]
            #     except:
            #         try:
            #             review_rating = review.find_element_by_css_selector('div ._-mq').get_attribute('aria-label')[0]
            #         except:
            #             print('could not fetch review rating')
            # self.driver.execute_script("window.scrollTo(0, 220)")
            try:
                #checks if you can show more of the review
                review.find_element_by_css_selector('[role="button"]').click()
                sleep(.01)
            except:
                pass
            try:
                #checks if you can translate the review
                review.find_element_by_css_selector('[id*=transLink]').click()
                sleep(.2)
                translated = True
            except:
                pass
            try:
                splits = re.split("\n", review.text)
            except:
                print('An error occurred in fetching review, skipping to next product page...')
                break
            review_splits = []
            cleaned_review = ''
            month_lst = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                          'August', 'September', 'October', 'November', 'December']
            for split in splits:
                if any(month in split for month in month_lst):
                    continue
                if split == '' or 'Review provided' in split or 'Show in original' in split:
                    continue
                else:
                    review_splits.append(split)
                    cleaned_review = '. '.join(review_splits)
            #prevents returning selenium driver objects in the case that months are mentioned in every comment.
            if cleaned_review == '':
                continue
            reviews.append(cleaned_review)
            review_ratings.append(review_rating)
        self.driver.execute_script("window.history.go(-2)")
        return [reviews, review_ratings]

    def get_all_product_reviews_on_page(self):
        """Fetches reviews and product information for each product on page with reviews"""
        self.get_results()
        num_products = len(self.results)
        #Must be careful to avoid stale element reference.
        for prod in range(num_products):
            self.get_results()
            try:
                listing = self.results[prod].find_element_by_css_selector('h3').text
                price = self.results[prod].find_element_by_css_selector('span').text.split('.\n')[0]
                link = self.results[prod].find_element_by_css_selector('div .IHk3ob > a').get_attribute('href')
                overall_rating = self.results[prod].find_element_by_css_selector('div .vq3ore').get_attribute('aria-label')[:3].strip()
                reviews_and_ratings = self.get_product_reviews(self.results[prod])
                reviews = reviews_and_ratings[0]
                review_ratings = reviews_and_ratings[1]
                #extend all_reviews only if we were able to get reviews to begin with
                if reviews:
                    self.all_reviews['listing'].extend([listing]*len(reviews))
                    self.all_reviews['overall_rating'].extend([overall_rating]*len(reviews))
                    self.all_reviews['price'].extend([price]*len(reviews))
                    self.all_reviews['link'].extend([link]*len(reviews))
                    self.all_reviews['review'].extend(reviews)
                    self.all_reviews['review_ratings'].extend(review_ratings)
                    self.all_reviews['listing'][0]
                else:
                    continue
            except:
                continue

    def get_all_pages(self):
        """Fetches all reviews on every page for page in n_pages"""
        all_reviews = defaultdict(list)
        self.all_reviews = all_reviews
        if not self.page_is_empty:
            for page in range(self.n_pages):
                if page + 1  == 1:
                    #do first scan
                    self.get_all_product_reviews_on_page()
                else:
                    try:
                    #click on page n
                        try:
                            self.driver.find_element_by_css_selector(f'[aria-label="Page {page+1}"]').click()
                            sleep(1)
                        except:
                            self.driver.find_elements_by_css_selector('[class="fl"]')[page-1].click()
                            sleep(1)
                    #do scan
                        self.get_all_product_reviews_on_page()
                    except Exception as e:
                        print(e)
                        print('no more pages')
                print(f'page {page+1} is done!')
                #checks if it fetched any reviews on the page, if not, reload search.
                if len(self.all_reviews) == 0:
                    self.page_is_empty = True
            self.all_reviews['search'] = [self.product_name]*len(self.all_reviews['listing'])
        else:
            print(f'retrying search for {self.product_name}')
            self.driver.quit()
            self.load_shopping()
            sleep(1)
            self.prod_search()
            self.get_results()
            self.get_all_pages()
            self.page_is_empty = False
