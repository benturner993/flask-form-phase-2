import pandas as pd
import os

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from calculator import (calculate_months, calculate_value,
                        eligibility, format_currency)
from utils import (save_to_csv, save_transposed_to_csv)

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

        # write location for search db
        csv_file_path = os.path.join('data', db_schema_searches)

        # add in a broker specific filter here using url

        # filter for relevant customer based on registration-number
        customer = customers_df[customers_df['registration-number'].astype(str) == str(data['user-registration-number'])]

        if customer.empty:
            return jsonify({'Error 404': 'Customer details empty.'}), 404

        # retrieve user_info
        customer_data = customer.to_dict(orient='records')[0]

        # write to csv
        row_data = [data['guid'], data['user-registration-number'], data['url'], pd.to_datetime(data['search_datetime'])]
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

    user_info = {
            'user-registration-number': float(data['user-registration-number']),
            'user-renewal-date': datetime.strptime(data['user-renewal-date'], '%Y-%m-%d'),
            'user-payment-frequency': data['user-payment-frequency'],
            'user-annual-subs': float(data['user-annual-subs']),
            'user-months-arrears': float(data['user-months-arrears']),
            'user-financial-distress': 0,
            'user-months-free-last': str(data['user-months-free-last']),
            'user-months-free-this': float(data['user-months-free-this']),
            'user-color-segment': str(data['user-color-segment']),
            'user-claims-paid': str(data['user-claims-paid']),
            'user-intermediary': str(''),
            'user-intermediary-advisor': str(''),
            'url': data.get('url')
    }

    if 'intermediary' in data['url']:

            user_info['user-intermediary']: str(data['user-intermediary'])
            user_info['user-intermediary-advisor']: str(data['user-intermediary-advisor'])

    # calculate months free and eligibility
    months_free = calculate_months_free(user_info)
    offer_bin, offer_str = eligibility(months_free)
    total_payable, value, formatted_total_payable, formatted_value = calculate_financials(user_info, months_free)

    # save inputs and loaded db inputs into csv

    # write location for form db
    form_csv_file_path = os.path.join('data', db_schema_form)

    # Define the fields
    registration_details_fields = [
        'registration-number',
        'renewal-date',
        'payment-frequency',
        'annual-subs',
        'months-arrears',
        # 'user-financial-distress',
        'months-free-last',
        'months-free-this',
        'color-segment',
        'claims-paid',
        'timestamp',
        'intermediary',
        'intermediary-advisor'
    ]

    # Define the row data
    row_data = [
        data['user-registration-number'],
        pd.to_datetime(data['user-renewal-date']),
        data['user-payment-frequency'],
        data['user-annual-subs'],
        data['user-months-arrears'],
        # data['user-financial-distress'],
        data['user-months-free-last'],
        data['user-months-free-this'],
        data['user-color-segment'],
        data['user-claims-paid'],
        datetime.now()]

    if 'intermediary' in data['url']:
        intermediary = data['user-intermediary']
        intermediary_advisor = data['user-intermediary-advisor']
        row_data.extend([intermediary, intermediary_advisor])
    else:
        row_data.extend(['',''])

    # Prepare transposed data
    transposed_data = []
    for field, value in zip(registration_details_fields, row_data):
        transposed_data.append([data['guid'], 'user-input', field, value])

    # Function to save transposed data to CSV
    save_transposed_to_csv(form_csv_file_path, transposed_data)

    # Define the row data
    row_data = [
        data['db_registration_number'],
        pd.to_datetime(data['db_renewal']),
        data['db_payment_frequency'],
        data['db_total_annual_subs'],
        data['db_arrears'],
        # data['db_financial_distress'],
        data['db_mf_last_year'],
        data['db_mf_this_year'],
        data['db_segment'],
        data['db_claims_paid'],
        datetime.now()]

    if 'intermediary' in data['url']:
        intermediary = data['db_intermediary']
        intermediary_advisor = str('')
        row_data.extend([intermediary, intermediary_advisor])
    else:
        row_data.extend(['',''])

    # Prepare transposed data
    transposed_data = []
    for field, value in zip(registration_details_fields, row_data):
        transposed_data.append([data['guid'], 'database', field, value])

    # Function to save transposed data to CSV
    save_transposed_to_csv(form_csv_file_path, transposed_data)

    # create json output
    if 'intermediary' in data['url']:

        output = jsonify({
        'result': offer_str,
        'eligible': offer_bin,
        'value': formatted_value,
        'total_payable': formatted_total_payable,
        'db_registration_number': user_info['user-registration-number'],
        'db_renewal': pd.to_datetime(user_info['user-renewal-date']),
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
        'db_registration_number': user_info['user-registration-number'],
        'db_renewal': pd.to_datetime(user_info['user-renewal-date']),
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
        user_info['user-registration-number'],
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
        data = request.json
        print(data)

        csv_file_path = os.path.join('data', db_schema_outcomes)

        base_row_data = [
            data['guid'],
            pd.to_datetime(data['currentDatetime']),
            data['webUrl'],
            data['registrationNumber'],
            data['userRenewalDate'],
            data['userAnnualSubs'],
            data['totalPayable'],
            data['customerOffer'],
            data['customerOfferAccepted']
        ]

        save_to_csv(csv_file_path, base_row_data)

        return jsonify({'message': 'Successfully submitted.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)