# Smart Homework Assistant MVP - AWS Lambda with Authentication (FIXED)
# Enhanced version with API key authentication for production deployment
# Author: Pioneer AI Academy Intern

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
            'encouragement': "Take your time and work step by step!"
        }
    
    def _subtraction_hints(self, num1: int, num2: int) -> Dict[str, any]:
        """Generate subtraction hints."""
        if num1 < num2:
            return {
                'operation': 'subtraction',
                'error': 'problem_check_needed',
                'message': "Check your problem - you can't take away more than you have!",
                'suggestion': f"Did you mean {num2} - {num1} instead?",
                'encouragement': "Double-check the order of your numbers!"
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
            'encouragement': "Remember: subtraction is the opposite of addition!"
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
            'encouragement': "Multiplication is just fast addition!"
        }
    
    def _division_hints(self, num1: int, num2: int) -> Dict[str, any]:
        """Generate division hints."""
        if num2 == 0:
            return {
                'operation': 'division',
                'error': 'division_by_zero',
                'message': "You cannot divide by zero!",
                'suggestion': "Check your problem - the second number should not be zero",
                'encouragement': "Math rules help keep everything working correctly!"
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
                f"Ask: How many groups of {num2} can I make from {num1}?",
                f"Or: How many times does {num2} go into {num1}?",
                "This should divide evenly (no remainder)",
                f"Think of the multiplication table for {num2}"
            ]
            strategy = "Perfect division (no remainder)"
        
        else:  # Has remainder
            quotient = num1 // num2
            steps = [
                f"Find how many complete groups of {num2} fit in {num1}",
                f"That's {quotient} complete groups",
                f"There will be {remainder} left over (remainder)",
                f"Answer: {quotient} remainder {remainder}"
            ]
            strategy = "Division with remainders"
        
        return {
            'operation': 'division',
            'difficulty': 'medium',
            'strategy': strategy,
            'steps': steps,
            'abacus_tip': self._get_abacus_tip('division', num1, num2),
            'mental_math_trick': self._get_mental_math_trick('division', num1, num2),
            'encouragement': "Division is about fair sharing!"
        }
    
    def _assess_difficulty(self, num1: int, num2: int, operation: str) -> str:
        """Assess problem difficulty for appropriate hint generation."""
        if operation in ['addition', 'subtraction']:
            if max(num1, num2) <= 10:
                return 'easy'
            elif max(num1, num2) <= 50:
                return 'medium'
            else:
                return 'hard'
        
        elif operation == 'multiplication':
            if max(num1, num2) <= 5:
                return 'easy'
            elif max(num1, num2) <= 10:
                return 'medium'
            else:
                return 'hard'
        
        return 'medium'
    
    def _get_abacus_tip(self, operation: str, num1: int, num2: int) -> str:
        """Generate abacus-specific learning tips."""
        tips = {
            'addition': [
                "Use your abacus to show both numbers, then count all beads together",
                "Remember: 5 bottom beads = 1 top bead for efficient counting",
                "Start with the larger number on your abacus, then add the smaller"
            ],
            'subtraction': [
                f"Start with {num1} on your abacus, then remove {num2} beads",
                "Use the 'friends of 10' method - numbers that add to 10",
                "Move beads away to show subtraction clearly"
            ],
            'multiplication': [
                f"Make {num2} groups of {num1} beads each on your abacus",
                "Count all the beads in all groups for your answer",
                "Use repeated addition if multiplication is tricky"
            ],
            'division': [
                f"Start with {num1} beads, try to make equal groups of {num2}",
                "Count how many complete groups you can make",
                "Any leftover beads are the remainder"
            ]
        }
        
        return tips.get(operation, ["Use your abacus to visualize the problem"])[0]
    
    def _get_mental_math_trick(self, operation: str, num1: int, num2: int) -> str:
        """Generate mental math tricks and shortcuts."""
        if operation == 'addition':
            if num2 == 9:
                return f"Quick trick: Add 10 to {num1}, then subtract 1"
            elif num2 in [11, 12, 13, 14, 15]:
                return f"Add 10 first ({num1} + 10), then add {num2 - 10}"
            elif (num1 + num2) % 10 == 0:
                return "Notice how these numbers make a nice round number!"
        
        elif operation == 'subtraction':
            if num2 == 9:
                return f"Quick trick: Subtract 10 from {num1}, then add 1"
            elif num1 % 10 == 0:
                return "Subtracting from round numbers is easier - break it down!"
        
        elif operation == 'multiplication':
            if num2 == 2:
                return "Multiplying by 2 is the same as doubling (adding the number to itself)"
            elif num2 == 5:
                return "Multiplying by 5: multiply by 10, then divide by 2"
            elif num2 == 10:
                return "Multiplying by 10: just add a zero to the end!"
        
        elif operation == 'division':
            if num2 == 2:
                return "Dividing by 2 is the same as finding half"
            elif num2 == 10:
                return "Dividing by 10: move the decimal point left (or remove a zero)"
        
        return "Look for patterns and shortcuts to make math easier!"
    
    # MISSING METHODS - These were causing the error
    def _unknown_problem_help(self) -> Dict[str, any]:
        """Help for unrecognized problems."""
        return {
            'operation': 'unknown',
            'message': "I can help with basic math problems!",
            'supported_operations': ['Addition (+)', 'Subtraction (-)', 'Multiplication (×)', 'Division (÷)'],
            'examples': [
                "25 + 17 = ?",
                "What is 45 - 18?", 
                "7 × 8",
                "56 ÷ 7",
                "Sarah has 20 candies and gives 5 to Tom. How many are left?"
            ],
            'tips': [
                "Use clear numbers and operation symbols",
                "I understand word problems too!",
                "Make sure your problem has at least 2 numbers"
            ],
            'encouragement': "Try rephrasing your problem and I'll help you learn!"
        }
    
    def _insufficient_numbers_help(self) -> Dict[str, any]:
        """Help when not enough numbers are found."""
        return {
            'operation': 'incomplete',
            'message': "I need at least 2 numbers to help with math problems",
            'suggestion': "Make sure your problem includes the numbers you want to work with",
            'examples': ["15 + 8", "20 - 7", "4 × 6"],
            'encouragement': "Include the numbers in your problem and I'll help!"
        }

