"""
Evaluator-Optimizer Pattern for SWIFT Message Validation

This module implements iterative validation and correction of SWIFT messages.
The evaluator identifies issues, and the optimizer corrects them.
"""

from typing import Dict, List, Any, Tuple
from agents.workflow_agents.base_agents import SwiftCorrectionAgent
from config import Config


class EvaluatorAgent:
    """
    Evaluator Agent - Responsible for assessing SWIFT message validity.

    This agent is a distinct, reusable component that can be used independently
    to validate SWIFT messages against standards. It encapsulates all validation
    logic and can be easily swapped or extended.

    VALIDATION CAPABILITIES:
    1. Code-based validation (always active):
       - BIC format validation
       - Currency code validation
       - Amount range validation
       - Reference length validation
       - Required field validation

    2. AI-powered semantic validation (optional, requires API credits):
       - Remittance information coherence analysis
       - Suspicious pattern detection
       - Business logic consistency checks
       - Fraud indicator detection

    Usage:
        # Basic validation (code-based only)
        evaluator = EvaluatorAgent()
        is_valid, errors = evaluator.evaluate(message)

        # With AI-powered semantic checks
        evaluator = EvaluatorAgent(enable_llm_checks=True)
        is_valid, errors = evaluator.evaluate(message)
    """

    def __init__(self, enable_llm_checks=False):
        """
        Initialize the Evaluator Agent with SWIFT standards.

        Args:
            enable_llm_checks: If True, enables AI-powered semantic validation
                              (requires OpenAI API key and credits)
        """
        self.config = Config()
        self.enable_llm_checks = enable_llm_checks

        # Initialize LLM service if semantic checks are enabled
        if self.enable_llm_checks:
            try:
                from services.llm_service import LLMService
                self.llm_service = LLMService()
            except Exception as e:
                print(f"Warning: Could not initialize LLM service: {e}")
                self.enable_llm_checks = False

        # SWIFT validation rules
        self.SWIFT_STANDARDS = {
            "max_reference_length": 16,
            "max_amount": 999999999.99,
            "min_amount": 0.01,
            "required_fields": [
                "message_type", "reference", "amount",
                "sender_bic", "receiver_bic"
            ],
            "valid_message_types": ["MT103", "MT202"],
            "valid_currencies": ["USD", "EUR", "GBP", "JPY", "CHF"]
        }

    def evaluate(self, message: Dict) -> Tuple[bool, List[str]]:
        """
        Evaluate a SWIFT message for compliance with standards.

        This is the main interface method for the Evaluator Agent.
        It assesses message validity and returns detailed error information.

        Args:
            message: SWIFT message to evaluate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        for field in self.SWIFT_STANDARDS["required_fields"]:
            if field not in message or not message[field]:
                errors.append(f"Missing required field: {field}")

        # Validate message type
        if message.get("message_type") not in self.SWIFT_STANDARDS["valid_message_types"]:
            errors.append(f"Invalid message type: {message.get('message_type')}")

        # Validate reference length
        reference = message.get("reference", "")
        if len(reference) > self.SWIFT_STANDARDS["max_reference_length"]:
            errors.append(f"Reference too long: {len(reference)} chars (max {self.SWIFT_STANDARDS['max_reference_length']})")

        # Validate amount
        try:
            amount_str = message.get("amount", "0")
            # Extract numeric value from amount string (e.g., "1000.00 USD" -> 1000.00)
            amount_value = float(''.join(c for c in amount_str.split()[0] if c.isdigit() or c == '.'))

            if amount_value > self.SWIFT_STANDARDS["max_amount"]:
                errors.append(f"Amount exceeds maximum: {amount_value}")
            elif amount_value < self.SWIFT_STANDARDS["min_amount"]:
                errors.append(f"Amount below minimum: {amount_value}")
        except (ValueError, IndexError, AttributeError):
            errors.append(f"Invalid amount format: {message.get('amount')}")

        # Validate BIC codes
        sender_bic = message.get("sender_bic", "")
        receiver_bic = message.get("receiver_bic", "")

        if not self._validate_bic(sender_bic):
            errors.append(f"Invalid sender BIC: {sender_bic}")
        if not self._validate_bic(receiver_bic):
            errors.append(f"Invalid receiver BIC: {receiver_bic}")

        # Check if same sender and receiver
        if sender_bic and sender_bic == receiver_bic:
            errors.append("Sender and receiver BIC cannot be the same")

        # Validate currency
        if "amount" in message:
            try:
                currency = message["amount"].split()[-1]
                if currency not in self.SWIFT_STANDARDS["valid_currencies"]:
                    errors.append(f"Invalid currency: {currency}")
            except (IndexError, AttributeError):
                errors.append("Cannot extract currency from amount")

        # Optional: AI-powered semantic validation (if enabled)
        if self.enable_llm_checks:
            semantic_errors = self._llm_semantic_check(message)
            errors.extend(semantic_errors)

        is_valid = len(errors) == 0
        return is_valid, errors

    def _llm_semantic_check(self, message: Dict) -> List[str]:
        """
        Optional AI-powered semantic validation using LLM.

        This demonstrates the AI capabilities of the evaluator by checking:
        - Coherence of remittance information
        - Suspicious patterns in text fields
        - Business logic consistency

        Args:
            message: SWIFT message to check

        Returns:
            List of semantic errors detected by LLM
        """
        semantic_errors = []

        try:
            # Only check MT103 messages with remittance info
            if message.get('message_type') != 'MT103':
                return semantic_errors

            remittance = message.get('remittance_info', '')
            if not remittance or len(remittance) < 5:
                return semantic_errors

            # Create LLM prompt for semantic validation
            from openai import OpenAI
            import json

            client = OpenAI(
                base_url="https://openai.vocareum.com/v1",
                api_key=self.config.OPENAI_API_KEY
            )

            system_prompt = """You are a SWIFT transaction semantic validator.
