"""
Base Agent Classes for SWIFT Transaction Processing

This module contains the base classes that all agents inherit from.
You will implement the BaseAgent abstract class and the SwiftCorrectionAgent.
"""

# TODO 6: Create BaseAgent abstract class (10 points) - COMPLETED
from abc import ABC, abstractmethod
from config import Config
from services.llm_service import LLMService

class BaseAgent(ABC):
    """Base abstract class for all agents"""

    def __init__(self):
        """Initialize the base agent with config and LLM service"""
        self.config = Config()
        self.llm_service = LLMService()

    @abstractmethod
    def create_prompt(self, data):
        """Each agent must implement their own prompt creation"""
        pass

    def respond(self, prompt: str):
        """Common method to get LLM response"""
        return self.llm_service.get_swift_correction(prompt)


class SwiftCorrectionAgent:
    """Agent for correcting SWIFT messages based on validation errors."""

    def __init__(self):
        # TODO 7: Define LLMService (5 points) - COMPLETED
        # INSTRUCTIONS: Initialize self.llm_service with an instance of LLMService
        # HINT: from services.llm_service import LLMService
        # Then: self.llm_service = LLMService()
        from services.llm_service import LLMService
        self.llm_service = LLMService()

    def create_prompt(self, message, errors):
        """
        Create a prompt for the LLM to correct a SWIFT message.

        Args:
            message: The SWIFT message data
            errors: List of validation errors to fix

        Returns:
            str: The formatted prompt for the LLM
        """
        system_prompt = """You are a SWIFT message correction expert.
        Fix the validation errors while maintaining the business intent.
        Return the corrected message in JSON format."""

        user_prompt = f"""
        Original SWIFT Message:
        {message}

        Validation Errors to Fix:
        {errors}

        Please correct these errors and return the complete corrected message in JSON format.
        """

        return system_prompt, user_prompt

    def respond(self, message, errors):
        """
        Get LLM response to correct the SWIFT message.

        Args:
            message: The SWIFT message to correct
            errors: The validation errors to fix

        Returns:
            dict: The corrected message data
        """
        import json
        from openai import OpenAI

        system_prompt, user_prompt = self.create_prompt(message, errors)

        try:
            client = OpenAI(
                base_url="https://openai.vocareum.com/v1",
                api_key=self.llm_service.config.OPENAI_API_KEY
            )
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # TODO 8: Set response format (3 points) - COMPLETED
                # INSTRUCTIONS: Add the response_format parameter to ensure JSON output
                # The format should be: response_format={"type": "json_object"}
                # This ensures the LLM returns valid JSON that we can parse
                response_format={"type": "json_object"},
                temperature=0.1
            )

            # TODO 9: Parse response result (2 points) - COMPLETED
            # INSTRUCTIONS: Extract and parse the JSON content from the response
            # HINT: The response content is in response.choices[0].message.content
            # You'll need to:
            # 1. Get the content from response.choices[0].message.content
            # 2. Use json.loads() to parse it into a Python dictionary
            # 3. Return the parsed result

            content = response.choices[0].message.content
            result = json.loads(content)
            return result

        except Exception as e:
            print(f"Error in SwiftCorrectionAgent: {e}")
            return message  # Return original if correction fails


class FraudAmountDetectionAgent:
    """Agent for detecting fraud based on transaction amounts."""

    def __init__(self):
        self.rules = [
            {"condition": "amount > 10000", "risk_score": 0.3},
            {"condition": "round_amount", "risk_score": 0.2},
            {"condition": "unusual_precision", "risk_score": 0.1}
        ]

    def analyze(self, message):
        """
        Analyze a SWIFT message for amount-based fraud patterns.

        Args:
            message: The SWIFT message to analyze

        Returns:
            dict: Fraud analysis results with risk score and reasons
        """
        risk_score = 0
        fraud_reasons = []

        try:
            # Extract amount from message
            amount_str = message.get('amount', '0')
            # Remove currency code and convert to float
            amount = float(''.join(c for c in amount_str if c.isdigit() or c == '.'))

            # Rule 1: Large amounts
            if amount > 10000:
                risk_score += 0.3
                fraud_reasons.append(f"High amount transaction: {amount}")

            # Rule 2: Round amounts (multiples of 1000)
            if amount % 1000 == 0 and amount > 0:
                risk_score += 0.2
                fraud_reasons.append(f"Suspiciously round amount: {amount}")

            # Rule 3: Unusual precision for large amounts
            if amount > 100000 and (amount % 1) != 0:
                risk_score += 0.1
                fraud_reasons.append("Large amount with unusual decimal precision")

        except (ValueError, TypeError) as e:
            print(f"Error analyzing amount: {e}")

        return {
            "agent": "FraudAmountDetectionAgent",
            "risk_score": min(risk_score, 1.0),
            "fraud_reasons": fraud_reasons
        }


