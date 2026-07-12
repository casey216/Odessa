from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


# Custom template filters
def format_currency(value):
    if value is None:
        return "—"
    return f"₦{float(value):,.2f}"


def format_km(value):
    if value is None:
        return "—"
    return f"{int(value):,} km"


def format_date(value):
    if value is None:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%b %d, %Y")
    return str(value)


def days_until(value):
    if value is None:
        return None
    from datetime import date

    if hasattr(value, "date"):
        d = value.date()
    else:
        d = value
    delta = (d - date.today()).days
    return delta


def truncate_uuid(value):
    if value is None:
        return None
    return str(value)[:8]


templates.env.filters["currency"] = format_currency
templates.env.filters["km"] = format_km
templates.env.filters["fmt_date"] = format_date
templates.env.filters["days_until"] = days_until
templates.env.filters["truncate_uuid"] = truncate_uuid
