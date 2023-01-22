from myapp.models import *

def get_currency_list():
    currency_list = list()
    import requests
    from bs4 import BeautifulSoup
    url = "https://thefactfile.org/countries-currencies-symbols/"
    response = requests.get(url)
    if not response.status_code == 200:
        return currency_list
    soup = BeautifulSoup(response.content)
    data_lines = soup.find_all('tr')
    for line in data_lines:
        try:
            detail = line.find_all('td')
            currency = detail[2].get_text().strip()
            iso = detail[3].get_text().strip()
            if (currency, iso) in currency_list:
                continue
            if len(iso) == 3:
                currency_list.append((currency, iso))
        except:
            continue
    return currency_list


def add_currencies(currency_list):
    for currency in currency_list:
        currency_name = currency[0]
        currency_symbol = currency[1]
        try:
            c = Currency.objects.get(iso=currency_symbol)
        except:
            c = Currency(long_name=currency_name, iso=currency_symbol)
        c.name = currency_name
        c.save() #To test out the code, replace this by print(c)

def get_currency_rates(iso_code):
    url = "http://www.xe.com/currencytables/?from=" + iso_code
    import requests
    from bs4 import BeautifulSoup
    x_rate_list = list()
    try:
        page_source = BeautifulSoup(requests.get(url).content)
    except:
        return x_rate_list
    data = page_source.find('tbody')
    data_lines = data.find_all('tr')
    for line in data_lines:
        symbol = line.find('th').get_text()
        data = line.find_all('td')
        try:
            x_rate = float(data[1].get_text().strip())
            x_rate_list.append((symbol, x_rate))
        except:
            continue
    return x_rate_list


def update_xrates(currency):
    try:
        new_rates = get_currency_rates(currency.iso)
        for new_rate in new_rates:
            from datetime import datetime, timezone
            time_now = datetime.now(timezone.utc)
            try:
                rate_object = Rates.objects.get(currency=currency, x_currency=new_rate[0])
                rate_object.rate = new_rate[1]
                rate_object.last_update_time = time_now
            except:
                rate_object = Rates(currency=currency, x_currency=new_rate[0], rate=new_rate[1],
                                    last_update_time=time_now)
            rate_object.save()
    except:
        pass

def DMS_to_decimal(dms_coordinates):
    degrees = int(dms_coordinates.split('°')[0])

    try:
        minutes = int(dms_coordinates.split('°')[1].split("′")[0])
        seconds = int(dms_coordinates.split('°')[1].split("′")[1][:2])
    except:
        seconds = 0.0
    decimal = degrees + minutes/60 + seconds/3600
    try:
        if dms_coordinates[-1] == "S":
            decimal = -decimal
    except:
        pass
    try:
        if dms_coordinates[-1] == "W":
            decimal = -decimal
    except:
        pass
    return decimal

def degrees_to_decimal(coordinate):
    decimal = 0.0
    try:
        decimal = float(coordinate.split('°')[0])
    except:
        pass
    try:
        if coordinate[-1] == "S":
            decimal = -decimal
    except:
        pass
    try:
        if coordinate[-1] == "W":
            decimal = -decimal
    except:
        pass

    return decimal



def get_lat_lon(city, state, country):
    import requests
    from bs4 import BeautifulSoup
    lat = 0
    lon = 0
    try:
        url = "https://www.google.com/search?num=1&q="
        if len(state) > 0:
            url += city.replace(" ", "+") + "+" + state.replace(" ", "+") + "+" + country.replace(" ", "+") + "+coordinates"
        else:
            url += city.replace(" ", "+") + "+" + country.replace(" ", "+") + "+coordinates"

        text = requests.get(url).text
        soup = BeautifulSoup(text)

        degree_tags = soup.find_all(lambda tag: len(tag.find_all()) == 0 and "°" in tag.text)

        try:
            lat_lon = degree_tags[0].get_text().split(', ')
            lat = degrees_to_decimal(lat_lon[0])
            lon = degrees_to_decimal(lat_lon[1])
        except:
            pass
    except:
        pass

    return lat, lon

def add_markers(m, city_list):
    import folium
    lat_lon_list = list()
    for place in city_list:
        city = place[0]
        state = place[1]
        country = place[2]
        lat, lon = get_lat_lon(city, state, country)
        print(city, state, country, lat, lon)
        if lat != 0.0 and lon != 0.0:
            icon = folium.Icon(color="blue", prefix="fa", icon="plane")
            marker = folium.Marker((lat, lon), icon=icon)
            marker.add_to(m)
            lat_lon_list.append([lat, lon])
    #Add line. First rearrange lat lons by longitude
    lat_lon_list.sort(key=lambda x: x[1])
    line_string = list()
    for i in range(len(lat_lon_list)-1):
        line_string.append([lat_lon_list[i],lat_lon_list[i+1]])
    line = folium.PolyLine(line_string, color="red", weight=5)
    line.add_to(m)

    print('got thru line added')

    sw_lat = min(lat_lon_list[0][0], lat_lon_list[1][0])
    sw_lon = min(lat_lon_list[0][1], lat_lon_list[1][1])
    ne_lat = max(lat_lon_list[0][0], lat_lon_list[1][0])
    ne_lon = max(lat_lon_list[0][1], lat_lon_list[1][1])

    sw = [sw_lat, sw_lon]
    ne = [ne_lat, ne_lon]

    m.fit_bounds([sw, ne])

    print('finished mapping function')

    return m

