from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_community.llms.huggingface_hub import HuggingFaceHub
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
import logging
import tempfile
import os
import re

load_dotenv()

class T5Model:
    
    _instance = None
    _chat_history = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(T5Model, cls).__new__(cls)
            
            os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
            
            cls._llm = HuggingFaceHub(
                repo_id="google/flan-t5-large",
                model_kwargs={"temperature": 0.5, "max_length": 512}
            )
            
            cls._embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
            )
            
            logging.info("T5 Model Initialized")
        
        return cls._instance
  
      
    def read_pdf(self, pdf) -> list:
        try:
            ## save pdf to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(pdf.getvalue())
                file_path = temp_file.name
            
            ## load pdf into Document objects
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            ## rmv temp file
            os.remove(file_path)
            return documents
        except FileNotFoundError:
            return "File not found."
        except Exception as e:
            return f"An error occurred: {e}"


    def _text_splitter(self, text) -> list:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=40,
            length_function=len
        )
        
        return text_splitter.split_documents(text)
    
   
    def _remove_pua(self, text) -> str:       
        """ 
        Remove PUA (Private Use Area) characters from text 
        """
        
        # Remove PUA from BMP
        text = re.sub(r'[\ue000-\uf8ff]', '', text)

        # Remove PUA from Supplementary Area A
        text = re.sub(r'[\U000f0000-\U000ffffd]', '', text)

        # Remove PUA from Supplementary Area B
        text = re.sub(r'[\U00100000-\U0010fffd]', '', text)
        return text
    
    
    def _remove_characters(self, pdf_text) -> list:
        for i in range(len(pdf_text)):
            pdf_text[i].page_content = pdf_text[i].page_content.replace("-\n", "") # remove hyphenation
            pdf_text[i].page_content = pdf_text[i].page_content.replace("\n", " ") # remove new lines
            pdf_text[i].page_content = self._remove_pua(pdf_text[i].page_content ) # remove PUA characters
            pdf_text[i].page_content = re.sub(r'\s+', ' ', pdf_text[i].page_content) # remove extra spaces
        return pdf_text
 
    
    def preprocess(self, pdf) -> bool:
        try:
            pdf_text = self.read_pdf(pdf)
            pdf_text = self._text_splitter(pdf_text)
            self._pdf_text = self._remove_characters(pdf_text)
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False


    def faiss(self) -> bool:
        try:
            
            logging.debug("Creating vector store")
            
            self._vectorstore = FAISS.from_documents(self._pdf_text, self._embeddings)
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    
    
    def retrieve(self, k:int = 7, search_type: str = "mmr") -> bool:
        try:
            
            logging.debug("Creating retriever")
            
            self._retriever = self._vectorstore.as_retriever(
                search_kwargs={"k":k},
                search_type=search_type
            )
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        
        
    def clear_history(self):
        self._chat_history = []
        
        
    def query(self, question: str) -> dict:

        logging.debug(f"Query : {question}")
        qa_chain = ConversationalRetrievalChain.from_llm(self._llm, self._retriever, return_source_documents=True)

        result = qa_chain({
                    "question": question,
                    "chat_history": self._chat_history
                })

        self._chat_history.append((question, result["answer"]))
        
        logging.debug(f"Result : {result}")
        
        return {"answer": result["answer"], "reference": result["source_documents"]}