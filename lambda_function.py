# Smart Homework Assistant MVP - AWS Lambda with Authentication
# Enhanced version with API key authentication for production deployment
# Author: Efehi- A Pioneer AI Academy Intern

import json
import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import uuid
import base64
import hashlib
import os
from functools import wraps

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Authentication Configuration
VALID_API_KEYS = {
    # Format: 'key_id': 'actual_api_key'
    'teacher_001': 'school_district_alpha_2025',
    'parent_001': 'family_access_beta_2025', 
    'student_001': 'kid_learning_gamma_2025',
    'demo_key': 'demo_access_homework_2025',
    'admin_001': 'admin_super_access_2025'
}

# User roles and permissions
USER_ROLES = {
    'school_district_alpha_2025': {'role': 'teacher', 'daily_limit': 1000},
    'family_access_beta_2025': {'role': 'parent', 'daily_limit': 100},
    'kid_learning_gamma_2025': {'role': 'student', 'daily_limit': 50},
    'demo_access_homework_2025': {'role': 'demo', 'daily_limit': 10},
    'admin_super_access_2025': {'role': 'admin', 'daily_limit': 10000}
}

def verify_api_key(event):
    """
    Verify API key from request headers and return user info.
    
    Args:
        event: Lambda event object
        
    Returns:
        Tuple[bool, str, Dict]: (is_valid, message, user_info)
    """
    headers = event.get('headers', {})
    
    # Check for API key in headers (case insensitive)
    api_key = None
    for key, value in headers.items():
        if key.lower() in ['x-api-key', 'authorization', 'api-key']:
            api_key = value.replace('Bearer ', '').strip()
            break
    
    if not api_key:
        return False, "Missing API key in request headers", {}
    
    # Validate API key
    if api_key in VALID_API_KEYS.values():
        user_info = USER_ROLES.get(api_key, {})
        return True, "Valid API key", user_info
    
    return False, "Invalid API key provided", {}

def log_usage(api_key, problem_text, success, user_info):
    """Log usage for monitoring and rate limiting."""
    logger.info(f"Usage: {user_info.get('role', 'unknown')} | Success: {success} | Problem: {problem_text[:50]}...")

