from bs4 import BeautifulSoup
from dateutil import parser
import urllib.request
import urllib.response
import re
import time
import http.client
import json


domain = "https://www.nwhc.usgs.gov"
site = "https://www.nwhc.usgs.gov/disease_information/avian_influenza/index.jsp"
archive_link = domain + "/disease_information/avian_influenza/"
headers = { 'User-Agent': 'Flu scraper / Contact me: Matt Diller diller17@ufl.edu', 'Accept-Encoding': 'gzip' }

flu_subtype = re.compile('^H[0-9]N[0-9] in ')


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

def format_date_for_output(old_date_string):
    '''
    Format date according to ISO's E8601DAw format (i.e., yyyy-mm-dd).
    '''

    dt = parser.parse(old_date_string)
    new_date_string = dt.strftime("%Y-%m-%d")

    return new_date_string

def format_date_for_fname(date_string):
    '''
    Format date as yyyy_mm_dd for file name.
    '''

    dt = parser.parse(date_string)
    date_string_for_fname = dt.strftime("%Y_%m_%d")

    return date_string_for_fname


def scrap_report_content(html_content, url):
    '''
    Take as input the html content; return headers and content of each report subsection, and the date and url
    of the report.
    '''

    report_table = html_content.find('table', id='maincontent')
    report_date = format_date_for_output(html_content.find(selected=True).string)

    td_tags = report_table.find_all('td')

    for td in td_tags:
        if td.find(selected=True):
            td_tags.remove(td)
        elif len(list(td.stripped_strings)) > 1:
            td_string = list(td.stripped_strings)
            td_string = list(str.replace('\xa0', ' ') for str in td_string)
            td_string = list(str.replace('?s', '\'s') for str in td_string)
            td_string = list(str.replace('?', '') for str in td_string)

            report_dict = dict()

            td_string_len = len(td_string)
            section_header_indices = list()
            count = 0

            for i in range(0, td_string_len):

                if "Avian Influenza in " in td_string[i] or re.match(flu_subtype, td_string[i]):
                    section_header_indices.append(i)
                    continue

                if not i in section_header_indices:

                    if len(td_string[i - 1]) < len(td_string[i]) and not td_string[i - 1] == "Back":
                        count += 1

                        subsection_header_label = "subsection_header_" + str(count)
                        subsection_content_label = "subsection_content_" + str(count)

                        report_dict[subsection_header_label] = td_string[i - 1]
                        report_dict[subsection_content_label] = td_string[i]
                        report_dict["report_date"] = report_date
                        report_dict["report_url"] = url

            return report_dict


if __name__ == '__main__':
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

            #reports_lst.append(scrap_report_content(latest_report_content, link_to_archives)) # Scrap specific textual information from report

            while True: # Initiate while loop for scraping all previous reports
                reports_lst = list()

                try:
                    page_content = scrap_content(next_report_url)
                    report_url = next_report_url

                except http.client.HTTPException:
                    print("Disconnected from server. Please stand by.")
                    time.sleep(30)

                else:
                    next_report_url = find_next_url(page_content)

                    reports_lst.append(scrap_report_content(page_content, report_url))

                    date_of_report = format_date_for_fname(page_content.find(selected=True).string)
                    fname = "usgs_avian_flu_report_" + date_of_report + ".json"

                    print("Writing to JSON...")

                    #with open(fname, 'w') as report_f:
                        #json.dump(reports_lst, report_f, indent="\t")

                finally:
                    if not next_report_url:
                        break

            else:
                print("Done.")