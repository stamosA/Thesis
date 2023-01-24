import logging
from pathlib import Path
path = Path.cwd()
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from utils import similar_multi, unique_list_elements, removeNonAscii, list_to_dict, remove_greek_accents
from text_cleansing import words_to_delete, stopwords, mapping_list

# Load maintenance file
activities = pd.read_excel(path.joinpath('MaintenanceActivitiesDataSet_20210802.xlsx'))

# Capitalize activities description text
activities['ActivityDescription_Curated'] = activities.ActivityDescription.str.upper().copy()

# Remove greek accents
activities = remove_greek_accents(activities, 'ActivityDescription_Curated')

# Separate words that are glued with special characters in order to simplify word splitting 
activities['ActivityDescription_Curated'] = (
    activities.ActivityDescription_Curated.str.upper()
        .str.replace('&', ' & ')  # Split words with & in between
        .str.replace(',', ' , ')  # Split words with , in between
        .str.replace('.', '. ')  # Split words with . in between
        .str.replace('-', ' ')  # Split words with - in between
        .str.replace(':', ' ')  # Split words with : in between
        .str.replace('>', ' ')  # Split words with > in between
        .str.replace('(', ' ( ')  # Split words with ( in between
        .str.replace(')', ' ) ')  # Split words with ) in between
        .str.replace('  ', ' ')  # Replace double space "  " with single space " "
)


# Delete stopwords, single characters and words which do not add valuable info to the activities description
for word in words_to_delete+stopwords:
    activities['ActivityDescription_Curated'] = (
        activities.ActivityDescription_Curated
        .str.replace(fr' {word} ', ' ', regex=True)
        .str.replace(fr'^{word} ', ' ', regex=True)
        .str.replace(fr' {word}$', ' ', regex=True)
    )
    

# Perform Lemmatization 
mapping_dict = list_to_dict(mapping_list)
for k, v in mapping_dict.items():
    print(k, v)
    activities['ActivityDescription_Curated'] = (
        activities.ActivityDescription_Curated
            .str.replace(fr' {k} ', f' {v} ', regex=True)
            .str.replace(fr'^{k} ', f'{v} ', regex=True)
            .str.replace(fr' {k}$', f' {v}', regex=True)
    )
# Remove extra whitespaces
activities['ActivityDescription_Curated'] = activities.ActivityDescription_Curated.str.strip()
activities['ActivityDescription_Curated'] = activities.ActivityDescription_Curated.str.replace(r'\s+', ' ', regex=True)

# List of unique activity descriptions
activities_descriptions = unique_list_elements(activities['ActivityDescription_Curated'].values.tolist())
# Frequency of activity descriptions
frequency_of_activities = activities.groupby(
    'ActivityDescription_Curated').ActivityDescription_Curated.count().sort_values(ascending=False)
# List of unique words met in the activities description
list_of_words = []
for x in activities_descriptions:
    list_of_words += str(x).split()
list_of_words = unique_list_elements(list_of_words)
list_of_words.sort()


print('Number of unique activity descriptions: {}'.format(activities['ActivityDescription_Curated'].nunique()))
print('Number of rows in maintenance activities: {}'.format(activities.shape[0]))
print('Number of unique activity descriptions: {}'.format(len(activities_descriptions)))
print('Number of unique words in activities description: {}'.format(len(list_of_words)))


# Actual activity time (imputation)
activities['ActualActivityTime_Curated'] = activities.ActualActivityTime.copy()

# Number of rows with nonzero ActualActivityTime 
print('Number of rows with nonzero ActualActivityTime: ', (activities.ActualActivityTime>0).sum())
# Number of rows with nonzero ActualActivityTime or ActivityTime or EstimatedDuration
print('Number of rows with nonzero ActualActivityTime or ActivityTime or EstimatedDuration: ', (activities[['ActivityTime','ActualActivityTime','EstimatedDuration']]!=0).any(axis=1).sum())
activities.loc[activities.ActualActivityTime.eq(0) & activities.ActivityTime.ne(0), 'ActualActivityTime_Curated'] = activities.loc[activities.ActualActivityTime.eq(0) & activities.ActivityTime.ne(0), 'ActivityTime']
activities.loc[activities.ActualActivityTime.eq(0) & activities.EstimatedDuration.ne(0), 'ActualActivityTime_Curated'] = activities.loc[activities.ActualActivityTime.eq(0) & activities.EstimatedDuration.ne(0), 'EstimatedDuration']