Analyze the remittance information for:
1. Coherence - Does it make sense as a payment description?
2. Suspicious patterns - Generic/placeholder text, test data, or fraud indicators
3. Business logic - Does it match the transaction type and amount?

Return JSON with:
{
    "is_coherent": true/false,
    "issues": ["list of specific issues if any"],
    "risk_level": "low/medium/high"
}"""

            user_prompt = f"""Analyze this SWIFT MT103 transaction:

Message Type: {message.get('message_type')}
Amount: {message.get('amount')}
Remittance Info: "{remittance}"
Sender BIC: {message.get('sender_bic')}
Receiver BIC: {message.get('receiver_bic')}

Is the remittance information coherent and appropriate for this transaction?"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)

            # Add semantic errors if detected
            if not result.get('is_coherent', True):
                for issue in result.get('issues', []):
                    semantic_errors.append(f"Semantic issue: {issue}")

            if result.get('risk_level') == 'high':
                semantic_errors.append("High semantic risk detected in remittance info")

        except Exception as e:
            # Don't fail validation if LLM check fails
            print(f"LLM semantic check failed (non-critical): {e}")

        return semantic_errors

    def _validate_bic(self, bic: str) -> bool:
        """
        Validate a BIC (Bank Identifier Code) format.

        BIC format: 8 or 11 characters
        - 4 letters: Bank code
        - 2 letters: Country code
        - 2 letters/digits: Location code
        - 3 letters/digits: Branch code (optional)

        Args:
            bic: BIC code to validate

        Returns:
            True if valid, False otherwise
        """
        if not bic:
            return False

        # BIC must be 8 or 11 characters
        if len(bic) not in [8, 11]:
            return False

        # First 4 characters must be letters (bank code)
        if not bic[:4].isalpha():
            return False

        # Characters 5-6 must be letters (country code)
        if not bic[4:6].isalpha():
            return False

        # Characters 7-8 must be alphanumeric (location code)
        if not bic[6:8].isalnum():
            return False

        # If 11 characters, last 3 must be alphanumeric (branch code)
        if len(bic) == 11 and not bic[8:11].isalnum():
            return False

        return True


