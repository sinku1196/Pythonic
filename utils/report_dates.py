from datetime import datetime


def get_months_between(start_date_str, end_date_str):
    """
    Returns list of months between two dates (inclusive)
    formatted as 'Month YYYY'
    """
    start_date = datetime.strptime(start_date_str, "%m/%d/%Y")
    end_date = datetime.strptime(end_date_str, "%m/%d/%Y")

    # Ensure start_date is earlier
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    months = []
    
    # Start from the first day of the start month
    current = start_date.replace(day=1)

    while current <= end_date:
        months.append(current.strftime("%B %Y"))
        
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return months