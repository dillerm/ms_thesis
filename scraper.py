'''
Web crawler for USGS Avian Influenza website that identifies all of the HTML tags that each section header is in.
'''
import bs4
from bs4 import BeautifulSoup
from dateutil import parser
import re
import json
from collections import OrderedDict
import os
import io


flu_subtype = re.compile('^H[0-9]N[0-9]\s?[A-Za-z]*\s?(in)?\s?')
pathogenicity_subtype1 = re.compile('^[HL]PAI H[0-9]N?[0-9]? in ')
pathogenicity_subtype2 = re.compile('^[A-Za-z]+ \((([HL]PAI|possible)?\s?H[0-9]N?[0-9]?.*|.*\s?AI|.bird flu.)\)$')
pathogenicity_subtype3 = re.compile('^[A-Za-z]+ [A-Za-z]+ \((([HL]PAI|possible)?\s?H[0-9]N?[0-9]?.*|.*\s?AI)|.bird flu.\)')
punctuation = re.compile('[?.!]')
location_heading = re.compile('^\s?[A-Za-z]+?\s?[A-Za-z]+?[\.|\:]\s?$')
location = re.compile('^\w+?\s?\w+?[\.|\:]')


def format_date_for_fname(date_string):
    '''
    Format date as yyyy_mm_dd for file name.
    '''

    dt = parser.parse(date_string)
    date_string_for_fname = dt.strftime("%Y_%m_%d")

    return date_string_for_fname

def find_header(lst, regex_expression):
    for l in lst:
        if re.match(regex_expression, l):
            return True
        else:
            return False


dhand = input("Directory name: ")

empty_keys = set()
empty_dicts = set()

