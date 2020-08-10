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
        driver = webdriver.Chrome(chrome_options=None)
        driver.get('https://shopping.google.com/?nord=1')
        self.driver = driver

    def __init__(self, product_name, n_reviews=10, n_pages=3):
        self.n_reviews = n_reviews
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
        list_or_grid = self.driver.find_element_by_css_selector('div#taw > div > div > div > div > a')
        if list_or_grid.get_attribute('title') == 'List':
            #click list view of results
            list_or_grid.click()
    def get_results(self):
        """Fetches list of results that have product reviews on the page"""
        results = self.driver.find_elements_by_class_name('sh-dlr__list-result')
        results_with_reviews = []
        for result in results:
            if 'product reviews' in result.text:
                results_with_reviews.append(result)
        self.results = results_with_reviews

    def get_product_info(self, result):
        pass

    def get_product_reviews(self, result):
        """Scrapes product reviews of of the first page.
        Will implement scraping on multiple pages later."""
        try:
            result.find_element_by_css_selector(' a > span:nth-of-type(2)').click()
            sleep(1)
        except:
            return None
        #click on all reviews
        self.driver.find_element_by_css_selector("section#reviews > div:nth-of-type(2) > div > a").click()
        for _ in range(math.floor(self.n_reviews/10 - 1)):
            try:
                #NOTE reviews are displayed 10 at a time, will have to click twice to display 30 reviews
                self.driver.find_element_by_css_selector("div#sh-fp__pagination-button-wrapper").click()
            except:
                print('no more review pages')
                break
            sleep(1)
        reviews = []
        review_table = self.driver.find_element_by_css_selector('div#sh-rol__reviews-cont')
        for i in range(self.n_reviews):
            translated = False
            #checks if there are more reviews
            try:
                review = review_table.find_element_by_css_selector(f'div#sh-rol__reviews-cont > div:nth-of-type({i+1})')
            except:
                print('no more reviews on this page.')
                break
            self.driver.execute_script("window.scrollTo(0, 220)")
            try:
                #checks if you can show more of the review
                review.find_element_by_css_selector('[role="button"]').click()
                sleep(.1)
            except:
                pass
            try:
                #checks if you can translate the review
                review.find_element_by_css_selector('[id*=transLink]').click()
                sleep(.1)
                translated = True
            except:
                pass
            splits = re.split("\n", review.text)
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
        self.driver.execute_script("window.history.go(-2)")
        return reviews

    def get_all_product_reviews_on_page(self):
        """Fetches reviews and product information for each product on page with reviews"""
        self.get_results()
        num_products = len(self.results)
        #Must be careful to avoid stale element reference.
        for prod in range(num_products):
            self.get_results()
            listing = self.results[prod].find_element_by_css_selector('h3').text
            price = self.results[prod].find_element_by_css_selector('span').text.split('.\n')[0]
            link = self.results[prod].find_element_by_css_selector('div .IHk3ob > a').get_attribute('href')
            reviews = self.get_product_reviews(self.results[prod])
            #extend all_reviews only if we were able to get reviews to begin with
            if reviews:
                self.all_reviews['listing'].extend([listing]*len(reviews))
                self.all_reviews['price'].extend([price]*len(reviews))
                self.all_reviews['link'].extend([link]*len(reviews))
                self.all_reviews['review'].extend(reviews)
                self.all_reviews['listing'][0]
            else:
                continue

    def get_all_pages(self):
        """Fetches all reviews on every page for page in n_pages"""
        all_reviews = defaultdict(list)
        self.all_reviews = all_reviews
        for page in range(self.n_pages):
            if page + 1  == 1:
                #do first scan
                self.get_all_product_reviews_on_page()
            else:
                try:
                #click on page n
                    self.driver.find_element_by_css_selector(f'[aria-label="Page {page+1}"]').click()
                    sleep(1)
                #do scan
                    self.get_all_product_reviews_on_page()
                except Exception as e:
                    print(e)
                    print('no more pages')
            print(f'page {page+1} is done!')
        self.all_reviews['search'] = [self.product_name]*len(self.all_reviews['listing'])