class EvaluatorOptimizerPattern:
    """
    Orchestrator for the Evaluator-Optimizer pattern using distinct agents.

    ARCHITECTURE:
    This pattern implements a true multi-agent architecture with two distinct agents:

    1. EvaluatorAgent - Independent agent that assesses message validity
       - Can be reused in other parts of the system
       - Encapsulates all validation logic
       - Returns (is_valid, errors) tuple

    2. OptimizerAgent (SwiftCorrectionAgent) - Independent agent that corrects errors
       - Uses LLM to intelligently fix validation issues
       - Maintains business intent while fixing errors
       - Returns corrected message

    WORKFLOW:
    1. Pattern calls EvaluatorAgent.evaluate() to assess message
    2. If invalid, Pattern calls OptimizerAgent.respond() to correct
    3. Pattern re-evaluates with EvaluatorAgent.evaluate()
    4. Repeats up to MAX_ITERATIONS times

    This modular design allows each agent to be:
    - Tested independently
    - Swapped with alternative implementations
    - Reused in other workflows
    - Extended without affecting the other agent
    """

    def __init__(self):
        """
        Initialize the evaluator-optimizer pattern.

        This pattern orchestrates between two distinct agents:
        1. EvaluatorAgent - Assesses message validity
        2. OptimizerAgent (SwiftCorrectionAgent) - Corrects identified issues
        """
        self.config = Config()
        self.MAX_ITERATIONS = 3

        # Initialize the two distinct agents
        self.evaluator_agent = EvaluatorAgent()
        self.optimizer_agent = SwiftCorrectionAgent()

        # Store SWIFT standards reference (delegates to evaluator agent)
        self.SWIFT_STANDARDS = self.evaluator_agent.SWIFT_STANDARDS

    def evaluate_message(self, message: Dict) -> Tuple[bool, List[str]]:
        """
        Evaluate a SWIFT message for compliance with standards.

        IMPORTANT: This method delegates to the EvaluatorAgent, implementing
        the true Evaluator-Optimizer pattern with distinct agents.

        Args:
            message: SWIFT message to evaluate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Delegate evaluation to the Evaluator Agent
        return self.evaluator_agent.evaluate(message)

    def optimize_message(self, message: Dict, errors: List[str]) -> Dict:
        """
        Optimize (correct) a SWIFT message based on identified errors.

        IMPORTANT: This method delegates to the OptimizerAgent (SwiftCorrectionAgent),
        implementing the true Evaluator-Optimizer pattern with distinct agents.

        Args:
            message: SWIFT message to optimize
            errors: List of errors to correct

        Returns:
            Optimized message
        """
        if not errors:
            return message

        try:
            # Delegate optimization to the Optimizer Agent
            corrected = self.optimizer_agent.respond(message, errors)

            # Ensure all required fields are present in the corrected message
            for field in self.SWIFT_STANDARDS["required_fields"]:
                if field not in corrected:
                    corrected[field] = message.get(field, "")

            return corrected

        except Exception as e:
            print(f"Error during optimization: {e}")
            return message

    def process_with_evaluator_optimizer(self, messages: List[Dict]) -> List[Dict]:
        """
        Process messages through the evaluator-optimizer pattern.

        Args:
            messages: List of SWIFT messages to process

        Returns:
            List of validated and optimized messages
        """
        print("=" * 60)
        print("EVALUATOR-OPTIMIZER PATTERN PROCESSING")
        print("=" * 60)

        optimized_messages = []

        for i, message in enumerate(messages):
            print(f"\nProcessing message {i+1}/{len(messages)}: {message.get('message_id', 'Unknown')}")

            # Iterative evaluation and optimization
            for iteration in range(self.MAX_ITERATIONS):
                is_valid, errors = self.evaluate_message(message)

                if is_valid:
                    print(f"  [OK] Message valid after {iteration} iteration(s)")
                    message['validation_status'] = 'VALID'
                    message['validation_errors'] = []
                    break
                else:
                    print(f"  Iteration {iteration + 1}: Found {len(errors)} error(s)")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"    - {error}")

                    if iteration < self.MAX_ITERATIONS - 1:
                        # Attempt to optimize
                        print(f"  Attempting optimization...")
                        message = self.optimize_message(message, errors)
                    else:
                        # Max iterations reached
                        print(f"  [ERROR] Max iterations reached. Message still has errors.")
                        message['validation_status'] = 'INVALID'
                        message['validation_errors'] = errors

            optimized_messages.append(message)

        # Print summary
        valid_count = sum(1 for m in optimized_messages if m.get('validation_status') == 'VALID')
        print(f"\n{'=' * 60}")
        print(f"EVALUATOR-OPTIMIZER SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total messages processed: {len(optimized_messages)}")
        print(f"Valid messages: {valid_count}")
        print(f"Invalid messages: {len(optimized_messages) - valid_count}")

        return optimized_messages

    def test_pattern(self):
        """
        Test the evaluator-optimizer pattern with sample messages.
        You can use this to verify the pattern works with your implementations.
        """
        test_messages = [
            {
                'message_id': 'VALID001',
                'message_type': 'MT103',
                'reference': 'REF123456',
                'amount': '5000.00 USD',
                'sender_bic': 'CHASUS33XXX',
                'receiver_bic': 'DEUTDEFFXXX',
                'remittance_info': 'Invoice payment'
            },
            {
                'message_id': 'INVALID001',
                'message_type': 'MT999',  # Invalid type
                'reference': 'THIS_REFERENCE_IS_WAY_TOO_LONG_12345',  # Too long
                'amount': '9999999999.99 USD',  # Too large
                'sender_bic': 'INVALID',  # Invalid BIC
                'receiver_bic': 'INVALID',  # Invalid BIC
                'remittance_info': 'Test invalid message'
            },
            {
                'message_id': 'FIXABLE001',
                'message_type': 'MT103',
                'reference': 'REF_NEEDS_FIX_123456789',  # Slightly too long
                'amount': '0.001 USD',  # Too small
                'sender_bic': 'TEST1234',  # Invalid format
                'receiver_bic': 'BARCGB22XXX',
                'remittance_info': 'Should be fixable'
            }
        ]

        print("Testing Evaluator-Optimizer Pattern\n")
        results = self.process_with_evaluator_optimizer(test_messages)

        print("\nTest Results:")
        for msg in results:
            print(f"\n{msg.get('message_id')}:")
            print(f"  Status: {msg.get('validation_status')}")
            if msg.get('validation_errors'):
                print(f"  Remaining errors: {len(msg.get('validation_errors'))}")

        return results


if __name__ == "__main__":
    # Test the evaluator-optimizer pattern
    pattern = EvaluatorOptimizerPattern()
    pattern.test_pattern()