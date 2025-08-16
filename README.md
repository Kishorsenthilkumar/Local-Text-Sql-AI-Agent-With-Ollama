# SQL AI Agent with Ollama and ChromaDB

A powerful AI-powered SQL query generator that converts natural language questions into SQL queries using local LLMs (Ollama), vector search (ChromaDB), and Langflow for workflow orchestration.

## 🚀 Features

- **Natural Language to SQL**: Convert plain English questions into SQL queries
- **Local AI Processing**: Uses Ollama for local LLM inference (no cloud dependencies)
- **RAG-Enhanced**: ChromaDB vector database for intelligent schema retrieval
- **Multiple Interfaces**: FastAPI backend with Streamlit frontend
- **Database Agnostic**: Works with SQLite, MySQL, PostgreSQL, and more
- **Secure**: All processing happens locally on your machine

## 🏗️ Architecture

```
User Query (Natural Language)
    ↓
Streamlit Frontend
    ↓
FastAPI Backend
    ↓
Langflow Workflow
    ↓
Ollama LLM + ChromaDB RAG
    ↓
Database Query Execution
    ↓
Results Display
```

## 📋 Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Required Ollama models (see setup instructions)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd langchain
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and setup Ollama**
   ```bash
   # Download and install Ollama from https://ollama.ai/
   
   # Pull required models
   ollama pull sqlcoder:7b-q2_K
   ollama pull nomic-embed-text
   ```

5. **Setup Langflow**
   ```bash
   # Install Langflow
   pip install langflow
   
   # Start Langflow
   langflow
   ```
   
   Then create a flow with:
   - ChatInput node (receives the prompt)
   - Ollama node (connected to sqlcoder model)
   - ChatOutput node (returns the SQL)

6. **Create the test database**
   ```bash
   python create_db.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URI=sqlite:///./my_test_database.db

# Ollama Models
OLLAMA_SQL_MODEL=sqlcoder:7b-q2_K
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Langflow Configuration
LANGFLOW_API_URL=http://localhost:7860/api/v1/run/<YOUR_FLOW_ID>
LANGFLOW_API_KEY=your_api_key_if_needed

# Backend URL (for Streamlit)
BACKEND_URL=http://127.0.0.1:8000/query-database
```

### ChromaDB Configuration

The ChromaDB data directory is configured in `chroma_utils.py`:

```python
CHROMA_DB_PATH = "D:\chromadb"  # Change this to your preferred path
```

## 🚀 Usage

### 1. Start the Backend (FastAPI)

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend (Streamlit)

```bash
streamlit run streamlit_app.py
```

### 3. Use the Application

1. Open your browser to `http://localhost:8501`
2. Enter a natural language query like:
   - "Show me all employees in the Sales department"
   - "What is the average salary by department?"
   - "List employees with salaries above $70,000"
3. Click "Generate & Execute SQL"
4. View the generated SQL and results

### Application Interface

![AI Agent Workflow Design with Langflow](output/ai_agent_workflow_design_with_langflow.png)

*The Streamlit interface showing natural language query input, generated SQL, and query results with data visualization.*

## 📁 Project Structure

```
langchain/
├── app.py                 # FastAPI backend with SQL generation logic
├── streamlit_app.py       # Streamlit frontend interface
├── chroma_utils.py        # ChromaDB utilities for RAG
├── create_db.py           # Database setup and sample data
├── requirements.txt       # Python dependencies
├── my_test_database.db    # SQLite test database
├── test_prompt.txt        # Test prompts for development
├── Modelfile.txt          # Ollama model configuration
├── test_schema.py         # Schema testing utilities
└── documentation/         # Project documentation
```

## 🔧 Core Components

### 1. FastAPI Backend (`app.py`)
- RESTful API for SQL generation
- Database schema introspection
- Integration with Langflow and Ollama
- ChromaDB-based RAG for schema retrieval

### 2. Streamlit Frontend (`streamlit_app.py`)
- User-friendly web interface
- Real-time query processing
- Results visualization with pandas
- Error handling and user feedback

### 3. ChromaDB Utilities (`chroma_utils.py`)
- Vector database operations
- Schema embedding and indexing
- Semantic search for relevant schema parts
- Ollama integration for embeddings

### 4. Database Setup (`create_db.py`)
- SQLite database creation
- Sample data population
- Table structure definition

## 🧠 How It Works

1. **Schema Indexing**: On startup, the application introspects your database schema and stores it in ChromaDB with embeddings
2. **Query Processing**: When a user asks a question:
   - The query is embedded using Ollama
   - ChromaDB finds relevant schema parts
   - A context-aware prompt is sent to Langflow
   - Langflow orchestrates the SQL generation using Ollama
3. **Query Execution**: The generated SQL is executed against your database
4. **Results Display**: Results are formatted and displayed in the Streamlit interface

## 🔍 Example Queries

The system comes with a sample database containing Employees and Departments tables. Try these queries:

- "Show me all employees"
- "What departments exist?"
- "Find employees in the Sales department"
- "What is the average salary?"
- "Show employees with salaries above $70,000"
- "List departments and their locations"

## 🛡️ Security Considerations

- **Local Processing**: All AI processing happens locally via Ollama
- **No Data Leakage**: Your database schema and queries never leave your machine
- **SQL Injection Protection**: Generated SQL is executed through SQLAlchemy with proper parameterization
- **Environment Variables**: Sensitive configuration is stored in environment variables

## 🐛 Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Verify models are pulled: `ollama list`

2. **ChromaDB Path Issues**
   - Update `CHROMA_DB_PATH` in `chroma_utils.py`
   - Ensure the directory is writable

3. **Langflow Connection Error**
   - Verify Langflow is running on the correct port
   - Check your Flow ID in the API URL
   - Ensure the flow is properly configured

4. **Database Connection Issues**
   - Verify the database file exists
   - Check the `DATABASE_URI` configuration
   - Run `python create_db.py` to recreate the database

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector database
- [Langflow](https://github.com/logspace-ai/langflow) for workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Streamlit](https://streamlit.io/) for the frontend interface

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments for configuration details
3. Open an issue on the repository

---

**Note**: This project is designed for educational and development purposes. Always test generated SQL queries before using them in production environments.
