#!/usr/bin/env python3
"""
Quality Feedback Survey System for Self-Improvement

Collects structured feedback on agent output quality to enable
continuous improvement and track evolution over time.
"""

import json
from datetime import datetime
from pathlib import Path
import sys

class QualityFeedbackSurvey:
    """Structured 3-question quality survey."""

    SURVEY_QUESTIONS = [
        {
            "id": "authenticity",
            "question": "How authentic is JD Vance's perspective in the response?",
            "type": "rating",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Not at all", "Somewhat", "Neutral", "Quite", "Extremely"],
            "description": "Does the response capture his actual views on working-class America, meritocracy, and bootstraps?"
        },
        {
            "id": "contextual_awareness",
            "question": "How well does the response address the specific prompt/question?",
            "type": "rating",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Irrelevant", "Tangential", "Partially", "Mostly", "Directly"],
            "description": "Is the response on-topic and engaging with the actual question asked?"
        },
        {
            "id": "intellectual_depth",
            "question": "Does the response show genuine intellectual reasoning or just quips?",
            "type": "rating",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Superficial", "Shallow", "Adequate", "Thoughtful", "Nuanced"],
            "description": "Is there depth to the reasoning, or is it just random JD Vance phrases?"
        },
    ]

    def __init__(self, feedback_file: Path = None):
        self.feedback_file = feedback_file or Path(__file__).parent / "quality_feedback.jsonl"

    def display_survey(self):
        """Display survey and collect responses interactively."""
        print("\n" + "="*72)
        print("🇺🇸 QUALITY FEEDBACK SURVEY - Help Improve the Agent 🇺🇸")
        print("="*72 + "\n")

        responses = {
            "timestamp": datetime.now().isoformat(),
            "answers": {}
        }

        for q in self.SURVEY_QUESTIONS:
            print(f"\nQuestion: {q['question']}")
            print(f"Description: {q['description']}\n")

            if q["type"] == "rating":
                # Display scale
                for scale_val, label in zip(q["scale"], q["labels"]):
                    print(f"  [{scale_val}] {label}")

                # Get rating
                while True:
                    try:
                        rating = int(input(f"\nYour rating (1-5): ").strip())
                        if rating in q["scale"]:
                            responses["answers"][q["id"]] = rating
                            break
                        else:
                            print(f"Please enter a number between 1 and 5.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            # Optional comment
            comment = input(f"Optional comment (press Enter to skip): ").strip()
            if comment:
                responses["answers"][f"{q['id']}_comment"] = comment

        self.save_feedback(responses)
        self._print_summary(responses)

        return responses

    def save_feedback(self, responses: dict):
        """Save feedback to file."""
        with open(self.feedback_file, "a") as f:
            f.write(json.dumps(responses) + "\n")
        print(f"\n✓ Feedback saved to {self.feedback_file}")

    def _print_summary(self, responses: dict):
        """Print summary of feedback."""
        answers = responses["answers"]

        print("\n" + "="*72)
        print("FEEDBACK SUMMARY")
        print("="*72)

        for q in self.SURVEY_QUESTIONS:
            rating = answers.get(q["id"])
            label = q["labels"][rating - 1] if rating else "N/A"
            comment = answers.get(f"{q['id']}_comment", "")

            print(f"\n{q['id'].upper()}: {rating}/5 ({label})")
            if comment:
                print(f"  Comment: {comment}")

        print("\n" + "="*72 + "\n")

    def analyze_feedback(self):
        """Analyze all feedback collected so far."""
        if not self.feedback_file.exists():
            print("No feedback collected yet.")
            return

        all_responses = []
        with open(self.feedback_file, "r") as f:
            for line in f:
                try:
                    all_responses.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        if not all_responses:
            print("No valid feedback found.")
            return

        print("\n" + "="*72)
        print("QUALITY FEEDBACK ANALYSIS")
        print("="*72)
        print(f"Total feedback entries: {len(all_responses)}\n")

        # Calculate averages
        for q in self.SURVEY_QUESTIONS:
            ratings = [r["answers"].get(q["id"]) for r in all_responses if q["id"] in r["answers"]]
            if ratings:
                avg = sum(ratings) / len(ratings)
                print(f"{q['id'].upper():20s}: {avg:.2f}/5.0 (from {len(ratings)} responses)")

        print("\n" + "="*72 + "\n")

def run_feedback_survey():
    """Run the interactive feedback survey."""
    survey = QualityFeedbackSurvey()
    survey.display_survey()

def analyze_quality_feedback():
    """Analyze collected feedback."""
    survey = QualityFeedbackSurvey()
    survey.analyze_feedback()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        analyze_quality_feedback()
    else:
        run_feedback_survey()
