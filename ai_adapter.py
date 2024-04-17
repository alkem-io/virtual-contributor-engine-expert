import json
from langchain.vectorstores import FAISS
from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_openai import AzureOpenAIEmbeddings
from langchain_openai import AzureOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.schema import format_document
from langchain_core.messages import get_buffer_string
from langchain_core.messages.ai import AIMessage
from langchain_core.runnables import RunnableBranch
from langchain.callbacks import get_openai_callback

from operator import itemgetter
import logging
import sys
import io
from config import config, vectordb_path, local_path, LOG_LEVEL, max_token_limit
from ingest import ingest


import os
# configure logging
logger = logging.getLogger(__name__)
assert LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
logger.setLevel(getattr(logging, LOG_LEVEL))  # Set logger level


# Create handlers
c_handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, line_buffering=True))
f_handler = logging.FileHandler(os.path.join(os.path.expanduser(local_path), 'app.log'))

c_handler.setLevel(level=getattr(logging, LOG_LEVEL))
f_handler.setLevel(logging.WARNING)

# Create formatters and add them to handlers
c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%m-%d %H:%M:%S')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%m-%d %H:%M:%S')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

logger.info(f"log level {os.path.basename(__file__)}: {LOG_LEVEL}")

# verbose output for LLMs
if LOG_LEVEL == "DEBUG":
    verbose_models = True
else:
    verbose_models = False

# define internal configuration parameters

# does chain return the source documents?
return_source_documents = True


# Define a dictionary containing country codes as keys and related languages as values

language_mapping = {
    'EN': 'English',
    'US': 'English',
    'UK': 'English',
    'FR': 'French',
    'DE': 'German',
    'ES': 'Spanish',
    'NL': 'Dutch',
    'BG': 'Bulgarian',
    'UA': "Ukranian"
}

# function to retrieve language from country
def get_language_by_code(language_code):
    """Returns the language associated with the given code. If no match is found, it returns 'English'."""
    return language_mapping.get(language_code, 'English')


chat_system_template = """
You are a friendly and talkative conversational agent, tasked with answering questions based on the context provided below delimited by triple pluses.
Use the following step-by-step instructions to respond to user inputs:

1 - Provide an answer of 250 words or less that is professional, engaging, accurate and exthausive If the answer cannot be found within the context, write 'Hmm, I am not sure'. 
2 - If the question is not is not professional write 'Unfortunately, I cannot answer that question'. 
3 - Only return the answer from step 3, do not show any code or additional information.
5 - Always answer in Dutch.

+++
{context}
+++
"""

condense_question_template = """"
{question}
"""


condense_question_prompt = PromptTemplate.from_template(condense_question_template)

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", chat_system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)


# generic_llm = AzureOpenAI(azure_deployment=os.environ["LLM_DEPLOYMENT_NAME"],
#                           temperature=0, verbose=verbose_models)

chat_llm = AzureChatOpenAI(azure_deployment=os.environ["LLM_DEPLOYMENT_NAME"],
                           temperature=float(os.environ["AI_MODEL_TEMPERATURE"]),
                           max_tokens=max_token_limit, verbose=verbose_models)

# condense_llm = AzureChatOpenAI(azure_deployment=os.environ["LLM_DEPLOYMENT_NAME"],
#                                temperature=0,
                                # verbose=verbose_models)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=config['embeddings_deployment_name'],
    chunk_size=1
)

def load_vector_db():
    """
    Purpose:
        Load the data into the vector database.
    Args:

    Returns:
        vectorstore: the vectorstore object
    """
    # Check if the vector database exists
    if os.path.exists(vectordb_path + os.sep + "index.pkl"):
        logger.info(f"The file vector database is present")
    else:
        logger.info(f"The file vector database is not present, ingesting")
        ingest()

    return FAISS.load_local(vectordb_path, embeddings)


vectorstore = load_vector_db()

retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": .5})

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)

async def query_chain(question, language, chat_history):

    logger.info(question)

    docs = retriever.invoke(question['question'])

    logger.info(list(map(lambda d: d.metadata['source'], docs)))

    review_system_prompt = SystemMessagePromptTemplate(
    prompt=PromptTemplate(
        input_variables=["context"],
        template=chat_system_template
    )
    )

    review_human_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["question"],
            template=condense_question_template
        )
    )

    messages = [review_system_prompt, review_human_prompt]

    review_prompt_template = ChatPromptTemplate(
        input_variables=["context", "question"],
        messages=messages,
    )

    review_chain = review_prompt_template | chat_llm

    result = review_chain.invoke({"question": question["question"], "context": _combine_documents(docs) })
    return {'answer': result, 'source_documents': docs}
