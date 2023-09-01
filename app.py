import streamlit as st
import pandas as pd
from src.pd_functions import *
import base64
from streamlit.components.v1 import html
import random
import math

# Path to results
RESULTS_PATH = 'data/results.csv'

def main():
    # Get participant name
    participant_name = get_participant_name()

    # Handle file upload
    if participant_name:
        uploaded_file = st.file_uploader("Choose a file")
        process_file_upload(uploaded_file, participant_name)

    # Show leaderboard
    try:
        show_leaderboard()
    except:
        st.write("There are no submissions yet.")

def get_participant_name():
    text_input_container = st.empty()
    text_input_container.text_input("Introduce participant name: ", key="text_input")

    if st.session_state.text_input != "":
        text_input_container.empty()
        st.info(f'Participant name {st.session_state.text_input}')
        return st.session_state.text_input

    return None

def process_file_upload(uploaded_file, participant_name):
    if uploaded_file is not None:
        try:
            test = get_ready_test(RESULTS_PATH, uploaded_file)
            participant_results = get_metrics(RESULTS_PATH, test)

            st.success('Dataframe uploaded successfully!')
            if (participant_results.iloc[0,3]) == 0:
                autoplay_audio('static/claps.mp3')
                rain("healed.png",math.floor(random.random()*100))
            else:
                autoplay_audio('static/poison.mp3')
                rain("poisoned.png",math.floor(random.random()*100),300)

            display_participant_results(participant_results)

            update_submissions(participant_results)

        except Exception as e:
            st.error(f"The file has a wrong format, please, review it and load it again. {str(e)}")

def display_participant_results(participant_results):
    st.title('Participant results')
    st.dataframe(participant_results)

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )
def rain(photo,x,width=100):
    # Define your javascript
   
    my_css="""
    .rainPhoto {
  position: fixed;
  animation-duration: 20s;
  animation-name: slidedown;
  animation-fill-mode: forwards;
  width: %dpx;
  top: 0;
  left: %dvw;
}

@keyframes slidedown {
  to {
    top: 120%%;
  }
}
    """ % (width,x)
    # Wrapt the javascript as html code
    my_html = f'<style>{my_css}</style><img class="rainPhoto" src="./app/static/{photo}"/>'
    st.write(my_html,unsafe_allow_html=True)


if __name__ == "__main__":
    main()