def get_airport_list():
    airport_list = list()
    import requests
    from bs4 import BeautifulSoup
    url = "http://www.airportcodes.org/"
    response = requests.get(url)
    if not response.status_code == 200:
        return airport_list
    soup = BeautifulSoup(response.content)

    #Get the list of Canadian province abbreviations from the airportcodes webpage
    minor_divs = soup.find_all('div', class_='minor')
    can_states_list = list()
    for j in minor_divs[1].stripped_strings:
        can_states_list.append(j[0:2])

    #Get the list of US state abbreviations from the FAA website
    url_states = "https://www.faa.gov/air_traffic/publications/atpubs/cnt_html/appendix_a.html"
    response_states = requests.get(url_states)
    soup_states = BeautifulSoup(response_states.content)

    us_state_list = list()
    for item in soup_states.find_all('td'):
        text = item.get_text().strip()
        if len(text) == 2:
            us_state_list.append(text)

    data_lines = list()
    for string in soup.stripped_strings:
        if "(" in string and ")" in string:
            data_lines.append(string)

    for line in data_lines:
        data_dict = dict()
        airport_code = ''
        if line.find(',') != -1:
            open_paren_pos = line.rfind('(')
            first_open_paren_pos = line.find('(')
            first_close_paren_pos = line.find(')')

            if open_paren_pos != first_open_paren_pos:
                line = line[0:first_open_paren_pos-1] + line[first_close_paren_pos+1:len(line)]

            dash_pos = line.find(' - ')
            open_paren_pos = line.rfind('(')
            close_paren_pos = line.rfind(')')
            first_comma_pos = line.find(',')
            last_comma_pos = line.rfind(',')

            airport_code = line[open_paren_pos + 1: close_paren_pos]

            if ', (' in line and dash_pos == -1:
                state_or_country = line[first_comma_pos + 2: last_comma_pos]
                airport_name = line[0: first_comma_pos]
                city = airport_name
            elif ', (' in line and dash_pos != -1:
                state_or_country = line[first_comma_pos + 2: dash_pos - 1]
                airport_name = line[dash_pos + 3: last_comma_pos]
                city = line[0: first_comma_pos]
            elif dash_pos != -1:
                state_or_country = line[last_comma_pos + 2: dash_pos]
                airport_name = line[dash_pos + 3: open_paren_pos - 1]
                city = line[0: first_comma_pos]
            else:
                state_or_country = line[last_comma_pos + 2: open_paren_pos - 1]
                airport_name = line[0: first_comma_pos]
                city = airport_name

        if state_or_country in us_state_list:
            state = state_or_country
            country = 'United States'
        elif state_or_country in can_states_list:
            state = state_or_country
            country = 'Canada'
        else:
            state = ''
            country = state_or_country

        data_dict["code"] = airport_code
        data_dict["name"] = airport_name
        data_dict["city"] = city
        data_dict["state"] = state
        data_dict["country"] = country

        if ' Bus' not in airport_name and 'service' not in airport_name:
            #print(airport_code + ': ' + city + ' - ' + airport_name + ' - ' + state + ' ' + country)
            airport_list.append(data_dict)
    return airport_list

def add_airports(airport_list):
    for airport in airport_list:
        airport_code = airport["code"]
        airport_name = airport["name"]
        airport_city = airport["city"]
        airport_state = airport["state"]
        airport_country = airport["country"]

        try:
            a = Airport.objects.get(code=airport_code)
        except:
            a = Airport(code=airport_code, name=airport_name, city=airport_city, state=airport_state, country=airport_country)

        a.save()

