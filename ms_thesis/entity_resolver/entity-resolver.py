import sqlite3
import pandas as pd
from datetime import datetime
from datetime import timedelta
import datetime as dt
import itertools
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import os


def remove_letters(d):
    d_split = d.split("-")
    yr = d_split[0]
    month = d_split[1]
    day = d_split[2]

    if day.endswith("th"):
        day = day[:-2]

    formatted_d = dt.date(int(yr), int(month), int(day))
    return formatted_d


def days_between(d1, d2):
    d1 = datetime.strptime(remove_letters(d1), "%Y-%m-%d")
    d2 = datetime.strptime(remove_letters(d2), "%Y-%m-%d")
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

    conn = sqlite3.connect('flu-tuples.db')
    c = conn.cursor()

    # Drop the table
    c.execute('''DROP TABLE epidemics''')

    # Re-create table with new values
    deduplicated_data.to_sql('epidemics', conn)

else:
    conn = sqlite3.connect('flu-tuples.db')
    c = conn.cursor()

    query = c.execute('''
    SELECT * FROM epidemics
    ORDER BY epidemic_date, flu_pathogen, country, location
    ''')

    q2 = c.execute('''select * from epidemics''')
    column_names = [d[0] for d in q2.description]
    #print(column_names)

    rows = query.fetchall()
    same_epidemic = list()
    matched_epidemics = list()
    unmatched_epidemics = list()

    print("Number of rows in table: ", len(rows))
    #print(rows)

    report_count = 0

    while rows:
        last_row_id = str(rows[-1][0])
        first = rows.pop(0)
        same_epidemic.append(first)

        report_ids = list()

        first_id = first[0]
        first_pathogen = first[3]
        first_country = first[5]

        report_ids.append(first_id)

        while True:
            row_id = ""
            for tup in rows:
                row_id = str(tup[0])

                if row_id in report_ids:
                    continue
                elif tup[5] == first_country and tup[3] == first_pathogen:
                    earliest_epi_date = remove_letters(same_epidemic[0][2])
                    latest_epi_date = remove_letters(same_epidemic[-1][2])
                    this_epi_date = remove_letters(tup[2])
                    margin = timedelta(days=60)

                    if earliest_epi_date - margin <= this_epi_date <= latest_epi_date + margin:
                        same_epidemic.append(tup)
                        same_epidemic.sort(key=lambda x: remove_letters(x[2]))
                        report_ids.append(row_id)
                        break
                    else:
                        continue

            if row_id == last_row_id:
                break

        if len(same_epidemic) > 1:
            matched_epidemics.append(same_epidemic)
        else:
            unmatched_epidemics.append(same_epidemic[0])
        rows[:] = [row for row in rows if row not in same_epidemic]
        same_epidemic = []

    #print(len(matched_epidemics))
    #print(len(unmatched_epidemics))
    #for epi in matched_epidemics:
        #print(epi)

    '''# Plot number of epidemics per country

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
    ax.set_title('Number of Avian Influenza Epidemics by Country (2006-2017)')
    ax.set_yticks(ind)
    ax.set_yticklabels(list(reversed(country_names)))
    ax.set_xlim(0, 250)
    ax.set_xlabel('Count of influenza epidemics')

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
    ax.set_title('Number of Avian Influenza Epidemics that Affected Each Host (2006-2017)')
    ax.set_yticks(ind)
    ax.set_yticklabels(list(reversed(host_names)))
    ax.set_xticks(x_ind)
    ax.set_xbound(0, 600)
    ax.set_xlabel('Count of influenza epidemics')

    plt.show()
    '''

    '''
    no_of_years = set()
    year_count = list()

    for epidemic in all_epidemics:
        year_str = epidemic[0][2]
        year = year_str.split('-')[0]

        no_of_years.add(year)
        year_count.append(year)

    year_counter = Counter(year_count).most_common()
    print(year_counter)

    years = list()
    year_freq = list()

    for y in sorted(year_counter):
        years.append(y[0])
        year_freq.append(y[1])

    fig, ax = plt.subplots()
    ind = np.arange(2005, 2018)

    plt.plot(years, year_freq, color='green')
    ax.set_ylabel('Count of influenza epidemics')
    ax.set_title('Number of Avian Influenza Epidemics by Year')
    plt.xticks(ind, years, rotation=90)

    plt.show()
    '''

    '''
    no_of_pathogens = set()
    pathogen_count = list()

    for epidemic in all_epidemics:
        pathogen_str = epidemic[0][3]
        pathogens_split = pathogen_str.split('; ')

        for pathogen in pathogens_split:
            no_of_pathogens.add(pathogen)
            pathogen_count.append(pathogen)

    pathogen_counter = Counter(pathogen_count).most_common(18)

    pathogen_names = list()
    pathogen_num = list()

    for p in pathogen_counter:
        if p[0] == 'Influenza A virus' : continue
        pathogen_names.append(p[0])
        pathogen_num.append(p[1])

    fig, ax = plt.subplots()
    ind = np.arange(1, 18)
    x_ind = np.arange(0, 775, 50)

    b = plt.barh(ind, list(reversed(pathogen_num)), color='green')
    ax.set_title('Number of Avian Influenza Epidemics by Influenza Subtype (2006-2017)')
    ax.set_yticks(ind)
    ax.set_yticklabels(list(reversed(pathogen_names)))
    ax.set_xticks(x_ind)
    ax.set_xbound(0, 775)
    ax.set_xlabel('Count of influenza epidemics')

    for i in ax.patches:
        if i.get_width() < 40:
            x_coord = i.get_width()+5
            y_coord = i.get_y()+.25
            string = 'count=' + str(int(i.get_width()))
            ax.text(x=x_coord, y=y_coord, s=string, fontsize=8)

    plt.show()
    '''

    epidemic_count = 0

    # Remove duplicate epidemic tuples from each set of matched tuples.
    # Assign epidemic identifier to remaining tuples.
    # Create a merged epidemic tuple from remaining matched tuples.
    merged_tuples = list()

    for epi in matched_epidemics:
        epidemic_id = "flu_"
        epidemic_count += 1
        no_of_leading_zeroes = 5 - len(str(epidemic_count))

        for z in range(no_of_leading_zeroes):
            epidemic_id = epidemic_id + "0"
        epidemic_id = epidemic_id + str(epidemic_count)

        no_of_epi_tuples = range(len(epi))
        tuples_to_remove = set()
        deleted_tuple_ids = list()

        for i in no_of_epi_tuples:
            epidemic_to_check = epi[i]

            if epidemic_to_check[0] in deleted_tuple_ids:
                continue

            for e in epi:
                tuple_no = e[0]
                report_id = e[1]
                epi_date = e[2]
                epi_location = e[4]
                epi_country = e[5]
                epi_host = e[6]

                if tuple_no == epidemic_to_check[0]:
                    continue
                elif report_id == epidemic_to_check[1] \
                        and epi_date == epidemic_to_check[2] \
                        and epi_location == epidemic_to_check[4] \
                        and epi_country == epidemic_to_check[5] \
                        and epidemic_to_check[6] in epi_host:
                    tuples_to_remove.add(e)
                    deleted_tuple_ids.append(tuple_no)
                elif "(country)" in epi_location \
                        and report_id == epidemic_to_check[1] \
                        and epi_date == epidemic_to_check[2] \
                        and epi_country == epidemic_to_check[5] \
                        and epidemic_to_check[6] in epi_host:
                    tuples_to_remove.add(e)

        for t in tuples_to_remove:
            epi.remove(t)

        #print('<------------------------- NEW EPIDEMIC ------------------------->')
        epi_hosts = set()
        epi_locations = set()
        epi_reports = set()
        epi_dates = set()
        for e in epi:
            if ");" in e[4]:
                epi_locations.add(e[4].replace(");", "),"))
            else:
                epi_locations.add(e[4])

            epi_reports.add(e[1])
            epi_dates.add(e[2])
            host_lst = e[6].split("; ")
            for h in host_lst:
                epi_hosts.add(h)

            e_list = list(e)
            e_list.append(epidemic_id)

        dates = sorted(epi_dates)

        if len(epi_locations) > 1:
            for l in epi_locations.copy():
                if "(country)" in l:
                    epi_locations.remove(l)

        # Merge each tuple into one epidemic tuple
        date_range = "{} to {}".format(dates[0], dates[-1])
        pathogen = epi[0][3]
        locations = "; ".join(epi_locations)
        country = epi[0][5]
        hosts = "; ".join(epi_hosts)
        source_reports = "; ".join(epi_reports)

        epidemic_tuple = (epidemic_id, date_range, pathogen, locations, country, hosts, source_reports)
        merged_tuples.append(epidemic_tuple)

    print("Number of matched epidemics: ", len(matched_epidemics))
    print("Number of unmatched epidemics: ", len(unmatched_epidemics))

    # Write merged tuples to a CSV file
    epidemic_fields = ["epidemic_id", "date_range", "pathogen", "locations", "country", "hosts", "source_reports"]

    merged_tuples_df = pd.DataFrame.from_records(merged_tuples, columns=epidemic_fields)

    today = datetime.today().strftime("%Y-%m-%d")
    path = "data/entity_resolver_output"
    epidemics_filename = "er-out-epidemic-tuples-{}.csv".format(today)
    epidemics_filename = os.path.join(path, epidemics_filename)

    merged_tuples_df.to_csv(epidemics_filename)

    # Write unmatched tuples to a CSV file
    labels = ['index', 'report_id', 'epidemic_date', 'flu_pathogen', 'location', 'country', 'host']
    unmatched_tuples_df = pd.DataFrame.from_records(unmatched_epidemics, columns=labels)

    unmatched_tuples_filename = "er-out-unmatched-tuples-{}.csv".format(today)
    unmatched_tuples_filename = os.path.join(path, unmatched_tuples_filename)

    unmatched_tuples_df.to_csv(unmatched_tuples_filename, index=False)
