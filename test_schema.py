# test_schema.py
from app import get_db_schema, get_structured_db_schema, DATABASE_URI

if __name__ == "__main__":
    print("=== Testing Database Schema Extraction ===\n")
    
    # Test 1: Basic DDL Schema Extraction
    print("1. Testing get_db_schema() - Basic DDL format:")
    print("-" * 50)
    try:
        schema_ddl = get_db_schema(DATABASE_URI)
        if schema_ddl.startswith("Error"):
            print(f"❌ Error: {schema_ddl}")
        else:
            print("✅ Success! Extracted DDL schema:")
            print(schema_ddl)
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Structured Schema Extraction
    print("2. Testing get_structured_db_schema() - Structured format:")
    print("-" * 50)
    try:
        structured_schema = get_structured_db_schema(DATABASE_URI)
        
        if structured_schema.get("error"):
            print(f"❌ Error: {structured_schema['error']}")
        else:
            print("✅ Success! Extracted structured schema:")
            print(f"📊 Tables found: {len(structured_schema['tables'])}")
            print(f"🔗 Relationships found: {len(structured_schema['relationships'])}")
            
            # Display table details
            for i, table in enumerate(structured_schema['tables'], 1):
                print(f"\n📋 Table {i}: {table['name']}")
                print(f"   Description: {table['description']}")
                print(f"   Columns: {len(table['columns'])}")
                print(f"   Foreign Keys: {len(table['foreign_keys'])}")
                
                # Show first few columns
                if table['columns']:
                    print(f"   Sample columns: {', '.join(table['columns'][:3])}")
                    if len(table['columns']) > 3:
                        print(f"   ... and {len(table['columns']) - 3} more")
            
            # Display relationships
            if structured_schema['relationships']:
                print(f"\n🔗 Relationships:")
                for rel in structured_schema['relationships']:
                    print(f"   {rel['description']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Database Connection Test
    print("3. Testing database connection:")
    print("-" * 50)
    try:
        from sqlalchemy import create_engine, inspect
        engine = create_engine(DATABASE_URI)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        print(f"✅ Database connection successful!")
        print(f"📋 Tables in database: {table_names}")
        
        # Test a simple query
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"🔍 Verified tables: {tables}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    print("\n" + "="*60)
    print("🎉 Schema extraction test completed!")
    print("If all tests passed, your schema functions are working correctly.")
    print("You can now run your FastAPI application with confidence.")
