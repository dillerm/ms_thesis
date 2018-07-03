import csv
from SPARQLWrapper import SPARQLWrapper, JSON
import re
from dateutil import parser
import time
from time import strptime
from collections import namedtuple
from collections import Counter
from Bio import Entrez
import xml.etree.ElementTree as ET


Entrez.email = 'diller17@ufl.edu'


def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)


PATH_TO_NLP_RESULTS = 'data/nlp-results/final-data.tsv' #input("Path to NLP output tsv file: ")
PATH_TO_REPORT_IDS = 'data/nlp-results/report-ids-final-data' #input("Path to report IDs file: ")
REPORT_INDEX = 1

ALL_REPORTS = list()
REPORT_DATES = list()

FLU_SUBTYPE = re.compile('H[0-9]N[0-9]')
YEAR = re.compile('[1-3][0-9][0-9][0-9]')
DAY = re.compile('\s[0-3]?[0-9]\D*')

with open(PATH_TO_NLP_RESULTS, 'r') as tsvin:
    sentence = []
    report = []
    count = 0
    rt_bracket_counter = 0

    tsvin = csv.reader(tsvin, delimiter='\t')

    for row in tsvin:
        if len(row) == 3 : row.remove(row[2])

        # When blank line is reached, append report list to ALL_REPORTS and create a new report list
        if not row or row[0] == '':
            ALL_REPORTS.append(report)
            #print('Report: ', report)
            report = []

        # Only add words tagged w/ 'Influenza', 'Location', 'Date', and 'Host_organism' tags to the sentence list
        # Also, count how many 'O'-tagged words exist between entity tags
        elif row[0] == '.' and row[1] == 'O':  # TODO change to line == \'.0\' in final version
            report.append(sentence)
            count = 0
            sentence = []

        elif row[1] == 'O' and sentence:
            count += 1

        elif row[1] == 'Influenza':
            flu_term = row[0] + '|flu'

            if count == 0 and sentence:
                try:
                    prev_ann = sentence.pop()
                    prev_term, prev_tag = prev_ann.split('|')[0], prev_ann.split('|')[1]

                    if prev_tag == 'flu':
                        if prev_term == ' -LRB-':
                            prev_term = '('
                        if prev_term == ' -RRB-':
                            prev_term = ')'

                        flu_term = '{} {}|flu'.format(prev_term, row[0])

                except IndexError : continue

            count = 0
            sentence.append(flu_term)

        elif row[1] == 'Location':
            loc_term = row[0] + '|loc'

            if count == 0 and sentence:
                try:
                    prev_ann = sentence.pop()
                    prev_term, prev_tag = prev_ann.split('|')[0], prev_ann.split('|')[1]

                    if prev_tag == 'loc':
                        if prev_term == ' -LRB-':
                            prev_term = '('
                        if prev_term == ' -RRB-':
                            prev_term = ')'

                        loc_term = '{} {}|loc'.format(prev_term, row[0])
                except IndexError : continue

            count = 0
            sentence.append(loc_term)

        elif row[1] == 'Date':
            date_term = row[0] + '|date'

            if count == 0 and sentence:
                try:
                    prev_ann = sentence.pop()
                    prev_term, prev_tag = prev_ann.split('|')[0], prev_ann.split('|')[1]

                    if prev_tag == 'date':
                        if prev_term == ' -LRB-':
                            prev_term = '('
                        if prev_term == ' -RRB-':
                            prev_term = ')'

                        date_term = '{} {}|date'.format(prev_term, row[0])
                except IndexError : continue

            count = 0
            sentence.append(date_term)

        elif row[1] == 'Host_organism':
            host_term = row[0] + '|host'

            if count == 0 and sentence:
                try:
                    prev_ann = sentence.pop()
                    prev_term, prev_tag = prev_ann.split('|')[0], prev_ann.split('|')[1]

                    if prev_tag == 'host':
                        if prev_term == ' -LRB-':
                            prev_term = '('
                        if prev_term == ' -RRB-':
                            prev_term = ')'

                        host_term = '{} {}|host'.format(prev_term, row[0])
                except IndexError : continue

            count = 0
            sentence.append(host_term)

        elif row[0] == '-RRB-' and row[1] == 'O':
            if report:
                count += 1
                continue
            else:
                rt_bracket_counter += 1
                report.append(sentence)
                count = 0
                sentence = []

with open(PATH_TO_REPORT_IDS, 'r') as fname2:
    for line in fname2:
        line = line.rstrip('\n')
        REPORT_DATES.append(line)

epidemic_lst = list()
row_number = 0

