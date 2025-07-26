"""
Advanced Similarity Detection Engine

This module implements multiple similarity detection algorithms and advanced
scoring mechanisms for comprehensive copyright analysis.
"""

import re
import math
from typing import Dict, List, Tuple, Any, Optional
from difflib import SequenceMatcher
from collections import Counter
import numpy as np


class SimilarityAlgorithm:
    """Base class for similarity algorithms"""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0.0 - 1.0)"""
        raise NotImplementedError
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for comparison"""
        # Normalize case and whitespace
        text = text.lower().strip()
        # Remove punctuation except apostrophes
        text = re.sub(r"[^\w\s']", ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text


class ExactMatchAlgorithm(SimilarityAlgorithm):
    """Exact string matching"""
    
    def __init__(self):
        super().__init__("exact_match", weight=2.0)  # High weight for exact matches
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        processed1 = self.preprocess_text(text1)
        processed2 = self.preprocess_text(text2)
        
        return 1.0 if processed1 == processed2 else 0.0


class EditDistanceAlgorithm(SimilarityAlgorithm):
    """Levenshtein edit distance similarity"""
    
    def __init__(self):
        super().__init__("edit_distance", weight=1.5)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        processed1 = self.preprocess_text(text1)
        processed2 = self.preprocess_text(text2)
        
        # Use difflib's SequenceMatcher for efficiency
        matcher = SequenceMatcher(None, processed1, processed2)
        return matcher.ratio()


class JaccardSimilarityAlgorithm(SimilarityAlgorithm):
    """Jaccard similarity based on word sets"""
    
    def __init__(self):
        super().__init__("jaccard", weight=1.2)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        processed1 = self.preprocess_text(text1)
        processed2 = self.preprocess_text(text2)
        
        words1 = set(processed1.split())
        words2 = set(processed2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


class CosineSimilarityAlgorithm(SimilarityAlgorithm):
    """Cosine similarity using TF-IDF vectors"""
    
    def __init__(self):
        super().__init__("cosine", weight=1.3)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        processed1 = self.preprocess_text(text1)
        processed2 = self.preprocess_text(text2)
        
        # Create word frequency vectors
        words1 = processed1.split()
        words2 = processed2.split()
        
        # Get all unique words
        all_words = set(words1 + words2)
        
        if not all_words:
            return 1.0
        
        # Create frequency vectors
        vec1 = [words1.count(word) for word in all_words]
        vec2 = [words2.count(word) for word in all_words]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


class NGramSimilarityAlgorithm(SimilarityAlgorithm):
    """N-gram based similarity"""
    
    def __init__(self, n: int = 3):
        super().__init__(f"ngram_{n}", weight=1.1)
        self.n = n
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        processed1 = self.preprocess_text(text1)
        processed2 = self.preprocess_text(text2)
        
        # Generate n-grams
        ngrams1 = self._generate_ngrams(processed1, self.n)
        ngrams2 = self._generate_ngrams(processed2, self.n)
        
        if not ngrams1 and not ngrams2:
            return 1.0
        
        # Calculate similarity using Jaccard on n-grams
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_ngrams(self, text: str, n: int) -> set:
        """Generate n-grams from text"""
        if len(text) < n:
            return {text}
        
        return {text[i:i+n] for i in range(len(text) - n + 1)}


class SemanticPatternAlgorithm(SimilarityAlgorithm):
    """Semantic pattern matching for lyrics"""
    
    def __init__(self):
        super().__init__("semantic_pattern", weight=1.4)
        
        # Common lyrical patterns that indicate similarity
        self.pattern_templates = [
            # Emotional expressions
            (r'\b(i|you|we)\s+(love|need|want|miss)\s+(you|me|us)\b', 'emotional_declaration'),
            (r'\b(dont|wont|cant)\s+(leave|go|stop)\b', 'negative_plea'),
            (r'\b(all|every)\s+(night|day|time)\b', 'temporal_intensity'),
            
            # Action patterns
            (r'\b(dance|party|celebrate)\s+(all|through|until)\s+(night|dawn|morning)\b', 'celebration'),
            (r'\b(hold|take|give)\s+(me|you|us)\s+(tight|close|forever)\b', 'intimate_action'),
            (r'\b(shake|move|rock)\s+(it|your|that)\s+(off|away|out)\b', 'movement_action'),
            
            # Relationship patterns
            (r'\b(baby|honey|darling|sweetheart)\s+(please|dont|come)\b', 'romantic_address'),
            (r'\b(never|always|forever)\s+(gonna|going to)\b', 'commitment_expression'),
            
            # Universal themes
            (r'\b(dream|dreams)\s+(come|came)\s+(true|alive)\b', 'dream_fulfillment'),
            (r'\b(heart|soul)\s+(on|in)\s+(fire|flames)\b', 'passionate_metaphor'),
        ]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        processed1 = self.preprocess_text(text1)
        processed2 = self.preprocess_text(text2)
        
        patterns1 = self._extract_patterns(processed1)
        patterns2 = self._extract_patterns(processed2)
        
        if not patterns1 and not patterns2:
            return 0.0
        
        # Calculate pattern overlap
        common_patterns = patterns1.intersection(patterns2)
        total_patterns = patterns1.union(patterns2)
        
        if not total_patterns:
            return 0.0
        
        base_similarity = len(common_patterns) / len(total_patterns)
        
        # Boost score if multiple patterns match
        pattern_boost = min(0.3, len(common_patterns) * 0.1)
        
        return min(1.0, base_similarity + pattern_boost)
    
    def _extract_patterns(self, text: str) -> set:
        """Extract semantic patterns from text"""
        patterns = set()
        
        for pattern_regex, pattern_name in self.pattern_templates:
            if re.search(pattern_regex, text, re.IGNORECASE):
                patterns.add(pattern_name)
        
        return patterns


class RhymePatternAlgorithm(SimilarityAlgorithm):
    """Rhyme and rhythm pattern similarity"""
    
    def __init__(self):
        super().__init__("rhyme_pattern", weight=1.0)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        processed1 = self.preprocess_text(text1)
        processed2 = self.preprocess_text(text2)
        
        # Extract ending sounds
        ending1 = self._get_ending_sound(processed1)
        ending2 = self._get_ending_sound(processed2)
        
        if not ending1 or not ending2:
            return 0.0
        
        # Check for rhyme similarity
        rhyme_similarity = self._calculate_rhyme_similarity(ending1, ending2)
        
        # Check syllable pattern similarity
        syllable_similarity = self._calculate_syllable_similarity(processed1, processed2)
        
        return (rhyme_similarity + syllable_similarity) / 2
    
    def _get_ending_sound(self, text: str) -> str:
        """Extract ending sound pattern"""
        words = text.split()
        if not words:
            return ""
        
        last_word = words[-1].lower()
        
        # Extract ending sound (simplified phonetic matching)
        if len(last_word) >= 3:
            return last_word[-3:]
        else:
            return last_word
    
    def _calculate_rhyme_similarity(self, ending1: str, ending2: str) -> float:
        """Calculate rhyme similarity"""
        if ending1 == ending2:
            return 1.0
        
        # Check for partial rhyme matches
        common_chars = 0
        min_length = min(len(ending1), len(ending2))
        
        for i in range(1, min_length + 1):
            if ending1[-i] == ending2[-i]:
                common_chars += 1
            else:
                break
        
        return common_chars / max(len(ending1), len(ending2))
    
    def _calculate_syllable_similarity(self, text1: str, text2: str) -> float:
        """Calculate syllable pattern similarity"""
        syllables1 = self._estimate_syllables(text1)
        syllables2 = self._estimate_syllables(text2)
        
        if syllables1 == 0 and syllables2 == 0:
            return 1.0
        
        # Calculate similarity based on syllable count difference
        max_syllables = max(syllables1, syllables2)
        if max_syllables == 0:
            return 1.0
        
        return 1.0 - abs(syllables1 - syllables2) / max_syllables
    
    def _estimate_syllables(self, text: str) -> int:
        """Rough syllable estimation"""
        # Simple vowel-based syllable counting
        vowel_groups = re.findall(r'[aeiouAEIOU]+', text)
        return max(1, len(vowel_groups)) if text.strip() else 0


class AdvancedSimilarityEngine:
    """
    Advanced similarity engine combining multiple algorithms
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize similarity engine with configuration
        
        Args:
            config: Configuration dictionary with thresholds and weights
        """
        self.config = config or self._get_default_config()
        
        # Initialize all similarity algorithms
        self.algorithms = [
            ExactMatchAlgorithm(),
            EditDistanceAlgorithm(),
            JaccardSimilarityAlgorithm(),
            CosineSimilarityAlgorithm(),
            NGramSimilarityAlgorithm(n=3),
            NGramSimilarityAlgorithm(n=4),
            SemanticPatternAlgorithm(),
            RhymePatternAlgorithm()
        ]
        
        # Similarity cache for performance
        self.similarity_cache = {}
    
    def calculate_comprehensive_similarity(self, phrase1: str, phrase2: str) -> Dict[str, Any]:
        """
        Calculate comprehensive similarity using all algorithms
        
        Args:
            phrase1: First phrase to compare
            phrase2: Second phrase to compare
            
        Returns:
            Comprehensive similarity analysis
        """
        # Check cache first
        cache_key = f"{hash(phrase1)}_{hash(phrase2)}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Calculate similarity using each algorithm
        algorithm_results = {}
        weighted_scores = []
        
        for algorithm in self.algorithms:
            try:
                score = algorithm.calculate_similarity(phrase1, phrase2)
                algorithm_results[algorithm.name] = {
                    'score': score,
                    'weight': algorithm.weight,
                    'weighted_score': score * algorithm.weight
                }
                weighted_scores.append(score * algorithm.weight)
                
            except Exception as e:
                print(f"⚠️ Algorithm {algorithm.name} failed: {e}")
                algorithm_results[algorithm.name] = {
                    'score': 0.0,
                    'weight': algorithm.weight,
                    'weighted_score': 0.0,
                    'error': str(e)
                }
        
        # Calculate overall similarity
        total_weight = sum(alg.weight for alg in self.algorithms)
        overall_similarity = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
        
        # Determine risk level based on similarity and configuration
        risk_level = self._determine_risk_level(overall_similarity, algorithm_results)
        
        # Generate explanation
        explanation = self._generate_similarity_explanation(
            phrase1, phrase2, overall_similarity, algorithm_results, risk_level
        )
        
        result = {
            'overall_similarity': overall_similarity,
            'risk_level': risk_level,
            'algorithm_results': algorithm_results,
            'explanation': explanation,
            'flagged': overall_similarity >= self.config['flagging_threshold'],
            'confidence': self._calculate_confidence(algorithm_results)
        }
        
        # Cache result
        self.similarity_cache[cache_key] = result
        
        return result
    
    def _determine_risk_level(self, overall_similarity: float, algorithm_results: Dict) -> str:
        """Determine risk level based on similarity scores"""
        
        thresholds = self.config['risk_thresholds']
        
        # Check for exact matches first
        if algorithm_results.get('exact_match', {}).get('score', 0) == 1.0:
            return 'CRITICAL'
        
        # Check semantic pattern matches
        semantic_score = algorithm_results.get('semantic_pattern', {}).get('score', 0)
        if semantic_score >= 0.8:
            return 'HIGH'
        
        # Use overall similarity with thresholds
        if overall_similarity >= thresholds['critical']:
            return 'CRITICAL'
        elif overall_similarity >= thresholds['high']:
            return 'HIGH'
        elif overall_similarity >= thresholds['medium']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_confidence(self, algorithm_results: Dict) -> float:
        """Calculate confidence in the similarity assessment"""
        
        # Count algorithms that agree on high similarity
        high_similarity_count = 0
        total_algorithms = 0
        
        for result in algorithm_results.values():
            if 'error' not in result:
                total_algorithms += 1
                if result['score'] >= 0.7:
                    high_similarity_count += 1
        
        if total_algorithms == 0:
            return 0.0
        
        # Confidence based on algorithm agreement
        agreement_ratio = high_similarity_count / total_algorithms
        
        # Boost confidence if multiple strong algorithms agree
        if high_similarity_count >= 3:
            agreement_ratio = min(1.0, agreement_ratio + 0.2)
        
        return agreement_ratio
    
    def _generate_similarity_explanation(self, phrase1: str, phrase2: str, 
                                       overall_similarity: float, algorithm_results: Dict, 
                                       risk_level: str) -> str:
        """Generate human-readable explanation"""
        
        explanations = []
        
        # Overall assessment
        if overall_similarity >= 0.9:
            explanations.append("Phrases are nearly identical")
        elif overall_similarity >= 0.7:
            explanations.append("Phrases show strong similarity")
        elif overall_similarity >= 0.5:
            explanations.append("Phrases have moderate similarity")
        else:
            explanations.append("Phrases have low similarity")
        
        # Specific algorithm insights
        if algorithm_results.get('exact_match', {}).get('score', 0) == 1.0:
            explanations.append("Exact match detected")
        
        semantic_score = algorithm_results.get('semantic_pattern', {}).get('score', 0)
        if semantic_score >= 0.8:
            explanations.append("Similar lyrical patterns found")
        
        edit_distance = algorithm_results.get('edit_distance', {}).get('score', 0)
        if edit_distance >= 0.8:
            explanations.append("Very similar wording structure")
        
        rhyme_score = algorithm_results.get('rhyme_pattern', {}).get('score', 0)
        if rhyme_score >= 0.7:
            explanations.append("Similar rhyme and rhythm patterns")
        
        return "; ".join(explanations)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        
        return {
            'flagging_threshold': 0.7,
            'risk_thresholds': {
                'critical': 0.9,
                'high': 0.7,
                'medium': 0.5,
                'low': 0.0
            },
            'cache_enabled': True,
            'max_cache_size': 1000
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update engine configuration"""
        self.config.update(new_config)
        
        # Clear cache when config changes
        self.similarity_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.similarity_cache),
            'max_cache_size': self.config.get('max_cache_size', 1000),
            'cache_hit_rate': 'Not tracked'  # Could be enhanced
        }
    
    def clear_cache(self) -> None:
        """Clear similarity cache"""
        self.similarity_cache.clear()


# Global similarity engine instance
_similarity_engine = AdvancedSimilarityEngine()

def calculate_similarity(phrase1: str, phrase2: str) -> Dict[str, Any]:
    """
    Calculate similarity between two phrases (convenience function)
    
    Args:
        phrase1: First phrase
        phrase2: Second phrase
        
    Returns:
        Similarity analysis results
    """
    return _similarity_engine.calculate_comprehensive_similarity(phrase1, phrase2)

def configure_similarity_engine(config: Dict[str, Any]) -> None:
    """Configure the global similarity engine"""
    _similarity_engine.update_config(config)

def get_similarity_engine() -> AdvancedSimilarityEngine:
    """Get the global similarity engine instance"""
    return _similarity_engine