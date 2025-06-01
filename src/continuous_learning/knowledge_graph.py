"""
Knowledge Graph for Continuous Learning System

This module implements a knowledge graph for storing and retrieving learned patterns,
relationships, and recommendations for codebase analysis.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
from abc import ABC, abstractmethod

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.symbol import Symbol
from .pattern_engine import CodePattern, PatternType


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""
    CODE_PATTERN = "code_pattern"
    IMPLEMENTATION = "implementation"
    DEVELOPER = "developer"
    PROJECT = "project"
    ERROR = "error"
    OPTIMIZATION = "optimization"
    RECOMMENDATION = "recommendation"


class RelationshipType(Enum):
    """Types of relationships in the knowledge graph."""
    IMPLEMENTS = "implements"
    RESOLVES = "resolves"
    BELONGS_TO = "belongs_to"
    SIMILAR_TO = "similar_to"
    LEADS_TO = "leads_to"
    RECOMMENDS = "recommends"
    DEPENDS_ON = "depends_on"
    IMPROVES = "improves"


@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph."""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any]
    created_at: str
    updated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'properties': self.properties,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class KnowledgeRelationship:
    """Represents a relationship in the knowledge graph."""
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any]
    confidence: float
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary representation."""
        return {
            'relationship_id': self.relationship_id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'relationship_type': self.relationship_type.value,
            'properties': self.properties,
            'confidence': self.confidence,
            'created_at': self.created_at
        }


class KnowledgeGraphStorage(ABC):
    """Abstract base class for knowledge graph storage backends."""
    
    @abstractmethod
    def create_node(self, node: KnowledgeNode) -> bool:
        """Create a new node in the graph."""
        pass
    
    @abstractmethod
    def create_relationship(self, relationship: KnowledgeRelationship) -> bool:
        """Create a new relationship in the graph."""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Retrieve a node by its ID."""
        pass
    
    @abstractmethod
    def find_nodes(self, node_type: NodeType, filters: Dict[str, Any]) -> List[KnowledgeNode]:
        """Find nodes matching the given criteria."""
        pass
    
    @abstractmethod
    def find_relationships(self, source_id: str, relationship_type: RelationshipType) -> List[KnowledgeRelationship]:
        """Find relationships from a source node."""
        pass
    
    @abstractmethod
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """Update node properties."""
        pass


