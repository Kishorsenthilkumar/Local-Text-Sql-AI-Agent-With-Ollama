# chroma_utils.py

import chromadb
import os
import ollama # To interact with Ollama for embeddings

# --- Configuration ---
# Define the directory where ChromaDB will store its data
# This directory will be created if it doesn't exist.
CHROMA_DB_PATH = "D:\chromadb"

# Define the Ollama model to use for generating embeddings
# 'nomic-embed-text' is a good general-purpose embedding model available on Ollama.
# Make sure you have pulled this model: `ollama pull nomic-embed-text`
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"

# --- ChromaDB Client Initialization ---
def initialize_chroma_client():
    """
    Initializes and returns a persistent ChromaDB client.
    Ensures the data directory exists.
    """
    if not os.path.exists(CHROMA_DB_PATH):
        os.makedirs(CHROMA_DB_PATH)
        print(f"Created ChromaDB data directory: {CHROMA_DB_PATH}")
    
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        print(f"ChromaDB persistent client initialized at: {CHROMA_DB_PATH}")
        return client
    except Exception as e:
        print(f"Error initializing ChromaDB client: {e}")
        raise

# --- Embedding Function using Ollama ---
def get_ollama_embedding(text: str) -> list[float]:
    """
    Generates an embedding for the given text using the specified Ollama model.
    """
    try:
        # Ensure Ollama server is running and the embedding model is pulled
        response = ollama.embeddings(model=OLLAMA_EMBEDDING_MODEL, prompt=text)
        return response['embedding']
    except ollama.ResponseError as e:
        print(f"Error generating embedding with Ollama: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during embedding: {e}")
        raise

# --- Adding Schema to ChromaDB ---
def add_schema_to_chroma(client: chromadb.PersistentClient, schema_info: dict):
    """
    Adds database schema information to a ChromaDB collection.
    
    Args:
        client: An initialized ChromaDB client.
        schema_info: A dictionary containing schema details.
                     Expected format:
                     {
                         "tables": [
                             {"name": "Employees", "ddl": "CREATE TABLE Employees (...);", "description": "Details about company employees."},
                             {"name": "Departments", "ddl": "CREATE TABLE Departments (...);", "description": "Information about company departments."},
                             # ... more tables
                         ],
                         "relationships": [
                             {"description": "Employees.DepartmentID references Departments.DepartmentID."}
                         ]
                     }
                     
                     For simplicity, we'll process 'ddl' and 'description' from tables
                     and 'description' from relationships.
    """
    collection_name = "sql_schema_embeddings"
    collection = client.get_or_create_collection(name=collection_name)
    print(f"Using ChromaDB collection: {collection_name}")

    documents = []
    metadatas = []
    ids = []
    
    # Add table DDLs and descriptions
    for i, table in enumerate(schema_info.get("tables", [])):
        table_name = table.get("name", f"table_{i}")
        ddl = table.get("ddl", "")
        description = table.get("description", f"Schema for table {table_name}.")
        
        # Combine DDL and description for better context in embedding
        doc_content = f"Table: {table_name}\nDDL: {ddl}\nDescription: {description}"
        
        documents.append(doc_content)
        metadatas.append({"type": "table_schema", "table_name": table_name})
        ids.append(f"schema_table_{table_name}_{i}")

    # Add relationship descriptions
    for i, rel in enumerate(schema_info.get("relationships", [])):
        rel_description = rel.get("description", f"Database relationship {i}.")
        
        documents.append(rel_description)
        metadatas.append({"type": "relationship"})
        ids.append(f"schema_rel_{i}")

    # Generate embeddings and add to collection
    if documents:
        # ChromaDB can automatically embed if you set an embedding function for the collection.
        # However, since we're using Ollama, we'll manually embed here for clarity.
        # If you want ChromaDB to handle it, you'd pass `embedding_function=ollama_embedding_function`
        # when creating the collection.
        embeddings = [get_ollama_embedding(doc) for doc in documents]
        
        # Add or update documents in the collection
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings # Provide pre-computed embeddings
        )
        print(f"Added/Updated {len(documents)} schema documents to ChromaDB.")
    else:
        print("No schema documents to add to ChromaDB.")

