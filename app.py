import pandas as pd
import os

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)
from utils import save_to_csv

# static variables
db = 'consumer_retention'
db_schema_customers = f'{db}-customers.csv'
db_schema_searches = f'{db}-searches.csv'
db_schema_form = f'{db}-registration-details.csv'
db_schema_outcomes = f'{db}-outcomes.csv'

# load the customers CSV file into a DataFrame
customers_df = pd.read_csv(f'data/{db_schema_customers}')

app = Flask(__name__)

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

@app.route('/find_customer', methods=['POST'])
def find_customer():
    try:
        data = request.json
        guid = data.get('guid')
        registration_number = data.get('registration-number')
        url = data.get('url')
        search_datetime = data.get('search_datetime')

        # write location for search db
        csv_file_path = os.path.join('data', db_schema_searches)

        # filter for relevant customer based on registration-number
        customer = customers_df[customers_df['registration-number'].astype(str) == str(registration_number)]

        if customer.empty:
            row_data = [guid, registration_number, url, pd.to_datetime(search_datetime), 'fail']
            save_to_csv(csv_file_path, row_data)
            return jsonify({'error': 'customer details empty'}), 404

        # retrieve user_info
        customer_data = customer.to_dict(orient='records')[0]

        # write to csv
        row_data = [guid, registration_number, url, pd.to_datetime(search_datetime), 'success']
        save_to_csv(csv_file_path, row_data)

        return jsonify({
            'db_registration_number': float(customer_data['registration-number']),
            'db_renewal': datetime.strptime(customer_data['renewal-date'], '%Y-%m-%d'),
            'db_payment_frequency': customer_data['payment-frequency'],
            'db_total_annual_subs': float(customer_data['annual-subs']),
            'db_arrears': float(customer_data['months-arrears']),
            'db_financial_distress': 0,
            'db_mf_last_year': str(customer_data['months-free-last']),
            'db_mf_this_year': float(customer_data['months-free-this']),
            'db_segment': str(customer_data['color-segment']),
            'db_claims_paid': str(customer_data['claims-paid']),
            'db_intermediary': str(customer_data['intermediary'])
                })
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 400