class EducationalResponseGenerator:
    """
    Generates age-appropriate educational responses that encourage learning.
    """
    
    @staticmethod
    def format_response(problem_text: str, operation: str, numbers: List[int], 
                       hints: Dict[str, any], user_info: Dict = None) -> Dict[str, any]:
        """
        Format the final educational response with user customization.
        
        Args:
            problem_text (str): Original problem
            operation (str): Identified operation
            numbers (List[int]): Extracted numbers
            hints (Dict): Generated hints
            user_info (Dict): User role and information
            
        Returns:
            Dict: Complete educational response
        """
        
        # Base response structure
        response = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'original_problem': problem_text,
            'analysis': {
                'operation_identified': operation,
                'numbers_found': numbers,
                'difficulty_level': hints.get('difficulty', 'unknown')
            }
        }
        
        # Add user context if available
        if user_info:
            response['user_context'] = {
                'role': user_info.get('role', 'student'),
                'customization_applied': True
            }
        
        # Handle different response types
        if operation == 'unknown':
            response.update({
                'success': False,
                'help_message': hints['message'],
                'supported_operations': hints['supported_operations'],
                'examples': hints['examples'],
                'tips': hints['tips']
            })
        
        elif 'error' in hints:
            response.update({
                'success': False,
                'error_type': hints['error'],
                'error_message': hints['message'],
                'suggestion': hints['suggestion']
            })
        
        else:
            # Successful problem identification
            response.update({
                'educational_guidance': {
                    'learning_strategy': hints['strategy'],
                    'step_by_step_hints': hints['steps'],
                    'abacus_technique': hints['abacus_tip'],
                    'mental_math_trick': hints['mental_math_trick']
                },
                'learning_reminders': [
                    "Work through each step yourself",
                    "Understanding the process is more important than the answer",
                    "Practice makes perfect!",
                    "Ask for help if you get stuck"
                ],
                'encouragement': hints['encouragement']
            })
            
            # Add role-specific content
            if 'teacher_notes' in hints:
                response['teacher_notes'] = hints['teacher_notes']
            if 'parent_tips' in hints:
                response['parent_tips'] = hints['parent_tips']
        
        # Add educational footer
        response['pi_and_beads_tip'] = "Remember: Math is like learning to use an abacus - practice and patience lead to mastery!"
        
        return response

