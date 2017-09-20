from bs4 import BeautifulSoup
from dateutil import parser
import urllib.request
import re

domain = "https://www.nwhc.usgs.gov"
site = "https://www.nwhc.usgs.gov/disease_information/avian_influenza/index.jsp"
archive_link = domain + "/disease_information/avian_influenza/"
headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36' }

archive_report_links = []


def scrap_content(url_to_archive_page):
    further_requests = urllib.request.Request(url_to_archive_page, headers=headers)
    navigate_hrefs = urllib.request.urlopen(further_requests)
    archive_soup = BeautifulSoup(navigate_hrefs, 'html.parser')

    return archive_soup

def find_next_url(page_soup):

    report_links = page_soup.find_all("a")

    for report_link in report_links:
        if "older" in str(report_link):
            next_report_url = archive_link + str(report_link["href"])
            return next_report_url
        elif str(report_link) == str(report_links[-1]):
            #print("DONE")
            return False
        else : continue

def format_date(old_date_string):
    dt = parser.parse(old_date_string)
    new_date_string = dt.strftime("%Y-%m-%d")

    return new_date_string


#def find_section_headers(tag, content):



initial_request = urllib.request.Request(site, headers=headers)

print("Opening web page....")
index_page = urllib.request.urlopen(initial_request)

print("Parsing latest report....")
soup = BeautifulSoup(index_page, 'html.parser')

find_links = soup.find_all("a")

for link in find_links:
    if "Archive" in str(link.string) or "archive" in str(link.string):
        link_to_archives = domain + link["href"]

        latest_report_content = scrap_content(link_to_archives)

        next_report_url = find_next_url(latest_report_content)

        # Need to add code here for pulling out the HTML content from the latest report
        host_type_in_p = set()
        host_type_in_h2 = set()
        host_type_in_b = set()
        host_type_in_strong = set()
        host_type_in_br = set()

        #try:
        while True:

            page_content = scrap_content(next_report_url)
            next_report_url = find_next_url(page_content)

            report_table = page_content.find('table', id='maincontent')
            report_date = format_date(page_content.find(selected=True).string)

            p_tags = report_table.find_all('p')
            h2_tags = report_table.find_all('h2')
            td_tags = report_table.find_all('td')

            flu_subtype = re.compile('^H[0-9]N[0-9] in ')

            for td in td_tags:
                if not td.find(selected=True):
                    td_string = list( td.stripped_strings )
                    td_string = list( str.replace('\xa0', ' ') for str in td_string )
                    print(td_string)

            for h2_tag in h2_tags:
                h2_str = h2_tag.string
                if h2_str is not None:
                    if "Avian Influenza in " in h2_str:
                        host_type_in_h2.add(report_date)
                    elif re.match(flu_subtype, h2_str):
                        host_type_in_h2.add(report_date)
                    else : break


