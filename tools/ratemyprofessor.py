import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for the requests
BASE_URL = "https://www.ratemyprofessors.com/graphql"
AUTHORIZATION = os.getenv("RMP_AUTHORIZATION")  # Load Authorization token from .env

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,ar-DZ;q=0.8,ar;q=0.7",
    "Authorization": f"Basic {AUTHORIZATION}",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    # "Cookie": COOKIES,
    "Origin": "https://www.ratemyprofessors.com",
    "Referer": "https://www.ratemyprofessors.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}

def load_query_from_file(file_path: str) -> str:
    """
    Load a GraphQL query from a file.

    Args:
        file_path (str): The path to the file containing the GraphQL query.

    Returns:
        str: The GraphQL query as a string.
    """
    
    current_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_path, file_path)
    with open(file_path, 'r', encoding="utf-8") as file:
        return file.read()

def send_graphql_request(query: str, variables: dict):
    """
    Send a GraphQL request to the RateMyProfessors API.

    Args:
        query (str): The GraphQL query string.
        variables (dict): The variables for the GraphQL query.

    Returns:
        dict: The response from the API in JSON format, or an error message.
    """
    payload = {
        "query": query,
        "variables": variables
    }

    try:
        response = requests.post(BASE_URL, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()  # Raises an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def format_university_response(response, limit):
    """
    Format the response for universities to a specific schema.

    Args:
        response (dict): The JSON response from the API.
        limit (int): The maximum number of results to return.

    Returns:
        list: A list of dictionaries containing university details.
    """
    formatted_data = []
    if "data" in response and "newSearch" in response["data"] and "schools" in response["data"]["newSearch"]:
        edges = response["data"]["newSearch"]["schools"]["edges"]
        for edge in edges[:limit]:
            node = edge["node"]
            university_info = {
                "id": node.get("id"),
                "legacyId": node.get("legacyId"),
                "name": node.get("name"),
                "city": node.get("city"),
                "state": node.get("state"),
                "avgRatingRounded": node.get("avgRatingRounded"),
                "numRatings": node.get("numRatings"),
                "departments": [{"id": dept.get("id"), "name": dept.get("name")} for dept in node.get("departments", [])],
                "summary": node.get("summary", {})
            }
            formatted_data.append(university_info)
    return formatted_data

def format_professor_response(response, limit):
    """
    Format the response for professors to a specific schema.

    Args:
        response (dict): The JSON response from the API.
        limit (int): The maximum number of results to return.

    Returns:
        list: A list of dictionaries containing professor details.
    """
    formatted_data = []
    if "data" in response and "newSearch" in response["data"] and "teachers" in response["data"]["newSearch"]:
        edges = response["data"]["newSearch"]["teachers"]["edges"]
        for edge in edges[:limit]:
            node = edge["node"]
            professor_info = {
                "id": node.get("id"),
                "legacyId": node.get("legacyId"),
                "firstName": node.get("firstName"),
                "lastName": node.get("lastName"),
                "department": node.get("department"),
                "school": node.get("school", {}).get("name"),
                "avgRating": node.get("avgRating"),
                "numRatings": node.get("numRatings"),
                "wouldTakeAgainPercentRounded": node.get("wouldTakeAgainPercentRounded"),
                "ratingsDistribution": node.get("ratingsDistribution", {}),
                "mandatoryAttendance": node.get("mandatoryAttendance", {}),
                "takenForCredit": node.get("takenForCredit", {})
            }
            formatted_data.append(professor_info)
    return formatted_data

def get_professor(name: str, limit: int = 5):
    """
    Get a professor by their name.

    Args:
        name (str): The name of the professor.
        limit (int): The maximum number of results to return.

    Returns:
        list: A list of formatted professor details or an error message.
    """
    query = load_query_from_file('search_professor_by_name.graphql')
    variables = {
        "query": {"text": name},
        "count": limit
    }
    
    response = send_graphql_request(query, variables)
    return format_professor_response(response, limit)

def get_university(university: str, limit: int = 5):
    """
    Get professors by university.

    Args:
        university (str): The name of the university.
        limit (int): The maximum number of results to return.

    Returns:
        list: A list of formatted university details or an error message.
    """
    query = load_query_from_file('search_university_by_name.graphql')
    variables = {
        "query": {"text": university}
    }

    response = send_graphql_request(query, variables)
    return format_university_response(response, limit)


def get_professors_by_university_id(school_id: str, professor_name: str, limit: int = 5):
    """
    Get teachers by school ID.

    Args:
        school_id (str): The ID of the school.
        professor_name (str): The text to search for within the teachers.
        limit (int): The maximum number of results to return.

    Returns:
        list: A list of formatted teacher details or an error message.
    """
    query = load_query_from_file('search_teachers_by_school_id.graphql')
    variables = {
        "query": {"text": professor_name, "schoolID": school_id},
        "count": limit
    }

    response = send_graphql_request(query, variables)
    return format_professor_response(response, limit)

# # Example usage:
# # Example 1: Search for a Professor by Name
# result_professor = get_professor(name="John", limit=1)
# print("Professor Search Result:", result_professor)
# print("----------------------")

# # Example 2: Search for a University by Name
# result_university = get_university(university="Harvard", limit=1)
# print("University Search Result:", result_university)
# print("----------------------")

# # Example 3: Search for Professors by University ID
# result_professors_by_university = get_professors_by_university_id(
#     school_id="U2Nob29sLTQ3NzM=", professor_name="Ha", limit=5
# )
# print("Professors by University ID Result:", result_professors_by_university)
# print("----------------------")


from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent

# Define Pydantic Models for Arguments
class GetProfessorArgs(BaseModel):
    name: str = Field(..., title="The name of the professor to be searched.")
    limit: int = Field(5, title="The maximum number of results to return.")

class GetUniversityArgs(BaseModel):
    university: str = Field(..., title="The name of the university to be searched.")
    limit: int = Field(5, title="The maximum number of results to return.")

class GetProfessorsByUniversityIDArgs(BaseModel):
    school_id: str = Field(..., title="The ID of the school.")
    professor_name: str = Field(..., title="The search field for the professor's name.")
    limit: int = Field(5, title="The maximum number of results to return.")


rate_tools = [
    StructuredTool.from_function(
        func=get_professor,
        name="GetProfessor",
        description="Get a professor by their name.",
        args_schema=GetProfessorArgs,
    ),
    StructuredTool.from_function(
        func=get_university,
        name="GetUniversity",
        description="Get Universities and Their Departments.",
        args_schema=GetUniversityArgs,
    ),
    StructuredTool.from_function(
        func=get_professors_by_university_id,
        name="GetProfessorsByUniversityID",
        description="Get professors by university ID. You can use the GetUniversity tool to get the university ID.",
        args_schema=GetProfessorsByUniversityIDArgs,
    ),
]

# Initialize a ChatOpenAI model
llm = ChatOpenAI(model="gpt-4o-mini")

prompt = hub.pull("hwchase17/openai-tools-agent")

agent = create_tool_calling_agent(
    llm=llm,
    tools=rate_tools,
    prompt=prompt,
)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=rate_tools,
    verbose=True,
    handle_parsing_errors=True,
)


def run_tools(input: str, chat_history: list):
    """
    Run the tools on the input and chat history.

    Args:
        input (str): The input text.
        chat_history (list): The chat history.

    Returns:
        dict: The output of the tools.
    """
    return agent_executor.invoke({"input": input, "chat_history": chat_history})["output"]

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, AIMessage
    chat_history = []
    while True:
        query = input("You: ")
        if query == "exit":
            break
        print("----------------------")
        chat_history.append(HumanMessage(query))
        ai_message =agent_executor.invoke({"input": query, "chat_history": chat_history})["output"]
        print("AI: ", ai_message)
        chat_history.append(AIMessage(ai_message))