import sqlite3
import pandas as pd
from datetime import datetime
import itertools
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter


def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)


SELECT_OPERATION = input('Will you be adding rows to the table? [y/n] ')

if SELECT_OPERATION == 'y':
    DATA_INPUT = input('Location of csv file: ')

    df = pd.read_csv(DATA_INPUT)
    data = df.values.tolist()

    duplicates = list()

    for i in range(len(data) - 1):
        epidemic_indv = data[i]
        prev_epidemic_indv = data[i - 1]

        prev_report_id = prev_epidemic_indv[0]
        prev_flu_pathogen = prev_epidemic_indv[2]
        prev_location = prev_epidemic_indv[3]
        prev_host = prev_epidemic_indv[5]

        current_report_id = epidemic_indv[0]
        current_flu_pathogen = epidemic_indv[2]
        current_location = epidemic_indv[3]
        current_host = epidemic_indv[5]

        if i == 0 : continue
        else:
            if current_report_id != prev_report_id : continue
            elif current_flu_pathogen == prev_flu_pathogen \
                    and current_location == prev_location \
                    and current_host == prev_host:
                print('Removed duplicate: ', epidemic_indv)
                duplicates.append(epidemic_indv)
            elif current_flu_pathogen == prev_flu_pathogen \
                    and current_location == prev_location \
                    and current_host != prev_host:
                ch_split = current_host.split('; ')
                ph_split = prev_host.split('; ')

                for host in ch_split:
                    if host in ph_split : continue
                    else:
                        ph_split.append(host)
                        joined_hosts = '; '.join(ph_split)
                        prev_epidemic_indv.append(joined_hosts)
                        prev_epidemic_indv.remove(prev_epidemic_indv[5])
                duplicates.append(epidemic_indv)

    for dup in duplicates:
        data.remove(dup)
    print('Number of rows after de-deupication: ', len(data))

    labels = ['report_id', 'epidemic_date', 'flu_pathogen', 'location', 'country', 'host']
    deduplicated_data = pd.DataFrame.from_records(data, columns=labels)
    df.columns = deduplicated_data.columns.str.strip()

    conn = sqlite3.connect('flu-epidemics-test.db')
    c = conn.cursor()

    # Drop the table
    c.execute('''DROP TABLE epidemics''')

    # Re-create table with new values
    deduplicated_data.to_sql('epidemics', conn)

