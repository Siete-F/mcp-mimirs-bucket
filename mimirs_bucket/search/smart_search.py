"""
Smart search functionality for Mimir's Bucket

This module provides enhanced search capabilities including:
- Fuzzy matching for typo-tolerance
- Search across both title and content
- Query expansion for better recall
- Ranking of results by relevance 
- Suggestion of related search terms
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
import string
import datetime
import logging
from difflib import SequenceMatcher

logger = logging.getLogger("mimirs_bucket.search")

class SmartSearch:
    """Smart search implementation for ArangoDB-based knowledge base"""
    
    def __init__(self, db):
        """Initialize with database connection"""
        self.db = db
        
    def search(self, query: str, limit: int = 10, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        Smart search across documents
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_score: Minimum relevance score (0-1)
            
        Returns:
            List of documents with relevance scores
        """
        # Clean and process the query
        clean_query = self._clean_query(query)
        query_terms = self._extract_terms(clean_query)
        expanded_terms = self._expand_query(query_terms)
        
        logger.info(f"Search query: '{query}' -> {expanded_terms}")
        
        # Build AQL query with relevance scoring
        aql = """
        LET terms = @terms
        FOR doc IN documents
            LET score_title = (
                FOR term IN terms
                    LET title_score = CONTAINS(LOWER(doc.title), term) ? 1.0 : 0.0
                    RETURN title_score
            )
            LET score_content = (
                FOR term IN terms
                    LET content_score = CONTAINS(LOWER(doc.content), term) ? 0.5 : 0.0
                    RETURN content_score
            )
            LET score_summary = (
                FOR term IN terms
                    LET summary_score = (doc.summary && CONTAINS(LOWER(doc.summary), term)) ? 0.8 : 0.0
                    RETURN summary_score
            )
            LET score_tags = (
                FOR term IN terms
                    LET tag_matches = (
                        FOR tag IN doc.tags
                            FILTER CONTAINS(LOWER(tag), term)
                            RETURN 1
                    )
                    RETURN LENGTH(tag_matches) > 0 ? 0.7 : 0.0
            )
            
            LET max_scores = FLATTEN([score_title, score_content, score_summary, score_tags])
            LET relevance_score = AVG(max_scores)
            
            FILTER relevance_score >= @minScore
            SORT relevance_score DESC
            LIMIT @limit
            RETURN {
                doc: doc,
                score: relevance_score
            }
        """
        
        # Execute the query
        results = self.db.aql.execute(aql, bind_vars={
            "terms": list(expanded_terms),
            "minScore": min_score,
            "limit": limit
        })
        
        # Convert to list and return
        return [result for result in results]
        
    def fuzzy_search(self, query: str, limit: int = 10, min_score: float = 0.3, 
                    max_distance: int = 2) -> List[Dict[str, Any]]:
        """
        Fuzzy search to handle typos
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_score: Minimum relevance score
            max_distance: Maximum edit distance for fuzzy matching
            
        Returns:
            List of documents with relevance scores
        """
        clean_query = self._clean_query(query)
        query_terms = self._extract_terms(clean_query)
        
        logger.info(f"Fuzzy search query: '{query}' -> {query_terms}")
        
        # ArangoDB doesn't directly support fuzzy search, 
        # so we implement a hybrid approach
        
        # First, get candidate documents with any of the terms
        candidates_aql = """
        FOR doc IN documents
            LET text = CONCAT(doc.title, " ", doc.content)
            FOR term IN @terms
                FILTER CONTAINS(LOWER(text), term)
                COLLECT docKey = doc._key INTO matched
                RETURN document(documents, docKey)
        """
        
        candidates = list(self.db.aql.execute(candidates_aql, bind_vars={
            "terms": list(query_terms)
        }))
        
        # Then, score each document using fuzzy matching
        results = []
        for doc in candidates:
            doc_text = (doc["title"] + " " + doc["content"]).lower()
            score = self._compute_fuzzy_score(doc_text, clean_query)
            
            if score >= min_score:
                results.append({
                    "doc": doc,
                    "score": score
                })
        
        # Sort and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
            
    def get_suggestions(self, query: str, max_suggestions: int = 5) -> List[str]:
        """
        Get search term suggestions based on a partial query
        
        Args:
            query: Partial search query
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested search terms
        """
        clean_query = self._clean_query(query)
        
        if not clean_query:
            return self._get_top_tags(max_suggestions)
        
        # Look for terms that start with the query
        aql = """
        LET content_terms = (
            FOR doc IN documents
                LET words = SPLIT(LOWER(doc.title), " ")
                FOR word IN words
                    FILTER STARTS_WITH(word, @query)
                    COLLECT term = word WITH COUNT INTO count
                    SORT count DESC
                    LIMIT @limit
                    RETURN {term: term, count: count}
        )
        
        LET tag_terms = (
            FOR doc IN documents
                FOR tag IN doc.tags
                    FILTER STARTS_WITH(LOWER(tag), @query)
                    COLLECT term = tag WITH COUNT INTO count
                    SORT count DESC
                    LIMIT @limit
                    RETURN {term: term, count: count}
        )
        
        FOR term IN APPEND(content_terms, tag_terms)
            SORT term.count DESC
            LIMIT @limit
            RETURN term.term
        """
        
        results = self.db.aql.execute(aql, bind_vars={
            "query": clean_query,
            "limit": max_suggestions
        })
        
        return [result for result in results]
    
    def similar_queries(self, query: str, max_suggestions: int = 3) -> List[str]:
        """
        Generate similar queries based on user's input
        
        Args:
            query: User's search query
            max_suggestions: Maximum number of suggested queries
            
        Returns:
            List of suggested queries
        """
        clean_query = self._clean_query(query)
        query_terms = self._extract_terms(clean_query)
        
        if not query_terms:
            return []
        
        # Get related terms
        related_terms = set()
        for term in query_terms:
            related = self._find_related_terms(term)
            related_terms.update(related)
        
        # Remove original query terms
        related_terms = related_terms - query_terms
        
        # Create new queries by combining original and related terms
        suggestions = []
        for related_term in list(related_terms)[:max_suggestions]:
            new_query = clean_query + " " + related_term
            suggestions.append(new_query)
        
        return suggestions
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the search query"""
        # Convert to lowercase
        query = query.lower()
        
        # Remove punctuation
        translator = str.maketrans('', '', string.punctuation)
        query = query.translate(translator)
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        return query
    
    def _extract_terms(self, text: str) -> Set[str]:
        """Extract search terms from text"""
        # Split by whitespace
        terms = text.split()
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        terms = [term for term in terms if term not in stop_words and len(term) > 1]
        
        return set(terms)
    
    def _expand_query(self, terms: Set[str]) -> Set[str]:
        """Expand query with related terms"""
        expanded = terms.copy()
        
        # Add stemmed/lemmatized versions of terms
        for term in terms:
            # Simple stemming (just as an example)
            if term.endswith('ing'):
                expanded.add(term[:-3])  # Remove 'ing'
            elif term.endswith('s') and not term.endswith('ss'):
                expanded.add(term[:-1])  # Remove plural 's'
            elif term.endswith('ed'):
                expanded.add(term[:-2])  # Remove 'ed'
        
        return expanded
    
    def _compute_fuzzy_score(self, text: str, query: str) -> float:
        """Compute fuzzy match score between text and query"""
        matcher = SequenceMatcher(None, text, query)
        return matcher.ratio()
    
    def _find_related_terms(self, term: str, limit: int = 5) -> List[str]:
        """Find terms related to a given term based on co-occurrence"""
        # Get documents containing the term
        aql = """
        FOR doc IN documents
            FILTER CONTAINS(LOWER(doc.content), @term) 
               OR CONTAINS(LOWER(doc.title), @term)
               OR @term IN doc.tags
            
            // Extract unique words from content
            LET content_words = UNIQUE(
                FOR word IN SPLIT(LOWER(SUBSTITUTE(doc.content, /[.,;:!?()[\]{}]/g, " ")), " ")
                    FILTER LENGTH(word) > 3 AND word != @term
                    RETURN word
            )
            
            // Extract words from title
            LET title_words = UNIQUE(
                FOR word IN SPLIT(LOWER(SUBSTITUTE(doc.title, /[.,;:!?()[\]{}]/g, " ")), " ")
                    FILTER LENGTH(word) > 3 AND word != @term
                    RETURN word
            )
            
            // Combine all related terms
            LET words = APPEND(content_words, title_words, doc.tags)
            
            RETURN UNIQUE(words)
        """
        
        results = self.db.aql.execute(aql, bind_vars={"term": term})
        
        # Flatten results and count occurrences
        term_counts = {}
        for doc_terms in results:
            for related_term in doc_terms:
                term_counts[related_term] = term_counts.get(related_term, 0) + 1
        
        # Sort by frequency and return top terms
        related_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        return [term for term, count in related_terms[:limit]]
    
    def _get_top_tags(self, limit: int = 5) -> List[str]:
        """Get the most frequently used tags"""
        aql = """
        FOR doc IN documents
            FOR tag IN doc.tags
                COLLECT tagName = tag WITH COUNT INTO count
                SORT count DESC
                LIMIT @limit
                RETURN tagName
        """
        
        results = self.db.aql.execute(aql, bind_vars={"limit": limit})
        return [result for result in results]
