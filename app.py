import streamlit as st
from model.t5 import T5Model
import logging


class mainUI:

    def __init__(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        
        st.set_page_config(page_title="Chat with PDF", page_icon=":books:")
        
        if "messages" not in st.session_state:
                st.session_state.messages = []
                st.session_state.messages.append({"role": "ai", "content": "Hello! I am a chatbot that can help you with your PDFs. Ask me anything!"})
        
        if "t5_model" not in st.session_state:
            with st.spinner('Setting up...'):
                st.session_state.t5_model = T5Model()                 
        
        self.t5 = st.session_state.t5_model
        
    def titleUI(self):
        st.title("PDF Chatbot :books:")
        st.markdown("This is a chatbot that allows you to upload PDFs and ask questions about them.")

    def uploadPdfUI(self):
        
        with st.sidebar:
            docs = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
            
            if 'current_doc_id' not in st.session_state:
                st.session_state.current_doc_id = None
                
            if docs is not None and docs._file_urls.file_id != st.session_state.current_doc_id:
                
                self.processPdf(docs)               
                st.session_state.current_doc_id = docs._file_urls.file_id
           
    @st.dialog("Processing PDF")      
    def processPdf(self, docs):
        
        st.write("Please don't close it until it successfully run.")
        st.write("Note: If your PDF size is large it will take some time to process.")
        
        with st.spinner("Please wait while we process the PDF..."):
            pdf_status= self.t5.preprocess(docs)
            logging.debug(f"Preprocess : {pdf_status}")
                   
        with st.spinner("Storing into vector database...."):           
            faiss_status= self.t5.faiss()
            logging.debug(f"faiss_status : {faiss_status}")
            
        with st.spinner("Almost done..."):            
            retrieve_status= self.t5.retrieve()
            logging.debug(f"retrieve_status : {retrieve_status}")
            
        logging.info("PDF Uploaded Successfully!")
            
        st.success("PDF Uploaded Successfully!")
        st.toast("PDF Uploaded Successfully!")
           
    def displayChatMessageUI(self):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    def displayLastChatMessageUI(self):
        with st.chat_message(st.session_state.messages[-1]["role"]):
                st.write(st.session_state.messages[-1]["content"])
            
    def chatInputUI(self) -> dict:
        return st.chat_input("Ask me anything!")
            
    def chatMessageHandler(self, message: str):         
        st.session_state.messages.append({"role": "user", "content": message}) 
        
        self.displayLastChatMessageUI()
        
        with st.spinner("Thinking...."):
            try:
                if st.session_state.current_doc_id is not None:
                    logging.debug(f"Query : {message}")
                    result = self.t5.query(message)
                else:
                    result = "Please upload a PDF before asking."
            except Exception as e:
                result = f"{e}. I am sorry, I could not understand that. Please try again."   
        
        # AI response
        st.session_state.messages.append({"role": "ai", "content": result})
        st.rerun()
          
    def clearHistory(self):
        
        with st.sidebar:
            if st.button("Clear Chat History"):
                st.session_state.messages = []
                st.session_state.messages.append({"role": "ai", "content": "Hello! I am a chatbot that can help you with your PDFs. Ask me anything!"})    
                self.t5.clear_history()
    
    def display(self):
        self.titleUI()
        self.uploadPdfUI()
        self.clearHistory()
        self.displayChatMessageUI()
        
    
        input = self.chatInputUI()
        
        if input:
            self.chatMessageHandler(input)
        
        
    
if __name__ == "__main__":
    mainUI().display()