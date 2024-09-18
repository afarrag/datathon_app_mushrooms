import pandas as pd
import numpy as np
import streamlit as st
import numpy as np
import os

from urllib.parse import quote_plus

dbuser,dbpass,dbhost,dbport = os.getenv('dbuser'),quote_plus(os.getenv('dbpass')),os.getenv('dbhost'),os.getenv('dbport')
connection_string = f'mysql+pymysql://{dbuser}:{dbpass}@{dbhost}:{dbport}/mushroom'

def get_ready_test(RESULTS_PATH: str, uploaded_file):
    """
    This function prepares the test file to be evaluated and 
    check if it has the correct format.
    """
    results = pd.read_csv(RESULTS_PATH)
    results.columns = ['id', 'real']

    test = pd.read_csv(uploaded_file)
    if (test.columns.to_list() != ['Id', 'poisonous']):
        st.error('Column names must match "Id" and "poisonous" - case sensitive!')
        return 0
    if(test.shape != (1625, 2)):
        st.error('Your file should contain 1625 rows and 2 columns')
        return 0
    if((test.poisonous.unique().tolist() != [0, 1]) &
        (test.poisonous.unique().tolist() != [1, 0]) &
        (test.poisonous.unique().tolist() != [1]) &
            (test.poisonous.unique().tolist() != [0])):
        st.error('Predictions should only have values of 0 and 1')
        return 0
    if((test.Id == results.id).sum() != 1625):
        st.error(
            "Your Id column might be wrong or mixed up. " +
            "You should have same Id's as the test file. " +
            "Order of Id's should also be the same.")
        return 0
    test.columns = ['id', 'preds']

    return (
        test
        .assign(
            id=lambda df_: df_['id'].astype('int32'),
            preds=lambda df_: df_['preds'].astype('object'),
        )
    )


def get_metrics(RESULTS_PATH: str, test: pd.DataFrame):
    """
    This function calculates the metrics for the test file.
    Metrics are: Accuracy, Recall, Deaths, Edible but uneaten.
    """
    results = pd.read_csv(RESULTS_PATH)
    results.columns = ['id', 'real']

    row_evaoluation = (
        results
        .assign(
            id=lambda df_: df_['id'].astype('int32'),
            real=lambda df_: df_['real'].astype('object')
        )
        .merge(test, how='left', on='id')
        .assign(
            tp=lambda df_: np.where((df_['real'] == 1) & (
                df_['preds'] == 1), True, False),
            correct=lambda df_: df_['real'] == df_['preds'],
            fn=lambda df_: np.where((df_['real'] == 1) & (
                df_['preds'] == 0), True, False),
            opportunity_cost=lambda df_: np.where(
                (df_['real'] == 0) & (df_['preds'] == 1), True, False)
        )
        .agg({
            'tp': 'sum',
            'correct': 'sum',
            'fn': 'sum',
            'opportunity_cost': 'sum'
        })
    )

    return (
        pd.DataFrame([[
            st.session_state.text_input,
            row_evaoluation['tp'] /
            (row_evaoluation['tp'] + row_evaoluation['fn']),
            row_evaoluation['correct']/results.shape[0],
            row_evaoluation['fn'],
            row_evaoluation['opportunity_cost'],
            pd.Timestamp.now()
        ]],
            columns=['Participant', 'Recall', 'Accuracy', 'Deaths', 'Edible but uneaten', 'submission_time'])
    )


def plot_submissions():
    """
    This function plots the submissions over time given the 
    submissions.pkl file."""

    participant_submissions = (
        pd.read_sql("submissions",con=connection_string)
        .query('Participant == @st.session_state.text_input')
        .filter(['submission_time', 'Recall'])
        .set_index('submission_time')
        .copy()
    )
    if participant_submissions.shape[0] > 1:
        st.line_chart(participant_submissions)
    else:
        st.success('Congratulations on your first submission!')


def update_submissions(participant_results: pd.DataFrame):
    """
    This function updates the submissions.pkl file with the
    new results."""
    
    submissions_path = 'files_to_update/submissions.pkl'

    if os.path.isfile(submissions_path):
        all_submissions = pd.read_sql("submissions",con=connection_string)
    else:
        all_submissions = pd.DataFrame()

    (
        pd.concat([
            all_submissions,
            participant_results
        ])
        .to_sql("submissions",con=connection_string,if_exists='append', index=False)
    )



def show_leaderboard():
    """
    This function shows the leaderboard given the submissions.pkl"""

    st.title('LEADERBOARD')

    st.dataframe(
        pd.read_sql("submissions",con=connection_string)
        .assign(Attempts=lambda df_: df_.groupby('Participant')['Participant'].transform('count'))
        .sort_values(['Recall', 'Accuracy'], ascending=[False, False])
        .drop_duplicates(['Participant'], keep='first')
        .assign(position=lambda df_: range(1, len(df_)+1))
        .set_index('position')
        .filter(['Participant', 'Recall', 'Accuracy', 'Deaths', 'Edible but uneaten', 'Attempts'])
    )
