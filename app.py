from flask import Flask, render_template, request, jsonify
# from flask_azure_oauth import FlaskAzureOAuth
import os
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)
from utils import save_to_csv

# to do:
# add required inputs and tests on inputs

# static variables
schema = 'consumer_retention'
db_schema_searches = f'{schema}-searches.csv'
db_schema_outcomes = f'{schema}-outcomes.csv'

app = Flask(__name__)


# params for azure deployment
# app.config['AZURE_OAUTH_CLIENT_ID'] = '<your-client-id>'
# app.config['AZURE_OAUTH_CLIENT_SECRET'] = '<your-client-secret>'
# app.config['AZURE_OAUTH_TENANT'] = '<your-tenant-id>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/direct')
def direct():
    return render_template('direct.html')

@app.route('/intermediary')
def intermediary():
    return render_template('intermediary.html')

@app.route('/training')
def training():
    return render_template('training.html')

@app.route('/calculate_offer', methods=['POST'])
def calculate_offer():
    try:
        data = request.json
        user_info = extract_user_info(data)
        months_free = calculate_months_free(user_info)
        offer_bin, offer_str = eligibility(months_free)
        total_payable, value, formatted_total_payable, formatted_value = calculate_financials(user_info, months_free)
        csv_file_path = os.path.join('data', db_schema_searches)
        save_outcomes(data, csv_file_path, user_info, months_free, offer_bin, offer_str, value, total_payable)

        return jsonify({
            'result': offer_str,
            'eligible': offer_bin,
            'value': formatted_value,
            'total_payable': formatted_total_payable,
            'user_data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def extract_user_info(data):
    """
    Extract user information from a given dictionary and return it in a standardized format.

    Args:
        data (dict): A dictionary containing user data with the following keys:
            - 'registration-number' (str): Registration number as a string.
            - 'renewal-date' (str): Renewal date in 'YYYY-MM-DD' format.
            - 'payment-frequency' (str): Payment frequency.
            - 'annual-subs' (str): Total annual subscriptions as a string.
            - 'months-arrears' (str): Number of months in arrears as a string.
            - 'months-free-last' (str): Number of months free last year.
            - 'months-free-this' (str): Number of months free this year as a string.
            - 'color-segment' (str): Color segment.
            - 'claims-paid' (str): Claims paid.
            - 'url' (str, optional): URL if available.

    Returns:
        dict: A dictionary with the following keys:
            - 'registration' (float): Registration number as a float.
            - 'renewal' (datetime): Renewal date as a datetime object.
            - 'payment_frequency' (str): Payment frequency.
            - 'total_annual_subs' (float): Total annual subscriptions as a float.
            - 'arrears' (float): Number of months in arrears as a float.
            - 'financial_distress' (int): Set to 0.
            - 'mf_last_year' (str): Number of months free last year.
            - 'mf_this_year' (float): Number of months free this year as a float.
            - 'segment' (str): Color segment.
            - 'claims_paid' (str): Claims paid.
            - 'url' (str, optional): URL if available.
    """
    return {
        'registration': float(data['registration-number']),
        'renewal': datetime.strptime(data['renewal-date'], '%Y-%m-%d'),
        'payment_frequency': data['payment-frequency'],
        'total_annual_subs': float(data['annual-subs']),
        'arrears': float(data['months-arrears']),
        'financial_distress': 0,
        'mf_last_year': str(data['months-free-last']),
        'mf_this_year': float(data['months-free-this']),
        'segment': str(data['color-segment']),
        'claims_paid': str(data['claims-paid']),
        'url': data.get('url')
    }
def calculate_months_free(user_info):
    """
    Calculate the number of months free for a user based on their information.

    Args:
        user_info (dict): A dictionary containing user information with the following keys:
            - 'total_annual_subs' (float): Total annual subscriptions.
            - 'registration' (float): Registration number.
            - 'arrears' (float): Number of months in arrears.
            - 'financial_distress' (int): Financial distress status (not used in this calculation).
            - 'mf_last_year' (str): Number of months free last year.
            - 'mf_this_year' (float): Number of months free this year.
            - 'segment' (str): Color segment.
            - 'claims_paid' (str): Claims paid.

    Returns:
        int: The calculated number of months free.
    """
    return calculate_months(
        user_info['total_annual_subs'],
        user_info['registration'],
        user_info['arrears'],
        user_info['financial_distress'],
        user_info['mf_last_year'],
        user_info['mf_this_year'],
        user_info['segment'],
        user_info['claims_paid']
    )

def calculate_financials(user_info, months_free):
    """
    Calculate financials based on user information and number of months free.

    Args:
        user_info (dict): A dictionary containing user information with the following keys:
            - 'total_annual_subs' (float): Total annual subscriptions.
            - 'payment_frequency' (str): Payment frequency.
            - 'renewal' (datetime): Renewal date.
            - 'arrears' (float): Number of months in arrears (not used in this calculation).
            - 'financial_distress' (int): Financial distress status (not used in this calculation).
            - 'mf_last_year' (str): Number of months free last year (not used in this calculation).
            - 'mf_this_year' (float): Number of months free this year (not used in this calculation).
            - 'segment' (str): Color segment (not used in this calculation).
            - 'claims_paid' (str): Claims paid (not used in this calculation).

        months_free (int): Number of months free.

    Returns:
        tuple: A tuple containing the following elements:
            - total_payable (float): Total payable amount after considering months free.
            - value (float): Value after deducting total payable from total annual subscriptions.
            - formatted_total_payable (str): Total payable amount formatted as a currency string.
            - formatted_value (str): Value formatted as a currency string.
    """
    total_payable = calculate_value(
        user_info['total_annual_subs'],
        user_info['payment_frequency'],
        user_info['renewal'],
        months_free
    )
    value = user_info['total_annual_subs'] - total_payable
    formatted_total_payable = format_currency(total_payable)
    formatted_value = format_currency(value)
    return total_payable, value, formatted_total_payable, formatted_value

def save_outcomes(data, csv_file_path, user_info, months_free, offer_bin, offer_str, value, total_payable):
    """
    Save outcomes and user information to a CSV file.

    Args:
        data (dict): A dictionary containing additional data.
        csv_file_path (str): The file path of the CSV file to save the outcomes.
        user_info (dict): A dictionary containing user information with the following keys:
            - 'registration' (float): Registration number.
            - 'renewal' (datetime): Renewal date.
            - 'payment_frequency' (str): Payment frequency.
            - 'total_annual_subs' (float): Total annual subscriptions.
            - 'arrears' (float): Number of months in arrears.
            - 'financial_distress' (int): Financial distress status.
            - 'mf_last_year' (str): Number of months free last year.
            - 'mf_this_year' (float): Number of months free this year.
            - 'segment' (str): Color segment.
            - 'claims_paid' (str): Claims paid.
            - 'url' (str): URL.
        months_free (int): Number of months free.
        offer_bin (str): Binary representation of the offer.
        offer_str (str): String representation of the offer.
        value (float): Value after deducting total payable from total annual subscriptions.
        total_payable (float): Total payable amount after considering months free.
    """
    row_data = [
        user_info['registration'],
        user_info['renewal'],
        user_info['payment_frequency'],
        user_info['total_annual_subs'],
        user_info['arrears'],
        user_info['financial_distress'],
        user_info['mf_last_year'],
        user_info['mf_this_year'],
        user_info['segment'],
        user_info['claims_paid'],
        user_info['url'],
        months_free,
        offer_bin,
        offer_str,
        value,
        total_payable,
        datetime.now()
    ]

    if 'intermediary' in user_info['url']:
        intermediary = data['intermediary']
        intermediary_advisor = data['intermediary-advisor']
        row_data.extend([intermediary, intermediary_advisor])
    else:
        row_data.extend(['', ''])

    save_to_csv(csv_file_path, row_data)

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        user_data = request.json.get('user_data', {})
        outcomes_data = request.json.get('outcomes_data', {})
        url = request.json.get('url')
        csv_file_path = os.path.join('data', db_schema_outcomes)
        row_data = prepare_submission_data(user_data, outcomes_data, url)
        save_to_csv(csv_file_path, row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def prepare_submission_data(user_data, outcomes_data, url):
    """
    Prepare data for submission to a database or file.

    Args:
        user_data (dict): A dictionary containing user data with the following keys:
            - 'registration-number' (str, optional): Registration number.
            - 'renewal-date' (str, optional): Renewal date.
            - 'annual-subs' (str, optional): Total annual subscriptions.
            - 'color-segment' (str, optional): Color segment.
            - 'claims-paid' (str, optional): Claims paid.
            - 'payment-frequency' (str, optional): Payment frequency.
            - 'months-arrears' (str, optional): Number of months in arrears.
            - 'months-free-last' (str, optional): Number of months free last year.
            - 'months-free-this' (str, optional): Number of months free this year.
            - 'intermediary' (str, optional): Intermediary.
            - 'intermediary-advisor' (str, optional): Intermediary advisor.
        outcomes_data (dict): A dictionary containing outcomes data with the following keys:
            - 'offer' (str, optional): Offer.
            - 'offer-accepted' (str, optional): Offer accepted.
        url (str): URL.

    Returns:
        list: A list containing prepared data for submission, with the following elements:
            - Registration number.
            - Renewal date.
            - Total annual subscriptions.
            - Color segment.
            - Claims paid.
            - Payment frequency.
            - Number of months in arrears.
            - Number of months free last year.
            - Number of months free this year.
            - Current date and time.
            - URL.
            - Offer.
            - Offer accepted.
            - Intermediary (if present in URL).
            - Intermediary advisor (if present in URL).
    """
    base_row_data = [
        user_data.get('registration-number', ''),
        user_data.get('renewal-date', ''),
        user_data.get('annual-subs', ''),
        user_data.get('color-segment', ''),
        user_data.get('claims-paid', ''),
        user_data.get('payment-frequency', ''),
        user_data.get('months-arrears', ''),
        user_data.get('months-free-last', ''),
        user_data.get('months-free-this', ''),
        datetime.now(),
        url,
        outcomes_data.get('offer', ''),
        outcomes_data.get('offer-accepted', '')
    ]

    if 'intermediary' in url:
        base_row_data.extend([
            user_data.get('intermediary', ''),
            user_data.get('intermediary-advisor', '')
        ])
    else:
        base_row_data.extend(['', ''])

    return base_row_data

if __name__ == '__main__':
    app.run(debug=True)