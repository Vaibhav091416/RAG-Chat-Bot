import streamlit as st

from utils import upload_to_dir
from utils import Indexer, Talk

import os
import sys
from pathlib import Path

from logger import logging
from exception import CustomException

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

#-------------------------------------------Function Starts-----------------------------------------------------------

@st.cache_resource(show_spinner=False)
def process_indexing(file_name):
    
    indexer=Indexer(save_dir,uploaded_file.name)
    store=indexer.indexing()
    return store
    
@st.cache_resource(show_spinner=False)
def process_talker(_store):
    talk = Talk(_store)
    return talk

#----------------------------------------------APP STARTS-------------------------------------------------------------

st.title("File Intelligence Hub")
uploaded_file = st.file_uploader("Upload your PDF or Excel file to begin", type=["pdf", "xlsx"])


save_dir = Path("./file_directory")



if uploaded_file is not None:

    file_name=f"{uploaded_file.name}"
    chat_file=os.path.join(save_dir,file_name)

    st.info(f"Selected file: {uploaded_file.name}")  
    logging.info("File Uploaded Successfully!")

    with st.spinner('Processing your files'):
        upload_to_dir(uploaded_file)
        try:
            logging.info("Indexer begins")
            store=process_indexing(uploaded_file.name)
        except Exception as e:
            st.info("Something Went Wrong")
            cust_error=CustomException(e,sys)
            logging.error(cust_error.error_message)
            st.stop()

        try: 
            talk=process_talker(store)
        except Exception as e:
            st.info("Something Went Wrong")
            cust_error=CustomException(e,sys)
            logging.error(cust_error.error_message)
            st.stop()
                    

    logging.info("Chat Section Begin")
    st.subheader(" Chat with your File 💬")

    
    user_question = st.chat_input("Ask a question about this document...")
    if user_question:
        if user_question.lower()=='exit':
            st.stop()
        try:
                for chat in talk.chat_history:
                    role='user' if chat.type=='human' else 'assistant'
                    with st.chat_message(role):
                        st.write(chat.content)

                with st.chat_message("user"):
                    st.write(user_question)
                    
                
                res = talk.chat(user_question)
                
                
                with st.chat_message("assistant"):
                    st.write(res)

        except Exception as e:
                logging.critical(f"There was an error while making the chat going\n{e}")
else:
    st.info("Please drop your file above to unlock the chat and analysis features.")