def ticket_search(origin_code, random_airport, departure_date, budget):
    import requests
    from bs4 import BeautifulSoup

    # embed the above variables into the URL of "skyticket.com" #
    # fixed parameter = one-way, economy, 1 adult, 0 children, 0 infants #
    target_url = "https://skyticket.com/international-flights/ia_fare_result_mix.php?select_career_only_flg=&trip_type=1&dep_port0=" + origin_code + "&arr_port0=" + random_airport + "&dep_date%5B%5D=" + departure_date + "&cabin_class=Y&adt_pax=1"

    response_test = requests.get(target_url)
    soup_test = BeautifulSoup(response_test.content)

    if "There are no flights matching your search preferences. Please change your flight criteria and search again." in soup_test.stripped_strings:
        return []

    cheapest_price_text = soup_test.find('li', text='Cheapest Plan').find_next_sibling().get_text()
    cheapest_price = float(cheapest_price_text.replace(",","").replace("~","")[3:])

    if cheapest_price > budget:
        return ["Too expensive", cheapest_price]

    index = 0

    for price in soup_test.find_all('span', class_="price_aside"):
        if float(price.get_text().replace(",","")[3:]) == cheapest_price:
            break
        index += 1

    airline = soup_test.find_all('div', class_="list_price clearfix")[index].get_text()[2:].split("\t")[0]

    #airline_list = []
    #for airline in soup_test.find_all('div', class_="list_price clearfix"):
    #    additional_entry = airline.get_text()[2:].split("\t")[0]
    #    airline_list.append(additional_entry)

    #price_list = []
    #for price in soup_test.find_all('span', class_="price_aside"):
    #    price_list.append(float(price.get_text().replace(",","")[3:]))

    # merge "airline_list" & "price_list" #
    #travel_dict = {}
    #for i in range(len(airline_list)):
    #    travel_dict[airline_list[i]] = price_list[i]

    #try:
    #    min_value = min(travel_dict.values())
    #except:
    #    min_value = ""

    #flight = ""
    #for t in travel_dict.keys():
    #    if travel_dict[t] == min_value:
    #        flight = t

    min_ticket_price = [airline, cheapest_price]

    try:

        return min_ticket_price
    except:
        return min_ticket_price

def recommend_attraction(city, state, country):
    import requests
    from bs4 import BeautifulSoup
    from collections import defaultdict
    import re

    search_word = 'tripadvisor'

    if len(state) > 0:
        search_word += "+" + city.replace(" ", "+") + "+" + state.replace(" ", "+") + "+" + country.replace(" ", "+")
    else:
        search_word += "+" + city.replace(" ", "+") + "+" + country.replace(" ", "+")
    url_for_location_id = "https://www.google.com/search?num=1&q=" + search_word
    request = requests.get(url_for_location_id)
    soup = BeautifulSoup(request.text, "html.parser")
    search_site = soup.select('div.kCrYT > a')

    tripadvisor_location_id = search_site[0]['href'].replace('/url?q=', '').split('-')[1]

    print(tripadvisor_location_id)

    attraction = {}

    url_for_recommendation = "https://www.tripadvisor.com/Attractions-" + tripadvisor_location_id
    user_agent = ({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \AppleWebKit/537.36 (KHTML, like Gecko) \Chrome/90.0.4430.212 Safari/537.36','Accept-Language': 'en-US, en;q=0.5'})

    request = requests.get(url_for_recommendation, headers = user_agent)
    soup = BeautifulSoup(request.text, 'html.parser')
    search_site = soup.findAll('div',{'class':'XfVdV o AIbhI'})

    print("search successful")

    for thing in search_site:
        rank = int(thing.text.strip().split(".")[0])
        if not rank >= 4: ### pick up top 3 ###
            attraction.setdefault(rank,[]).append(thing.text.strip().split(". ")[1])
        else:
            break

    search_site = soup.findAll('div',{'class':'PFVlz'})

    print("search_site_2 before loop")

    for a in search_site:
        url_of_attraction = 'https://www.tripadvisor.com' + a.find('a', href=re.compile('Attraction_Review-')).attrs['href']
        if not search_site.index(a) +1 >= 4: ### pick up top 3 ###
            attraction[search_site.index(a)+1].append(url_of_attraction)

            print("check this")
            request = requests.get(url_of_attraction, headers = user_agent)
            soup = BeautifulSoup(request.text, 'html.parser')
            imgs = soup.findAll('img', src=re.compile('https://dynamic-media-cdn.tripadvisor.com/media/photo-o/'))
            url_top_image = imgs[0]['src']
            attraction[search_site.index(a)+1].append(url_top_image)

        else:
            break

    return attraction

def random_suggestion(origin_code, departure_date, budget, past_destination_airport_list):
    import random
    suggestion_list = {}

    airport_query_set = Airport.objects.all().values('code')
    airport_list = list(airport_query_set)
    random.shuffle(airport_list)
    airport_list = airport_list[0:10]
    print(airport_list)

    for i in range(len(airport_list)):
        random_airport = airport_list[i]['code']
        if (random_airport in past_destination_airport_list) or (random_airport == origin_code):
            continue
        else:
            try:
                search_result = ticket_search(origin_code, random_airport, departure_date, budget)
                print(search_result)
                prechecked_price = search_result[1]

                if prechecked_price <= budget:
                    suggestion_list['destination_airport_code'] = random_airport
                    suggestion_list['price'] = prechecked_price
                    suggestion_list['airline'] = search_result[0]
                    return suggestion_list
                    break
                else:
                    continue
            except:
                continue

    return {}
