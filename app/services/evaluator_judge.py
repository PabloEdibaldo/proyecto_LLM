from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.api.models import EvaluationCase
from app.agents.graph import app_graph
from app.core.logger import logger
import asyncio

class EvaluatorJudge:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert evaluator. Compare the generated answer to the expected answer. "
                       "Score the generated answer on a scale of 0 to 1 based on how well it matches the facts and intent of the expected answer. "
                       "Output ONLY the numeric score (e.g. 0.8) and nothing else."),
            ("user", "Query: {query}\n\nExpected Answer: {expected_answer}\n\nGenerated Answer: {generated_answer}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def evaluate_case(self, case: EvaluationCase) -> dict:
        logger.info(f"Evaluating query: {case.query}")
        
        # Run graph to get generated answer
        try:
            # We can use invoke or ainvoke, app_graph is currently sync
            final_state = await asyncio.to_thread(app_graph.invoke, {"query": case.query})
            generated_answer = final_state.get("final_response", "")
        except Exception as e:
            logger.error(f"Error generating answer for evaluation: {e}")
            generated_answer = ""
            
        score = 0.0
        if generated_answer:
            try:
                score_str = await self.chain.ainvoke({
                    "query": case.query,
                    "expected_answer": case.expected_answer,
                    "generated_answer": generated_answer
                })
                score = float(score_str.strip())
            except ValueError:
                logger.warning(f"Could not parse score from LLM: {score_str}")
            except Exception as e:
                logger.error(f"Error calling LLM judge: {e}")

        return {
            "query": case.query,
            "expected": case.expected_answer,
            "generated": generated_answer,
            "score": min(max(score, 0.0), 1.0) # Clamp between 0 and 1
        }

    async def evaluate_batch(self, cases: list[EvaluationCase]) -> dict:
        results = []
        for case in cases:
            res = await self.evaluate_case(case)
            results.append(res)
            
        avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
        
        return {
            "average_score": avg_score,
            "results": results
        }

evaluator_judge = EvaluatorJudge()