@app.route('/calculate_offer', methods=['POST'])
def calculate_offer():

    data = request.json
    print(data)
    if 'intermediary' in data['url']:

        user_info = {
            'registration-number': float(data['registration-number']),
            'user-renewal-date': datetime.strptime(data['user-renewal-date'], '%Y-%m-%d'),
            'user-payment-frequency': data['user-payment-frequency'],
            'user-annual-subs': float(data['user-annual-subs']),
            'user-months-arrears': float(data['user-months-arrears']),
            'user-financial-distress': 0,
            'user-months-free-last': str(data['user-months-free-last']),
            'user-months-free-this': float(data['user-months-free-this']),
            'user-color-segment': str(data['user-color-segment']),
            'user-claims-paid': str(data['user-claims-paid']),
            'user-intermediary': str(data['user-intermediary']),
            'user-intermediary-advisor': str(data['user-intermediary-advisor']),
            'url': data.get('url')
        }

    else:

        user_info = {
            'registration-number': float(data['registration-number']),
            'user-renewal-date': datetime.strptime(data['user-renewal-date'], '%Y-%m-%d'),
            'user-payment-frequency': data['user-payment-frequency'],
            'user-annual-subs': float(data['user-annual-subs']),
            'user-months-arrears': float(data['user-months-arrears']),
            'user-financial-distress': 0,
            'user-months-free-last': str(data['user-months-free-last']),
            'user-months-free-this': float(data['user-months-free-this']),
            'user-color-segment': str(data['user-color-segment']),
            'user-claims-paid': str(data['user-claims-paid']),
            'url': data.get('url')
        }

    months_free = calculate_months_free(user_info)
    offer_bin, offer_str = eligibility(months_free)
    total_payable, value, formatted_total_payable, formatted_value = calculate_financials(user_info, months_free)

    # write location for form db
    csv_file_path = os.path.join('data', db_schema_form)

    # create data outputs as a list
    row_data = [data['guid'], data['calculate_datetime'], data['registration-number'],
                data['user-renewal-date'], data['user-payment-frequency'], data['user-annual-subs'],
                data['user-months-arrears'], data['user-months-free-last'], data['user-months-free-this'],
                data['user-color-segment'], data['user-claims-paid'], data['db_arrears'],
                data['db_claims_paid'], data['db_financial_distress'], data['db_mf_last_year'],
                data['db_mf_this_year'], data['db_payment_frequency'], data['db_registration_number'],
                data['db_renewal'], data['db_segment'], data['db_total_annual_subs'],
                datetime.now(), data['url']]

    if 'intermediary' in data['url']:
        intermediary = data['user-intermediary']
        intermediary_advisor = data['user-intermediary-advisor']
        row_data.extend([intermediary, intermediary_advisor])
    else:
        row_data.extend(['', ''])

    # save to csv
    save_to_csv(csv_file_path, row_data)

    if 'intermediary' in data['url']:

        output = jsonify({
        'result': offer_str,
        'eligible': offer_bin,
        'value': formatted_value,
        'total_payable': formatted_total_payable,
        'db_registration_number': user_info['registration-number'],
        'db_renewal': user_info['user-renewal-date'],
        'db_payment_frequency': user_info['user-payment-frequency'],
        'db_total_annual_subs': user_info['user-annual-subs'],
        'db_arrears': user_info['user-months-arrears'],
        'db_financial_distress': user_info['user-financial-distress'],
        'db_mf_last_year': user_info['user-months-free-last'],
        'db_mf_this_year': user_info['user-months-free-this'],
        'db_segment': user_info['user-color-segment'],
        'db_claims_paid': user_info['user-claims-paid'],
        'db_intermediary': user_info['user-intermediary'],
        'db_intermediary_advisor': user_info['user-intermediary-advisor']
        # 'user_data': "data"
            })

    else:

        output = jsonify({
        'result': offer_str,
        'eligible': offer_bin,
        'value': formatted_value,
        'total_payable': formatted_total_payable,
        'db_registration_number': user_info['registration-number'],
        'db_renewal': user_info['user-renewal-date'],
        'db_payment_frequency': user_info['user-payment-frequency'],
        'db_total_annual_subs': user_info['user-annual-subs'],
        'db_arrears': user_info['user-months-arrears'],
        'db_financial_distress': user_info['user-financial-distress'],
        'db_mf_last_year': user_info['user-months-free-last'],
        'db_mf_this_year': user_info['user-months-free-this'],
        'db_segment': user_info['user-color-segment'],
        'db_claims_paid': user_info['user-claims-paid'],
        # 'db_intermediary': user_info['user-intermediary'],
        # 'db_intermediary_advisor': user_info['user-intermediary-advisor']
        # 'user_data': "data"
            })

    return output

def calculate_months_free(user_info):
    return calculate_months(
        user_info['user-annual-subs'],
        user_info['registration-number'],
        user_info['user-months-arrears'],
        user_info['user-financial-distress'],
        user_info['user-months-free-last'],
        user_info['user-months-free-this'],
        user_info['user-color-segment'],
        user_info['user-claims-paid']
    )

def calculate_financials(user_info, months_free):
    total_payable = calculate_value(
        user_info['user-annual-subs'],
        user_info['user-payment-frequency'],
        user_info['user-renewal-date'],
        months_free
    )
    value = user_info['user-annual-subs'] - total_payable
    formatted_total_payable = format_currency(total_payable)
    formatted_value = format_currency(value)
    return total_payable, value, formatted_total_payable, formatted_value

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        user_data = request.json.get('user_data', {})
        outcomes_data = request.json.get('outcomes_data', {})
        guid = request.json.get('guid')
        csv_file_path = os.path.join('data', db_schema_outcomes)
        row_data = [guid, user_data['registration-number'], user_data['user-annual-subs'],
                    outcomes_data['offer'], outcomes_data['offer-accepted'], datetime.now()]
        save_to_csv(csv_file_path, row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)