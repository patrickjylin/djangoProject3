import folium as folium
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from myapp import support_functions
from myapp.models import Currency, AccountHolder, Airport


# Create your views here.

def home(request):
    data = dict()
    a_list = Airport.objects.all().order_by('code')
    data["airports"] = a_list
    return render(request, "home.html", context=data)

def maintenance(request):
    data = dict()
    try:
        choice = request.GET['selection']
        if choice == "airports":
            support_functions.add_airports(support_functions.get_airport_list())
            a_list = Airport.objects.all()
            print("Got a_list", len(a_list))
            data['airports'] = a_list
            return HttpResponseRedirect(reverse('airports'))
        elif choice == "currencies":
            support_functions.add_currencies(support_functions.get_currency_list())
            c_list = Currency.objects.all()
            print("Got c_list", len(c_list))
            data['currencies'] = c_list
            return HttpResponseRedirect(reverse('currencies'))

    except:
        pass
    return render(request, "maintenance.html", context=data)

def view_currencies(request):
    data = dict()
    c_list = Currency.objects.all()
    data['currencies'] = c_list
    return render(request, "currencies.html", context=data)

def currency_selection(request):
    data = dict()
    currencies = Currency.objects.all().order_by('long_name')
    data['currencies'] = currencies
    return render(request, "currency_selector.html", data)

def exch_rate(request):
    data=dict()
    try:
        currency1 = request.GET['currency_from']
        currency2 = request.GET['currency_to']
        c1 = Currency.objects.get(iso=currency1)
        c2 = Currency.objects.get(iso=currency2)
        try:
            user = request.user
            if user.is_authenticated:
                account_holder = AccountHolder.objects.get(user=user)
                account_holder.currencies_visited.add(c1)
                account_holder.currencies_visited.add(c2)
                data['currencies_visited'] = account_holder.currencies_visited.all()
        except:
            pass
        support_functions.update_xrates(c1)
        data['currency1'] = c1
        data['currency2'] = c2

        try:
            rate = c1.rates_set.get(x_currency=c2.iso).rate
            data['rate'] = rate
        except:
            data['rate'] = "Not Available"
    except:
        pass
    return render(request, "exchange_detail.html", data)

def register_new_user(request):
    context = dict()
    form = UserCreationForm(request.POST)
    if form.is_valid():
        new_user = form.save()
        #dob = request.POST["dob"]
        acct_holder = AccountHolder(user=new_user, date_of_birth='2000-01-01')
        acct_holder.save()
        return render(request, "home.html", context=dict())
    else:
        form = UserCreationForm()
        context['form'] = form
        return render(request, "registration/register.html", context)

def test_html(request):
    data=dict()
    return render(request, "assignment2.html", data)

def app_maintenance(request):
    data=dict()
    return render(request, "app_maintenance.html", data)

def view_airports(request):
    data = dict()
    a_list = Airport.objects.all().order_by('city', 'state', 'country', 'name')
    data['airports'] = a_list
    return render(request, "airports.html", context=data)

def map(request):
    data = dict()
    m = folium.Map()

    try:
        request.GET['reset']
        print("resetting")
        data['number_of_cities'] = 0
        data['m'] = m._repr_html_
        return render(request, "map.html", context=data)
    except:
        pass

    try:
        request.GET['city_list']
        visiting_cities = list()
        number_of_cities = int(request.GET["number_of_cities"])

        for i in range(number_of_cities):
            name = "city" + str(i)
            city_name = request.GET[name]
            visiting_cities.append(city_name)
        m = support_functions.add_markers(m, visiting_cities)
        data['visiting_cities'] = visiting_cities
        m = m._repr_html_
        data['m'] = m
        return render(request, "map.html", data)
    except:
        pass

    try:
        number_of_cities = int(request.GET["number_of_cities"])
        if number_of_cities > 0:
            names = list()
            for i in range(number_of_cities):
                names.append("city" + str(i))
            data['names'] = names
            data['number_of_cities'] = number_of_cities
        m = m._repr_html_
        data['m'] = m
    except:
        data['number_of_cities'] = 0
        m = m._repr_html_
        data['m'] = m
    return render(request, "map.html", context=data)

def wander(request):
    data = dict()
    from datetime import date
    try:
        origin = request.GET['origin']
        origin = origin[0:3]
        dep_date = request.GET['dep_date']
        budget = float(request.GET['budget'])

        data['origin'] = origin
        data['dep_date'] = dep_date
        data['budget'] = int(budget)
        print(origin)
        print(dep_date)
        print(budget)
        #dep_date = date(dep_date_str[0:4], dep_date_str[5:7], dep_date_str[9:11])

        try:
            user = request.user
            print(user.is_authenticated)
            if user.is_authenticated:
                print("user is authenticated")
                wander_result = support_functions.random_suggestion(origin, dep_date, budget, [])
                print(wander_result)
                if len(wander_result) == 0:
                    return render(request, "no_result.html", context=data)
                data['destination_airport_code'] = wander_result['destination_airport_code']
                data['price'] = int(wander_result['price'])
                data['airline'] = wander_result['airline']
                p1 = Airport.objects.get(code=origin)
                o_city = p1.city
                o_state = p1.state
                o_country = p1.country
                d_code = wander_result['destination_airport_code']
                p2 = Airport.objects.get(code=d_code)
                d_city = p2.city
                d_state = p2.state
                d_country = p2.country
                if len(d_state) > 0:
                    data['destination'] = d_city + ', ' + d_state + ', ' + d_country
                else:
                    data['destination'] = d_city + ', ' + d_country

                """    
                data['attraction_1'] = 'Wow'
                data['attraction_2'] = 'Wow'
                data['attraction_3'] = 'Wow'
                data['attraction_1_url'] = ''
                data['attraction_2_url'] = ''
                data['attraction_3_url'] = ''
                data['attraction_1_image'] = ''
                data['attraction_2_image'] = ''
                data['attraction_3_image'] = ''
                """

                a = support_functions.recommend_attraction(d_city, d_state, d_country)
                data['attraction_1'] = a[1][0]
                data['attraction_2'] = a[2][0]
                data['attraction_3'] = a[3][0]
                data['attraction_1_url'] = a[1][1]
                data['attraction_2_url'] = a[2][1]
                data['attraction_3_url'] = a[3][1]
                data['attraction_1_image'] = a[1][2]
                data['attraction_2_image'] = a[2][2]
                data['attraction_3_image'] = a[3][2]
                print(a)

                connecting_cities = list()
                connecting_cities.append([o_city, o_state, o_country])
                connecting_cities.append([d_city, d_state, d_country])
                ma = folium.Map()
                ma = support_functions.add_markers(ma, connecting_cities)
                ma = ma._repr_html_
                data['ma'] = ma
                print("finished mapping")

                return render(request, "suggestion.html", context=data)

            return render(request, "register_prompt.html", context=data)

        except:
            pass

    except:
        pass

    return render(request, "error.html", context=data)


def no_result(request):
    data = dict()
    data['budget'] = 100
    return render(request, "no_result.html", context=data)


def suggestion(request):
    data = dict()
    return render(request, "suggestion.html", context=data)
