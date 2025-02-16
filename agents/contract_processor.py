from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from models import Contract, ProcessingResponse, Clause, Party
from utils.pdf_parser import PDFParser
from utils.helpers import get_logger
import json



logger = get_logger(__name__)

# Get the schema for expected output
contract_schema = Contract.model_json_schema()
party_schema = Party.model_json_schema()

# Create a sample structure with only the metadata-relevant fields
metadata_structure = {
    "contract_title": contract_schema["properties"]["contract_title"],
    "contract_date": contract_schema["properties"]["contract_date"],
    "parties_involved": contract_schema["properties"]["parties_involved"]
}

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
            show_tool_calls=True,
            response_model=Contract,
            structured_outputs=True,
        )

        # Clause Extraction Agent
        self.clause_agent = Agent(
            name="Clause Extractor",
            role="Contract clause extraction specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Identify and extract individual contract clauses"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True,
        )

        # Clause Classification Agent
        self.classification_agent = Agent(
            name="Clause Classifier",
            role="Contract clause classification specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Classify contract clauses into standard categories"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True,
        )

        # NER Agent
        self.ner_agent = Agent(
            name="NER Processor",
            role="Named Entity Recognition specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Extract dates, amounts, and named entities from clauses"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True,
        )

        # Clause Generation Agent
        self.generation_agent = Agent(
            name="Clause Generator",
            role="Contract clause improvement specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Generate improved versions of contract clauses"],
            markdown=True,
            show_tool_calls=True,
            response_model=Clause,
            structured_outputs=True
        )

        # Summarization Agent
        self.summary_agent = Agent(
            name="Contract Summarizer",
            role="Contract summarization specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=["Create concise summaries of full contracts"],
            markdown=True,
            show_tool_calls=True,
            response_model=Contract,
            structured_outputs=True
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
            show_tool_calls=True,
            response_model=ProcessingResponse,
            structured_outputs=True
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
            logger.debug(f"Extracted text length: {len(text)}")
            # logger.debug(f"First 500 chars of text: {text[:500]}")


            # Process the extracted text
            logger.info("Processing extracted text through contract pipeline")
            return self.process_contract(text, pdf_path)

        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}", exc_info=True)
            return ProcessingResponse(
                status="error",
                error=f"PDF processing failed: {str(e)}",
                document=None
            )

    def process_contract(self, text: str, pdf_path: Path) -> ProcessingResponse:
        """
        Process a contract document through the entire pipeline of agents.

        Args:
            text (str): The raw text content of the contract
            pdf_path (Path): The path to the PDF file

        Returns:
            ProcessingResponse: Processing result with either the structured contract data or error
        """
        try:
            # 1. Extract and structure contract metadata
            logger.info("Step 1: Extracting contract metadata")
            metadata_prompt = f"""
            AI Document Parser: Extract contract metadata and structure with prescribed format.

            1. Extract Contract Metadata:
            - Title: Full contract title (exact)
            - Date: Official start date
            - Parties: Extract name and role for each party
            Format: {{"party_name": "Company A", "role": "Service Provider"}}

            2. Extract Major Sections:
            - Category: Legal function (Financial, Termination, etc.)
            - Name: Exact heading/title
            - Text: Full clause content
            - Dates: Leave for NER processing
            - Amounts: Leave for NER processing
            - Metadata: Include confidence score

            3. Output Requirements:
            ✓ Success Format:
            - "status": "success"
            - "document": {{ structured contract output }}

            ✗ Error Format:
            - "status": "failed"
            - "error": "Specific error message"

            Flag any missing/unclear data with "warning" field.

            Text: {text}
            """

            metadata_result = self.parsing_agent.run(metadata_prompt)
            logger.debug(f"Raw metadata result: {metadata_result}")
            logger.debug(f"Metadata type: {type(metadata_result)}")
            logger.info(f"Metadata extraction result: {metadata_result.content if hasattr(metadata_result, 'content') else metadata_result}")

            print(f"metadata_result type: {type(metadata_result)}")
            print(f"metadata_result dir: {dir(metadata_result)}")

            # 2. Extract clauses
            logger.info("Step 2: Extracting clauses")

            clause_prompt = f"""
            Extract and structure clauses with:

            1. Structure Requirements:
            - clause: sequential number
            - section_name: section header/name
            - clause_text: complete text
            - related_dates: [YYYY-MM-DD format]
            - related_amounts: [monetary values with currency]
            - metadata: {{ confidence_score: float 0-1 }}

            2. Output Format:
            {{
                "clauses": [
                    {{
                        "clause": 1,
                        "section_name": "NATURE OF RELATIONSHIP",
                        "clause_text": "...",
                        "related_dates": ["2025-03-01"],
                        "related_amounts": ["$50,000"],
                        "metadata": {{ "confidence_score": 0.95 }}
                    }}
                ]
            }}

            3. Guidelines:
            - Preserve original formatting/numbering
            - Use YYYY-MM-DD for dates
            - Include currency symbols
            - Maintain section hierarchy
            - Flag incomplete/ambiguous clauses

            Text: {text}
            """

            clauses_result = self.clause_agent.run(clause_prompt)
            logger.debug(f"Raw clauses result: {clauses_result}")
            logger.debug(f"Clauses type: {type(clauses_result)}")
            logger.info(f"Clause extraction result: {clauses_result.content if hasattr(clauses_result, 'content') else clauses_result}")

            # 3. Classify clauses
            logger.info("Step 3: Classifying clauses")

            classification_prompt = f"""
            1. Legal Categories:
            - Financial Terms: Payment, Fees, Compensation, Penalties
            - Confidentiality & NDA: Data Protection, Trade Secrets, Non-Disclosure
            - Termination & Breach: Exit Clauses, Rights, Auto-Renewals
            - Indemnification & Liability: Risk Allocation, Damages
            - Dispute Resolution: Arbitration, Mediation, Jurisdiction
            - Rights & Restrictions: Ownership, IP, Licensing, Non-Compete
            - Miscellaneous: Other clauses not fitting above categories

            2. Classification Rules:
            - Use primary function for multi-category clauses
            - Label unclear clauses as "Miscellaneous"
            - Preserve original text and structure
            - Add warnings for uncertain classifications

            3. Output Format:
            {{
                "status": "success|failed",
                "document": {{
                    "clauses": [
                        {{
                            "clause_category": "category_name",
                            "clause_text": "original_text",
                            "warning": "optional_warning_message"
                        }}
                    ]
                }},
                "error": "error_message_if_failed"
            }}

            Input Clauses: {clauses_result.content}
            """

            classified_clauses = self.classification_agent.run(classification_prompt)
            logger.info(f"Classification result: {classified_clauses.content if hasattr(classified_clauses, 'content') else classified_clauses}")


            # 4. Extract entities from each clause
            logger.info("Step 4: Extracting named entities")

            ner_prompt = f"""
            1. Entity Extraction Requirements:
            - Dates (related_dates):
            * Contract dates, deadlines, renewals
            * Convert relative to explicit dates
            * Format: ["YYYY-MM-DD"]

            - Amounts (amounts):
            * Financial values with currency
            * Include percentages and fees
            * Format: ["$10,000", "2%"]

            - Parties (parties_involved):
            * Names and roles
            * Format: [
                {{ "party_name": "ABC Corp", "role": "Provider" }}
                ]

            - Jurisdiction:
            * Legal jurisdiction references
            * Flag multiple jurisdictions

            2. Output Format:
            {{
                "related_dates": ["2025-03-01"],
                "amounts": ["$50,000"],
                "parties_involved": [
                    {{ "party_name": "Name", "role": "Role" }}
                ],
                "warning": "optional_warning_message"
            }}

            3. Warning Cases:
            - Unclear dates/amounts
            - Ambiguous party roles
            - Multiple jurisdictions
            - Missing required data

            Input Clauses: {classified_clauses.content}
            """

            enriched_clauses = self.ner_agent.run(ner_prompt)
            logger.info(f"NER result: {enriched_clauses.content if hasattr(enriched_clauses, 'content') else enriched_clauses}")


            # 5. Generate alternative clauses (optional)
            logger.info("Step 5: Generating alternative clauses")
            generation_prompt = f"""
            1. Enhancement Requirements:
            - Preserve legal intent
            - Remove ambiguity/redundancy
            - Ensure term definitions
            - Validate external references

            2. Improvement Guidelines:
            - Make terms explicit
            - Use legally binding language
            - Simplify without losing accuracy
            - Maintain document consistency

            3. Output Format:
            {{
                "clauses": [
                    {{
                        "clause_category": "Category",
                        "original_clause_text": "Original",
                        "improved_clause_text": "Enhanced",
                        "modification_reason": "Change explanation",
                        "warning": "optional_warning"
                    }}
                ]
            }}

            4. Special Cases:
            - Return optimal clauses as-is with justification
            - Flag unclear external references
            - Note undefined terms
            - Mark ambiguous improvements

            Input Clauses: {enriched_clauses.content}
            """

            generated_clauses = self.generation_agent.run(generation_prompt)
            logger.debug(f"Raw generated result: {generated_clauses}")
            logger.debug(f"Generated type: {type(generated_clauses)}")
            logger.info(f"Generation result: {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}")

            # 6. Create contract summary
            logger.info("Step 6: Creating contract summary")
            summary_prompt = f"""
            1. Core Elements:
            - Basic: title, date, parties
            - Scope: purpose, obligations
            - Deliverables: services, expectations

            2. Key Terms:
            - Financial: payments, penalties, taxes
            - Termination: conditions, renewals, notices
            - Legal: dispute resolution, jurisdiction
            - Confidentiality: NDAs, IP rights, restrictions

            3. Risk Overview:
            - Liability terms
            - Risk level
            - Critical obligations
            - Potential issues

            4. Output Format:
            {{
                "contract_title": "Title",
                "contract_date": "Date",
                "parties_involved": [
                    {{ "party_name": "Name", "role": "Role" }}
                ],
                "summary": {{
                    "agreement_scope": "Description",
                    "financial_terms": {{
                        "total_value": "Amount",
                        "payment_schedule": "Schedule",
                        "penalties": "Terms"
                    }},
                    "termination_terms": {{
                        "notice_period": "Period",
                        "penalties": "Terms"
                    }},
                    "confidentiality_terms": "Description",
                    "risk_assessment": "Level and explanation"
                }}
            }}

            Contract Metadata: {metadata_result.content}
            Key Clauses: {generated_clauses.content}
            """

            summary_result = self.summary_agent.run(summary_prompt)
            logger.debug(f"Raw summary result: {summary_result}")
            logger.debug(f"Summary type: {type(summary_result)}")
            logger.info(f"Summary result: {summary_result.content if hasattr(summary_result, 'content') else summary_result}")

            # 7. Combine results
            logger.info("Step 7: Combining all results")
            try:
                # Get metadata from RunResponse
                metadata_content = metadata_result.content if hasattr(metadata_result, 'content') else metadata_result

                # Get clauses from RunResponse
                clauses_content = generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses

                # Get summary from RunResponse
                summary_content = summary_result.content if hasattr(summary_result, 'content') else summary_result

                # Add debug logging
                logger.debug(f"Clauses content type: {type(clauses_content)}")
                logger.debug(f"Clauses content: {clauses_content}")

                contract_data = {
                    "pdf_name": pdf_path.name,
                    "contract_title": metadata_content.contract_title,
                    "contract_date": metadata_content.contract_date,
                    "parties_involved": metadata_content.parties_involved,
                    "clauses": metadata_content.clauses,
                    "summary": summary_content.summary,
                    "amounts": metadata_content.amounts
                }

                return ProcessingResponse(
                    status="success",
                    error=None,
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
                error=f"Contract processing failed: {str(e)}",
                document=None
            )