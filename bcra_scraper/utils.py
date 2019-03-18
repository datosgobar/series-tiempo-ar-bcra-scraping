from datetime import date, timedelta


def get_most_recent_previous_business_day(business_date=date.today()):
    if date.weekday(business_date) == 0:
        return business_date - timedelta(days=3)
    elif date.weekday(business_date) in [1, 2, 3, 4, 5]:
        return business_date - timedelta(days=1)
    else:
        return business_date - timedelta(days=2)