class FraudPatternDetectionAgent:
    """Agent for detecting fraud based on transaction patterns."""

    def __init__(self):
        self.high_risk_patterns = ['TEST', 'FAKE', 'DEMO', '999', '000000']
        self.suspicious_keywords = ['urgent', 'immediately', 'secret', 'confidential']

    def analyze(self, message):
        """
        Analyze a SWIFT message for pattern-based fraud indicators.

        Args:
            message: The SWIFT message to analyze

        Returns:
            dict: Fraud analysis results with risk score and reasons
        """
        risk_score = 0
        fraud_reasons = []

        # Check BIC codes for test patterns
        sender_bic = message.get('sender_bic', '')
        receiver_bic = message.get('receiver_bic', '')

        for pattern in self.high_risk_patterns:
            if pattern in sender_bic.upper() or pattern in receiver_bic.upper():
                risk_score += 0.4
                fraud_reasons.append(f"Test/fake pattern detected in BIC: {pattern}")

        # Check for same sender and receiver
        if sender_bic and sender_bic == receiver_bic:
            risk_score += 0.5
            fraud_reasons.append("Same sender and receiver BIC")

        # Check remittance info for suspicious keywords
        remittance = message.get('remittance_info', '').lower()
        for keyword in self.suspicious_keywords:
            if keyword in remittance:
                risk_score += 0.2
                fraud_reasons.append(f"Suspicious keyword in remittance: {keyword}")

        return {
            "agent": "FraudPatternDetectionAgent",
            "risk_score": min(risk_score, 1.0),
            "fraud_reasons": fraud_reasons
        }


class FraudAggAgent:
    """Agent for aggregating fraud detection results from multiple agents."""

    def __init__(self):
        self.threshold = 0.5  # Fraud threshold (50%)

    def aggregate_results(self, fraud_results):
        """
        Aggregate fraud detection results from multiple agents.

        Args:
            fraud_results: List of fraud detection results from different agents

        Returns:
            dict: Aggregated fraud assessment
        """
        if not fraud_results:
            return {
                "is_fraudulent": False,
                "confidence": 0,
                "total_risk_score": 0,
                "aggregated_reasons": []
            }

        # Calculate average risk score
        total_risk = sum(r.get('risk_score', 0) for r in fraud_results)
        avg_risk = total_risk / len(fraud_results)

        # Aggregate all fraud reasons
        all_reasons = []
        for result in fraud_results:
            agent_name = result.get('agent', 'Unknown')
            reasons = result.get('fraud_reasons', [])
            for reason in reasons:
                all_reasons.append(f"[{agent_name}] {reason}")

        # Determine if fraudulent based on threshold
        is_fraudulent = avg_risk >= self.threshold

        return {
            "is_fraudulent": is_fraudulent,
            "confidence": round(avg_risk * 100, 2),
            "total_risk_score": round(avg_risk, 3),
            "aggregated_reasons": all_reasons
        }


class GeographicRiskAgent:
    """Agent for detecting fraud based on geographic risk factors."""

    def __init__(self):
        # High-risk country codes based on common financial crime patterns
        self.high_risk_countries = ['IR', 'KP', 'SY', 'SD', 'CU', 'BY', 'MM', 'VE', 'ZW']
        self.medium_risk_countries = ['AF', 'IQ', 'LB', 'LY', 'SO', 'YE', 'PK']
        self.offshore_tax_havens = ['KY', 'BM', 'VG', 'PA', 'LI', 'MC']

    def analyze(self, message):
        """
        Analyze a SWIFT message for geographic risk indicators.

        Args:
            message: The SWIFT message to analyze

        Returns:
            dict: Fraud analysis results with risk score and reasons
        """
        risk_score = 0
        fraud_reasons = []

        # Extract country codes from BIC codes (characters 5-6)
        sender_bic = message.get('sender_bic', '')
        receiver_bic = message.get('receiver_bic', '')

        sender_country = sender_bic[4:6] if len(sender_bic) >= 6 else ''
        receiver_country = receiver_bic[4:6] if len(receiver_bic) >= 6 else ''

        # Check for high-risk countries
        if sender_country in self.high_risk_countries:
            risk_score += 0.7
            fraud_reasons.append(f"Transaction from high-risk country: {sender_country}")

        if receiver_country in self.high_risk_countries:
            risk_score += 0.7
            fraud_reasons.append(f"Transaction to high-risk country: {receiver_country}")

        # Check for medium-risk countries
        if sender_country in self.medium_risk_countries:
            risk_score += 0.4
            fraud_reasons.append(f"Transaction from medium-risk country: {sender_country}")

        if receiver_country in self.medium_risk_countries:
            risk_score += 0.4
            fraud_reasons.append(f"Transaction to medium-risk country: {receiver_country}")

        # Check for offshore tax havens
        if sender_country in self.offshore_tax_havens or receiver_country in self.offshore_tax_havens:
            risk_score += 0.3
            fraud_reasons.append(f"Transaction involves offshore tax haven")

        # Check for unusual country combinations (e.g., both parties from same high-risk region)
        if sender_country == receiver_country and sender_country in self.high_risk_countries:
            risk_score += 0.2
            fraud_reasons.append("Domestic transaction in high-risk country")

        return {
            "agent": "GeographicRiskAgent",
            "risk_score": min(risk_score, 1.0),
            "fraud_reasons": fraud_reasons
        }