class InMemoryKnowledgeGraphStorage(KnowledgeGraphStorage):
    """In-memory implementation of knowledge graph storage for development/testing."""
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.relationships: Dict[str, KnowledgeRelationship] = {}
        self.node_index: Dict[NodeType, Set[str]] = {nt: set() for nt in NodeType}
        self.relationship_index: Dict[str, Set[str]] = {}
    
    def create_node(self, node: KnowledgeNode) -> bool:
        """Create a new node in the graph."""
        try:
            self.nodes[node.node_id] = node
            self.node_index[node.node_type].add(node.node_id)
            return True
        except Exception:
            return False
    
    def create_relationship(self, relationship: KnowledgeRelationship) -> bool:
        """Create a new relationship in the graph."""
        try:
            self.relationships[relationship.relationship_id] = relationship
            
            # Update relationship index
            source_key = f"{relationship.source_node_id}_{relationship.relationship_type.value}"
            if source_key not in self.relationship_index:
                self.relationship_index[source_key] = set()
            self.relationship_index[source_key].add(relationship.relationship_id)
            
            return True
        except Exception:
            return False
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Retrieve a node by its ID."""
        return self.nodes.get(node_id)
    
    def find_nodes(self, node_type: NodeType, filters: Dict[str, Any]) -> List[KnowledgeNode]:
        """Find nodes matching the given criteria."""
        candidate_ids = self.node_index.get(node_type, set())
        matching_nodes = []
        
        for node_id in candidate_ids:
            node = self.nodes[node_id]
            if self._matches_filters(node, filters):
                matching_nodes.append(node)
        
        return matching_nodes
    
    def find_relationships(self, source_id: str, relationship_type: RelationshipType) -> List[KnowledgeRelationship]:
        """Find relationships from a source node."""
        source_key = f"{source_id}_{relationship_type.value}"
        relationship_ids = self.relationship_index.get(source_key, set())
        
        return [self.relationships[rel_id] for rel_id in relationship_ids]
    
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """Update node properties."""
        if node_id in self.nodes:
            self.nodes[node_id].properties.update(properties)
            return True
        return False
    
    def _matches_filters(self, node: KnowledgeNode, filters: Dict[str, Any]) -> bool:
        """Check if a node matches the given filters."""
        for key, value in filters.items():
            if key not in node.properties or node.properties[key] != value:
                return False
        return True


class SimilarityMatcher:
    """Handles similarity matching between patterns and implementations."""
    
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def calculate_pattern_similarity(self, pattern1: CodePattern, pattern2: CodePattern) -> float:
        """Calculate similarity between two code patterns."""
        # Simple similarity based on pattern type and description
        type_similarity = 1.0 if pattern1.pattern_type == pattern2.pattern_type else 0.0
        
        # Text similarity (simplified)
        desc_similarity = self._text_similarity(pattern1.description, pattern2.description)
        
        # Weighted combination
        return 0.6 * type_similarity + 0.4 * desc_similarity
    
    def find_similar_patterns(self, target_pattern: CodePattern, all_patterns: List[CodePattern]) -> List[Tuple[CodePattern, float]]:
        """Find patterns similar to the target pattern."""
        similar_patterns = []
        
        for pattern in all_patterns:
            if pattern.pattern_id != target_pattern.pattern_id:
                similarity = self.calculate_pattern_similarity(target_pattern, pattern)
                if similarity >= self.similarity_threshold:
                    similar_patterns.append((pattern, similarity))
        
        # Sort by similarity score
        similar_patterns.sort(key=lambda x: x[1], reverse=True)
        return similar_patterns
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)


class RecommendationEngine:
    """Generates recommendations based on knowledge graph data."""
    
    def __init__(self, knowledge_graph: 'KnowledgeGraph'):
        self.knowledge_graph = knowledge_graph
        self.similarity_matcher = SimilarityMatcher()
    
    def generate_recommendations(self, codebase: Codebase, patterns: List[CodePattern]) -> List[Dict[str, Any]]:
        """Generate recommendations based on codebase analysis and known patterns."""
        recommendations = []
        
        # Pattern-based recommendations
        recommendations.extend(self._generate_pattern_recommendations(patterns))
        
        # Similarity-based recommendations
        recommendations.extend(self._generate_similarity_recommendations(patterns))
        
        # Historical success recommendations
        recommendations.extend(self._generate_historical_recommendations(codebase))
        
        # Sort by confidence and return top recommendations
        recommendations.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return recommendations[:10]  # Return top 10 recommendations
    
    def _generate_pattern_recommendations(self, patterns: List[CodePattern]) -> List[Dict[str, Any]]:
        """Generate recommendations based on identified patterns."""
        recommendations = []
        
        for pattern in patterns:
            if pattern.confidence > 0.6:
                # Find related optimizations
                optimizations = self.knowledge_graph.find_related_optimizations(pattern.pattern_id)
                
                for optimization in optimizations:
                    recommendation = {
                        'type': 'optimization',
                        'title': f"Apply {optimization.properties.get('name', 'optimization')}",
                        'description': optimization.properties.get('description', ''),
                        'confidence': pattern.confidence * 0.8,
                        'source_pattern': pattern.pattern_id,
                        'impact': optimization.properties.get('impact', 'medium')
                    }
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_similarity_recommendations(self, patterns: List[CodePattern]) -> List[Dict[str, Any]]:
        """Generate recommendations based on pattern similarity."""
        recommendations = []
        
        for pattern in patterns:
            # Find similar patterns in knowledge graph
            similar_patterns = self.knowledge_graph.find_similar_patterns(pattern)
            
            for similar_pattern, similarity_score in similar_patterns:
                recommendation = {
                    'type': 'similar_pattern',
                    'title': f"Consider pattern similar to {pattern.pattern_type.value}",
                    'description': f"Based on similarity to {similar_pattern.description}",
                    'confidence': similarity_score * pattern.confidence,
                    'source_pattern': pattern.pattern_id,
                    'similar_pattern': similar_pattern.pattern_id,
                    'impact': 'medium'
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_historical_recommendations(self, codebase: Codebase) -> List[Dict[str, Any]]:
        """Generate recommendations based on historical success data."""
        recommendations = []
        
        # Find successful implementations for similar projects
        project_characteristics = self._extract_project_characteristics(codebase)
        successful_implementations = self.knowledge_graph.find_successful_implementations(project_characteristics)
        
        for implementation in successful_implementations:
            recommendation = {
                'type': 'historical_success',
                'title': f"Apply proven implementation: {implementation.properties.get('name', 'implementation')}",
                'description': implementation.properties.get('description', ''),
                'confidence': implementation.properties.get('success_rate', 0.5),
                'impact': implementation.properties.get('impact', 'medium'),
                'evidence': f"Successful in {implementation.properties.get('success_count', 0)} similar projects"
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _extract_project_characteristics(self, codebase: Codebase) -> Dict[str, Any]:
        """Extract characteristics of the current project."""
        return {
            'file_count': len(list(codebase.files)),
            'function_count': len(list(codebase.functions)),
            'class_count': len(list(codebase.classes)),
            'complexity': 'medium'  # Simplified complexity assessment
        }


class KnowledgeGraph:
    """Main knowledge graph class that coordinates storage, similarity matching, and recommendations."""
    
    def __init__(self, storage: Optional[KnowledgeGraphStorage] = None):
        self.storage = storage or InMemoryKnowledgeGraphStorage()
        self.similarity_matcher = SimilarityMatcher()
        self.recommendation_engine = RecommendationEngine(self)
    
    def add_pattern(self, pattern: CodePattern) -> str:
        """Add a code pattern to the knowledge graph."""
        node_id = self._generate_node_id(pattern.pattern_id)
        
        node = KnowledgeNode(
            node_id=node_id,
            node_type=NodeType.CODE_PATTERN,
            properties={
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type.value,
                'confidence': pattern.confidence,
                'frequency': pattern.frequency,
                'description': pattern.description,
                'examples': pattern.examples,
                'metadata': pattern.metadata
            },
            created_at=self._current_timestamp(),
            updated_at=self._current_timestamp()
        )
        
        self.storage.create_node(node)
        return node_id
    
    def add_implementation(self, implementation_data: Dict[str, Any]) -> str:
        """Add an implementation record to the knowledge graph."""
        node_id = self._generate_node_id(f"impl_{implementation_data.get('name', 'unknown')}")
        
        node = KnowledgeNode(
            node_id=node_id,
            node_type=NodeType.IMPLEMENTATION,
            properties=implementation_data,
            created_at=self._current_timestamp(),
            updated_at=self._current_timestamp()
        )
        
        self.storage.create_node(node)
        return node_id
    
    def create_relationship(self, source_id: str, target_id: str, relationship_type: RelationshipType, 
                          properties: Optional[Dict[str, Any]] = None, confidence: float = 1.0) -> str:
        """Create a relationship between two nodes."""
        relationship_id = self._generate_relationship_id(source_id, target_id, relationship_type)
        
        relationship = KnowledgeRelationship(
            relationship_id=relationship_id,
            source_node_id=source_id,
            target_node_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
            confidence=confidence,
            created_at=self._current_timestamp()
        )
        
        self.storage.create_relationship(relationship)
        return relationship_id
    
    def find_similar_patterns(self, target_pattern: CodePattern) -> List[Tuple[CodePattern, float]]:
        """Find patterns similar to the target pattern."""
        # Get all patterns from storage
        pattern_nodes = self.storage.find_nodes(NodeType.CODE_PATTERN, {})
        
        all_patterns = []
        for node in pattern_nodes:
            pattern = self._node_to_pattern(node)
            all_patterns.append(pattern)
        
        return self.similarity_matcher.find_similar_patterns(target_pattern, all_patterns)
    
    def find_related_optimizations(self, pattern_id: str) -> List[KnowledgeNode]:
        """Find optimizations related to a specific pattern."""
        # Find pattern node
        pattern_nodes = self.storage.find_nodes(NodeType.CODE_PATTERN, {'pattern_id': pattern_id})
        if not pattern_nodes:
            return []
        
        pattern_node = pattern_nodes[0]
        
        # Find relationships to optimizations
        relationships = self.storage.find_relationships(pattern_node.node_id, RelationshipType.IMPROVES)
        
        optimizations = []
        for rel in relationships:
            optimization_node = self.storage.get_node(rel.target_node_id)
            if optimization_node and optimization_node.node_type == NodeType.OPTIMIZATION:
                optimizations.append(optimization_node)
        
        return optimizations
    
    def find_successful_implementations(self, project_characteristics: Dict[str, Any]) -> List[KnowledgeNode]:
        """Find implementations that were successful in similar projects."""
        # Simplified implementation - in practice, this would use more sophisticated matching
        implementation_nodes = self.storage.find_nodes(NodeType.IMPLEMENTATION, {})
        
        successful_implementations = []
        for node in implementation_nodes:
            success_rate = node.properties.get('success_rate', 0)
            if success_rate > 0.7:  # Consider implementations with >70% success rate
                successful_implementations.append(node)
        
        return successful_implementations
    
    def get_recommendations(self, codebase: Codebase, patterns: List[CodePattern]) -> List[Dict[str, Any]]:
        """Get recommendations for the given codebase and patterns."""
        return self.recommendation_engine.generate_recommendations(codebase, patterns)
    
    def update_pattern_feedback(self, pattern_id: str, feedback_data: Dict[str, Any]):
        """Update pattern based on user feedback."""
        pattern_nodes = self.storage.find_nodes(NodeType.CODE_PATTERN, {'pattern_id': pattern_id})
        
        for node in pattern_nodes:
            # Update confidence based on feedback
            current_confidence = node.properties.get('confidence', 0.5)
            feedback_score = feedback_data.get('score', 0.5)
            
            # Use exponential moving average
            new_confidence = 0.8 * current_confidence + 0.2 * feedback_score
            
            self.storage.update_node(node.node_id, {
                'confidence': new_confidence,
                'last_feedback': feedback_data,
                'updated_at': self._current_timestamp()
            })
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        stats = {}
        
        for node_type in NodeType:
            nodes = self.storage.find_nodes(node_type, {})
            stats[f"{node_type.value}_count"] = len(nodes)
        
        return stats
    
    def _generate_node_id(self, base_id: str) -> str:
        """Generate a unique node ID."""
        return hashlib.md5(base_id.encode()).hexdigest()
    
    def _generate_relationship_id(self, source_id: str, target_id: str, relationship_type: RelationshipType) -> str:
        """Generate a unique relationship ID."""
        combined = f"{source_id}_{target_id}_{relationship_type.value}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _current_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.utcnow().isoformat()
    
    def _node_to_pattern(self, node: KnowledgeNode) -> CodePattern:
        """Convert a knowledge node to a CodePattern object."""
        props = node.properties
        return CodePattern(
            pattern_id=props['pattern_id'],
            pattern_type=PatternType(props['pattern_type']),
            confidence=props['confidence'],
            frequency=props['frequency'],
            description=props['description'],
            examples=props['examples'],
            metadata=props['metadata']
        )

