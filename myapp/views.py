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
    import datetime
    time = datetime.datetime.now()
    data["time_of_day"] = time
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
        dob = request.POST["dob"]
        acct_holder = AccountHolder(user=new_user, date_of_birth=dob)
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
    a_list = Airport.objects.all().order_by(Airport.city, Airport.state, Airport.country, Airport.name)
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

