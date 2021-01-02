import phonenumbers


def normalize(number, default_region):
    # ignore internal numbers
    if number.startswith("**"):
        return number
    try:
        converted_number = phonenumbers.parse(number, default_region)
        return phonenumbers.format_number(converted_number, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.phonenumberutil.NumberParseException:
        return number  # on error just return the raw number