def require_auth(func):
    """Decorator to require authentication for protected endpoints."""
    @wraps(func)
    def wrapper(event, context):
        # Skip auth for OPTIONS requests (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return func(event, context)
        
        # Skip auth for root GET request (API documentation)
        if event.get('httpMethod') == 'GET' and event.get('resource') == '/':
            return func(event, context)
        
        # Verify API key for protected endpoints
        is_valid, message, user_info = verify_api_key(event)
        
        if not is_valid:
            logger.warning(f"Authentication failed: {message}")
            return {
                'statusCode': 401,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS, GET',
                    'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Authentication Required',
                    'message': message,
                    'instructions': {
                        'header_required': 'X-API-Key',
                        'example': 'X-API-Key: your_api_key_here',
                        'contact': 'Contact your teacher, parent, or administrator for an API key'
                    },
                    'demo_access': {
                        'note': 'For testing purposes only',
                        'demo_key': 'demo_access_homework_2025',
                        'limits': 'Limited to 10 requests per day'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Add user info to event for use in main handler
        event['user_info'] = user_info
        logger.info(f"Authenticated user: {user_info.get('role', 'unknown')}")
        
        return func(event, context)
    return wrapper

class MathProblemSolver:
    """
    Enhanced core class for analyzing math problems and providing educational hints.
    Now includes user-specific customization based on authentication.
    """
    
    def __init__(self, user_role='student'):
        self.user_role = user_role
        
        # Basic operation patterns for elementary math
        self.patterns = {
            'addition': [
                r'(\d+)\s*\+\s*(\d+)',
                r'(\d+)\s*plus\s*(\d+)',
                r'add\s*(\d+)\s*and\s*(\d+)',
                r'sum\s*of\s*(\d+)\s*and\s*(\d+)'
            ],
            'subtraction': [
                r'(\d+)\s*-\s*(\d+)',
                r'(\d+)\s*minus\s*(\d+)',
                r'subtract\s*(\d+)\s*from\s*(\d+)',
                r'(\d+)\s*take\s*away\s*(\d+)'
            ],
            'multiplication': [
                r'(\d+)\s*[×*x]\s*(\d+)',
                r'(\d+)\s*times\s*(\d+)',
                r'multiply\s*(\d+)\s*by\s*(\d+)'
            ],
            'division': [
                r'(\d+)\s*[÷/]\s*(\d+)',
                r'(\d+)\s*divided\s*by\s*(\d+)',
                r'divide\s*(\d+)\s*by\s*(\d+)'
            ]
        }
        
        # Word problem keywords
        self.word_patterns = {
            'addition': ['total', 'sum', 'altogether', 'combined', 'both', 'plus'],
            'subtraction': ['left', 'remaining', 'difference', 'less', 'fewer', 'take away', 'gave away'],
            'multiplication': ['groups of', 'rows of', 'times', 'each'],
            'division': ['share', 'split', 'divide', 'groups', 'each group']
        }
    
    def extract_numbers(self, text: str) -> List[int]:
        """Extract all numbers from text."""
        numbers = re.findall(r'\b\d+\b', text)
        max_number = 10000 if self.user_role == 'teacher' else 1000  # Teachers can handle bigger numbers
        return [int(n) for n in numbers if int(n) <= max_number]
    
    def identify_operation(self, text: str) -> Tuple[str, List[int]]:
        """
        Identify math operation and extract numbers.
        
        Args:
            text (str): Math problem text
            
        Returns:
            Tuple[str, List[int]]: (operation_type, numbers_list)
        """
        text = text.lower().strip()
        
        # First, try direct pattern matching
        for operation, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    if operation == 'subtraction' and 'from' in text:
                        # Handle "subtract X from Y" = Y - X
                        return operation, [int(match.group(2)), int(match.group(1))]
                    return operation, [int(match.group(1)), int(match.group(2))]
        
        # If no direct pattern, analyze word problems
        numbers = self.extract_numbers(text)
        if len(numbers) >= 2:
            return self._analyze_word_problem(text, numbers)
        
        return 'unknown', numbers
    
    def _analyze_word_problem(self, text: str, numbers: List[int]) -> Tuple[str, List[int]]:
        """Analyze word problems based on keywords."""
        text = text.lower()
        
        for operation, keywords in self.word_patterns.items():
            if any(keyword in text for keyword in keywords):
                return operation, numbers[:2]  # Take first two numbers
        
        return 'unknown', numbers
    
    def generate_educational_hint(self, operation: str, numbers: List[int]) -> Dict[str, any]:
        """
        Generate educational hints customized for user role.
        
        Args:
            operation (str): Type of math operation
            numbers (List[int]): Numbers in the problem
            
        Returns:
            Dict: Educational guidance and hints
        """
        if operation == 'unknown':
            return self._unknown_problem_help()
        
        if len(numbers) < 2:
            return self._insufficient_numbers_help()
        
        # Route to specific operation helpers
        hint_generators = {
            'addition': self._addition_hints,
            'subtraction': self._subtraction_hints,
            'multiplication': self._multiplication_hints,
            'division': self._division_hints
        }
        
        hints = hint_generators[operation](numbers[0], numbers[1])
        
        # Customize based on user role
        if self.user_role == 'teacher':
            hints['teacher_notes'] = self._get_teacher_notes(operation, numbers)
        elif self.user_role == 'parent':
            hints['parent_tips'] = self._get_parent_tips(operation, numbers)
        
        return hints
    
    def _get_teacher_notes(self, operation: str, numbers: List[int]) -> str:
        """Generate notes specifically for teachers."""
        notes = {
            'addition': f"Common mistakes: Students might forget to carry over when adding {numbers[0]} + {numbers[1]}",
            'subtraction': f"Watch for borrowing errors with {numbers[0]} - {numbers[1]}",
            'multiplication': f"Great opportunity to review times tables for {min(numbers)}",
            'division': f"Check if students understand remainders with {numbers[0]} ÷ {numbers[1]}"
        }
        return notes.get(operation, "Monitor student's problem-solving approach")
    
    def _get_parent_tips(self, operation: str, numbers: List[int]) -> str:
        """Generate tips specifically for parents."""
        tips = {
            'addition': "Use physical objects like coins or toys to make this concrete",
            'subtraction': "Try the 'counting backwards' method if your child struggles",
            'multiplication': "Relate to real-world grouping (like packs of items)",
            'division': "Use sharing scenarios (like dividing snacks equally)"
        }
        return tips.get(operation, "Encourage your child to explain their thinking process")
    
    def _addition_hints(self, num1: int, num2: int) -> Dict[str, any]:
        """Generate addition hints with role-based customization."""
        steps = []
        difficulty = self._assess_difficulty(num1, num2, 'addition')
        
        if difficulty == 'easy':  # Both numbers ≤ 10
            steps = [
                f"Start by counting {num1} on your fingers or abacus",
                f"Now add {num2} more",
                "Count all together to find your answer",
                "Double-check by counting again!"
            ]
            strategy = "Use the counting-on strategy"
        
        elif difficulty == 'medium':  # One number > 10, < 50
            steps = [
                f"Break down the larger number: {max(num1, num2)}",
                f"Start with the bigger number: {max(num1, num2)}",
                f"Add the smaller number: {min(num1, num2)}",
                "Think about place values (tens and ones)",
                "Check if you need to regroup"
            ]
            strategy = "Use place value thinking"
        
        else:  # Large numbers
            steps = [
                "Line up the numbers by place value",
                "Start adding from the ones place",
                "If sum > 9, carry over to tens place",
                "Continue with tens place",
                "Check your work by estimating"
            ]
            strategy = "Use the standard algorithm"
        
        return {
            'operation': 'addition',
            'difficulty': difficulty,
            'strategy': strategy,
            'steps': steps,
            'abacus_tip': self._get_abacus_tip('addition', num1, num2),
            'mental_math_trick': self._get_mental_math_trick('addition', num1, num2),
            'encouragement': "Take your time and work step by step! 🌟"
        }
    
    def _subtraction_hints(self, num1: int, num2: int) -> Dict[str, any]:
        """Generate subtraction hints."""
        if num1 < num2:
            return {
                'operation': 'subtraction',
                'error': 'problem_check_needed',
                'message': "Check your problem - you can't take away more than you have!",
                'suggestion': f"Did you mean {num2} - {num1} instead?",
                'encouragement': "Double-check the order of your numbers! 🔍"
            }
        
        steps = []
        difficulty = self._assess_difficulty(num1, num2, 'subtraction')
        
        if difficulty == 'easy':
            steps = [
                f"Start with {num1} items",
                f"Take away {num2} items",
                "Count what's left",
                "You can use your fingers or abacus to help"
            ]
            strategy = "Use take-away method"
        
        elif difficulty == 'medium':
            steps = [
                f"Start with {num1}",
                f"Subtract {num2}",
                "Break it down if needed (subtract 10s first, then 1s)",
                "Check: does your answer make sense?"
            ]
            strategy = "Break down by place value"
        
        else:
            steps = [
                "Line up numbers by place value",
                "Start subtracting from ones place",
                "If you need to borrow, take 1 from tens place",
                "Continue with tens place",
                "Check by adding your answer to the second number"
            ]
            strategy = "Use borrowing method"
        
        return {
            'operation': 'subtraction',
            'difficulty': difficulty,
            'strategy': strategy,
            'steps': steps,
            'abacus_tip': self._get_abacus_tip('subtraction', num1, num2),
            'mental_math_trick': self._get_mental_math_trick('subtraction', num1, num2),
            'encouragement': "Remember: subtraction is the opposite of addition! 🔄"
        }
    
    def _multiplication_hints(self, num1: int, num2: int) -> Dict[str, any]:
        """Generate multiplication hints."""
        steps = []
        difficulty = self._assess_difficulty(num1, num2, 'multiplication')
        
        if difficulty == 'easy':  # Both ≤ 5
            steps = [
                f"Think of {num1} groups with {num2} items each",
                f"Or think of adding {num1} to itself {num2} times",
                "You can draw pictures to help visualize",
                "Count all the items in your groups"
            ]
            strategy = "Use repeated addition or grouping"
        
        elif difficulty == 'medium':  # One factor ≤ 10
            smaller = min(num1, num2)
            larger = max(num1, num2)
            steps = [
                f"Use the multiplication table for {smaller}",
                f"Remember: {smaller} × {larger} = {larger} × {smaller}",
                "Break down if needed (like 6 × 12 = 6 × 10 + 6 × 2)",
                "Check your answer makes sense"
            ]
            strategy = "Use multiplication tables and breaking down"
        
        else:
            steps = [
                "Break both numbers into tens and ones",
                "Multiply each part separately",
                "Add all the parts together",
                "Example: 23 × 15 = (20×15) + (3×15)"
            ]
            strategy = "Use the distributive property"
        
        return {
            'operation': 'multiplication',
            'difficulty': difficulty,
            'strategy': strategy,
            'steps': steps,
            'abacus_tip': self._get_abacus_tip('multiplication', num1, num2),
            'mental_math_trick': self._get_mental_math_trick('multiplication', num1, num2),
            'encouragement': "Multiplication is just fast addition! 🚀"
        }
    
    def _division_hints(self, num1: int, num2: int) -> Dict[str, any]:
        """Generate division hints."""
        if num2 == 0:
            return {
                'operation': 'division',
                'error': 'division_by_zero',
                'message': "You cannot divide by zero!",
                'suggestion': "Check your problem - the second number should not be zero",
                'encouragement': "Math rules help keep everything working correctly! 📏"
            }
        
        steps = []
        remainder = num1 % num2
        
        if num1 < num2:
            steps = [
                f"Notice that {num1} is smaller than {num2}",
                "This means the answer will be less than 1",
                f"Think: How many whole groups of {num2} fit into {num1}?",
                f"The answer is 0 with remainder {num1}"
            ]
            strategy = "Understanding division with smaller dividends"
        
        elif num1 % num2 == 0:  # Divides evenly
            steps = [
                f"Ask: How many groups of {num