"""
Requirement Categorizer for ReqBot

Automatically categorizes requirements based on their content, keywords,
and semantic patterns. Helps organize requirements into logical groups
for better analysis and reporting.

Categories:
- Functional: Core functionality and features
- Safety: Safety-critical requirements
- Performance: Speed, efficiency, resource usage
- Security: Authentication, encryption, access control
- Interface: UI/UX, API, external interfaces
- Data: Data management, storage, integrity
- Compliance: Regulatory and standards compliance
- Documentation: Documentation requirements
- Testing: Test and verification requirements
- Other: Uncategorized requirements
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Category definitions with keywords and patterns
CATEGORY_DEFINITIONS = {
    'Safety': {
        'keywords': [
            'safety', 'hazard', 'fail-safe', 'failsafe', 'critical', 'fault',
            'emergency', 'risk', 'dangerous', 'injury', 'harm', 'protection',
            'safeguard', 'prevent', 'accident', 'malfunction'
        ],
        'patterns': [
            r'\bfail[- ]?safe\b',
            r'\bemergency shutdown\b',
            r'\bsafety critical\b',
            r'\bhazard\w*\b',
            r'\bprevent\w* (injury|harm|accident)\b'
        ],
        'priority_boost': True  # Safety requirements get priority boost
    },

    'Security': {
        'keywords': [
            'security', 'authentication', 'authorization', 'encrypt', 'decrypt',
            'password', 'credential', 'access control', 'permission', 'firewall',
            'intrusion', 'vulnerability', 'threat', 'attack', 'breach', 'privacy',
            'confidential', 'secure', 'protected'
        ],
        'patterns': [
            r'\bencrypt\w*\b',
            r'\bauthenticat\w*\b',
            r'\baccess control\b',
            r'\bsecure\w* (connection|channel|communication)\b'
        ],
        'priority_boost': False
    },

    'Performance': {
        'keywords': [
            'performance', 'speed', 'fast', 'efficient', 'optimize', 'latency',
            'throughput', 'response time', 'processing time', 'cpu', 'memory',
            'resource', 'scalable', 'bandwidth', 'capacity', 'load'
        ],
        'patterns': [
            r'\b\d+\s*(ms|millisecond|second|minute)\b',
            r'\bresponse time\b',
            r'\bwithin \d+\b',
            r'\bno more than \d+\b',
            r'\bperformance\s+requirement\b'
        ],
        'priority_boost': False
    },

    'Functional': {
        'keywords': [
            'function', 'feature', 'capability', 'operation', 'process',
            'calculate', 'compute', 'generate', 'produce', 'display',
            'provide', 'support', 'enable', 'allow', 'perform'
        ],
        'patterns': [
            r'\bthe system (shall|must|will|should) (provide|support|allow)\b',
            r'\bthe (application|software|system) (shall|must|will)\b',
            r'\b(user|operator) (shall|must|will) be able to\b'
        ],
        'priority_boost': False
    },

    'Interface': {
        'keywords': [
            'interface', 'gui', 'ui', 'user interface', 'screen', 'display',
            'button', 'menu', 'dialog', 'window', 'api', 'endpoint',
            'integration', 'communicate', 'connect', 'interact'
        ],
        'patterns': [
            r'\buser interface\b',
            r'\bapi\b',
            r'\bgui\b',
            r'\bscreen\b',
            r'\binterface with\b'
        ],
        'priority_boost': False
    },

    'Data': {
        'keywords': [
            'data', 'database', 'storage', 'store', 'retrieve', 'query',
            'record', 'file', 'save', 'load', 'backup', 'restore',
            'integrity', 'consistency', 'format', 'structure'
        ],
        'patterns': [
            r'\bdata(base)?\b',
            r'\bstor(e|age)\b',
            r'\bdata integrity\b',
            r'\b(save|load|retrieve|store) (data|information|record)\b'
        ],
        'priority_boost': False
    },

    'Compliance': {
        'keywords': [
            'comply', 'compliance', 'standard', 'regulation', 'regulatory',
            'requirement', 'law', 'legal', 'mandate', 'certification',
            'iso', 'iec', 'fda', 'hipaa', 'gdpr', 'astm'
        ],
        'patterns': [
            r'\b(ISO|IEC|FDA|ASTM|HIPAA|GDPR)\b',
            r'\bcompl(y|iance) with\b',
            r'\b(standard|regulation)\s+\w+[-\d]+\b'
        ],
        'priority_boost': False
    },

    'Documentation': {
        'keywords': [
            'document', 'documentation', 'manual', 'guide', 'help',
            'instruction', 'specification', 'report', 'log', 'record'
        ],
        'patterns': [
            r'\bdocumentation\b',
            r'\buser (manual|guide)\b',
            r'\b(create|generate|produce) (report|document)\b'
        ],
        'priority_boost': False
    },

    'Testing': {
        'keywords': [
            'test', 'verify', 'validation', 'verification', 'qa',
            'quality assurance', 'check', 'validate', 'confirm'
        ],
        'patterns': [
            r'\btest\w*\b',
            r'\bverif(y|ication)\b',
            r'\bvalidat(e|ion)\b'
        ],
        'priority_boost': False
    }
}


class RequirementCategorizer:
    """
    Categorizes requirements based on content analysis.
    """

    def __init__(self):
        """Initialize the categorizer."""
        self.categories = CATEGORY_DEFINITIONS
        # Compile regex patterns for efficiency
        self._compiled_patterns = {}
        for category, info in self.categories.items():
            self._compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in info.get('patterns', [])
            ]

    def categorize(self, text: str, priority: str = '') -> str:
        """
        Categorize a single requirement text.

        Args:
            text: Requirement description text
            priority: Current priority (may influence categorization)

        Returns:
            Category name, or 'Other' if no category matches
        """
        text_lower = text.lower()
        scores = {}

        # Score each category
        for category, info in self.categories.items():
            score = 0

            # Check keywords
            for keyword in info['keywords']:
                if keyword in text_lower:
                    score += 1

            # Check patterns (weighted higher)
            for pattern in self._compiled_patterns.get(category, []):
                if pattern.search(text):
                    score += 3  # Patterns are more reliable

            scores[category] = score

        # Safety override: if priority is already safety or security, boost those categories
        if priority.lower() == 'safety':
            scores['Safety'] = scores.get('Safety', 0) + 10
        if priority.lower() == 'security':
            scores['Security'] = scores.get('Security', 0) + 10

        # Get category with highest score
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                # Get category with highest score
                for category, score in scores.items():
                    if score == max_score:
                        logger.debug(f"Categorized as '{category}' with score {score}: {text[:50]}...")
                        return category

        # Default category
        return 'Functional'  # Most requirements are functional by default

    def categorize_batch(self, requirements: List[Dict]) -> List[Dict]:
        """
        Categorize a batch of requirements.

        Args:
            requirements: List of requirement dicts with 'Description' and optionally 'Priority'

        Returns:
            Same list with 'Category' field added to each requirement
        """
        categorized = []
        category_counts = {}

        for req in requirements:
            text = req.get('Description', '')
            priority = req.get('Priority', '')

            category = self.categorize(text, priority)
            req['Category'] = category

            # Track counts
            category_counts[category] = category_counts.get(category, 0) + 1
            categorized.append(req)

        logger.info(f"Categorized {len(requirements)} requirements:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {category}: {count}")

        return categorized

    def get_category_description(self, category: str) -> str:
        """
        Get human-readable description of a category.

        Args:
            category: Category name

        Returns:
            Description string
        """
        descriptions = {
            'Functional': 'Core functionality and features',
            'Safety': 'Safety-critical requirements',
            'Performance': 'Speed, efficiency, and resource usage',
            'Security': 'Authentication, encryption, and access control',
            'Interface': 'User interface and API requirements',
            'Data': 'Data management and storage',
            'Compliance': 'Regulatory and standards compliance',
            'Documentation': 'Documentation requirements',
            'Testing': 'Test and verification requirements',
            'Other': 'Uncategorized requirements'
        }
        return descriptions.get(category, 'Unknown category')

    def get_all_categories(self) -> List[str]:
        """
        Get list of all possible categories.

        Returns:
            List of category names
        """
        return list(self.categories.keys()) + ['Other']


# Singleton instance
_categorizer_instance = None


def get_categorizer() -> RequirementCategorizer:
    """
    Get the singleton RequirementCategorizer instance.

    Returns:
        RequirementCategorizer instance
    """
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = RequirementCategorizer()
    return _categorizer_instance