# Number of rows with nonzero ActualActivityTime 
print('Number of rows with nonzero ActualActivityTime_Curated: ', (activities.ActualActivityTime_Curated>0).sum())
print('Number of rows with zero ActualActivityTime_Curated: ', (activities.ActualActivityTime_Curated==0).sum())

# Median activity time grouppped by pump and activity
median_pupmp_activity_time = activities.groupby(['EquipmentHashKey', 'ActivityDescription_Curated'],as_index=False).ActualActivityTime_Curated.median().rename(columns={'ActualActivityTime_Curated': 'Pump_Activity_Median_Time'})
activities = activities.merge(median_pupmp_activity_time, on=['EquipmentHashKey', 'ActivityDescription_Curated'])

# Median activity time grouppped by activity
median_activity_time = activities.groupby(['ActivityDescription_Curated'],as_index=False).ActualActivityTime_Curated.median().rename(columns={'ActualActivityTime_Curated': 'Activity_Median_Time'})
activities = activities.merge(median_activity_time, on=['ActivityDescription_Curated'])

activities.loc[activities.ActualActivityTime_Curated.eq(0) & activities.Pump_Activity_Median_Time.ne(0), 'ActualActivityTime_Curated'] = activities.loc[activities.ActualActivityTime_Curated.eq(0) & activities.Pump_Activity_Median_Time.ne(0), 'Pump_Activity_Median_Time']
activities.loc[activities.ActualActivityTime_Curated.eq(0) & activities.Activity_Median_Time.ne(0), 'ActualActivityTime_Curated'] = activities.loc[activities.ActualActivityTime_Curated.eq(0) & activities.Activity_Median_Time.ne(0), 'Activity_Median_Time']

# Number of rows with nonzero ActualActivityTime 
print('Number of rows with nonzero ActualActivityTime_Curated: ', (activities.ActualActivityTime_Curated>0).sum())
print('Number of rows with zero ActualActivityTime_Curated: ', (activities.ActualActivityTime_Curated==0).sum())


# Fill in missing ActualStartingDate values with EstimatedStartingDate values
activities['ActualStartingDate_Curated'] = activities.ActualStartingDate.copy()

activities.loc[activities.ActualStartingDate_Curated.isnull() 
               & activities.EstimatedStartingDate.notnull(), 'ActualStartingDate_Curated'] = \
    activities.loc[activities.ActualStartingDate_Curated.isnull() 
                   & activities.EstimatedStartingDate.notnull(), 'EstimatedStartingDate']

# Months column
activities['Month'] = activities.ActualStartingDate_Curated.dt.month




# Plot on  sum of activity time per maintencaetype
df = activities.groupby(['MaintenanceType'], as_index=False).ActualActivityTime_Curated.sum()
df = df.pivot_table(index ='MaintenanceType', values='ActualActivityTime_Curated') 
plt.style.use('seaborn')
df.plot.bar(stacked=True)


df_equip_act = activities.groupby(['EquipmentHashKey'], as_index=False).ActualActivityTime_Curated.sum()

df_equip_count = activities.groupby(['EquipmentHashKey'], as_index=False).ActualActivityTime_Curated.count()

df_activity_count = activities.groupby(['ActivityDescription_Curated'], as_index=False).ActualActivityTime_Curated.count()

df_activity_act = activities.groupby(['ActivityDescription_Curated'], as_index=False).ActualActivityTime_Curated.sum()


# Plot on  sum of activity time per Month
df = activities.groupby(['Month'], as_index=False).ActualActivityTime_Curated.sum()
df = df.pivot_table(index ='Month', values='ActualActivityTime_Curated') 
plt.style.use('seaborn')
df.plot.bar(stacked=True)

plt.show()

plt.clf()


import seaborn as sns

plt.style.use('seaborn')
sns.countplot(activities['Month'], palette = "Set2")
plt.show()


