from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import RunnableLambda,RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from pathlib import Path
import os
from dotenv import load_dotenv
from logger import logging


def upload_to_dir(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    save_dir = Path("./file_directory")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(file_bytes)


    


class Indexer:
    def __init__(self,path,file_name,chunk_size=1000,chunk_overlap=200,embd_model_name='sentence-transformers/all-MiniLM-L6-v2'):
        print("Initializing Indexer")
        self.path=path
        self.file_name=file_name
        self.chunk_size=chunk_size
        self.chunk_overlap=chunk_overlap
        self.embd_model_name=embd_model_name
        print("Indexr Initaization Success")

    def get_loader(self):
        try:
            print("Initializing Loader")
            path=Path(self.path)/Path(self.file_name)
            loader=PyMuPDFLoader(str(path))
            docs=list(loader.lazy_load())
            print("Loader Initaization Success")
            return docs
        except Exception as e:
            print("There was an error",e)

    def get_chunks(self,docs):
        try:
            print("Getting Chunks")
            sm=0
            for  doc in docs:
                sm+=len(doc.page_content)
            if sm>self.chunk_size:
                splitter=RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    length_function=len,
                    separators=['\n\n','\n',' ','']
                )
                chunks=splitter.split_documents(docs)
            else:
                chunks=docs 

            print("Chunks loaded")
            return chunks
        except Exception:
            raise

    def get_embeddings(self,chunks):
        try:
            print("Getting Embeddings now...")
            transformer=embeddings = HuggingFaceEmbeddings(
                model_name=self.embd_model_name
            )  
            vector_store = FAISS.from_documents(chunks, transformer)
            print("Embedding fetch Success")
            return vector_store
        except Exception as e:
            print("There was an error",e)

    def indexing(self):

        try:
            # chain=RunnableLambda(get_loader)|RunnableLambda(get_chunks)|RunnableLambda(get_embeddings)
            # vector_store=chain.invoke({'path':self.path,'file_name':self.file_name})
            print("Building Indexer")
            docs=self.get_loader()
            chunks=self.get_chunks(docs)
            if not docs: 
                raise("Nothing in Docs")
            
            store=self.get_embeddings(chunks)
            print("Indexer build Success")
            return store
        except Exception as e:
            print("There was an error",e)

class Talk:
    def __init__(self,vector_store,chat_history=[],model_name='llama-3.1-8b-instant'):
        print("Initializing Indexer")
        self.vector_store=vector_store
        self.chat_history=chat_history 
        self.model_name=model_name
        self.par=StrOutputParser()
        logging.info("Talk Object Setup Complete")

    def get_context(self,query):
        print("Getting Cotext")
        retrieve_obj=self.vector_store.as_retriever(search_type='similarity', search_kwargs={'k':2})
        context=' '.join([doc.page_content for doc in retrieve_obj.invoke(query)])
        print("Context retrieval Success!")
        return context


    def stage(self):
        logging.info("Staging the talker")
        load_dotenv()
        model = ChatGroq(
            model=self.model_name, 
            temperature=0.7
        )
        ch_temp=ChatPromptTemplate([
            ('system','You are a helpful chatbot, answer thir query based on {context}, if you do not feel you have sufficient context then just say insufficient context under 5 lines'),
            MessagesPlaceholder(variable_name='chat_history'),
            ('human','{query}')
        ])

        pchain=RunnableParallel({
                'query':RunnablePassthrough(),
                'chat_history':RunnableLambda(lambda _:self.chat_history),
                'context':RunnableLambda(self.get_context)
        })

        chain=pchain|ch_temp|model|self.par
        print("Talker Staged Succesfully!")
        return chain 

    def chat(self,query):
        
        chain=self.stage()
        results=chain.invoke(query)
        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(AIMessage(content=results))
    
        logging.info("Chat success")
        return results
    