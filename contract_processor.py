from typing import Type
from pydantic import BaseModel
from pathlib import Path
from pydantic import ValidationError
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from models import Clause, ClauseCategory, ClauseMetadata, Contract, Party, ProcessingResponse
from pdf_parser import PDFParser
from utils.helpers import get_logger
import json

logger = get_logger(__name__)

class ContractProcessingAgent:
    def __init__(self, api_key: str):
        self.pdf_parser = PDFParser()
        self.contract_schema = self._get_schema(Contract)
        self.clause_schema = self._get_schema(Clause)
        self.party_schema = self._get_schema(Party)
        self.clause_metadata_schema = self._get_schema(ClauseMetadata)

        # Document Parsing Agent
        self.parsing_agent = Agent(
            name="Document Parser",
            role="Document parsing specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=[
                "Extract key contract information including metadata, parties, and clauses.",
                "Focus on accuracy and completeness of extraction."
            ],
            # markdown=True,
            # show_tool_calls=True,
            # response_model=Contract,
            structured_outputs=True,
        )

        # Clause Extraction Agent
        self.clause_agent = Agent(
            name="Clause Extractor",
            role="Contract clause specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=[
                "Identify and extract distinct contract clauses.",
                "Ensure each clause is complete and properly separated."
            ],
            # markdown=True,
            # show_tool_calls=True,
            # response_model=Clause,
            structured_outputs=True,
        )

        # Clause Classification Agent
        self.classification_agent = Agent(
            name="Clause Classifier",
            role="Contract clause classification specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=[
                "Classify each clause into its appropriate category.",
                f"Use only valid categories: {', '.join(ClauseCategory.__members__.keys())}"
            ],
            # markdown=True,
            # show_tool_calls=True,
            # response_model=Clause,
            structured_outputs=True,
        )

        # NER Agent
        self.ner_agent = Agent(
            name="NER Processor",
            role="Named Entity Recognition specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=[
                "Extract dates, amounts, and named entities from contract clauses.",
                "Focus on accuracy of extracted values."
            ],
            # markdown=True,
            # show_tool_calls=True,
            # response_model=Clause,
            structured_outputs=True,
        )

        # Clause Generation Agent
        self.generation_agent = Agent(
            name="Clause Generator",
            role="Contract clause improvement specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=[
                "Generate improved versions of contract clauses.",
                "Maintain legal meaning while enhancing clarity."
            ],
            # markdown=True,
            # show_tool_calls=True,
            # response_model=Clause,
            structured_outputs=True
        )

        # Summarization Agent
        self.summary_agent = Agent(
            name="Contract Summarizer",
            role="Contract summarization specialist",
            model=OpenAIChat(id="gpt-4o", api_key=api_key),
            instructions=[
                "Create concise summaries of contract content.",
                "Highlight key terms, obligations, and conditions."
            ],
            # markdown=True,
            # show_tool_calls=True,
            # response_model=Contract,
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
            # markdown=True,
            # show_tool_calls=True,
            response_model=ProcessingResponse,
            structured_outputs=True
        )

    def _get_schema(self, model_class: Type[BaseModel]) -> dict:
        """Get clean JSON schema from a Pydantic model"""
        schema = model_class.model_json_schema()
        # Remove Pydantic-specific format specifications
        if 'properties' in schema:
            for prop in schema['properties'].values():
                prop.pop('format', None)
        return schema

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
            logger.debug(f"First 500 chars of text: {text[:500]}")

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
            Extract and structure the contract information according to this exact schema:
            {json.dumps(self.contract_schema, indent=2)}

            Contract text:
            {text}

            IMPORTANT: Return ONLY a valid JSON object matching the schema exactly.
            """
            metadata_result = self.parsing_agent.run(metadata_prompt)


            logger.info(f"Raw metadata_result: {metadata_result}")
            logger.info(f"Type of metadata_result: {type(metadata_result)}")
            if hasattr(metadata_result, 'content'):
                logger.info(f"Type of metadata_result.content: {type(metadata_result.content)}")
                logger.info(f"Content: {metadata_result.content}")


            # 2. Extract clauses
            logger.info("Step 2: Extracting clauses")

            clause_prompt = f"""
            Extract individual clauses according to this exact schema:
            {json.dumps(self.clause_schema, indent=2)}

            Valid clause categories are:
            {[cat.value for cat in ClauseCategory]}

            Contract text:
            {text}

            IMPORTANT: Return a list of clause objects matching this schema exactly.
            """

            clauses_result = self.clause_agent.run(clause_prompt)
            logger.debug(f"Raw clauses result: {clauses_result}")
            logger.debug(f"Clauses type: {type(clauses_result)}")
            logger.info(f"Clause extraction result: {clauses_result.content if hasattr(clauses_result, 'content') else clauses_result}")

            # 3. Classify clauses
            logger.info("Step 3: Classifying clauses")

            classification_prompt = f"""
            Classify each clause according to this schema:
            {json.dumps(self.clause_schema, indent=2)}

            Focus on the clause_category field, which must be one of:
            {[cat.value for cat in ClauseCategory]}

            Clauses to classify:
            {clauses_result.content if hasattr(clauses_result, 'content') else clauses_result}
            """

            classified_clauses = self.classification_agent.run(classification_prompt)
            logger.info(f"Classification result: {classified_clauses.content if hasattr(classified_clauses, 'content') else classified_clauses}")


            # 4. Extract entities from each clause
            logger.info("Step 4: Extracting named entities")

            ner_prompt = f"""
            Extract entities according to this schema:
            {json.dumps(self.clause_schema, indent=2)}

            Focus on:
            - related_dates
            - related_amounts
            - parties_involved (using this schema: {json.dumps(self.party_schema, indent=2)})

            Input clauses:
            {classified_clauses.content if hasattr(classified_clauses, 'content') else classified_clauses}
            """

            enriched_clauses = self.ner_agent.run(ner_prompt)
            logger.info(f"NER result: {enriched_clauses.content if hasattr(enriched_clauses, 'content') else enriched_clauses}")


            # 5. Generate alternative clauses (optional)
            logger.info("Step 5: Generating alternative clauses")
            generation_prompt = f"""
            Improve clauses according to this schema:
            {json.dumps(self.clause_schema, indent=2)}

            Each clause must maintain:
            - Exact category from the original
            - All identified dates and amounts
            - A confidence score in the metadata

            Input clauses:
            {enriched_clauses.content if hasattr(enriched_clauses, 'content') else enriched_clauses}
            """

            generated_clauses = self.generation_agent.run(generation_prompt)
            logger.debug(f"Raw generated result: {generated_clauses}")
            logger.debug(f"Generated type: {type(generated_clauses)}")
            logger.info(f"Generation result: {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}")

            # 6. Create contract summary
            logger.info("Step 6: Creating contract summary")
            contract_schema = self.contract_schema
            summary_prompt = f"""
            Create a complete contract summary according to this schema:
            {json.dumps(contract_schema, indent=2)}

            Ensure all required fields are populated including:
            - contract_title
            - contract_date
            - parties_involved
            - clauses (with all required fields)
            - summary

            Contract information:
            {metadata_result.content if hasattr(metadata_result, 'content') else metadata_result}

            Processed clauses:
            {generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses}
            """

            summary_result = self.summary_agent.run(
                summary_prompt,
                response_model=contract_schema
            )
            logger.debug(f"Raw summary result: {summary_result}")
            logger.debug(f"Summary type: {type(summary_result)}")
            logger.info(f"Summary result: {summary_result.content if hasattr(summary_result, 'content') else summary_result}")

            # 7. Combine results
            logger.info("Step 7: Combining all results")
            try:
                # Get metadata from RunResponse
                metadata_content = metadata_result.content if hasattr(metadata_result, 'content') else metadata_result
                logger.info(f"Final metadata_content type: {type(metadata_content)}")
                logger.info(f"Final metadata_content: {metadata_content}")

                # Handle string metadata content
                if isinstance(metadata_content, str):
                    try:
                        # First try to parse as direct JSON
                        try:
                            metadata_dict = json.loads(metadata_content)
                        except json.JSONDecodeError:
                            # If direct JSON parsing fails, try to extract structured data from the text
                            metadata_dict = {
                                "contract_title": None,
                                "contract_date": None,
                                "parties_involved": [],
                                "clauses": [],
                                "amounts": []
                            }

                            # Parse the text content
                            lines = metadata_content.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line.startswith("**Contract Title:**"):
                                    metadata_dict["contract_title"] = line.replace("**Contract Title:**", "").strip()
                                elif line.startswith("**Date:**"):
                                    metadata_dict["contract_date"] = line.replace("**Date:**", "").strip()
                                elif "Parties Involved:" in line:
                                    # Start collecting parties
                                    parties = []
                                    for party_line in lines[lines.index(line)+1:]:
                                        if party_line.strip().startswith("1.") or party_line.strip().startswith("2."):
                                            party_info = party_line.strip().split(".", 1)[1].strip()
                                            if "(" in party_info:
                                                name, role = party_info.split("(")
                                                role = role.rstrip(")").strip('"')
                                                parties.append({"party_name": name.strip(), "role": role.strip()})
                                        elif not party_line.strip() or party_line.startswith("**"):
                                            break
                                    metadata_dict["parties_involved"] = parties

                        # Get clauses from RunResponse
                        clauses_content = generated_clauses.content if hasattr(generated_clauses, 'content') else generated_clauses

                        # Get summary from RunResponse
                        summary_content = summary_result.content if hasattr(summary_result, 'content') else summary_result

                        # Create contract data
                        contract_data = {
                            "pdf_name": pdf_path.name,
                            "contract_title": metadata_dict.get("contract_title"),
                            "contract_date": metadata_dict.get("contract_date"),
                            "parties_involved": metadata_dict.get("parties_involved", []),
                            "clauses": metadata_dict.get("clauses", []),
                            "summary": summary_content if isinstance(summary_content, str) else summary_content.summary if hasattr(summary_content, 'summary') else "",
                            "amounts": metadata_dict.get("amounts", []),
                            "confidence_score": 0.9  # Default confidence score
                        }

                        # Validate the contract data
                        validated_contract = Contract(**contract_data)

                        return ProcessingResponse(
                            status="success",
                            error=None,
                            document=validated_contract
                        )

                    except Exception as e:
                        logger.error(f"Failed to parse metadata content: {str(e)}")
                        return ProcessingResponse(
                            status="error",
                            document={"filename": pdf_path.name},
                            error=f"Failed to parse metadata content: {str(e)}"
                        )
                else:
                    # Handle non-string metadata content (original logic)
                    contract_data = {
                        "pdf_name": pdf_path.name,
                        "contract_title": metadata_content.contract_title,
                        "contract_date": metadata_content.contract_date,
                        "parties_involved": metadata_content.parties_involved,
                        "clauses": metadata_content.clauses,
                        "summary": summary_content.summary,
                        "amounts": metadata_content.amounts
                    }

                    validated_contract = Contract(**contract_data)

                    return ProcessingResponse(
                        status="success",
                        error=None,
                        document=validated_contract
                    )

            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                return ProcessingResponse(
                    status="error",
                    document={"filename": pdf_path.name},
                    error=f"Data validation failed: {str(e)}"
                )
#
#

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            return ProcessingResponse(
                status="error",
                document={"filename": pdf_path.name if 'pdf_path' in locals() else "unknown"},
                error=str(e)
            )