@require_auth
def lambda_handler(event, context):
    """
    AWS Lambda handler for Smart Homework Assistant with authentication.
    
    This function processes math homework problems and returns educational hints
    without giving direct answers, encouraging students to learn through guided discovery.
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda runtime context
        
    Returns:
        Dict: API Gateway response with educational guidance
    """
    
    # CORS headers for web applications
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS, GET',
        'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization',
        'Content-Type': 'application/json'
    }
    
    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'CORS preflight successful'})
        }
    
    # Handle GET request for API info
    if event.get('httpMethod') == 'GET':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'service': 'Smart Homework Assistant MVP (Enhanced)',
                'version': '2.0.0',
                'description': 'Educational AI assistant for elementary math problems with authentication',
                'endpoints': {
                    'POST /process-homework': 'Submit math problems for educational hints (requires API key)',
                    'GET /': 'API information'
                },
                'authentication': {
                    'required': True,
                    'header': 'X-API-Key',
                    'demo_key': 'demo_access_homework_2025'
                },
                'created_by': 'Pioneer AI Academy Intern',
                'focus': 'Abacus and mental math education with role-based customization'
            })
        }
    
    try:
        # Get user info from authentication
        user_info = event.get('user_info', {})
        user_role = user_info.get('role', 'student')
        
        # Parse request body
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Missing request body',
                    'required': 'problem_text',
                    'example': {'problem_text': '25 + 17'}
                })
            }
        
        # Handle base64 encoded body
        body = event['body']
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
        
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Invalid JSON format',
                    'example': '{"problem_text": "25 + 17"}'
                })
            }
        
        # Validate required fields
        if 'problem_text' not in request_data:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Missing problem_text field',
                    'required_format': {'problem_text': 'Your math problem here'},
                    'examples': [
                        '25 + 17',
                        'What is 45 - 18?',
                        'I have 12 apples and eat 3. How many are left?'
                    ]
                })
            }
        
        problem_text = request_data['problem_text'].strip()
        
        if not problem_text:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Empty problem text',
                    'message': 'Please provide a math problem to solve'
                })
            }
        
        # Process the math problem
        logger.info(f"Processing problem for {user_role}: {problem_text}")
        
        # Initialize solver with user role for customization
        solver = MathProblemSolver(user_role=user_role)
        
        # Identify operation and extract numbers
        operation, numbers = solver.identify_operation(problem_text)
        
        # Generate educational hints
        hints = solver.generate_educational_hint(operation, numbers)
        
        # Format response with user customization
        response_generator = EducationalResponseGenerator()
        response_data = response_generator.format_response(
            problem_text, operation, numbers, hints, user_info
        )
        
        # Log successful processing with usage tracking
        log_usage(event.get('headers', {}).get('x-api-key', ''), problem_text, True, user_info)
        logger.info(f"Successfully processed {operation} problem with {len(numbers)} numbers for {user_role}")
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(response_data, default=str)
        }
        
    except Exception as e:
        # Log error for debugging
        logger.error(f"Unexpected error processing homework: {str(e)}")
        
        # Log failed usage
        user_info = event.get('user_info', {})
        if 'problem_text' in locals():
            log_usage(event.get('headers', {}).get('x-api-key', ''), problem_text, False, user_info)
        
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e) if user_info.get('role') == 'admin' else 'Sorry, something went wrong. Please try again.',
                'timestamp': datetime.utcnow().isoformat()
            })
        }