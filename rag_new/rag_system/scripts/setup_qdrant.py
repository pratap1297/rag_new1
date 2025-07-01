"""
Setup script for Qdrant vector database
"""
import subprocess
import time
import requests
import logging
from pathlib import Path

def setup_qdrant():
    """Setup Qdrant server using Docker"""
    
    logging.info("Setting up Qdrant server...")
    
    # Check if Docker is available
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        logging.info("Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("Docker is not available. Please install Docker first.")
        return False
    
    # Check if Qdrant is already running
    try:
        response = requests.get('http://localhost:6333/collections', timeout=5)
        if response.status_code == 200:
            logging.info("Qdrant is already running")
            return True
    except requests.exceptions.RequestException:
        pass
    
    # Start Qdrant container
    try:
        logging.info("Starting Qdrant container...")
        
        # Stop existing container if any
        subprocess.run(['docker', 'stop', 'qdrant'], capture_output=True)
        subprocess.run(['docker', 'rm', 'qdrant'], capture_output=True)
        
        # Run new container
        cmd = [
            'docker', 'run', '-d',
            '--name', 'qdrant',
            '-p', '6333:6333',
            '-p', '6334:6334',
            '-v', 'qdrant_storage:/qdrant/storage',
            'qdrant/qdrant'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Qdrant container started: {result.stdout.strip()}")
        
        # Wait for Qdrant to be ready
        logging.info("Waiting for Qdrant to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                time.sleep(1)
                response = requests.get('http://localhost:6333/collections', timeout=5)
                if response.status_code == 200:
                    logging.info("Qdrant is ready!")
                    return True
            except requests.exceptions.RequestException:
                continue
        
        logging.error("Qdrant failed to start within 30 seconds")
        return False
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to start Qdrant: {e}")
        return False

def check_qdrant_status():
    """Check if Qdrant is running"""
    try:
        response = requests.get('http://localhost:6333/collections', timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant is running and accessible")
            
            # Get collections info
            data = response.json()
            collections = data.get('result', {}).get('collections', [])
            print(f"📊 Collections: {len(collections)}")
            
            for collection in collections:
                name = collection.get('name', 'Unknown')
                # Try different possible field names for vector count
                vectors_count = (
                    collection.get('vectors_count') or 
                    collection.get('points_count') or 
                    collection.get('vectors') or 
                    'Unknown'
                )
                print(f"  - {name}: {vectors_count} vectors")
            
            return True
        else:
            print("❌ Qdrant is not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Qdrant is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error checking Qdrant status: {e}")
        return False

def stop_qdrant():
    """Stop Qdrant container"""
    try:
        subprocess.run(['docker', 'stop', 'qdrant'], check=True, capture_output=True)
        subprocess.run(['docker', 'rm', 'qdrant'], capture_output=True)
        print("Qdrant container stopped and removed")
        return True
    except subprocess.CalledProcessError:
        print("Failed to stop Qdrant container")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            setup_qdrant()
        elif sys.argv[1] == "status":
            check_qdrant_status()
        elif sys.argv[1] == "stop":
            stop_qdrant()
        else:
            print("Usage: python setup_qdrant.py [start|status|stop]")
    else:
        setup_qdrant() 