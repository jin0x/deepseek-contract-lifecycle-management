import json
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from models import Contract, ProcessingResponse
from pdf_parser import PDFParser
from utils.helpers import get_logger
import json

logger = get_logger(__name__)

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

    def process_pdf(self, pdf_path: str | Path) -> ProcessingResponse:
        """Process a PDF file through the entire pipeline"""
        try:
            logger.info(f"Starting PDF processing for file: {pdf_path}")

            pdf_path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
            logger.info(f"Using PDF path: {pdf_path.absolute()}")

            # Extract text from PDF
            logger.info("Extracting text from PDF")
            text = self.pdf_parser.parse_pdf(pdf_path)
            logger.info(f"Extracted text length: {len(text)}")

            # Process the extracted text
            logger.info("Processing extracted text through contract pipeline")
            return self.process_contract(text)

        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}", exc_info=True)
            return ProcessingResponse(
                status="error",
                error=f"PDF processing failed: {str(e)}"
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
            logger.info("Starting contract processing pipeline")
            logger.info(f"Input text length: {len(text)}")

            # 1. Extract basic contract metadata
            logger.info("Step 1: Extracting contract metadata")
            metadata_prompt = f"""Extract the basic contract information:
            - Contract title
            - Contract date
            - Parties involved (with their roles)

            Text: {text}

            Return the data in JSON format matching the schema exactly."""

            metadata_result = self.parsing_agent.run(metadata_prompt)
            logger.info(f"Metadata extraction result: {metadata_result.content if hasattr(metadata_result, 'content') else metadata_result}")

            # 2. Extract clauses
            logger.info("Step 2: Extracting clauses")
            clause_prompt = f"""Extract all contract clauses from the following text.
            For each clause, identify its name and full text content.

            Text: {text}

            Return as a list of clauses in JSON format."""

            clauses_result = self.clause_agent.run(clause_prompt)
            logger.info(f"Clause extraction result: {clauses_result.content if hasattr(clauses_result, 'content') else clauses_result}")

            # 3. Classify clauses
            logger.info("Step 3: Classifying clauses")
            classification_prompt = f"""Classify each of these clauses into standard categories.
            Input clauses: {clauses_result.content}

            Return the clauses with their classifications in JSON format."""

            classified_clauses = self.classification_agent.run(classification_prompt)
            logger.info(f"Classification result: {classified_clauses.content if hasattr(classified_clauses, 'content') else classified_clauses}")

            # 4. Extract entities from each clause
            ner_prompt = f"""Extract dates, monetary amounts, and named entities from these clauses:
            {classified_clauses.content}

            For each clause, return:
            - List of dates found
            - List of monetary amounts
            - Add metadata with confidence score and extractor attribution"""

            logger.info("Step 4: Extracting named entities")
            enriched_clauses = self.ner_agent.run(ner_prompt)
            logger.info(f"NER result: {enriched_clauses.content if hasattr(enriched_clauses, 'content') else enriched_clauses}")

            # 5. Generate alternative clauses (optional)
            logger.info("Step 5: Generating alternative clauses")
            generation_prompt = f"""For each clause, suggest an improved version that enhances clarity and reduces legal risk:
            {enriched_clauses.content}

            Return both original and alternative versions in JSON format."""

            generated_clauses = self.generation_agent.run(generation_prompt)
            logger.info(f"Generation result: {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}")

            # 6. Create contract summary
            logger.info("Step 6: Creating contract summary")
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
            logger.info(f"Summary result: {summary_result.content if hasattr(summary_result, 'content') else summary_result}")

            # 7. Combine results
            logger.info("Step 7: Combining all results")
            try:
                metadata_content = json.loads(metadata_result.content) if hasattr(metadata_result, 'content') else json.loads(metadata_result)
                clauses_content = json.loads(generated_clauses.content) if hasattr(generated_clauses, 'content') else json.loads(generated_clauses)
                summary_content = summary_result.content if hasattr(summary_result, 'content') else summary_result

                contract_data = {
                    **metadata_content,
                    "clauses": clauses_content,
                    "summary": summary_content
                }
                logger.info(f"Final contract data structure: {contract_data}")

                return ProcessingResponse(
                    status="success",
                    document=Contract(**contract_data)
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Raw metadata content: {metadata_result.content if hasattr(metadata_result, 'content') else metadata_result}")
                logger.error(f"Raw clauses content: {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}")
                raise

        except Exception as e:
            return ProcessingResponse(
                status="error",
                error=f"Contract processing failed: {str(e)}"
            )