else:

    conn = sqlite3.connect('flu-epidemics-test.db')
    c = conn.cursor()

    epidemics_over_time = list()

    query = c.execute('''
    SELECT * FROM epidemics
    ORDER BY epidemic_date, flu_pathogen, country, location
    ''')

    rows = query.fetchall()
    same_epidemic = list()
    all_epidemics = list()
    report_ids = set()

    print(len(rows))

    for row in rows:
        if not same_epidemic:
            same_epidemic.append(row)
        else:
            previous_report = same_epidemic[-1]

            prev_report_id = previous_report[1]
            prev_epidemic_date = previous_report[2]
            prev_pathogen = previous_report[3]
            prev_location = previous_report[4]
            prev_country = previous_report[5]

            if row[3] == prev_pathogen and row[5] == prev_country:

                date_1 = prev_epidemic_date
                date_2 = row[2]
                no_days = days_between(date_1, date_2)

                if no_days < 60:
                    same_epidemic.append(row)
                else:
                    for epi in all_epidemics:
                        print(epi)
                        for e in epi:
                            e_date = e[2]
                            e_pathogen = e[3]
                            e_country = e[5]

                            if row[3] == e_pathogen and row[5] == e_country:
                                no_days2 = days_between(e_date, row[2])

                                if no_days2 < 60:
                                    all_epidemics.remove(epi)
                                    epi.append(row)
                                    all_epidemics.append(epi)
                            else : continue

                    all_epidemics.append(same_epidemic)
                    same_epidemic = []
                    same_epidemic.append(row)

            else:
                all_epidemics.append(same_epidemic)
                same_epidemic = []
                same_epidemic.append(row)

        report_ids.add(row[1])
    print('Number of reports: ', len(report_ids))

    additional_matches = set()
    changed_epidemics = list()

    for i in range(len(all_epidemics) - 1):
        matches = list()

        this_epi = all_epidemics[i]
        last_tuple = this_epi[-1]

        if this_epi == all_epidemics[-1] : break

        for epi in all_epidemics[i+1:]:
            first_epi = epi[0]

            if first_epi[3] == last_tuple[3] and first_epi[5] == last_tuple[5]:
                d0 = last_tuple[2]
                d1 = first_epi[2]

                try:
                    no_days3 = days_between(d0, d1)
                except ValueError:
                    continue

                if no_days3 < 60:
                    epi = tuple(epi)
                    additional_matches.add(epi)
                    #matches.append(epi)

        #matches.append(this_epi)
        #new_epi = list(itertools.chain.from_iterable(matches))
        #all_epidemics.append(new_epi)
    addnl_match_lst = list(additional_matches)

    for match in addnl_match_lst:
        if match in all_epidemics:
            all_epidemics.remove(match)

    # Plot number of epidemics per country
    '''
    no_of_countries = set()
    country_count = list()

    for epidemic in all_epidemics:
        country = epidemic[0][5]

        if '1912' in country:
            no_of_countries.add('Taiwan')
            country_count.append('Taiwan')
        elif 'soviet' in country.lower():
            no_of_countries.add('Russia')
            country_count.append('Russia')
        elif country.lower() == 'east germany':
            no_of_countries.add('Germany')
            country_count.append('Germany')
        elif country.lower() == 'people\'s republic of china':
            no_of_countries.add('China')
            country_count.append('China')
        elif country.lower() == 'united states of america':
            no_of_countries.add('United States')
            country_count.append('United States')
        else:
            no_of_countries.add(country)
            country_count.append(country)

    country_counter = Counter(country_count).most_common(15)
    print(country_counter)

    country_names = list()
    country_num = list()

    for c in country_counter:
        country_names.append(c[0])
        country_num.append(c[1])


    fig, ax = plt.subplots()
    ind = np.arange(1,16)

    b = plt.barh(ind, list(reversed(country_num)))
    ax.set_yticks(ind)
    ax.set_yticklabels(list(reversed(country_names)))
    ax.set_xlim(0, 250)
    ax.set_xlabel('Number of influenza epidemics (2006-2017)')

    plt.show()
    '''

    # Plot of the number of epidemics that each host was participant in

    '''
    no_of_hosts = set()
    host_count = list()

    for epidemic in all_epidemics:
        host_str = epidemic[0][6]
        hosts_split = host_str.split('; ')

        for host in hosts_split:
            no_of_hosts.add(host)
            host_count.append(host)

    host_counter = Counter(host_count).most_common(15)
    print(host_counter)

    host_names = list()
    host_num = list()

    for h in host_counter:
        if host == 'Metazoa' : continue
        host_names.append(h[0])
        host_num.append(h[1])

    fig, ax = plt.subplots()
    ind = np.arange(1, 16)
    x_ind = np.arange(0, 600, 50)

    b = plt.barh(ind, list(reversed(host_num)), color='red')
    ax.set_yticks(ind)
    ax.set_yticklabels(list(reversed(host_names)))
    ax.set_xticks(x_ind)
    ax.set_xbound(0, 600)
    ax.set_xlabel('Number of influenza epidemics (2006-2017)')

    plt.show()
    '''

    no_of_years = set()
    year_count = list()

    for epidemic in all_epidemics:
        year_str = epidemic[0][2]
        year = year_str.split('-')[0]

        no_of_years.add(year)
        year_count.append(year)

    year_counter = Counter(year_count).most_common(15)
    print(year_counter)

    years = list()
    year_freq = list()

    for y in sorted(year_counter):
        years.append(y[0])
        year_freq.append(y[1])

    fig, ax = plt.subplots()
    ind = np.arange(2005, 2018)

    plt.plot(years, year_freq, color='green')
    ax.set_ylabel('Number of influenza epidemics (2006-2017)')
    plt.xticks(ind, years, rotation=90)

    plt.show()

    '''for epi in all_epidemics:
        print('<------------------------- NEW EPIDEMIC ------------------------->')
        for e in epi:
            print(e)'''


