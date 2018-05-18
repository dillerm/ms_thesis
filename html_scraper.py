from bs4 import BeautifulSoup
from dateutil import parser
import urllib.request
import urllib.response
import http.client
import time


def format_date_for_fname(date_string):
    '''
    Format date as yyyy_mm_dd for file name.
    '''

    dt = parser.parse(date_string)
    date_string_for_fname = dt.strftime("%Y_%m_%d")

    return date_string_for_fname

def scrap_content(url_to_archive_page):
    '''
    Send request to server, open up web page once .
    '''

    time.sleep(7)
    further_requests = urllib.request.Request(url_to_archive_page, headers=headers)
    navigate_hrefs = urllib.request.urlopen(further_requests)
    archive_soup = BeautifulSoup(navigate_hrefs, 'html.parser')

    return archive_soup

def find_next_url(page_soup):
    '''
    Grab all <a> tags, find the one with with a link to the previous report, and return that link.
    '''

    report_links = page_soup.find_all("a")

    for report_link in report_links:
        if "older" in str(report_link):
            next_report_url = archive_link + str(report_link["href"])
            return next_report_url
        elif str(report_link) == str(report_links[-1]):
            #print("DONE")
            return False
        else : continue

headers = { 'User-Agent': 'Flu scraper / Contact me: Matt Diller diller17@ufl.edu', 'Accept-Encoding': 'gzip' }
domain = "https://www.nwhc.usgs.gov"
archive_link = domain + "/disease_information/avian_influenza/"

site = input("URL for index page of Influenza Archives: ")

initial_request = urllib.request.Request(site, headers=headers)

print("Opening web page....")
index_page = urllib.request.urlopen(initial_request)

print("Parsing latest report....")
soup = BeautifulSoup(index_page, 'html.parser')

find_links = soup.find_all("a")

for link in find_links:
    if "Archive" in str(link.string) or "archive" in str(link.string): # Look for link to archive of reports
        link_to_archives = domain + link["href"]

        latest_report_content = scrap_content(link_to_archives) # Scrap HTML content of latest archived report
        next_report_url = find_next_url(latest_report_content)
        dt_latest_report = format_date_for_fname(latest_report_content.find(selected=True).string)
        f_name = 'flu_report_html/usgs_avian_flu_report_' + dt_latest_report + '.html'

        with open(f_name, 'w') as report1_f:
            report1_f.write(str(latest_report_content.prettify()))

        while True:
            try:
                page_content = scrap_content(next_report_url)
                dt = format_date_for_fname(page_content.find(selected=True).string)
                fname = 'flu_report_html/usgs_avian_flu_report_' + dt + '.html'
            except http.client.HTTPException:
                print("Disconnected from server. Please stand by.")
                time.sleep(30)
            else:
                next_report_url = find_next_url(page_content)
                with open(fname, 'w') as report_f:
                    report_f.write(str(page_content.prettify()))
                time.sleep(7)
            finally:
                if not next_report_url : break