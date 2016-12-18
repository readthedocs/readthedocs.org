import pytz
import datetime


def get_ad_day():
    date = pytz.utc.localize(datetime.datetime.utcnow())
    day = datetime.datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        tzinfo=pytz.utc,
    )
    return day