# --- Querying Schema from ChromaDB ---
def query_schema_from_chroma(client: chromadb.PersistentClient, natural_language_query: str, n_results: int = 5) -> list[str]:
    """
    Queries the ChromaDB collection for relevant schema information based on a natural language query.
    
    Args:
        client: An initialized ChromaDB client.
        natural_language_query: The user's question in natural language.
        n_results: The number of top relevant schema documents to retrieve.
        
    Returns:
        A list of strings, where each string is a relevant schema snippet.
    """
    collection_name = "sql_schema_embeddings"
    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        print(f"Collection '{collection_name}' not found. Please add schema data first.")
        return []

    # Generate embedding for the query
    query_embedding = get_ollama_embedding(natural_language_query)

    # Query the collection for similar schema documents
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances'] # Include documents and metadata in results
    )
    
    relevant_schema_snippets = []
    if results and results['documents']:
        print(f"\nFound {len(results['documents'][0])} relevant schema snippets:")
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            print(f"  Snippet {i+1} (Distance: {distance:.4f}, Type: {metadata.get('type')}):")
            print(f"    {doc.splitlines()[0]}...") # Print first line of doc
            relevant_schema_snippets.append(doc)
    else:
        print("No relevant schema snippets found.")
        
    return relevant_schema_snippets

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    # 1. Initialize ChromaDB client
    chroma_client = initialize_chroma_client()

    # 2. Define a dummy schema (replace with your actual database schema)
    # In a real scenario, this 'schema_data' would come from your SQLAlchemy introspection
    # in app.py's get_db_schema, formatted appropriately.
    dummy_schema_data = {
        "tables": [
            {
                "name": "Employees",
                "ddl": """CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    DepartmentID INT,
    Salary DECIMAL(10, 2)
);""",
                "description": "Contains information about all employees in the company, including their personal details, department, and salary."
            },
            {
                "name": "Departments",
                "ddl": """CREATE TABLE Departments (
    DepartmentID INT PRIMARY KEY,
    DepartmentName VARCHAR(50) NOT NULL,
    Location VARCHAR(100)
);""",
                "description": "Lists all departments within the organization and their physical locations."
            },
            {
                "name": "Projects",
                "ddl": """CREATE TABLE Projects (
    ProjectID INT PRIMARY KEY,
    ProjectName VARCHAR(100) NOT NULL,
    DepartmentID INT,
    StartDate DATE,
    EndDate DATE
);""",
                "description": "Details about various projects undertaken by the company, linked to departments."
            }
        ],
        "relationships": [
            {"description": "Employees.DepartmentID is a foreign key referencing Departments.DepartmentID."},
            {"description": "Projects.DepartmentID is a foreign key referencing Departments.DepartmentID."}
        ]
    }

    # 3. Add the dummy schema to ChromaDB
    print("\n--- Adding Schema to ChromaDB ---")
    add_schema_to_chroma(chroma_client, dummy_schema_data)

    # 4. Query ChromaDB for relevant schema snippets
    print("\n--- Querying ChromaDB ---")
    user_query_1 = "Show me the names and salaries of employees."
    relevant_snippets_1 = query_schema_from_chroma(chroma_client, user_query_1)
    print(f"\nRelevant snippets for '{user_query_1}':\n{'-'*30}\n" + "\n".join(relevant_snippets_1) + "\n" + '-'*30)

    user_query_2 = "What projects are in the marketing department?"
    relevant_snippets_2 = query_schema_from_chroma(chroma_client, user_query_2)
    print(f"\nRelevant snippets for '{user_query_2}':\n{'-'*30}\n" + "\n".join(relevant_snippets_2) + "\n" + '-'*30)

    user_query_3 = "List all departments."
    relevant_snippets_3 = query_schema_from_chroma(chroma_client, user_query_3)
    print(f"\nRelevant snippets for '{user_query_3}':\n{'-'*30}\n" + "\n".join(relevant_snippets_3) + "\n" + '-'*30)

    # You can reset the database for a clean start if needed (for testing purposes)
    # print("\n--- Resetting ChromaDB (for testing) ---")
    # chroma_client.reset()
    # print("ChromaDB reset. All data cleared.")