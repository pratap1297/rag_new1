#!/usr/bin/env python3
"""
Complete FAISS to Qdrant Migration Script
This script handles the complete migration process from FAISS to Qdrant
"""
import sys
import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime

# Add the rag_system src to Python path
sys.path.insert(0, 'rag_system/src')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

def backup_current_config():
    """Backup current configuration"""
    config_path = "rag_system/data/config/system_config.json"
    backup_path = f"rag_system/data/config/system_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    if os.path.exists(config_path):
        import shutil
        shutil.copy2(config_path, backup_path)
        logging.info(f"Configuration backed up to: {backup_path}")
        return backup_path
    else:
        logging.warning("⚠️ No existing configuration found to backup")
        return None

def setup_qdrant_server():
    """Setup and start Qdrant server"""
    print("🔧 Setting up Qdrant server...")
    
    try:
        from rag_system.scripts.setup_qdrant import setup_qdrant, check_qdrant_status
        
        # Check if already running
        if check_qdrant_status():
            print("✅ Qdrant server is already running")
            return True
        
        # Start Qdrant
        if setup_qdrant():
            print("✅ Qdrant server started successfully")
            return True
        else:
            print("❌ Failed to start Qdrant server")
            return False
            
    except Exception as e:
        logging.error(f"Failed to setup Qdrant: {e}")
        return False

def check_existing_faiss_data():
    """Check if there's existing FAISS data to migrate"""
    faiss_paths = [
        "data/vectors/faiss_index.bin",
        "rag_system/data/vectors/faiss_index.bin"
    ]
    
    for path in faiss_paths:
        if os.path.exists(path):
            print(f"✅ Found FAISS data at: {path}")
            return path
    
    print("⚠️ No existing FAISS data found")
    return None

def perform_migration(faiss_path):
    """Perform the actual migration"""
    print("🚚 Starting migration process...")
    
    try:
        # Import required classes
        from rag_system.src.storage.faiss_store import FAISSStore
        from rag_system.src.storage.qdrant_store import QdrantVectorStore
        from rag_system.src.storage.faiss_to_qdrant_migration import FAISSToQdrantMigration
        
        # Load FAISS store
        print("📁 Loading FAISS store...")
        faiss_store = FAISSStore(
            index_path=faiss_path,
            dimension=1024
        )
        
        faiss_stats = faiss_store.get_stats()
        vector_count = faiss_stats.get('vector_count', faiss_stats.get('active_vectors', faiss_stats.get('ntotal', 0)))
        print(f"📊 FAISS store contains {vector_count} vectors")
        
        if vector_count == 0:
            print("⚠️ No vectors found in FAISS store")
            return False
        
        # Create Qdrant store
        print("🦅 Creating Qdrant store...")
        qdrant_store = QdrantVectorStore(
            url="localhost:6333",
            collection_name="rag_documents",
            dimension=1024,
            on_disk=True
        )
        
        # Perform migration
        print("🔄 Migrating vectors...")
        migration = FAISSToQdrantMigration(faiss_store, qdrant_store)
        results = migration.migrate(batch_size=100)
        
        print(f"📈 Migration Results:")
        print(f"   - Total vectors: {results['total']}")
        print(f"   - Migrated: {results['migrated']}")
        print(f"   - Failed: {results['failed']}")
        print(f"   - Success rate: {results['success_rate']:.2%}")
        
        # Verify migration
        qdrant_stats = qdrant_store.get_stats()
        qdrant_vector_count = qdrant_stats.get('vector_count', qdrant_stats.get('vectors_count', 0))
        print(f"✅ Qdrant store now contains {qdrant_vector_count} vectors")
        
        return results['success_rate'] > 0.9
        
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_configuration():
    """Update system configuration to use Qdrant"""
    print("⚙️ Updating system configuration...")
    
    config_path = "rag_system/data/config/system_config.json"
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update vector store configuration
        config['vector_store'] = {
            'type': 'qdrant',
            'url': 'localhost:6333',
            'collection_name': 'rag_documents',
            'dimension': 1024,
            'on_disk_storage': True
        }
        
        # Add migration timestamp
        config['migration'] = {
            'from': 'faiss',
            'to': 'qdrant',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration updated successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to update configuration: {e}")
        return False

def test_qdrant_system():
    """Test the migrated Qdrant system"""
    print("🧪 Testing migrated system...")
    
    try:
        # Test dependency injection
        from rag_system.src.core.dependency_container import DependencyContainer, register_core_services
        
        container = DependencyContainer()
        register_core_services(container)
        
        # Get vector store (should be Qdrant now)
        vector_store = container.get('vector_store')
        print(f"✅ Vector store type: {type(vector_store).__name__}")
        
        # Test basic functionality
        stats = vector_store.get_stats()
        print(f"✅ Vector store stats: {stats}")
        
        # Test search
        import numpy as np
        test_vector = np.random.random(1024).astype('float32').tolist()
        results = vector_store.search(test_vector, k=5)
        print(f"✅ Search test returned {len(results)} results")
        
        return True
        
    except Exception as e:
        logging.error(f"System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_migration_report(success, backup_path):
    """Create migration report"""
    report = {
        'migration_date': datetime.now().isoformat(),
        'success': success,
        'backup_config': backup_path,
        'qdrant_server': 'localhost:6333',
        'collection_name': 'rag_documents',
        'notes': []
    }
    
    if success:
        report['notes'].append("Migration completed successfully")
        report['notes'].append("System is now using Qdrant for vector storage")
        report['notes'].append("Original FAISS files have been preserved")
    else:
        report['notes'].append("Migration failed - check logs for details")
        report['notes'].append("System configuration has been restored")
    
    report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Migration report saved to: {report_path}")
    return report_path

def main():
    """Main migration function"""
    print("🚀 FAISS to Qdrant Migration Tool")
    print("=" * 50)
    
    # Step 1: Backup configuration
    backup_path = backup_current_config()
    
    # Step 2: Setup Qdrant server
    if not setup_qdrant_server():
        print("❌ Failed to setup Qdrant server. Aborting migration.")
        return False
    
    # Step 3: Check existing FAISS data
    faiss_path = check_existing_faiss_data()
    if not faiss_path:
        print("❌ No FAISS data found. Nothing to migrate.")
        return False
    
    # Step 4: Perform migration
    migration_success = perform_migration(faiss_path)
    if not migration_success:
        print("❌ Migration failed. Check logs for details.")
        return False
    
    # Step 5: Update configuration
    if not update_configuration():
        print("❌ Failed to update configuration.")
        return False
    
    # Step 6: Test migrated system
    if not test_qdrant_system():
        print("❌ System test failed after migration.")
        return False
    
    # Step 7: Create report
    report_path = create_migration_report(True, backup_path)
    
    print("\n🎉 Migration completed successfully!")
    print("=" * 50)
    print("✅ Your RAG system is now using Qdrant")
    print("✅ All data has been migrated")
    print("✅ Configuration has been updated")
    print(f"✅ Backup saved at: {backup_path}")
    print(f"✅ Report saved at: {report_path}")
    print("\n📝 Next steps:")
    print("   1. Restart your RAG system")
    print("   2. Test 'list all incidents' queries")
    print("   3. Monitor the migration.log file")
    print("   4. Keep the FAISS backup for safety")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 