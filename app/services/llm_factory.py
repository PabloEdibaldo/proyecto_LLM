from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.services.metrics import TokenCostCallbackHandler

class LLMFactory:
    """Strategy pattern for dynamic model selection."""
    
    @staticmethod
    def get_model(query: str, purpose: str = "research"):
        """
        Dynamically select the model based on the query complexity and purpose.
        - purpose: 'research' (agent drafting) or 'evaluation' (agent reviewing)
        """
        callbacks = [TokenCostCallbackHandler()]
        
        # Determine model
        if purpose == "evaluation":
            # Evaluator gets a smarter, more capable model
            model_name = "gpt-4o"
        else:
            # Researcher gets a cheaper model unless query is very long
            if len(query) > 500:
                model_name = "gpt-4o"
            else:
                model_name = "gpt-4o-mini"
                
        return ChatOpenAI(
            model=model_name,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY or "dummy",
            callbacks=callbacks
        )
