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
    minutes = int(dms_coordinates.split('°')[1].split("′")[0])
    try:
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

def get_lat_lon(city_name):
    import requests
    from bs4 import BeautifulSoup
    try:
        city = City.objects.get(name=city_name)
        lat = city.latitude
        lon = city.longitude
        wiki_link = ""
    except:
        url = "https://en.wikipedia.org/wiki/"
        url += city_name.replace(" ", "_")
        wiki_link = url
        try:
            text = requests.get(url).text
            soup = BeautifulSoup(text)
            lat = soup.find('span', class_="latitude").get_text()
            lon = soup.find('span', class_="longitude").get_text()
            lat = DMS_to_decimal(lat)
            lon = DMS_to_decimal(lon)
        except:
            lat = 0.0
            lon = 0.0
    return lat, lon, wiki_link

def add_markers(m,visiting_cities):
    import folium
    lat_lon_list = list()
    for city_name in visiting_cities:
        lat, lon, wiki_link = get_lat_lon(city_name)
        print(city_name, lat, lon, wiki_link)
        if lat != 0.0 and lon != 0.0 and wiki_link != "":
            icon = folium.Icon(color="blue", prefix="fa", icon="plane")
            popup = "<a href="
            popup += wiki_link
            popup += ">" + city_name+ "</a>"
            marker = folium.Marker((lat, lon), icon=icon, popup=popup)
            marker.add_to(m)
            lat_lon_list.append([lat, lon])
    #Add line. First rearrange lat lons by longitude
    lat_lon_list.sort(key=lambda x: x[1])
    line_string = list()
    for i in range(len(lat_lon_list)-1):
        line_string.append([lat_lon_list[i],lat_lon_list[i+1]])
    line = folium.PolyLine(line_string, color="red", weight=5)
    line.add_to(m)
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