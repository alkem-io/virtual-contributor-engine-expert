from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langgraph.graph import END, StateGraph, START

from logger import setup_logger
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from typing import Dict, Annotated, List, Optional, TypedDict, Sequence, Any
import operator
from prompts import (
    combined_expert_prompt,
    evaluation_prompt,
    input_checker_prompt
)

from models import llm
from utils import (
    combine_documents,
    load_knowledge,
)


logger = setup_logger(__name__)

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    prompt: Optional[List[str]]
    bok_id: str
    knowledge_docs: Optional[Dict[str, Any]]  # List of knowledge documents
    context_answer: Optional[str]
    rephrased_question: Optional[str]
    context_question: Optional[str]
    description: Optional[str]
    display_name: Optional[str]
    knowledge_answer: Optional[str]
    source_scores: Optional[Dict[int, float]]
    human_language: Optional[str]
    knowledge_language: Optional[str]
    final_answer: Optional[str]

def format_messages(state: State):
    logger.info('Number of messages in the state: %d', len(state['messages']))
    return "\n".join(list(map(lambda message: f"{message.type}: {message.content}", state['messages'])))

def check_input(state: State):

    logger.info('Checking input')

    class FunctionOutput(BaseModel):
        rephrased_question: Optional[str] = Field(
            description="The rephrased question to make it more clear and concise.")
        context_answer: Optional[str] = Field(
            description="The answer to the last message if it is already contained in the conversation.")
        context_question: Optional[str] = Field(
            description="A question asking the user to provide more information if needed.")

    parser = PydanticOutputParser(pydantic_object=FunctionOutput)
    format_instructions = parser.get_format_instructions()
    prompt = PromptTemplate(
        template=input_checker_prompt,
        input_variables=["conversation"],
        partial_variables={"format_instructions": format_instructions}
    )

    chain = prompt | llm | parser

    result = chain.invoke({"conversation": format_messages(state)})

    logger.info(f'Input check result: {result.model_dump()}')

    return {**result.model_dump()}

def answer_question(state: State):

    class AnswerResponse(BaseModel):
        knowledge_answer: str = Field(description="Response to the human message")
        source_scores: Dict[int, float] = Field(
            description="Mapping of source_index to relevance_score (0-10)"
        )
        human_language: str = Field(
            description="ISO-639-1 code of human's message"
        )
        answer_language: str = Field(
            description="ISO-639-1 code of your response"
        )
        knowledge_language: str = Field(
            description="ISO-639-1 code of knowledge text"
        )

    parser = PydanticOutputParser(pydantic_object=AnswerResponse)
    format_instructions = parser.get_format_instructions()
    prompt = PromptTemplate(template=combined_expert_prompt,
                            input_variables=["vc_name", "knowledge", "question", "description"],
                            partial_variables={"format_instructions": format_instructions})

    chain = prompt | llm | parser
    result = chain.invoke({
        "vc_name": state['display_name'],
        "knowledge": combine_documents(state['knowledge_docs']),
        "question": state['rephrased_question'] or state['messages'][-1].content,
        "description": state['description']

    })

    logger.info(result)

    return {**result.model_dump()}

def retrieve(state: State):
    logger.info('Retrieving information from the knowledge base.')
    last_message = state['rephrased_question'] or state['messages'][-1].content
    knowledge_docs = load_knowledge(last_message, state['bok_id'])
    return {"knowledge_docs": knowledge_docs}

def evaluate_and_translate(state: State):
    logger.info('Evaluating and translating the best answer using a single LLM invocation with PromptTemplate and chaining.')

    class EvaluationResponse(BaseModel):
        final_answer: str = Field(
            description="The final answer to the user's question after evaluation and translation."
        )
        orinal_answer: Optional[str] = Field(
            description="The original answer before translation."
        )

    parser = PydanticOutputParser(pydantic_object=EvaluationResponse)
    format_instructions = parser.get_format_instructions()

    prompt = PromptTemplate(template=evaluation_prompt,
                            input_variables=["user_query", "context_answer", "knowledge_answer", "context_question"],
                            partial_variables={"output_instructions": format_instructions})

    chain = prompt | llm | parser

    result = chain.invoke({
        "user_query": state['rephrased_question'] or state['messages'][-1].content,
        "context_answer": state.get('context_answer', ''),
        "knowledge_answer": state.get('knowledge_answer', ''),
        "context_question": state.get('context_question', '')
    })

    logger.info(f"Evaluation result: {result.model_dump()}")

    return {**result.model_dump()}


graph_builder = StateGraph(State)
graph_builder.add_node("check_input", check_input)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("answer_question", answer_question)
graph_builder.add_node("evaluate_and_translate", evaluate_and_translate)

graph_builder.add_edge(START, "check_input")
graph_builder.add_edge("check_input", "retrieve")
graph_builder.add_edge("retrieve", "answer_question")
graph_builder.add_edge("answer_question", "evaluate_and_translate")
graph_builder.add_edge("evaluate_and_translate", END)


graph = graph_builder.compile()
