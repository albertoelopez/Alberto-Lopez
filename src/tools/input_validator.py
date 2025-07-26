"""
Input Validation Tools

Comprehensive validation and error handling for lyric input processing.
"""

import re
from typing import Dict, List, Tuple, Optional


class LyricValidationError(Exception):
    """Custom exception for lyric validation errors"""
    pass


class InputValidator:
    """
    Validates and sanitizes user input for lyric analysis
    """
    
    # Configuration constants
    MIN_LYRICS_LENGTH = 10  # characters
    MAX_LYRICS_LENGTH = 10000  # characters
    MAX_LINES = 200
    MIN_WORDS = 3
    MAX_WORDS = 2000
    
    # Suspicious patterns that might indicate abuse
    SUSPICIOUS_PATTERNS = [
        r'(.)\1{20,}',  # Repeated characters (20+ times)
        r'[^\w\s\'-.,!?;:()"\n]{5,}',  # Long sequences of special chars
        r'https?://\S+',  # URLs (might be spam)
        r'\b\d{10,}\b',  # Long numbers (might be phone/credit card)
    ]
    
    def __init__(self):
        self.validation_history = []
    
    def validate_lyrics_input(self, lyrics: str, user_id: Optional[str] = None) -> Dict[str, any]:
        """
        Comprehensive validation of lyrics input
        
        Args:
            lyrics: Raw lyrics text from user
            user_id: Optional user identifier for rate limiting
            
        Returns:
            Validation result with sanitized lyrics or error details
        """
        validation_result = {
            'valid': True,
            'sanitized_lyrics': '',
            'warnings': [],
            'errors': [],
            'metadata': {
                'original_length': len(lyrics) if lyrics else 0,
                'estimated_processing_time': 0.0
            }
        }
        
        try:
            # Basic input checks
            self._validate_basic_input(lyrics, validation_result)
            
            if not validation_result['valid']:
                return validation_result
            
            # Content validation
            self._validate_content(lyrics, validation_result)
            
            # Security checks
            self._validate_security(lyrics, validation_result)
            
            # Performance estimation
            self._estimate_processing_requirements(lyrics, validation_result)
            
            # If validation passed, sanitize the input
            if validation_result['valid']:
                validation_result['sanitized_lyrics'] = self._sanitize_validated_input(lyrics)
                
            # Log validation attempt
            self._log_validation_attempt(lyrics, validation_result, user_id)
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation failed: {str(e)}")
            return validation_result
    
    def _validate_basic_input(self, lyrics: str, result: Dict) -> None:
        """Validate basic input requirements"""
        
        # Null/empty check
        if not lyrics:
            result['valid'] = False
            result['errors'].append("No lyrics provided. Please enter some lyrics to analyze.")
            return
        
        # Type check
        if not isinstance(lyrics, str):
            result['valid'] = False
            result['errors'].append("Lyrics must be provided as text.")
            return
        
        # Length checks
        if len(lyrics) < self.MIN_LYRICS_LENGTH:
            result['valid'] = False
            result['errors'].append(f"Lyrics too short. Minimum {self.MIN_LYRICS_LENGTH} characters required.")
            return
        
        if len(lyrics) > self.MAX_LYRICS_LENGTH:
            result['valid'] = False
            result['errors'].append(f"Lyrics too long. Maximum {self.MAX_LYRICS_LENGTH} characters allowed.")
            return
    
    def _validate_content(self, lyrics: str, result: Dict) -> None:
        """Validate lyric content structure and quality"""
        
        # Line count check
        lines = lyrics.split('\n')
        if len(lines) > self.MAX_LINES:
            result['warnings'].append(f"Many lines detected ({len(lines)}). Processing may take longer.")
        
        # Word count check
        words = re.findall(r'\b\w+\b', lyrics)
        word_count = len(words)
        
        if word_count < self.MIN_WORDS:
            result['valid'] = False
            result['errors'].append(f"Too few words. Minimum {self.MIN_WORDS} words required for meaningful analysis.")
            return
        
        if word_count > self.MAX_WORDS:
            result['valid'] = False
            result['errors'].append(f"Too many words. Maximum {self.MAX_WORDS} words allowed.")
            return
        
        # Content quality checks
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        if len(non_empty_lines) == 0:
            result['valid'] = False
            result['errors'].append("No meaningful content found. Please provide actual lyrics.")
            return
        
        # Check for actual lyrical content vs gibberish
        if self._appears_to_be_gibberish(lyrics):
            result['warnings'].append("Input may not be actual lyrics. Analysis results may be limited.")
        
        # Language detection (basic)
        if not self._contains_english_words(lyrics):
            result['warnings'].append("Non-English content detected. Analysis optimized for English lyrics.")
    
    def _validate_security(self, lyrics: str, result: Dict) -> None:
        """Security validation to prevent abuse"""
        
        # Check for suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, lyrics, re.IGNORECASE):
                result['warnings'].append("Unusual patterns detected in input. Please ensure lyrics are properly formatted.")
                break
        
        # Check for potential injection attempts (basic)
        suspicious_keywords = ['<script', 'javascript:', 'eval(', 'exec(', '<?php']
        lyrics_lower = lyrics.lower()
        
        for keyword in suspicious_keywords:
            if keyword in lyrics_lower:
                result['valid'] = False
                result['errors'].append("Invalid characters detected. Please provide only song lyrics.")
                return
    
    def _estimate_processing_requirements(self, lyrics: str, result: Dict) -> None:
        """Estimate processing time and resource requirements"""
        
        word_count = len(re.findall(r'\b\w+\b', lyrics))
        line_count = len([line for line in lyrics.split('\n') if line.strip()])
        
        # Rough estimation based on content size
        base_time = 5.0  # Base processing time in seconds
        word_penalty = word_count * 0.01  # 0.01 seconds per word
        line_penalty = line_count * 0.1   # 0.1 seconds per line
        
        estimated_time = base_time + word_penalty + line_penalty
        
        result['metadata'].update({
            'word_count': word_count,
            'line_count': line_count,
            'estimated_processing_time': round(estimated_time, 1)
        })
        
        # Add performance warnings
        if estimated_time > 30:
            result['warnings'].append(f"Large input detected. Processing may take ~{int(estimated_time)} seconds.")
        
        if word_count > 500:
            result['warnings'].append("Large number of words may result in many phrases to analyze.")
    
    def _sanitize_validated_input(self, lyrics: str) -> str:
        """Sanitize validated input for processing"""
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', lyrics.strip())
        
        # Normalize line breaks
        sanitized = re.sub(r'\n+', '\n', sanitized)
        
        # Remove or normalize special characters
        sanitized = re.sub(r'[^\w\s\'-.,!?;:()\"\n]', ' ', sanitized)
        
        # Clean up extra spaces
        lines = sanitized.split('\n')
        cleaned_lines = [' '.join(line.split()) for line in lines]
        sanitized = '\n'.join(line for line in cleaned_lines if line.strip())
        
        return sanitized
    
    def _appears_to_be_gibberish(self, text: str) -> bool:
        """Basic check if text appears to be gibberish rather than lyrics"""
        
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) < 5:
            return False
        
        # Check for reasonable vowel-to-consonant ratio
        vowel_count = len(re.findall(r'[aeiou]', text.lower()))
        consonant_count = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', text.lower()))
        
        if consonant_count > 0:
            vowel_ratio = vowel_count / consonant_count
            if vowel_ratio < 0.2:  # Very few vowels compared to consonants
                return True
        
        # Check for excessive repetition
        unique_words = set(words)
        if len(unique_words) < len(words) * 0.3:  # Less than 30% unique words
            return True
        
        return False
    
    def _contains_english_words(self, text: str) -> bool:
        """Basic check for English language content"""
        
        common_english_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'can', 'could', 'should', 'may', 'might', 'must',
            'love', 'like', 'want', 'need', 'know', 'think', 'feel', 'see', 'hear', 'say',
            'go', 'come', 'get', 'make', 'take', 'give', 'put', 'tell', 'work', 'seem',
            'night', 'day', 'time', 'life', 'world', 'way', 'heart', 'eyes', 'hand', 'home'
        }
        
        words = set(re.findall(r'\b\w+\b', text.lower()))
        english_word_count = len(words & common_english_words)
        
        # If at least 20% of words are common English words, assume English
        return len(words) == 0 or english_word_count / len(words) >= 0.2
    
    def _log_validation_attempt(self, lyrics: str, result: Dict, user_id: Optional[str]) -> None:
        """Log validation attempt for monitoring and debugging"""
        
        log_entry = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'user_id': user_id,
            'input_length': len(lyrics),
            'valid': result['valid'],
            'error_count': len(result['errors']),
            'warning_count': len(result['warnings']),
            'estimated_time': result['metadata']['estimated_processing_time']
        }
        
        self.validation_history.append(log_entry)
        
        # Keep only last 100 entries to prevent memory issues
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
    
    def get_validation_stats(self) -> Dict[str, any]:
        """Get validation statistics for monitoring"""
        
        if not self.validation_history:
            return {'message': 'No validation history available'}
        
        total_attempts = len(self.validation_history)
        valid_attempts = sum(1 for entry in self.validation_history if entry['valid'])
        
        return {
            'total_validation_attempts': total_attempts,
            'successful_validations': valid_attempts,
            'success_rate': round(valid_attempts / total_attempts * 100, 1) if total_attempts > 0 else 0,
            'average_input_length': round(sum(entry['input_length'] for entry in self.validation_history) / total_attempts, 1),
            'average_processing_time': round(sum(entry['estimated_time'] for entry in self.validation_history) / total_attempts, 1)
        }


# Global validator instance
_validator = InputValidator()

def validate_lyrics_input(lyrics: str, user_id: Optional[str] = None) -> Dict[str, any]:
    """
    Public function for lyrics input validation
    
    Args:
        lyrics: Raw lyrics text from user
        user_id: Optional user identifier
        
    Returns:
        Validation result dictionary
    """
    return _validator.validate_lyrics_input(lyrics, user_id)

def get_validation_stats() -> Dict[str, any]:
    """Get validation statistics"""
    return _validator.get_validation_stats()