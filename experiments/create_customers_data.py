import pandas as pd
import os
import csv

# define the columns in the dataset
cols=['registration-number',
      'renewal-date',
      'payment-frequency',
      'annual-subs',
      'months-arrears',
      'months-free-last',
      'months-free-this',
      'color-segment',
      'claims-paid',
      'intermediary']

# create some example users to search
user1=[1,"2024-01-01","Monthly",1250,0,"No",0,"Red","Less Than £500", ""]
user2=[2,"2024-01-02","Monthly",999,0,"Yes",0,"Grey","More Than £1000", ""]
user3=[3,"2024-01-03","Monthly",123,0,"Yes",0,"Blue","Between £500 and £1000", ""]
user4=[4,"2024-01-04","Monthly",1250,0,"No",0,"Red","Less Than £500", "Active Quote"]
user5=[5,"2024-01-05","Monthly",999,0,"Yes",0,"Grey","More Than £1000", "Active Quote"]
user6=[6,"2024-01-06","Monthly",123,0,"Yes",0,"Blue","Between £500 and £1000", "Active Quote"]

# create a list of lists to write into csv file
data = [cols, user1, user2, user3, user4, user5, user6]

# change directory to data folder
os.chdir('.')
os.chdir('data')

# write output file
filename='consumer_retention-customers.csv'
with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)