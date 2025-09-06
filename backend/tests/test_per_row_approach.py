#!/usr/bin/env python3
"""
Test Per-Row Approach
=====================

This script tests the new per-row approach for vector database management.
It verifies that the per-row chunker can generate the expected vectors
and that the metadata structure is correct for graph relationships.
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend/src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag.utils.per_row_chunker import PerRowChunker
from rag.config import get_per_row_namespace

def test_per_row_chunker():
    """Test the per-row chunker functionality."""
    print("🧪 Testing Per-Row Chunker")
    print("=" * 50)
    
    try:
        # Initialize chunker
        chunker = PerRowChunker()
        
        # Test table statistics
        print("\n📊 Testing table statistics...")
        table_stats = chunker.get_table_stats()
        print(f"Table statistics: {table_stats}")
        
        total_rows = sum(table_stats.values())
        print(f"Total expected rows: {total_rows}")
        
        if total_rows == 0:
            print("⚠️  No data found in database. Make sure the database is populated.")
            return False
        
        # Test generating all rows
        print("\n🔄 Testing row generation...")
        all_rows = chunker.get_all_rows()
        
        print(f"Generated {len(all_rows)} row vectors")
        
        if len(all_rows) == 0:
            print("❌ No row vectors generated")
            return False
        
        # Test metadata structure
        print("\n🔍 Testing metadata structure...")
        test_row = all_rows[0]
        
        required_metadata_fields = ['node_id', 'table_name', 'primary_key', 'node_type']
        missing_fields = [field for field in required_metadata_fields if field not in test_row['metadata']]
        
        if missing_fields:
            print(f"❌ Missing required metadata fields: {missing_fields}")
            return False
        
        print(f"✅ Metadata structure is correct")
        print(f"   Node ID: {test_row['metadata']['node_id']}")
        print(f"   Table: {test_row['metadata']['table_name']}")
        print(f"   Node Type: {test_row['metadata']['node_type']}")
        
        # Test node type distribution
        print("\n📈 Testing node type distribution...")
        node_types = {}
        for row in all_rows:
            node_type = row['metadata']['node_type']
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("Node type distribution:")
        for node_type, count in sorted(node_types.items()):
            print(f"   {node_type}: {count}")
        
        # Test text generation
        print("\n📝 Testing text generation...")
        sample_texts = []
        for row in all_rows[:5]:  # Sample first 5 rows
            sample_texts.append({
                'table': row['metadata']['table_name'],
                'text': row['text'][:100] + "..." if len(row['text']) > 100 else row['text']
            })
        
        print("Sample generated texts:")
        for sample in sample_texts:
            print(f"   {sample['table']}: {sample['text']}")
        
        # Test graph relationship metadata
        print("\n🔗 Testing graph relationship metadata...")
        graph_metadata_count = 0
        for row in all_rows:
            # Count rows that have additional relationship metadata
            metadata = row['metadata']
            relationship_fields = [k for k in metadata.keys() if k not in required_metadata_fields and k != 'text']
            if relationship_fields:
                graph_metadata_count += 1
        
        print(f"Rows with graph relationship metadata: {graph_metadata_count}/{len(all_rows)}")
        
        # Test node ID uniqueness
        print("\n🆔 Testing node ID uniqueness...")
        node_ids = [row['metadata']['node_id'] for row in all_rows]
        unique_node_ids = set(node_ids)
        
        if len(node_ids) != len(unique_node_ids):
            print(f"❌ Duplicate node IDs found: {len(node_ids) - len(unique_node_ids)} duplicates")
            return False
        
        print(f"✅ All {len(node_ids)} node IDs are unique")
        
        # Test namespace configuration
        print("\n🏷️ Testing namespace configuration...")
        per_row_namespace = get_per_row_namespace()
        print(f"Per-row namespace: {per_row_namespace}")
        
        if per_row_namespace != "per_row":
            print(f"❌ Unexpected namespace: {per_row_namespace}")
            return False
        
        print("✅ Namespace configuration is correct")
        
        print(f"\n✅ All tests passed! Generated {len(all_rows)} per-row vectors")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_table_rows():
    """Test specific table row generation."""
    print("\n🧪 Testing Specific Table Rows")
    print("=" * 50)
    
    try:
        chunker = PerRowChunker()
        
        # Test each table individually
        test_functions = [
            ("Departments", chunker.get_department_rows),
            ("Faculties", chunker.get_faculty_rows),
            ("Degree Courses", chunker.get_degree_course_rows),
            ("Courses", chunker.get_course_rows),
            ("Course Editions", chunker.get_course_edition_rows),
            ("Professors", chunker.get_professor_rows),
            ("Materials", chunker.get_material_rows),
            ("Reviews", chunker.get_review_rows),
            ("Ratings", chunker.get_rating_rows),
            ("Platforms", chunker.get_platform_rows),
            ("Theses", chunker.get_thesis_rows),
            ("Students", chunker.get_student_rows),
            ("Users", chunker.get_user_rows)
        ]
        
        for table_name, test_func in test_functions:
            try:
                rows = test_func()
                print(f"✅ {table_name}: {len(rows)} rows")
                
                if rows:
                    # Show sample metadata
                    sample = rows[0]
                    print(f"   Sample: {sample['metadata']['node_id']} ({sample['metadata']['node_type']})")
                    
            except Exception as e:
                print(f"❌ {table_name}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Specific table test failed: {e}")
        return False

def test_metadata_consistency():
    """Test metadata consistency across all rows."""
    print("\n🧪 Testing Metadata Consistency")
    print("=" * 50)
    
    try:
        chunker = PerRowChunker()
        all_rows = chunker.get_all_rows()
        
        # Check that all rows have consistent metadata structure
        metadata_fields = set()
        for row in all_rows:
            metadata_fields.update(row['metadata'].keys())
        
        print(f"All metadata fields found: {sorted(metadata_fields)}")
        
        # Check required fields are present in all rows
        required_fields = ['node_id', 'table_name', 'primary_key', 'node_type']
        missing_required = 0
        
        for row in all_rows:
            for field in required_fields:
                if field not in row['metadata']:
                    missing_required += 1
                    print(f"❌ Missing {field} in row {row['id']}")
        
        if missing_required == 0:
            print("✅ All required metadata fields present in all rows")
        else:
            print(f"❌ {missing_required} missing required fields")
            return False
        
        # Check node type consistency
        node_types = set()
        for row in all_rows:
            node_types.add(row['metadata']['node_type'])
        
        expected_node_types = {
            'dept', 'faculty', 'degree', 'course', 'edition', 'professor',
            'material', 'review', 'rating', 'platform', 'thesis', 'student', 'user'
        }
        
        unexpected_types = node_types - expected_node_types
        if unexpected_types:
            print(f"⚠️  Unexpected node types: {unexpected_types}")
        
        print(f"✅ Node types found: {sorted(node_types)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata consistency test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Per-Row Approach Tests")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if database connection is available
    if not os.getenv("DATABASE_URL") and not os.getenv("DB_NEON_HOST"):
        print("⚠️  No database configuration found. Make sure DATABASE_URL or DB_NEON_* variables are set.")
        print("   Tests will likely fail without database access.")
    
    # Run tests
    tests = [
        ("Per-Row Chunker", test_per_row_chunker),
        ("Specific Table Rows", test_specific_table_rows),
        ("Metadata Consistency", test_metadata_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The per-row approach is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 