try:
    for f_name in os.listdir(dhand):
        if f_name == '.DS_Store' : continue
        f_name = dhand + '/' + f_name

        with open(f_name, 'rb') as f_hand:
            print("Parsing latest report....")
            soup = BeautifulSoup(f_hand, 'html.parser')

            change_filename = f_name.split('.html')
            rm_dir = change_filename[0].split('/')
            fname = 'flu_report_json/' + rm_dir[1] + '.json'

            report_table = soup.find('table', id='maincontent')

            td_tags = report_table.find_all('td')
            print("Grabbed all tags...")

            content_dct = OrderedDict()

            for td in td_tags:
                if td.find(selected=True):
                    td_tags.remove(td)
                elif len(list(td.stripped_strings)) > 1:
                    count = 1
                    td_strings = list(td.stripped_strings)

                    try:
                        td_strings.remove('Back')
                    except ValueError:
                        pass

                    for s in td_strings:
                        h = td_strings.index(s)
                        if s.endswith('('):
                            td_strings[h:h+3] = [ ''.join(td_strings[h:h+3]) ]

                    for s in td_strings:
                        i = td_strings.index(s)
                        encoded_str = s.encode().decode()

                        if (encoded_str.startswith('Avian Influenza in ') and not find_header(td_strings[i:], pathogenicity_subtype2))\
                                or re.match(flu_subtype, encoded_str) \
                                or re.match(pathogenicity_subtype1, encoded_str)\
                                or re.match(pathogenicity_subtype2, encoded_str)\
                                or re.match(pathogenicity_subtype3, encoded_str):
                            #print(encoded_str)
                            header_label = 'header_' + str(count)
                            if header_label in content_dct.keys():
                                count += 1
                                header_label = 'header_' + str(count)
                            header = encoded_str
                            content_label = 'content_' + str(count)
                            content_lst = list()
                            content = ''

                            remaining_strings = td_strings[i+1:]
                            trigger = ''

                            # If the web page contains the contents of the previous page, skip to the next page
                            for remaining_s in remaining_strings:
                                j = remaining_strings.index(remaining_s)
                                if remaining_s.startswith('News Update'):
                                    td_strings = []
                            if not td_strings : break

                            last_s = td_strings[-1]

                            # Loops over the sibling tags of the tag containing a section header
                            for remaining_s in remaining_strings:
                                j = remaining_strings.index(remaining_s)

                                if not (
                                    remaining_s.startswith('Avian Influenza in ') and not find_header(td_strings[i:],
                                                                                                  pathogenicity_subtype2)) \
                                        and not re.match(flu_subtype, remaining_s) \
                                        and not re.match(pathogenicity_subtype1, remaining_s) \
                                        and not re.match(pathogenicity_subtype2, remaining_s) \
                                        and not re.match(pathogenicity_subtype3, remaining_s):
                                    #print(remaining_s)
                                    if re.search(punctuation, remaining_s) is None \
                                            and not remaining_s.startswith('Avian Influenza in '):
                                        #print('289: '), remaining_s
                                        trigger = 'y'
                                        k = remaining_strings.index(remaining_s)

                                        header = td_strings[i] + ' in ' + remaining_s

                                        for possible_content in remaining_strings[k+1:]:
                                            if re.search(punctuation, possible_content) is not None:
                                                header_label = 'header_' + str(count)
                                                content_label = 'content_' + str(count)
                                                content = content + possible_content
                                                continue
                                            else:
                                                #print('301: ', header)
                                                content_dct[header_label] = header
                                                content_dct[content_label] = content

                                                content = ''
                                                header = ''
                                                count += 1
                                                break

                                    elif trigger == '':
                                        content_lst.append(remaining_s)
                                        content = ' '.join(content_lst)

                                    elif remaining_s == last_s:
                                        #print('315: ', header)
                                        content_dct[header_label] = header
                                        content_dct[content_label] = content
                                        print("Reached the end.")

                                else:
                                    if content == '' : break
                                    content_dct[header_label] = header
                                    content_dct[content_label] = content
                                    #print('324: ', header)

                                    content = ''
                                    header = ''
                                    count += 1
                                    break

                        elif not (encoded_str.startswith('Avian Influenza in ') and not find_header(td_strings[i:],
                                pathogenicity_subtype2)) \
                                and not re.match(flu_subtype, encoded_str) \
                                and not re.match(pathogenicity_subtype1, encoded_str) \
                                and not re.match(pathogenicity_subtype2, encoded_str) \
                                and not re.match(pathogenicity_subtype3, encoded_str):
                            header_label = 'header_' + str(count)
                            if header_label in content_dct.keys():
                                count += 1
                                header_label = 'header_' + str(count)
                            content_label = 'content_' + str(count)
                            content_lst = list()
                            content = ''

                            last_s = td_strings[-1]

                            if re.search(location_heading, encoded_str) is not None \
                                    and not encoded_str.startswith('Avian Influenza in '):
                                if trigger == 'y' : continue
                                #print(remaining_strings)
                                if remaining_s.startswith('Dr.'): continue
                                header = td_strings[i] + ' in ' + remaining_s

                                k = td_strings.index(encoded_str)

                                for possible_content in td_strings[k + 1:]:
                                    if re.search(location_heading, possible_content) is None:
                                        header_label = 'header_' + str(count)
                                        content_label = 'content_' + str(count)

                                        content = content + possible_content

                                        if possible_content == last_s:
                                            #print('364: ', header)
                                            content_dct[header_label] = header
                                            content_dct[content_label] = content
                                            print("Reached the end.")

                                        continue
                                    else:
                                        #print('371: ', header)
                                        content_dct[header_label] = header
                                        content_dct[content_label] = content

                                        content = ''
                                        header = ''
                                        count += 1
                                        break
            #print(content_dct)

            # Write parsing errors to errors.txt file
            if not content_dct:
                error_msg = 'Did not scrape content for following report: ' + f_name + '\n'
                empty_dicts.add(error_msg)

            for k,v in content_dct.items():
                if v == '':
                    error_msg = 'Empty values for following report: ' + f_name + '\n'
                    empty_keys.add(error_msg)

            # Write parsed text to JSON
            with io.open(fname, 'w', encoding='utf8') as report_f:
                json.dump(content_dct, report_f, indent="\t", ensure_ascii=False)


except UnicodeDecodeError:
    print('UnicodeDecodeError: ', f_name)

with open('errors.txt', 'a') as error_f:
    if empty_keys:
        error_f.write('------------- Reports with some content missing -------------\n\n')
        error_f.writelines(empty_keys)

    if empty_dicts:
        error_f.write('\n------------- Reports with all content missing -------------\n\n')
        error_f.writelines(empty_dicts)