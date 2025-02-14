import json
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from models import Contract, ProcessingResponse
from pdf_parser import PDFParser

class ContractProcessingAgent:
    def __init__(self, api_key: str):
        self.pdf_parser = PDFParser()

        # Document Parsing Agent
        self.parsing_agent = Agent(
            name="Document Parser",
            role="Document parsing specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Extract contract metadata and structure"],
            markdown=True,
            show_tool_calls=True
        )

        # Clause Extraction Agent
        self.clause_agent = Agent(
            name="Clause Extractor",
            role="Contract clause extraction specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Identify and extract individual contract clauses"],
            markdown=True,
            show_tool_calls=True
        )

        # Clause Classification Agent
        self.classification_agent = Agent(
            name="Clause Classifier",
            role="Contract clause classification specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Classify contract clauses into standard categories"],
            markdown=True,
            show_tool_calls=True
        )

        # NER Agent
        self.ner_agent = Agent(
            name="NER Processor",
            role="Named Entity Recognition specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Extract dates, amounts, and named entities from clauses"],
            markdown=True,
            show_tool_calls=True
        )

        # Clause Generation Agent
        self.generation_agent = Agent(
            name="Clause Generator",
            role="Contract clause improvement specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Generate improved versions of contract clauses"],
            markdown=True,
            show_tool_calls=True
        )

        # Summarization Agent
        self.summary_agent = Agent(
            name="Contract Summarizer",
            role="Contract summarization specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Create concise summaries of full contracts"],
            markdown=True,
            show_tool_calls=True
        )

        # Agent Team
        self.agent_team = Agent(
            name="Contract Processing Team",
            role="Contract analysis coordination",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            team=[
                self.parsing_agent,
                self.clause_agent,
                self.classification_agent,
                self.ner_agent,
                self.generation_agent,
                self.summary_agent
            ],
            instructions=["Coordinate contract analysis workflow"],
            markdown=True,
            show_tool_calls=True
        )

    def process_contract(self, text: str) -> ProcessingResponse:
        """
        Process a contract document through the entire pipeline of agents.

        Args:
            text (str): The raw text content of the contract

        Returns:
            ProcessingResponse: Processing result with either the structured contract data or error
        """
        try:
            # 1. Extract basic contract metadata
            metadata_prompt = f"""Extract the basic contract information:
            - Contract title
            - Contract date
            - Parties involved (with their roles)

            Text: {text}

            Return the data in JSON format matching the schema exactly."""

            metadata_result = self.parsing_agent.run(metadata_prompt)

            # 2. Extract clauses
            clause_prompt = f"""Extract all contract clauses from the following text.
            For each clause, identify its name and full text content.

            Text: {text}

            Return as a list of clauses in JSON format."""

            clauses_result = self.clause_agent.run(clause_prompt)

            # 3. Classify clauses
            classification_prompt = f"""Classify each of these clauses into standard categories.
            Input clauses: {clauses_result.content}

            Return the clauses with their classifications in JSON format."""

            classified_clauses = self.classification_agent.run(classification_prompt)

            # 4. Extract entities from each clause
            ner_prompt = f"""Extract dates, monetary amounts, and named entities from these clauses:
            {classified_clauses.content}

            For each clause, return:
            - List of dates found
            - List of monetary amounts
            - Add metadata with confidence score and extractor attribution"""

            enriched_clauses = self.ner_agent.run(ner_prompt)

            # 5. Generate alternative clauses (optional)
            generation_prompt = f"""For each clause, suggest an improved version that enhances clarity and reduces legal risk:
            {enriched_clauses.content}

            Return both original and alternative versions in JSON format."""

            generated_clauses = self.generation_agent.run(generation_prompt)

            # 6. Create contract summary
            summary_prompt = f"""Create a concise summary of this contract:
            Contract Metadata: {metadata_result.content}
            Key Clauses: {generated_clauses.content}

            Focus on:
            - Main agreement points
            - Key obligations
            - Important dates
            - Critical terms

            Return as a single summary string."""

            summary_result = self.summary_agent.run(summary_prompt)

            # 7. Combine all results into final contract structure
            contract_data = {
                **json.loads(metadata_result.content),
                "clauses": json.loads(generated_clauses.content),
                "summary": summary_result.content
            }

            return ProcessingResponse(
                status="success",
                document=Contract(**contract_data)
            )

        except Exception as e:
            return ProcessingResponse(
                status="error",
                error=f"Contract processing failed: {str(e)}"
            )