plt.clf()


plt.style.use('seaborn')
sns.countplot(activities['MaintenanceType'], palette = "Set2")
plt.show()


plt.clf()




# Plot on activity time per month per maintenacetype
df = activities.groupby(['Month', 'MaintenanceType'], as_index=False).ActualActivityTime_Curated.sum()
df = df.pivot_table(index ='Month', columns='MaintenanceType', values='ActualActivityTime_Curated') 
plt.style.use('seaborn')
df.plot.bar(stacked=True)
plt.show()

# Plot on count per month per maintenacetype
df = activities.groupby(['Month', 'MaintenanceType'], as_index=False).ActualActivityTime_Curated.count()
df = df.pivot_table(index ='Month', columns='MaintenanceType', values='ActualActivityTime_Curated') 
plt.style.use('seaborn')
df.plot.bar(stacked=True)
plt.show()

plt.style.use('seaborn')
df = activities.groupby(['EquipmentHashKey', 'MaintenanceType']).ActualActivityTime_Curated.agg(['count', 'sum', 'mean', 'min', 'max'])
df = df.reset_index()
df['color'] = 'green'
df.loc[df.MaintenanceType.eq('Corrective'), 'color'] = 'red'
df.plot.scatter(x='count', y='mean', s=df['max'].values, c=df['color'].values, alpha=0.5)
plt.ylabel('Average activity time')
plt.xlabel('Number of maintenance activities per pump')
plt.show()


#gia to sum tou corrective
TimeRestoringDamage=df.pivot_table(index='EquipmentHashKey', columns='MaintenanceType', values='sum')
TimeRestoringDamage['percentage']= 100 * TimeRestoringDamage.Corrective / TimeRestoringDamage.sum(axis=1)
TimeRestoringDamage=TimeRestoringDamage.fillna(0)
TimeRestoringDamage.plot(x='Corrective', y='percentage', style='o')
plt.show()

#gia to count tou corrective
TimesDestroyed=df.pivot_table(index='EquipmentHashKey', columns='MaintenanceType', values='count')
TimesDestroyed['percentage']= 100 * TimesDestroyed.Corrective / TimesDestroyed.sum(axis=1)
TimesDestroyed=TimesDestroyed.fillna(0)
TimesDestroyed.plot(x='Corrective', y='percentage', style='o')
plt.show()


#gia to sum tou preventive
TimeRestoringDamage=df.pivot_table(index='EquipmentHashKey', columns='MaintenanceType', values='sum')
TimeRestoringDamage['percentage']= 100 * TimeRestoringDamage.Preventive / TimeRestoringDamage.sum(axis=1)
TimeRestoringDamage=TimeRestoringDamage.fillna(0)
TimeRestoringDamage.plot(x='Preventive', y='percentage', style='o')
plt.show()

#gia to count tou preventive
TimesDestroyed=df.pivot_table(index='EquipmentHashKey', columns='MaintenanceType', values='count')
TimesDestroyed['percentage']= 100 * TimesDestroyed.Preventive / TimesDestroyed.sum(axis=1)
TimesDestroyed=TimesDestroyed.fillna(0)
TimesDestroyed.plot(x='Preventive', y='percentage', style='o')
plt.show()




#gia to sum tou predictive
TimeRestoringDamage=df.pivot_table(index='EquipmentHashKey', columns='MaintenanceType', values='sum')
TimeRestoringDamage['percentage']= 100 * TimeRestoringDamage.Predictive / TimeRestoringDamage.sum(axis=1)
TimeRestoringDamage=TimeRestoringDamage.fillna(0)
TimeRestoringDamage.plot(x='Predictive', y='percentage', style='o')
plt.show()

#gia to count tou predictive
TimesDestroyed=df.pivot_table(index='EquipmentHashKey', columns='MaintenanceType', values='count')
TimesDestroyed['percentage']= 100 * TimesDestroyed.Predictive / TimesDestroyed.sum(axis=1)
TimesDestroyed=TimesDestroyed.fillna(0)
TimesDestroyed.plot(x='Predictive', y='percentage', style='o')
plt.show()





