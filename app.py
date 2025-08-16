# app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama # Used by chroma_utils for embeddings
import json
import os
import requests # For making HTTP requests to Langflow API

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import reflection # Good practice to include for schema reflection

# Import chroma_utils.py functions
import chroma_utils 

app = FastAPI()

# --- Configuration ---
# Define the Ollama model for SQL generation (make sure you have pulled this: ollama pull sqlcoder)
OLLAMA_SQL_MODEL = os.getenv("OLLAMA_SQL_MODEL", "sqlcoder:7b-q2_K") 
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text") 


# Configure your database connection string
# For SQLite, ensure 'my_test_database.db' is created by running create_db.py
DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///./my_test_database.db")

# Extract database type from URI for LLM prompt (e.g., "sqlite", "mysql", "postgresql")
LLM_DB_TYPE = DATABASE_URI.split(":")[0].split("+")[0]

# --- Langflow API Configuration ---
# IMPORTANT: REPLACE <YOUR_FLOW_ID> with the actual Flow ID copied from Langflow's API Access
LANGFLOW_API_URL = os.getenv("LANGFLOW_API_URL", "http://localhost:7860/api/v1/run/<YOUR_FLOW_ID>")
# You might also need a LANGFLOW_API_KEY if your Langflow instance requires authentication
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY", "") # Leave empty if no API key is set in Langflow

# --- Pydantic Models for API Request/Response ---
class QueryRequest(BaseModel):
    natural_language_query: str
    
class QueryResponse(BaseModel):
    sql_query: str
    query_result: list # List of dictionaries for rows

# --- Global ChromaDB Client Initialization ---
# This client will be initialized once when the FastAPI app starts
chroma_client_global = chroma_utils.initialize_chroma_client()

# --- Helper Function to Get Database Schema (CRITICAL for LLM) ---
def get_db_schema(db_uri: str) -> str:
    """
    Connects to the database using SQLAlchemy and retrieves its schema information.
    The schema is formatted as a DDL-like string suitable for an LLM.
    """
    try:
        engine = create_engine(db_uri)
        inspector = inspect(engine)
        
        # Get all table names
        table_names = inspector.get_table_names()
        
        schema_info = []
        for table_name in table_names:
            schema_info.append(f"CREATE TABLE {table_name} (")
            
            columns = inspector.get_columns(table_name)
            col_definitions = []
            for col in columns:
                col_type = str(col['type'])
                col_def = f"    {col['name']} {col_type}"
                # Add primary key and not null constraints
                if col.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if not col.get('nullable'):
                    col_def += " NOT NULL"
                col_definitions.append(col_def)
            
            schema_info.append(",\n".join(col_definitions))
            schema_info.append(");")

            # Add foreign key constraints if they exist
            foreign_keys = inspector.get_foreign_keys(table_name)
            for fk in foreign_keys:
                # Construct FK definition. Note: SQLite FKs are often defined inline or as table constraints.
                # This is a generic representation for LLM.
                schema_info.append(
                    f"ALTER TABLE {table_name} ADD CONSTRAINT {fk['name']} "
                    f"FOREIGN KEY ({', '.join(fk['constrained_columns'])}) "
                    f"REFERENCES {fk['referred_table']} ({', '.join(fk['referred_columns'])});"
                )
            schema_info.append("\n") # Add a newline for readability between tables

        return "\n".join(schema_info)

    except Exception as e:
        print(f"Error getting database schema: {e}")
        return f"Error: Could not retrieve database schema. Details: {e}"

