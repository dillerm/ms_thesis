from bs4 import BeautifulSoup
from dateutil import parser
import urllib.request
import json
import os
import re


url = "https://www.nwhc.usgs.gov/disease_information/avian_influenza/"
headers = { 'User-Agent': 'Flu scraper / Contact me: Matt Diller diller17@ufl.edu', 'Accept-Encoding': 'gzip' }
flu_subtype = re.compile('^H[0-9]N[0-9] in ')

# Initiate GET request, open the URL, and parse the HTML content
initial_request = urllib.request.Request(url, headers=headers)
page = urllib.request.urlopen(initial_request)
soup = BeautifulSoup(page, 'html.parser')

# Extract date of report from h3 tag
grab_header = soup.find('h3').string
extract_date = grab_header.split()[-3:]
reconstruct_date = extract_date[0] + ' ' + extract_date[1] + ' ' + extract_date[2]
dt = parser.parse(reconstruct_date)
date_of_report = dt.strftime("%Y_%m_%d") # Date to append to file name
formatted_date = dt.strftime("%Y-%m-%d") # Date that will be written to the output JSON file

# Check to see if report has already been parsed. If it hasn't, extract the information and print to JSON file
dhand = input("Please enter the name of the directory with JSON files: ")
file_path = dhand + "/usgs_avian_flu_report_" + date_of_report + ".json"

if os.path.exists(file_path):
    print("Report on " + formatted_date + " has already been parsed.")
else:
    report_table = soup.find('table', id='maincontent') # Grabs table tag with the "maincontent" id

    td_tags = report_table.find_all('td') # Grabs all the td tags that are the children of the maincontent table

    for td in td_tags:
        try:
            if td.h1.string == "Avian Influenza": # Grabs the specific td tag that has the reports
                if len(list(td.stripped_strings)) > 1: # Fixes some encoding issues / TODO replace with decode()
                    td_string = list(td.stripped_strings)
                    td_string = list(str.replace('\xa0', ' ') for str in td_string)
                    td_string = list(str.replace('?s', '\'s') for str in td_string)
                    td_string = list(str.replace('?', '') for str in td_string)

                    # Dictionary containing all of the info from the reports on the web page
                    report_dict = dict()

                    td_string_len = len(td_string)
                    section_header_indices = list()
                    count = 0

                    for i in range(0, td_string_len):
                        # Excludes headers that don't contain relevant information
                        if "Avian Influenza in " in td_string[i] or \
                                re.match(flu_subtype, td_string[i]) or \
                                td_string[i] == "Avian Influenza" or \
                                td_string[i].split()[0] == "News":
                            section_header_indices.append(i)
                            continue

                        # Grabs report headers, report text content, date of report, and URL, and stores in dictionary
                        if not i in section_header_indices:

                            if len(td_string[i - 1]) < len(td_string[i]) and not td_string[i - 1] == "Back":
                                count += 1

                                subsection_header_label = "subsection_header_" + str(count)
                                subsection_content_label = "subsection_content_" + str(count)

                                report_dict[subsection_header_label] = td_string[i - 1]
                                report_dict[subsection_content_label] = td_string[i]
                                report_dict["report_date"] = formatted_date
                                report_dict["report_url"] = url

                    print("Writing to JSON...")
                    file_name = "usgs_avian_flu_report_" + date_of_report + ".json"

                    with open(file_name, 'w') as report_f:
                        json.dump(report_dict, report_f, indent="\t")

        except AttributeError : continue # If <table> doesn't have an <h1> child, skip it
