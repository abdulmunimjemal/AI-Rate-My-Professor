### AI Rate My Professor

**AI Rate My Professor** is an AI-powered chatbot that helps users find detailed information about professors by name or university.

#### Features

- **AI-Driven Search**: Provides detailed information using advanced AI models.
- **Real-Time Chat**: Supports real-time communication with WebSockets.
- **Light and Dark Mode**: User-friendly theme options.
- **Dynamic Responses**: Generates dynamic responses based on user queries.

#### Advanced Capabilities

- **LLM Tool Call Integration**: Dynamic interaction with external tools and APIs.
- **Agentic RAG**: Combines retrieval and generative models for accurate responses.

#### Screenshots

Here are some screenshots of the application in action:

|                                                  Dark Mode                                                   |                                                  Light Mode                                                   |
| :----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: |
| ![Dark Mode](https://raw.githubusercontent.com/abdulmunimjemal/AI-Rate-My-Professor/main/screenshot/ss1.png) | ![Light Mode](https://raw.githubusercontent.com/abdulmunimjemal/AI-Rate-My-Professor/main/screenshot/ss4.png) |

|                                             Professor Search Result                                              |                                            LLM Tool Calling Example                                             |
| :--------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------: |
| ![Search Result](https://raw.githubusercontent.com/abdulmunimjemal/AI-Rate-My-Professor/main/screenshot/ss2.png) | ![Tool Calling](https://raw.githubusercontent.com/abdulmunimjemal/AI-Rate-My-Professor/main/screenshot/ss3.png) |

#### Tech Stack

- Extensive Tech Stack:
  - **AI Tools:** Langchain, Pinecone, OpenAI, Agentic RAG, Custom Tool Calling
  - **Backend:** FastAPI, WebSockets
  - **Frontend:** HTML, CSS, JavaScript
  - **Dependency Management:** Poetry

#### Project Structure

- **`data/`**: Data files and databases.
- **`templates/`**: HTML templates.
- **`tools/`**: Agentic AI Tools for dynamic functionalities.
- **`agent.py`**: AI agent logic.
- **`main.py`**: FastAPI server.
- **`rag.py`**: RAG logic.

#### Getting Started

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/abdulmunimjemal/AI-Rate-My-Professor.git
   cd AI-Rate-My-Professor
   ```
2. **Install Dependencies**:
   ```bash
   poetry install
   ```
3. **Run the Application**:
   ```bash
   poetry run python main.py
   ```

#### License

MIT License.

#### Author

[Abdulmunim - Munim](https://github.com/abdulmunimjemal)
