from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Currency(models.Model):
    iso = models.CharField(max_length=3)
    long_name = models.CharField(max_length=50)
    def __repr__(self):
        return self.iso + " " + self.long_name
    def __str__(self):
        return self.iso + " " + self.long_name

class Holding(models.Model):
    iso = models.ForeignKey(Currency, on_delete=models.CASCADE)
    value = models.FloatField(default=0.0)
    buy_date = models.DateField()
    def __repr__(self):
        return self.iso.iso + " " + str(self.value) + " " + str(self.buy_date)
    def __str__(self):
        return self.iso.long_name + " " + str(self.value) + " " + str(self.buy_date)


class Rates(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    x_currency = models.CharField(max_length=3)
    rate = models.FloatField(default=1.0)
    last_update_time = models.DateTimeField()
    def __repr__(self):
        return self.currency.iso + " " + self.x_currency + " " + str(self.rate)
    def __str__(self):
        return self.currency.iso + " " + self.x_currency + " " + str(self.rate)

class AccountHolder(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    currencies_visited = models.ManyToManyField(Currency)
    def __str__(self):
        return self.user.username
    def __repr__(self):
        return self.user.username

class City(models.Model):
    name = models.CharField(max_length=50)
    wiki_link = models.URLField()
    latitude = models.FloatField(null=False)
    longitude = models.FloatField(null=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name + " " + str(self.latitude) + " " + str(self.longitude)

class Airport(models.Model):
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    def __repr__(self):
        if len(self.state) > 0:
            return self.code + " - " + self.name + " (" + self.city + ", " + self.state + ", " + self.country + ")"
        return self.code + " - " + self.name + " (" + self.name + ", " + self.country + ")"

    def __str__(self):
        if len(self.state) > 0:
            return self.code + " - " + self.name + " (" + self.city + ", " + self.state + ", " + self.country + ")"
        return self.code + " - " + self.name + " (" + self.name + ", " + self.country + ")"

class SuggestedAttraction(models.Model):
    suggested_city = models.CharField(max_length=50)
    rank = models.IntegerField(default=0)
    attraction_name = models.CharField(max_length=50)
    attraction_url = models.URLField()
    attraction_imageurl = models.URLField()
    def __repr__(self):
        return self.suggested_city + " " + str(self.rank) + " " + self.attraction_name
    def __str__(self):
        return self.suggested_city + " " + str(self.rank) + " " + self.attraction_name