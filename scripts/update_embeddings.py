#!/usr/bin/env python
"""
Script to update vector embeddings for all documents in the knowledge base.

This script can be run standalone to update embeddings for all documents
or specific documents by ID.
"""

import argparse
import sys
from typing import List
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mimirs_bucket.db import DocumentationSystem
from mimirs_bucket.search import VectorSearch
from mimirs_bucket.utils.log_utils import setup_logging

# Configure logging
logger = setup_logging(level="INFO", name="update-embeddings")

def update_all_embeddings(batch_size: int = 10, dry_run: bool = False) -> int:
    """
    Update embeddings for all documents in the database.
    
    Args:
        batch_size: Number of documents to process in a batch
        dry_run: If True, don't actually update the database
        
    Returns:
        Number of documents updated
    """
    # Initialize the database connection
    doc_system = DocumentationSystem()
    vector_search = VectorSearch(doc_system)
    
    # Get all documents
    aql = """
    FOR doc IN documents
        RETURN {
            _key: doc._key,
            title: doc.title,
            has_embedding: doc.embedding != null
        }
    """
    
    results = list(doc_system.db.aql.execute(aql))
    total_docs = len(results)
    docs_with_embeddings = sum(1 for doc in results if doc.get('has_embedding'))
    
    logger.info(f"Found {total_docs} documents total, {docs_with_embeddings} already have embeddings")
    
    if dry_run:
        logger.info("DRY RUN: No documents will be updated")
        return 0
    
    # Process documents in batches
    count = 0
    for i, doc_info in enumerate(results):
        doc_key = doc_info['_key']
        title = doc_info['title']
        has_embedding = doc_info['has_embedding']
        
        if i % batch_size == 0:
            logger.info(f"Processing batch {i // batch_size + 1} of {(total_docs + batch_size - 1) // batch_size}")
        
        # Get the full document
        doc = doc_system.get_document(doc_key)
        if not doc:
            logger.warning(f"Document {doc_key} not found when fetching full document")
            continue
            
        # Update the embedding
        logger.info(f"Processing document {doc_key} - '{title}' (already has embedding: {has_embedding})")
        success = vector_search._update_single_document_embedding(doc)
        
        if success:
            count += 1
            logger.info(f"Document {count}/{total_docs} updated successfully")
        else:
            logger.error(f"Failed to update document {doc_key}")
    
    logger.info(f"Updated embeddings for {count} documents")
    return count

def update_specific_documents(doc_keys: List[str], dry_run: bool = False) -> int:
    """
    Update embeddings for specific documents.
    
    Args:
        doc_keys: List of document keys to update
        dry_run: If True, don't actually update the database
        
    Returns:
        Number of documents updated
    """
    # Initialize the database connection
    doc_system = DocumentationSystem()
    vector_search = VectorSearch(doc_system)
    
    if dry_run:
        logger.info("DRY RUN: No documents will be updated")
        return 0
    
    count = 0
    for doc_key in doc_keys:
        # Get the document
        doc = doc_system.get_document(doc_key)
        if not doc:
            logger.warning(f"Document {doc_key} not found")
            continue
            
        # Update the embedding
        logger.info(f"Processing document {doc_key} - '{doc.title}'")
        
        success = vector_search._update_single_document_embedding(doc)
        
        if success:
            count += 1
            logger.info(f"Document {count}/{len(doc_keys)} updated successfully")
        else:
            logger.error(f"Failed to update document {doc_key}")
    
    logger.info(f"Updated embeddings for {count}/{len(doc_keys)} documents")
    return count

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update vector embeddings for documents")
    
    parser.add_argument(
        "--document", "-d", 
        action="append", 
        help="Update a specific document by key (can be repeated)"
    )
    
    parser.add_argument(
        "--batch-size", "-b", 
        type=int, 
        default=10, 
        help="Number of documents to process in a batch"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Don't actually update the database"
    )
    
    args = parser.parse_args()
    
    if args.document:
        count = update_specific_documents(args.document, args.dry_run)
    else:
        count = update_all_embeddings(args.batch_size, args.dry_run)
    
    print(f"Updated {count} documents")
    
if __name__ == "__main__":
    main()