try:
    for i in range(len(ALL_REPORTS)):
        row_number += 1
        print('<-------------------- New Report -------------------->')
        report_id, report = REPORT_DATES[i], ALL_REPORTS[i]
        sentence_count = 0
        report_date = '-'.join(report_id.split('_')[:3])
        report_year = report_id.split('_')[0]
        report_month = report_id.split('_')[1]
        report_day = report_id.split('_')[2]

        report_sentences = list()
        report_entities = list()

        for s in report:
            sentence_count += 1 # This counts every sentence in the report, even if it does not contain any tagged entities

            epi_locations = set()
            epi_pathogen = set()
            epi_host = set()
            epi_date = list()
            relative_dates = list()

            sentence_elements = list()

            if s:
                for entity in s:
                    word = entity.split('|')[0]
                    tag = entity.split('|')[1]

                    if '?' in word:
                        word = word.replace('?', '\'')

                    # Parse out words tagged as influenza pathogens
                    # If word refers to a subtype, add the subtype term to the sentence's pathogen set
                    # If word refers to influenza A virus, convert to 'influenza A virus'
                    if tag == 'flu':
                        match = FLU_SUBTYPE.search(word)

                        if epi_pathogen:
                            if match is not None:
                                subtype = match.group(0) + ' subtype'
                                epi_pathogen.add(subtype)
                                continue
                            else : continue

                        if match is not None:
                            subtype = match.group(0) + ' subtype'
                            epi_pathogen.add(subtype)
                            continue
                        elif word.lower() == 'virus' \
                                or word.lower() == 'viruses' \
                                or word.lower() == 'flu':
                            continue
                        elif word.lower() == 'influenza A virus' \
                                or 'canine' in word.lower():
                            epi_pathogen.add(word)
                        elif 'swine' in word.lower():
                            epi_pathogen.add('Swine influenza virus')
                        else:
                            if word.lower() == 'bird flu' \
                                    or word.lower() == 'bird flu virus' \
                                    or word.lower() == 'bird flu viruses' \
                                    or word.lower() == 'avian influenza' \
                                    or word.lower() == 'avian influenza virus' \
                                    or word.lower() == 'avian influenza viruses' \
                                    or word.lower() == 'flu virus' \
                                    or word.lower() == 'flu viruses' \
                                    or word.lower() == 'influenza virus' \
                                    or word.lower() == 'influenza viruses' \
                                    or word.lower() == 'influenza' \
                                    or word.lower() == 'ai' \
                                    or word.lower() == 'unspecified avian influenza' \
                                    or word.lower() == 'unspecified avian influenza virus' \
                                    or word.lower() == 'unspecified avian influenza viruses':
                                epi_pathogen.add('Influenza A virus')

                    # Parse out words tagged as hosts
                    # If synonymous with 'human', add 'human' to sentence's host set
                    elif tag == 'host':
                        if word.lower() == 'man' or word.lower() == 'men' \
                                or word.lower() == 'woman' or word.lower() == 'women' \
                                or word.lower() == 'child' or word.lower() == 'children' \
                                or word.lower() == 'boy' or word.lower() == 'boys' \
                                or word.lower() == 'girl' or word.lower() == 'girls' \
                                or word.lower() == 'patient' or word.lower() == 'patients' \
                                or word.lower() == 'person' or word.lower() == 'people' \
                                or word.lower() == 'humans' \
                                or 'male' in word.lower():
                            epi_host.add('human')
                        elif word.lower() == 'poultry':
                            epi_host.add('Galliformes')
                        elif 'piglet' in word.lower():
                            epi_host.add('Sus scrofa')
                        else:
                            epi_host.add(word)

                    # Parse out words tagged as locations
                    # If term consists of two locations separated by commas (e.g., 'Gainesville, FL'), split along the...
                    #...comma into two separate locations
                    elif tag == 'loc':
                        if ',' in word:
                            split_terms = word.split(',')

                            for st in split_terms:
                                st = st.strip()

                                if st == 'UK' \
                                        or st == 'U.K' \
                                        or st == 'U.K.':
                                    st = 'United Kingdom'
                                    epi_locations.add(st)
                                elif st == 'US' \
                                        or st == 'U.S' \
                                        or st == 'U.S.' \
                                        or st == 'USA' \
                                        or st == 'U.S.A' \
                                        or st == 'U.S.A.':
                                    st = 'United States'
                                    epi_locations.add(st)
                                elif word == 'UAE' \
                                        or word == 'U.A.E' \
                                        or word == 'U.A.E.':
                                    word = 'United Arab Emirates'
                                    epi_locations.add(word)
                                elif 'Palestin' in word:
                                    word = 'State of Palestine'
                                    epi_locations.add(word)
                                else:
                                    epi_locations.add(st)
                        elif 'city' in word.lower():
                            split_terms = word.lower().split(' city')
                            epi_locations.add(split_terms[0])
                        elif 'province' in word.lower():
                            split_terms = word.lower().split(' province')
                            epi_locations.add(split_terms[0])
                        elif 'district' in word.lower():
                            split_terms = word.lower().split(' district')
                            epi_locations.add(split_terms[0])
                        else:
                            if word == 'UK' \
                                    or word == 'U.K' \
                                    or word == 'U.K.':
                                word = 'United Kingdom'
                                epi_locations.add(word)
                            elif word == 'US' \
                                    or word == 'U.S' \
                                    or word == 'U.S.' \
                                    or word == 'USA' \
                                    or word == 'U.S.A' \
                                    or word == 'U.S.A.':
                                word = 'United States'
                                epi_locations.add(word)
                            elif word == 'UAE' \
                                    or word == 'U.A.E' \
                                    or word == 'U.A.E.':
                                word = 'United Arab Emirates'
                                epi_locations.add(word)
                            elif 'Palestin' in word:
                                word = 'State of Palestine'
                                epi_locations.add(word)
                            else:
                                epi_locations.add(word)

                    # Parse out words tagged as dates, and reformat to ISO 8601 (i.e., yyyy-mm-dd)
                    elif tag == 'date':
                        if has_numbers(word):
                            check_yr = YEAR.search(word)
                            check_day = DAY.search(word)

                            # If term consists of two dates separated by 'and' (e.g., 'Jan. 8 and 9'), use first date
                            if ' and ' in word:
                                word = word.split(' and ')[0]
                                if re.match(YEAR, word) : continue
                                month = word.split(' ')[0]
                                day = word.split(' ')[1]
                                formatted_m = str(strptime(month, '%B').tm_mon)

                                if len(day) == 1:
                                    day = '0{}'.format(str(day))
                                if len(formatted_m) == 1:
                                    formatted_m = '0{}'.format(str(formatted_m))

                                formatted_d = '{}-{}-{}'.format(report_year, formatted_m, day)
                                epi_date.append(formatted_d)

                            # If term is a year, skip if different year than that of report; else, assign it the same...                             #...month as month that the report was published in, '01' as the day if report published in...                          #...first half of the month, or '15' as the day if report published in second half of the month
                            elif len(word) == 4:
                                try:
                                    yr = word
                                    if yr == report_year:
                                        if int(report_day) > 15:
                                            formatted_d = '{}-{}-15'.format(yr, report_month)
                                            epi_date.append(formatted_d)
                                        elif int(report_day) <= 15:
                                            formatted_d = '{}-{}-01'.format(yr, report_month)
                                            epi_date.append(formatted_d)
                                    elif int(yr) < int(report_year) and report_month != '01' : continue
                                except ValueError : pass

                            # If date term is in the form 'dd of month', convert to ISO 8601
                            elif ' of ' in word:
                                day = word.split(' of ')[0]
                                month = word.split(' of ')[1]

                                day_numerals = list()

                                for char in day:
                                    try:
                                        numeral = int(char)
                                        day_numerals.append(char)
                                    except ValueError : break

                                try:
                                    unformatted_d = str(strptime(month, '%B').tm_mon)
                                except ValueError : continue
                                if len(unformatted_d) == 1:
                                    unformatted_d = '0' + unformatted_d

                                formatted_d = '{}-{}-{}'.format(report_year, unformatted_d, ''.join(day_numerals))
                                epi_date.append(formatted_d)

                            # If month, day, and year are separated by '/', convert to ISO 8601; assign the year that the...
                            #...report was published in if year is missing
                            elif '/' in word:
                                day = word.split('/')[1]
                                month = word.split('/')[0]

                                if len(word.split('/')) == 3:
                                    yr = word.split('/')[2]

                                    if yr == report_year[-2:]:
                                        formatted_d = '{}-{}-{}'.format(report_year, month, day)
                                        epi_date.append(formatted_d)
                                    elif yr != report_year[-2:] and report_month != '01' : continue
                                elif len(word.split('/')) == 2:
                                    formatted_d = '{}-{}-{}'.format(report_year, month, day)
                                    epi_date.append(formatted_d)

                            # If year is missing from date, assign the term the same year the report was published in
                            elif not check_yr:
                                if not check_day:
                                    try:
                                        if report_month == '01':
                                            if word == 'Dec.' or word == 'Dec' or word == 'December':
                                                month = '12'
                                                day = '15'
                                                yr = int(report_year) - 1

                                                formatted_d = '{}-{}-{}'.format(yr, month, day)
                                                epi_date.append(formatted_d)
                                        elif int(strptime(word, '%B').tm_mon) == int(report_month):
                                            if int(report_day) > 15:
                                                formatted_d = '{}-{}-15'.format(report_year, report_month)
                                                epi_date.append(formatted_d)
                                            if int(report_day) <= 15:
                                                formatted_d = '{}-{}-01'.format(report_year, report_month)
                                                epi_date.append(formatted_d)
                                        else : continue
                                    except ValueError : continue
                                elif report_month == '01' and 'Dec' in word:
                                    month = '12'
                                    day = word.split(' ')[1]
                                    yr = int(report_year) - 1

                                    formatted_d = '{}-{}-{}'.format(yr, month, day)
                                    epi_date.append(formatted_d)
                                else:
                                    try:
                                        word = word + ', ' + report_year
                                        d = parser.parse(word)
                                        formatted_d = d.strftime('%Y-%m-%d')
                                        epi_date.append(formatted_d)
                                    except ValueError : continue

                            # If day is missing, assign '01' if report was published in the first half of the month or...
                            #...'15' if report was published in the second half of the month
                            elif not check_day:
                                if int(report_day) > 15:
                                    if check_yr:
                                        split_date = word.split(' ')
                                        new_date = split_date[0] + '15, ' + split_date[1]
                                        d = parser.parse(new_date)
                                        formatted_d = d.strftime('%Y-%m-%d')
                                        epi_date.append(formatted_d)
                                    elif not check_yr:
                                        new_date = word + '15, ' + report_year
                                        d = parser.parse(new_date)
                                        formatted_d = d.strftime('%Y-%m-%d')
                                        epi_date.append(formatted_d)
                                if int(report_day) <= 15:
                                    if check_yr:
                                        if ',' in word:
                                            word = word.replace(', ', '')

                                        split_date = word.split(' ')

                                        try:
                                            new_date = split_date[0] + '01, ' + split_date[1]
                                        except IndexError : continue
                                        d = parser.parse(new_date)
                                        formatted_d = d.strftime('%Y-%m-%d')
                                        epi_date.append(formatted_d)
                                    elif not check_yr:
                                        new_date = word + '01, ' + report_year
                                        d = parser.parse(new_date)
                                        formatted_d = d.strftime('%Y-%m-%d')
                                        epi_date.append(formatted_d)
                            # Otherwise, if date is in 'month dd, yyyy' format, convert to ISO 8601
                            else:
                                try:
                                    if ' ,' in word:
                                        word = word.replace(' ,', ',')

                                    d = parser.parse(word)
                                    formatted_d = d.strftime('%Y-%m-%d')
                                    epi_date.append(formatted_d)
                                except ValueError:
                                    continue

                        # If date term is a relative date, append to relative_dates list
                        elif not has_numbers(word):
                            relative_dates.append(word)
            else : continue

            # If a particular entity tag wasn't assigned to any words in the sentence, add 'null' value to its set or list
            if not epi_pathogen : epi_pathogen.add('null')
            if not epi_host : epi_host.add('null')
            if not epi_locations : epi_locations.add('null')
            if not epi_date : epi_date.append('null')

            epi_pathogen = list(epi_pathogen)
            epi_locations = list(epi_locations)
            epi_host = list(epi_host)

            sentence_elements.append(report_id)
            sentence_elements.append(epi_locations)
            sentence_elements.append(epi_pathogen)
            sentence_elements.append(epi_date[0])
            sentence_elements.append(epi_host)

            # Create tuple for each tagged word in a sentence where index 0 contains the locations list, index 1 contains...         #...the pathogen, index 2 contains the date, and index 3 contains the host list
            # Then, add each sentence tuple to report_sentences
            sentence_tuple = tuple(sentence_elements)
            report_sentences.append(sentence_tuple)
        #print(report_sentences)

        epi_country = ''
        country_query_term = ''
        rep_id = ''

        sentence_num = 0

        for s in report_sentences:
            sentence_num += 1
            sentence_pathogens = set()
            epi_admin_subdivisions = list()
            sentence_hosts = list()

            loc = s[1]
            date = s[3]
            host = s[4]
            len_host = len(host)

            if not rep_id:
                if s[0] != 'null':
                    rep_id += s[0]

            for h in host:
                if h == 'null' : continue

                search_handle = Entrez.esearch(db='taxonomy', term=h, retmode='xml')
                search_record = Entrez.read(search_handle)
                search_handle.close()

                if len(search_record['IdList']) > 1:
                    print('Host ID query returned multiple results: ', search_record['IdList'])

                ids = ','.join(search_record['IdList'])

                fetch_handle = Entrez.efetch(db='taxonomy', id=ids, retmode='xml', version='2.0')
                fetch_record = fetch_handle.read()

                tree = ET.fromstring(fetch_record)
                taxa = tree.findall('./Taxon')
                if not taxa:
                    print('Did not retrieve Host ID from NCBI Taxonomy for ', h)
                    continue

                scientific_name = taxa[0].find('./ScientificName').text
                tax_id = taxa[0].find('./TaxId').text
                lineage = taxa[0].find('./Lineage').text.split('; ')

                # If multiple hosts identified in a sentence:
                #   1) Check if the ones that have already been processed are part of the current host's lineage
                #   2) Check if the current host is part of the lineages of any hosts that have been processed
                #   3) Check if the current host is a duplicate

                if len_host > 1:
                    if sentence_hosts:
                        for sh in sentence_hosts:
                            if sh[0] in lineage:
                                sentence_hosts.remove(sh)
                            elif scientific_name in sh[2] : continue
                            elif scientific_name == sh[0] : continue

                host_tuple = (scientific_name, tax_id, lineage)
                sentence_hosts.append(host_tuple)
                time.sleep(1)

            if s[2]:
                for p in s[2]:
                    if p == 'null' : continue

                    search_handle = Entrez.esearch(db='taxonomy', term=p, retmode='xml')
                    search_record = Entrez.read(search_handle)
                    search_handle.close()

                    if len(search_record['IdList']) > 1:
                        print('Host ID query returned multiple results: ', search_record['IdList'])

                    ids = ','.join(search_record['IdList'])

                    fetch_handle = Entrez.efetch(db='taxonomy', id=ids, retmode='xml', version='2.0')
                    fetch_record = fetch_handle.read()

                    tree = ET.fromstring(fetch_record)
                    taxa = tree.findall('./Taxon')
                    if not taxa: continue

                    scientific_name = taxa[0].find('./ScientificName').text
                    tax_id = taxa[0].find('./TaxId').text

                    pathogen_tuple = (scientific_name, tax_id)
                    sentence_pathogens.add(pathogen_tuple)
                    time.sleep(1)

            if loc:
                len_loc = len(loc)
                loc_count = 0

                for l_name in loc:
                    loc_count += 1
                    location_entities = list()

                    if count == len_loc : continue
                    if l_name == 'null' : continue
                    if l_name == '' : continue
                    if l_name == country_query_term:
                        loc.remove(l_name)
                        continue
                    query_term = l_name.lower()
                    print("Query term: ", query_term)


                    sparql = SPARQLWrapper('https://query.wikidata.org/sparql')

                    if not epi_country:
                        country_query = '''
                        SELECT ?item ?itemLabel
                        WHERE
                        {{
                        ?item wdt:P31 wd:Q6256 .
                        ?item rdfs:label ?itemLabel .
                        FILTER(CONTAINS(LCASE((?itemLabel)), "{}"@en))
                        }}
                        '''.format(query_term)

                        sparql.setQuery(country_query)
                        sparql.setReturnFormat(JSON)
                        results = sparql.query().convert()

                        if results["results"]["bindings"]:
                            for result in results["results"]["bindings"]:
                                if result["itemLabel"]["xml:lang"] == "en":
                                    epi_country += result["itemLabel"]["value"]
                                    country_query_term += l_name

                                    time.sleep(2)

                        else:
                            if l_name == 'null': continue
                            print('{} did not return a country label in Wikidata. Searching as admin subdivision level 1....'.format(query_term))

                            admin_subdivision_1_query = '''
                            SELECT DISTINCT ?item ?itemLabel ?countryLabel ?country
                            WHERE {{
                              {{
                              ?item wdt:P31 ?adminEntity1 .
                              ?adminEntity1 wdt:P279 wd:Q10864048 .
                              ?item rdfs:label ?itemLabel .
                              FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                              FILTER(langMatches(lang(?itemLabel), "EN")) .
                              ?item wdt:P17 ?country .
                              ?country rdfs:label ?countryLabel .
                              FILTER(langMatches(lang(?countryLabel), "EN"))
                            }}
                            UNION
                            {{
                              ?item wdt:P31 ?adminEntity1 .
                              ?adminEntity1 wdt:P279 ?adminEntity2 .
                              ?adminEntity2 wdt:P279 wd:Q10864048 .
                              ?item rdfs:label ?itemLabel .
                              FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                              FILTER(langMatches(lang(?itemLabel), "EN")) .
                              ?item wdt:P17 ?country .
                              ?country rdfs:label ?countryLabel .
                              FILTER(langMatches(lang(?countryLabel), "EN"))
                            }}
                            }}
                            LIMIT 1
                            '''.format(query_term, query_term)

                            sparql.setQuery(admin_subdivision_1_query)
                            sparql.setReturnFormat(JSON)
                            results = sparql.query().convert()

                            if results["results"]["bindings"]:
                                for result in results["results"]["bindings"]:
                                    country = result['countryLabel']['value']
                                    country_iri = result['country']['value']
                                    location = result['itemLabel']['value']
                                    location_iri = result['item']['value']

                                    admin1_tuple = namedtuple('admin1_tuple', 'location, location_iri, country, country_iri')
                                    t = admin1_tuple(
                                                     location=location,
                                                     location_iri=location_iri,
                                                     country=country,
                                                     country_iri=country_iri
                                                     )

                                    epi_admin_subdivisions.append(t)
                                    time.sleep(2)
                            else:
                                if l_name == 'null' : continue
                                print(
                                    '{} did not return an admin subdivision level 1 label in Wikidata. Searching as admin subdivision level 2....'.format(query_term))

                                admin_subdivision_2_query = '''
                                SELECT DISTINCT ?item ?itemLabel ?country ?countryLabel ?locatedIn ?locatedInLabel
                                WHERE {{
                                  {{
                                  ?item wdt:P31 ?adminEntity1 .
                                  ?adminEntity1 wdt:P279 ?adminEntity2 .
                                  ?adminEntity2 wdt:P279 wd:Q13220204 .
                                  ?item rdfs:label ?itemLabel .
                                  FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                  FILTER(langMatches(lang(?itemLabel), "EN")) .
                                  ?item wdt:P17 ?country .
                                  ?country rdfs:label ?countryLabel .
                                  FILTER(langMatches(lang(?countryLabel), "EN"))
                                  ?item wdt:P131 ?locatedIn .
                                  ?locatedIn rdfs:label ?locatedInLabel .
                                  FILTER(langMatches(lang(?locatedInLabel), "EN"))
                                }}
                                UNION
                                {{
                                  ?item wdt:P31 ?adminEntity1 .
                                  ?adminEntity1 wdt:P279 wd:Q13220204 .
                                  ?item rdfs:label ?itemLabel .
                                  FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                  FILTER(langMatches(lang(?itemLabel), "EN")) .
                                  ?item wdt:P17 ?country .
                                  ?country rdfs:label ?countryLabel .
                                  FILTER(langMatches(lang(?countryLabel), "EN"))
                                  ?item wdt:P131 ?locatedIn .
                                  ?locatedIn rdfs:label ?locatedInLabel .
                                  FILTER(langMatches(lang(?locatedInLabel), "EN"))
                                }}
                                }}
                                LIMIT 1
                                '''.format(query_term, query_term)

                                sparql.setQuery(admin_subdivision_2_query)
                                sparql.setReturnFormat(JSON)
                                results = sparql.query().convert()

                                if results["results"]["bindings"]:
                                    for result in results["results"]["bindings"]:
                                        sentence_label = 'admin2-{}-{}'.format(sentence_num, loc_count)
                                        country = result['countryLabel']['value']
                                        country_iri = result['country']['value']
                                        location = result['itemLabel']['value']
                                        location_iri = result['item']['value']
                                        located_in = result['locatedInLabel']['value']
                                        located_in_iri = result['locatedIn']['value']

                                        admin2_tuple = namedtuple('admin2_tuple',
                                                                  'location, location_iri, country, country_iri, located_in, located_in_iri')
                                        t = admin2_tuple(
                                            location=location,
                                            location_iri=location_iri,
                                            country=country,
                                            country_iri=country_iri,
                                            located_in=located_in,
                                            located_in_iri=located_in_iri
                                        )

                                        epi_admin_subdivisions.append(t)
                                        time.sleep(2)

                                else:
                                    print('{} did not return an admin level 2 label in Wikidata. Searching as district....'.format(query_term))

                                    district_query = '''
                                    SELECT DISTINCT ?item ?itemLabel ?locatedIn ?locatedInLabel ?country ?countryLabel
                                    WHERE {{
                                    {{
                                        ?item wdt:P31 wd:Q149621 .
                                        ?item rdfs:label ?itemLabel .
                                        FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?itemLabel), "EN")) .
                                        ?item wdt:P131 ?locatedIn .
                                        ?locatedIn rdfs:label ?locatedInLabel .
                                        FILTER(langMatches(lang(?locatedInLabel), "EN")) .
                                        ?item wdt:P17 ?country .
                                        ?country rdfs:label ?countryLabel .
                                        FILTER(langMatches(lang(?countryLabel), "EN"))
                                    }}
                                    UNION
                                    {{
                                        ?item wdt:P31 ?adminEntity1 .
                                        ?adminEntity1 wdt:P279 wd:Q149261 .
                                        ?item rdfs:label ?itemLabel .
                                        FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?itemLabel), "EN")) .
                                        ?item wdt:P131 ?locatedIn .
                                        ?locatedIn rdfs:label ?locatedInLabel .
                                        FILTER(langMatches(lang(?locatedInLabel), "EN")) .
                                        ?item wdt:P17 ?country .
                                        ?country rdfs:label ?countryLabel .
                                        FILTER(langMatches(lang(?countryLabel), "EN"))
                                        }}
                                    }}
                                    LIMIT 1
                                    '''.format(query_term, query_term)

                                    sparql.setQuery(district_query)
                                    sparql.setReturnFormat(JSON)
                                    results = sparql.query().convert()

                                    if results["results"]["bindings"]:
                                        for result in results["results"]["bindings"]:
                                            sentence_label = 'district-{}-{}'.format(sentence_num, loc_count)
                                            country = result['countryLabel']['value']
                                            country_iri = result['country']['value']
                                            location = result['itemLabel']['value']
                                            location_iri = result['item']['value']
                                            located_in = result['locatedInLabel']['value']
                                            located_in_iri = result['locatedIn']['value']

                                            district_tuple = namedtuple('district_tuple',
                                                                        'location, location_iri, country, country_iri, located_in, located_in_iri')

                                            t = district_tuple(
                                                location=location,
                                                location_iri=location_iri,
                                                country=country,
                                                country_iri=country_iri,
                                                located_in=located_in,
                                                located_in_iri=located_in_iri
                                            )

                                            epi_admin_subdivisions.append(t)
                                            time.sleep(2)

                                    else:
                                        print('{} did not return district label in Wikidata. Searching as city....'.format(query_term))

                                        city_query = '''
                                        SELECT DISTINCT ?item ?itemLabel ?country ?countryLabel
                                        WHERE {{
                                          {{
                                            ?item wdt:P31 wd:Q515 .
                                            ?item rdfs:label ?itemLabel .
                                            FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                            FILTER(langMatches(lang(?itemLabel), "EN")) .
                                            ?item wdt:P131 ?adminEntity1 .
                                            ?item wdt:P17 ?country .
                                            ?country rdfs:label ?countryLabel .
                                            FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                                            FILTER(langMatches(lang(?countryLabel), "EN"))
                                        }}
                                          UNION
                                          {{
                                            ?item wdt:P31 wd:Q1093829 .
                                            ?item rdfs:label ?itemLabel .
                                            FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                            FILTER(langMatches(lang(?itemLabel), "EN")) .
                                            ?item wdt:P131 ?adminEntity1 .
                                            ?item wdt:P17 ?country .
                                            ?country rdfs:label ?countryLabel .
                                            FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                                            FILTER(langMatches(lang(?countryLabel), "EN"))
                                            }}
                                          }}
                                        '''.format(query_term, epi_country.lower(),
                                                   query_term, epi_country.lower())

                                        sparql.setQuery(district_query)
                                        sparql.setReturnFormat(JSON)
                                        results = sparql.query().convert()

                                        if results["results"]["bindings"]:
                                            for result in results["results"]["bindings"]:
                                                sentence_label = 'district-{}-{}'.format(sentence_num, loc_count)
                                                country = result['countryLabel']['value']
                                                country_iri = result['country']['value']
                                                location = result['itemLabel']['value']
                                                location_iri = result['item']['value']
                                                located_in = result['locatedInLabel']['value']
                                                located_in_iri = result['locatedIn']['value']

                                                city_tuple = namedtuple('city_tuple',
                                                                        'location, location_iri, country, country_iri, located_in, located_in_iri')

                                                t = city_tuple(
                                                    location=location,
                                                    location_iri=location_iri,
                                                    country=country,
                                                    country_iri=country_iri,
                                                    located_in=located_in,
                                                    located_in_iri=located_in_iri
                                                )

                                                epi_admin_subdivisions.append(t)
                                                time.sleep(2)

                    elif epi_country:
                        if l_name == 'null': continue
                        print(
                            '{} did not return a country label in Wikidata. Searching as admin subdivision level 1....'.format(query_term))

                        admin_subdivision_1_query = '''
                        SELECT DISTINCT ?item ?itemLabel ?country ?countryLabel
                        WHERE {{
                          {{
                          ?item wdt:P31 ?adminEntity1 .
                          ?adminEntity1 wdt:P279 wd:Q10864048 .
                          ?item rdfs:label ?itemLabel .
                          FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                          FILTER(langMatches(lang(?itemLabel), "EN")) .
                          ?item wdt:P17 ?country .
                          ?country rdfs:label ?countryLabel .
                          FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                          FILTER(langMatches(lang(?countryLabel), "EN"))
                        }}
                        UNION
                        {{
                          ?item wdt:P31 ?adminEntity1 .
                          ?adminEntity1 wdt:P279 ?adminEntity2 .
                          ?adminEntity2 wdt:P279 wd:Q10864048 .
                          ?item rdfs:label ?itemLabel .
                          FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                          FILTER(langMatches(lang(?itemLabel), "EN")) .
                          ?item wdt:P17 ?country .
                          ?country rdfs:label ?countryLabel .
                          FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                          FILTER(langMatches(lang(?countryLabel), "EN"))
                        }}
                        }}
                        LIMIT 1
                        '''.format(query_term, epi_country.lower(), query_term, epi_country.lower())

                        sparql.setQuery(admin_subdivision_1_query)
                        sparql.setReturnFormat(JSON)
                        results = sparql.query().convert()

                        if results["results"]["bindings"]:
                            for result in results["results"]["bindings"]:
                                sentence_label = 'admin1-{}-{}'.format(sentence_num, loc_count)
                                country = result['countryLabel']['value']
                                country_iri = result['country']['value']
                                location = result['itemLabel']['value']
                                location_iri = result['item']['value']

                                admin1_tuple = namedtuple('admin1_tuple',
                                                          'location, location_iri, country, country_iri')

                                t = admin1_tuple(
                                    location=location,
                                    location_iri=location_iri,
                                    country=country,
                                    country_iri=country_iri
                                )

                                epi_admin_subdivisions.append(t)
                                time.sleep(2)
                        else:
                            print('{} did not return an admin subdivision level 1 label in Wikidata. Searching as admin subdivision level 2....'.format(query_term))

                            admin_subdivision_2_query = '''
                            SELECT DISTINCT ?item ?itemLabel ?itemType ?country ?countryLabel ?locatedIn ?locatedInLabel
                            WHERE {{
                              {{
                              ?item wdt:P31 ?adminEntity1 .
                              ?adminEntity1 wdt:P279 ?adminEntity2 .
                              ?adminEntity2 wdt:P279 wd:Q13220204 .
                              ?item rdfs:label ?itemLabel .
                              FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                              ?item wdt:P17 ?country .
                              ?country rdfs:label ?countryLabel .
                              FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                              FILTER(langMatches(lang(?countryLabel), "EN")) .
                              ?item wdt:P131 ?locatedIn .
                              ?locatedIn rdfs:label ?locatedInLabel .
                              FILTER(langMatches(lang(?locatedInLabel), "EN"))
                            }}
                            UNION
                            {{
                              ?item wdt:P31 ?adminEntity1 .
                              ?adminEntity1 wdt:P279 wd:Q13220204 .
                              ?item rdfs:label ?itemLabel .
                              FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                              ?item wdt:P17 ?country .
                              ?country rdfs:label ?countryLabel .
                              FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                              FILTER(langMatches(lang(?countryLabel), "EN")) .
                              ?item wdt:P131 ?locatedIn .
                              ?locatedIn rdfs:label ?locatedInLabel .
                              FILTER(langMatches(lang(?locatedInLabel), "EN"))
                            }}
                            }}
                            LIMIT 1
                            '''.format(query_term, epi_country.lower(), query_term, epi_country.lower())

                            sparql.setQuery(admin_subdivision_2_query)
                            sparql.setReturnFormat(JSON)
                            results = sparql.query().convert()

                            if results["results"]["bindings"]:
                                for result in results["results"]["bindings"]:
                                    sentence_label = 'admin2-{}-{}'.format(sentence_num, loc_count)
                                    country = result['countryLabel']['value']
                                    country_iri = result['country']['value']
                                    location = result['itemLabel']['value']
                                    location_iri = result['item']['value']
                                    located_in = result['locatedInLabel']['value']
                                    located_in_iri = result['locatedIn']['value']

                                    admin2_tuple = namedtuple('admin2_tuple',
                                                              'location, location_iri, country, country_iri, located_in, located_in_iri')

                                    t = admin2_tuple(
                                        location=location,
                                        location_iri=location_iri,
                                        country=country,
                                        country_iri=country_iri,
                                        located_in=located_in,
                                        located_in_iri=located_in_iri
                                    )

                                    epi_admin_subdivisions.append(t)
                                    time.sleep(2)

                            else:
                                print(
                                    '{} did not return an admin level 2 label in Wikidata. Searching as district....'.format(query_term))

                                district_query='''
                                SELECT DISTINCT ?item ?itemLabel ?locatedIn ?locatedInLabel ?country ?countryLabel
                                WHERE {{
                                {{
                                    ?item wdt:P31 wd:Q149621 .
                                    ?item rdfs:label ?itemLabel .
                                    FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                    FILTER(langMatches(lang(?itemLabel), "EN")) .
                                    ?item wdt:P131 ?locatedIn .
                                    ?locatedIn rdfs:label ?locatedInLabel .
                                    FILTER(langMatches(lang(?locatedInLabel), "EN")) .
                                    ?item wdt:P17 ?country .
                                    ?country rdfs:label ?countryLabel .
                                    FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                                    FILTER(langMatches(lang(?countryLabel), "EN"))
                                }}
                                UNION
                                    {{
                                        ?item wdt:P31 ?adminEntity1 .
                                        ?adminEntity1 wdt:P279 wd:Q149261 .
                                        ?item rdfs:label ?itemLabel .
                                        FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?itemLabel), "EN")) .
                                        ?item wdt:P131 ?locatedIn .
                                        ?locatedIn rdfs:label ?locatedInLabel .
                                        FILTER(langMatches(lang(?locatedInLabel), "EN")) .
                                        ?item wdt:P17 ?country .
                                        ?country rdfs:label ?countryLabel .
                                        FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?countryLabel), "EN"))
                                    }}
                                }}
                                LIMIT 1
                                '''.format(query_term, epi_country.lower(), query_term, epi_country.lower())

                                sparql.setQuery(district_query)
                                sparql.setReturnFormat(JSON)
                                results = sparql.query().convert()

                                if results["results"]["bindings"]:
                                    for result in results["results"]["bindings"]:
                                        sentence_label = 'district-{}-{}'.format(sentence_num, loc_count)
                                        country = result['countryLabel']['value']
                                        country_iri = result['country']['value']
                                        location = result['itemLabel']['value']
                                        location_iri = result['item']['value']
                                        located_in = result['locatedInLabel']['value']
                                        located_in_iri = result['locatedIn']['value']

                                        district_tuple = namedtuple('district_tuple',
                                                                  'location, location_iri, country, country_iri, located_in, located_in_iri')

                                        t = district_tuple(
                                            location=location,
                                            location_iri=location_iri,
                                            country=country,
                                            country_iri=country_iri,
                                            located_in=located_in,
                                            located_in_iri=located_in_iri
                                        )

                                        epi_admin_subdivisions.append(t)
                                        time.sleep(2)

                                else:
                                    print('{} did not return a admin level 2 label in Wikidata. Searching as district....'.format(query_term))

                                    city_query = '''
                                    SELECT DISTINCT ?item ?itemLabel ?country ?countryLabel
                                    WHERE {{
                                      {{
                                        ?item wdt:P31 wd:Q515 .
                                        ?item rdfs:label ?itemLabel .
                                        FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?itemLabel), "EN")) .
                                        ?item wdt:P131 ?adminEntity1 .
                                        ?item wdt:P17 ?country .
                                        ?country rdfs:label ?countryLabel .
                                        FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?countryLabel), "EN"))
                                    }}
                                      UNION
                                      {{
                                        ?item wdt:P31 wd:Q1093829 .
                                        ?item rdfs:label ?itemLabel .
                                        FILTER(CONTAINS(LCASE(?itemLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?itemLabel), "EN")) .
                                        ?item wdt:P131 ?adminEntity1 .
                                        ?item wdt:P17 ?country .
                                        ?country rdfs:label ?countryLabel .
                                        FILTER(CONTAINS(LCASE(?countryLabel), "{}"@en)) .
                                        FILTER(langMatches(lang(?countryLabel), "EN"))
                                        }}
                                      }}
                                    '''.format(query_term, epi_country.lower(), query_term, epi_country.lower())

                                    sparql.setQuery(district_query)
                                    sparql.setReturnFormat(JSON)
                                    results = sparql.query().convert()

                                    if results["results"]["bindings"]:
                                        for result in results["results"]["bindings"]:
                                            sentence_label = 'district-{}-{}'.format(sentence_num, loc_count)
                                            country = result['countryLabel']['value']
                                            country_iri = result['country']['value']
                                            location = result['itemLabel']['value']
                                            location_iri = result['item']['value']
                                            located_in = result['locatedInLabel']['value']
                                            located_in_iri = result['locatedIn']['value']

                                            city_tuple = namedtuple('city_tuple',
                                                                        'location, location_iri, country, country_iri, located_in, located_in_iri')

                                            t = city_tuple(
                                                location=location,
                                                location_iri=location_iri,
                                                country=country,
                                                country_iri=country_iri,
                                                located_in=located_in,
                                                located_in_iri=located_in_iri
                                            )

                                            epi_admin_subdivisions.append(t)
                                            time.sleep(2)

            sentence_entities_for_triples = list()

            sentence_entities_for_triples.append(epi_admin_subdivisions)
            sentence_entities_for_triples.append(sentence_pathogens)
            sentence_entities_for_triples.append(date)
            sentence_entities_for_triples.append(sentence_hosts)

            report_entities.append(sentence_entities_for_triples)

        report_entities.append(rep_id)
        #print(report_entities)

        # Start unpacking report_entities and connecting each entity to one another

        country_lst = list()
        nonsubtype_lst = list()
        subtype_lst = list()

        # Determine which country, pathogen, and date to assign to the report

        report_country_iri = ''
        report_country_label = ''
        report_pathogen_iri = ''
        report_pathogen_label = ''
        report_dates = list()

        for sentence_entities in report_entities:
            if sentence_entities == report_entities[-1] : continue

            if sentence_entities[1]:
                for pathogen_tup in sentence_entities[1]:
                    pathogen_label = pathogen_tup[0]
                    pathogen_id = pathogen_tup[1]

                    subtype_match = FLU_SUBTYPE.search(pathogen_label)

                    if subtype_match is not None:
                        subtype_lst.append('{}|{}'.format(pathogen_id, pathogen_label))
                    else:
                        nonsubtype_lst.append('{}|{}'.format(pathogen_id, pathogen_label))
            if sentence_entities[0]:
                for location_tup in sentence_entities[0]:
                    country_label = location_tup.country
                    country_iri = location_tup.country_iri

                    country_lst.append('{}|{}'.format(country_iri, country_label))
            if sentence_entities[2] and sentence_entities[2] != 'null':
                report_dates.append(sentence_entities[2])

        if country_lst:
            if len(country_lst) > 2:
                c1 = Counter(country_lst).most_common(1)
                iri = c1[0][0].split('|')[0]
                label = c1[0][0].split('|')[1]

                report_country_iri += iri
                report_country_label += label
            else:
                iri = country_lst[0].split('|')[0]
                label = country_lst[0].split('|')[1]

                report_country_iri += iri
                report_country_label += label
        else:
            if epi_country:
                report_country_label += epi_country
            print('No countries identified for ', report_id)
            continue

        if subtype_lst:
            if len(subtype_lst) > 2:
                c2 = Counter(subtype_lst).most_common(1)
                iri = c2[0][0].split('|')[0]
                label = c2[0][0].split('|')[1]

                report_pathogen_iri += iri
                report_pathogen_label += label
            else:
                iri = subtype_lst[0].split('|')[0]
                label = subtype_lst[0].split('|')[1]

                report_pathogen_iri += iri
                report_pathogen_label += label
        elif nonsubtype_lst:
            if len(nonsubtype_lst) > 2:
                c3 = Counter(nonsubtype_lst).most_common(1)
                iri = c3[0][0].split('|')[0]
                label = c3[0][0].split('|')[1]

                report_pathogen_iri += iri
                report_pathogen_label += label
            else:
                iri = nonsubtype_lst[0].split('|')[0]
                label = nonsubtype_lst[0].split('|')[1]

                report_pathogen_iri += iri
                report_pathogen_label += label
        else:
            report_pathogen_iri += '11320'
            report_pathogen_label += 'Influenza A virus'

        # For each lower-level administrative entity, check to see if they share a 'part-of' relationship with
        # any of the upper-level administrative entities that were tagged in the sentence. If they do, remove
        # that upper-level administrative entity from its respective list (i.e., admin1_tuples_lst,
        # admin2_tuples_lst, or district_tuples_lst).

        epidemic_entities = list()

        for sentence_entities in report_entities:
            #print(sentence_entities)
            no_locations_and_hosts_count = 0
            no_host = list()

            if sentence_entities == report_entities[-1] : continue
            if not sentence_entities[0] and not sentence_entities[3]:
                no_locations_and_hosts_count += 1
                if no_locations_and_hosts_count == len(report_entities):
                    print('No locations and hosts found for {}'.format(rep_id))
                continue

            if not sentence_entities[0] and sentence_entities[3]:
                if not no_host and epidemic_lst:
                    prev_epidemic_entities = epidemic_lst.pop()

                    for host_organism in sentence_entities[3]:
                        if host_organism[0] in prev_epidemic_entities[5] : continue
                        else:
                            previous_hosts = prev_epidemic_entities.pop().split('; ')
                            previous_hosts.append(host_organism[0])
                            prev_epidemic_entities.append('; '.join(previous_hosts))

                    epidemic_lst.append(prev_epidemic_entities)
                if no_host:
                    for host_organism in sentence_entities[3]:
                        no_host[5].append(host_organism[0])

                    print(no_host)
                    epidemic_lst.append(no_host)

            if not sentence_entities[0] and report_country_label:
                country_tuple = namedtuple('country_tuple', 'location, country')

                t = country_tuple(location=report_country_label, country=report_country_label)

                sentence_entities[0].append(t)

            if sentence_entities[0]:
                admin1_tuples_lst = [admin1_tup for admin1_tup in sentence_entities[0] if
                                     type(admin1_tup).__name__ == 'admin1_tuple']
                admin2_tuples_lst = [admin2_tup for admin2_tup in sentence_entities[0] if
                                     type(admin2_tup).__name__ == 'admin2_tuple']
                district_tuples_lst = [district_tup for district_tup in sentence_entities[0] if
                                       type(district_tup).__name__ == 'district_tuple']
                city_tuples_lst = [city_tup for city_tup in sentence_entities[0] if type(city_tup).__name__ == 'city_tuple']
                country_tuples_lst = [ country_tup for country_tup in sentence_entities[0] if type(country_tup).__name__ == 'country_tuple' ]

                if country_tuples_lst:
                    for country_tup in country_tuples_lst:
                        location_label = country_tup.location

                        # Add report identifier to index 0 of epidemic_entities

                        epidemic_entities.append(rep_id)

                        # Add epidemic date to index 1 of epidemic_entities

                        if sentence_entities[2] and sentence_entities[2] != 'null':
                            epidemic_entities.append(sentence_entities[2])
                        elif report_dates:
                            probable_date = report_dates.pop(0)
                            epidemic_entities.append(probable_date)
                        else:
                            split_rep_id = rep_id.split('_')
                            est_epi_date = '{}-{}-{}'.format(split_rep_id[0], split_rep_id[1], split_rep_id[2])
                            epidemic_entities.append(est_epi_date)

                        # Add influenza pathogen to index 2 of epidemic_entities

                        epidemic_entities.append(report_pathogen_label)

                        # Add location to index 3 and country to index 4 of epidemic_entities

                        country_location = '{} (country)'.format(location_label)
                        epidemic_entities.append(country_location)
                        epidemic_entities.append(report_country_label)

                        # Add host(s) to index 5 of epidemic_entities

                        hosts = list()

                        if sentence_entities[3]:
                            for host_organism in sentence_entities[3]:
                                hosts.append(host_organism[0])
                            epidemic_entities.append('; '.join(hosts))
                            epidemic_lst.append(epidemic_entities)
                            epidemic_entities = []
                        else:
                            epidemic_entities.append(hosts)
                            no_host.append(epidemic_entities)
                            epidemic_entities = []

                if city_tuples_lst:
                    for city_tup in city_tuples_lst:
                        c_location_label = city_tup.location
                        c_location_iri = city_tup.location_iri
                        c_located_in = city_tup.located_in
                        c_located_in_iri = city_tup.located_in_iri

                        if admin1_tuples_lst:
                            for admin1_t in admin1_tuples_lst:
                                a1_location_iri = admin1_t.location_iri
                                if c_located_in_iri == a1_location_iri:
                                    admin1_tuples_lst.remove(admin1_t)

                        if admin2_tuples_lst:
                            for admin2_t in admin2_tuples_lst:
                                a2_location_iri = admin2_t.location_iri
                                if c_located_in_iri == a2_location_iri:
                                    #print('Line 1285')
                                    admin2_tuples_lst.remove(admin2_t)

                        if district_tuples_lst:
                            for district_t in district_tuples_lst:
                                d_location_iri = district_t.location_iri
                                if c_located_in_iri == d_location_iri:
                                    #print('Line 1292')
                                    district_tuples_lst.remove(district_t)

                        # Add report identifier to index 0 of epidemic_entities

                        epidemic_entities.append(rep_id)

                        # Add epidemic date to index 1 of epidemic_entities

                        if sentence_entities[2] and sentence_entities[2] != 'null':
                            epidemic_entities.append(sentence_entities[2])
                        elif report_dates:
                            probable_date = report_dates.pop(0)
                            epidemic_entities.append(probable_date)
                        else:
                            split_rep_id = rep_id.split('_')
                            est_epi_date = '{}-{}-{}'.format(split_rep_id[0], split_rep_id[1], split_rep_id[2])
                            epidemic_entities.append(est_epi_date)

                        # Add influenza pathogen to index 2 of epidemic_entities

                        epidemic_entities.append(report_pathogen_label)

                        # Add location to index 3 and country to index 4 of epidemic_entities

                        if c_located_in != report_country_label:
                            city_location = '{} (city); {} (admin level 1)'.format(c_location_label, c_located_in)
                            epidemic_entities.append(city_location)
                            epidemic_entities.append(report_country_label)
                        else:
                            city_location = '{} (city)'.format(c_location_label)
                            epidemic_entities.append(city_location)
                            epidemic_entities.append(report_country_label)

                        # Add host(s) to index 5 of epidemic_entities

                        hosts = list()

                        if sentence_entities[3]:
                            for host_organism in sentence_entities[3]:
                                hosts.append(host_organism[0])
                            epidemic_entities.append('; '.join(hosts))
                            epidemic_lst.append(epidemic_entities)
                            print('1386', epidemic_entities)
                            epidemic_entities = []
                        else:
                            epidemic_entities.append(hosts)
                            no_host.append(epidemic_entities)
                            epidemic_entities = []

                if district_tuples_lst:
                    for district_tup in district_tuples_lst:
                        d_location_label = district_tup.location
                        d_location_iri = district_tup.location_iri
                        d_located_in = district_tup.located_in
                        d_located_in_iri = district_tup.located_in_iri

                        if admin1_tuples_lst:
                            for admin1_t in admin1_tuples_lst:
                                a1_location_iri = admin1_t.location_iri
                                if d_located_in_iri == a1_location_iri:
                                    #print('Line 1308')
                                    admin1_tuples_lst.remove(admin1_t)

                        if admin2_tuples_lst:
                            for admin2_t in admin2_tuples_lst:
                                a2_location_iri = admin2_t.location_iri
                                if d_located_in_iri == a2_location_iri:
                                    #print('Line 1315')
                                    admin2_tuples_lst.remove(admin2_t)

                        # Add report identifier to index 0 of epidemic_entities

                        epidemic_entities.append(rep_id)

                        # Add epidemic date to index 1 of epidemic_entities

                        if sentence_entities[2] and sentence_entities[2] != 'null':
                            epidemic_entities.append(sentence_entities[2])
                        elif report_dates:
                            probable_date = report_dates[0]
                            epidemic_entities.append(probable_date)
                        else:
                            split_rep_id = rep_id.split('_')
                            est_epi_date = '{}-{}-{}'.format(split_rep_id[0], split_rep_id[1], split_rep_id[2])
                            epidemic_entities.append(est_epi_date)

                        # Add influenza pathogen to index 2 of epidemic_entities

                        epidemic_entities.append(report_pathogen_label)

                        # Add location to index 3 and country to index 4 of epidemic_entities

                        if d_located_in != report_country_label:
                            district_location = '{} (admin level 2); {} (admin level 1)'.format(d_location_label,
                                                                                                d_located_in)
                            epidemic_entities.append(district_location)
                            epidemic_entities.append(report_country_label)
                        else:
                            district_location = '{} (admin level 2)'.format(d_location_label)
                            epidemic_entities.append(district_location)
                            epidemic_entities.append(report_country_label)

                        # Add host(s) to index 5 of epidemic_entities
                        hosts = list()
                        if sentence_entities[3]:
                            for host_organism in sentence_entities[3]:
                                hosts.append(host_organism[0])
                            epidemic_entities.append('; '.join(hosts))
                            epidemic_lst.append(epidemic_entities)
                            print('1456', epidemic_entities)
                            epidemic_entities = []
                        else:
                            epidemic_entities.append(hosts)
                            no_host.append(epidemic_entities)
                            epidemic_entities = []

                if admin2_tuples_lst:
                    for admin2_tup in admin2_tuples_lst:
                        a2_location_label = admin2_tup.location
                        a2_location_iri = admin2_tup.location_iri
                        a2_located_in = admin2_tup.located_in
                        a2_located_in_iri = admin2_tup.located_in_iri

                        if admin1_tuples_lst:
                            for admin1_t in admin1_tuples_lst:
                                a1_location_iri = admin1_t.location_iri
                                if a2_located_in_iri == a1_location_iri:
                                    #print('Line 1331')
                                    admin1_tuples_lst.remove(admin1_t)

                        # Add report identifier to index 0 of epidemic_entities

                        epidemic_entities.append(rep_id)

                        # Add epidemic date to index 1 of epidemic_entities

                        if sentence_entities[2] and sentence_entities[2] != 'null':
                            epidemic_entities.append(sentence_entities[2])
                        elif report_dates:
                            probable_date = report_dates[0]
                            epidemic_entities.append(probable_date)
                        else:
                            split_rep_id = rep_id.split('_')
                            est_epi_date = '{}-{}-{}'.format(split_rep_id[0], split_rep_id[1], split_rep_id[2])
                            epidemic_entities.append(est_epi_date)

                        # Add influenza pathogen to index 2 of epidemic_entities

                        epidemic_entities.append(report_pathogen_label)

                        # Add location to index 3 and country to index 4 of epidemic_entities

                        if a2_located_in != report_country_label:
                            admin2_location = '{} (admin level 2); {} (admin level 1)'.format(
                                a2_location_label,
                                a2_located_in)
                            epidemic_entities.append(admin2_location)
                            epidemic_entities.append(report_country_label)
                        else:
                            admin2_location = '{} (admin level 2)'.format(a2_location_label)
                            epidemic_entities.append(admin2_location)
                            epidemic_entities.append(report_country_label)

                        # Add host(s) to index 5 of epidemic_entities
                        hosts = list()
                        if sentence_entities[3]:
                            for host_organism in sentence_entities[3]:
                                hosts.append(host_organism[0])
                            epidemic_entities.append('; '.join(hosts))
                            epidemic_lst.append(epidemic_entities)
                            print('1520', epidemic_entities)
                            epidemic_entities = []
                        else:
                            epidemic_entities.append(hosts)
                            no_host.append(epidemic_entities)
                            epidemic_entities = []
                if admin1_tuples_lst:
                    for admin1_tup in admin1_tuples_lst:
                        a1_location_label = admin1_tup.location
                        a1_location_iri = admin1_tup.location_iri

                        # Add report identifier to index 0 of epidemic_entities

                        epidemic_entities.append(rep_id)

                        # Add epidemic date to index 1 of epidemic_entities

                        if sentence_entities[2] and sentence_entities[2] != 'null':
                            epidemic_entities.append(sentence_entities[2])
                        elif report_dates:
                            probable_date = report_dates[0]
                            epidemic_entities.append(probable_date)
                        else:
                            split_rep_id = rep_id.split('_')
                            est_epi_date = '{}-{}-{}'.format(split_rep_id[0], split_rep_id[1], split_rep_id[2])
                            epidemic_entities.append(est_epi_date)

                        # Add influenza pathogen to index 2 of epidemic_entities

                        epidemic_entities.append(report_pathogen_label)

                        # Add location to index 3 and country to index 4 of epidemic_entities

                        admin1_location = '{} (admin level 1)'.format(a1_location_label)
                        epidemic_entities.append(admin1_location)
                        epidemic_entities.append(report_country_label)

                        # Add host(s) to index 5 of epidemic_entities

                        hosts = list()
                        if sentence_entities[3]:
                            for host_organism in sentence_entities[3]:
                                hosts.append(host_organism[0])
                            epidemic_entities.append('; '.join(hosts))
                            epidemic_lst.append(epidemic_entities)
                            print('1567', epidemic_entities)
                            epidemic_entities = []
                        else:
                            epidemic_entities.append(hosts)
                            no_host.append(epidemic_entities)
                            epidemic_entities = []

    with open('er-out-final-2.csv', 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['report_id', 'epidemic_date', 'flu_pathogen', 'location', 'country', 'host'])

        for row in epidemic_lst:
            csv_out.writerow(row)
except:
    print(row_number)
    with open('er-out-final-2.csv', 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['report_id', 'epidemic_date', 'flu_pathogen', 'location', 'country', 'host'])

        for row in epidemic_lst:
            csv_out.writerow(row)