def get_structured_db_schema(db_uri: str) -> dict:
    """
    Connects to the database using SQLAlchemy and retrieves its schema information
    in a structured format optimized for ChromaDB indexing and RAG.
    Returns a dictionary with individual table DDLs and descriptions.
    """
    try:
        engine = create_engine(db_uri)
        inspector = inspect(engine)
        
        # Get all table names
        table_names = inspector.get_table_names()
        
        structured_schema = {
            "tables": [],
            "relationships": []
        }
        
        for table_name in table_names:
            # Build table DDL
            table_ddl_parts = [f"CREATE TABLE {table_name} ("]
            
            columns = inspector.get_columns(table_name)
            col_definitions = []
            column_descriptions = []
            
            for col in columns:
                col_type = str(col['type'])
                col_def = f"    {col['name']} {col_type}"
                
                # Add constraints
                constraints = []
                if col.get('primary_key'):
                    col_def += " PRIMARY KEY"
                    constraints.append("primary key")
                if not col.get('nullable'):
                    col_def += " NOT NULL"
                    constraints.append("not null")
                
                col_definitions.append(col_def)
                
                # Create column description for better RAG
                constraint_desc = f" ({', '.join(constraints)})" if constraints else ""
                column_descriptions.append(f"{col['name']} ({col_type}){constraint_desc}")
            
            table_ddl_parts.append(",\n".join(col_definitions))
            table_ddl_parts.append(");")
            table_ddl = "\n".join(table_ddl_parts)
            
            # Create table description
            table_description = f"Table {table_name} with columns: {', '.join(column_descriptions)}"
            
            # Add foreign key relationships
            foreign_keys = inspector.get_foreign_keys(table_name)
            fk_descriptions = []
            for fk in foreign_keys:
                fk_constraint = (
                    f"ALTER TABLE {table_name} ADD CONSTRAINT {fk['name']} "
                    f"FOREIGN KEY ({', '.join(fk['constrained_columns'])}) "
                    f"REFERENCES {fk['referred_table']} ({', '.join(fk['referred_columns'])});"
                )
                table_ddl += f"\n{fk_constraint}"
                
                # Add relationship description
                fk_desc = f"{table_name}.{', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}"
                fk_descriptions.append(fk_desc)
                structured_schema["relationships"].append({
                    "from_table": table_name,
                    "from_columns": fk['constrained_columns'],
                    "to_table": fk['referred_table'],
                    "to_columns": fk['referred_columns'],
                    "description": fk_desc
                })
            
            # Add table to structured schema
            structured_schema["tables"].append({
                "name": table_name,
                "ddl": table_ddl,
                "description": table_description,
                "columns": column_descriptions,
                "foreign_keys": fk_descriptions
            })
        
        return structured_schema

    except Exception as e:
        print(f"Error getting structured database schema: {e}")
        return {
            "tables": [],
            "relationships": [],
            "error": f"Could not retrieve database schema. Details: {e}"
        }

# --- Application Startup Event: Index Schema into ChromaDB ---
@app.on_event("startup")
async def startup_event():
    print("Application startup: Indexing database schema into ChromaDB...")
    try:
        # Use the new structured schema function for better RAG performance
        structured_schema = get_structured_db_schema(DATABASE_URI)
        
        if structured_schema.get("error"):
            print(f"Warning: Could not get structured schema for indexing: {structured_schema['error']}")
            return

        # The structured schema is now optimized for ChromaDB with individual table DDLs
        # and detailed descriptions for better semantic search
        chroma_utils.add_schema_to_chroma(chroma_client_global, structured_schema)
        print(f"Database schema indexed into ChromaDB successfully. Indexed {len(structured_schema['tables'])} tables and {len(structured_schema['relationships'])} relationships.")
    except Exception as e:
        print(f"Failed to index schema into ChromaDB: {e}")

# --- API Endpoint to Generate and Execute SQL ---
@app.post("/query-database", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    user_query = request.natural_language_query
    
    # 1. Get database schema
    full_db_schema = get_db_schema(DATABASE_URI)
    if full_db_schema.startswith("Error"):
        raise HTTPException(status_code=500, detail=full_db_schema)

    # Determine database type for LLM prompt (e.g., from URI dialect)
    llm_db_type = DATABASE_URI.split(":")[0].split("+")[0]

    # --- RAG Integration: Query ChromaDB for relevant schema snippets ---
    # Initialize ChromaDB client (if not already done globally, though better to do once)
    # For simplicity in this example, we'll re-initialize or assume it's ready.
    # In a real app, you'd initialize this once at app startup.
    chroma_client_instance = chroma_utils.initialize_chroma_client()
    
    # Query ChromaDB to get relevant schema parts
    # This is where the magic of RAG happens!
    relevant_schema_snippets = chroma_utils.query_schema_from_chroma(
        chroma_client_instance,
        user_query,
        n_results=5 # Adjust as needed
    )
    
    # Combine the relevant snippets into a single string for the LLM
    # If no relevant snippets found, use the full schema (fallback)
    schema_context_for_llm = "\n".join(relevant_schema_snippets) if relevant_schema_snippets else full_db_schema


    # 2. Construct full prompt for Ollama (now incorporating RAG context)
    # This prompt is what will be sent to your Langflow flow's Chat Input
    full_prompt_for_ollama = f"""
You are an expert SQL query generator.
Your task is to convert natural language questions into SQL queries for a {llm_db_type} database.
You must only return the SQL query and nothing else.
Focus only on the tables and columns provided in the schema below that are relevant to the user's question.

Here is the database schema:
```sql
{schema_context_for_llm}
```

Based on this schema, generate a SQL query for the following natural language question:
{user_query}
"""

    # --- Langflow API Call ---
    # IMPORTANT: Replace with your actual Langflow API URL and Flow ID
    LANGFLOW_API_URL = os.getenv("LANGFLOW_API_URL", "http://localhost:7860/api/v1/run/<YOUR_FLOW_ID>")
    # Make sure to replace <YOUR_FLOW_ID> with the actual ID from Langflow
    
    # Langflow expects a specific input format for its API
    # For the simplified flow, we send the complete prompt as input_value
    langflow_payload = {
        "inputs": {
            "input_value": full_prompt_for_ollama.strip()
        }
    }
    
    headers = {"Content-Type": "application/json"}
    if LANGFLOW_API_KEY:
        headers["X-API-Key"] = LANGFLOW_API_KEY # Add API key if required by Langflow

    try:
        print(f"Sending request to Langflow API: {LANGFLOW_API_URL}")
        # Use requests to call the Langflow API
        response = requests.post(LANGFLOW_API_URL, json=langflow_payload, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        langflow_result = response.json()
        
        # Extract the generated SQL from Langflow's response
        # The exact path depends on your Langflow flow's output structure.
        # For a simple ChatOutput, it's often in 'outputs'[0]['results']['message']['data']['text']
        generated_sql = "Error: Could not extract SQL from Langflow response."
        if langflow_result and langflow_result.get('outputs'):
            for output in langflow_result['outputs']:
                if output.get('results') and output['results'].get('message'):
                    generated_sql = output['results']['message']['data']['text'].strip()
                    break
        
        print(f"Generated SQL from Langflow:\n{generated_sql}")

        # Basic cleanup: remove common markdown or extra text if LLM includes it
        if generated_sql.startswith("```sql") and generated_sql.endswith("```"):
            generated_sql = generated_sql[len("```sql"): -len("```")].strip()
        
        # 4. Execute the SQL query (Placeholder - DANGER if not properly secured!)
        query_result = []
        try:
            engine = create_engine(DATABASE_URI)
            with engine.connect() as connection:
                # For SQLite, you might not need text() for simple SELECTs,
                # but it's good practice for general SQL execution.
                result = connection.execute(text(generated_sql))
                
                # Fetch results and column names
                column_names = list(result.keys())
                for row in result:
                    query_result.append(dict(zip(column_names, row))) # Convert row to dictionary
            
            if not query_result:
                print("No results found for the query.")

        except Exception as db_error:
            print(f"Database query execution failed: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database query failed. Possible invalid SQL: {db_error}")

        return QueryResponse(sql_query=generated_sql, query_result=query_result)

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail="Could not connect to Langflow API. Is Langflow running?")
    except requests.exceptions.RequestException as e:
        print(f"Langflow API request error: {e}")
        raise HTTPException(status_code=500, detail=f"Error from Langflow API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in backend: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")