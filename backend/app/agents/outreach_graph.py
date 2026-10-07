from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, List, Dict, Any, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the multi-agent workflow"""
    user_profile: Dict[str, Any]
    companies: Annotated[List[Dict[str, Any]], add_messages]
    current_company: Dict[str, Any]
    research_data: Dict[str, Any]
    outreach_strategy: Dict[str, Any]
    generated_email: Dict[str, str]
    messages: Annotated[List[Dict], add_messages]


class CompanyFinderAgent:
    """Agent for finding relevant companies"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
    
    async def run(self, state: AgentState) -> AgentState:
        """Find companies based on user profile"""
        user_profile = state["user_profile"]
        
        prompt = f"""Based on the following user profile, suggest {user_profile.get('num_companies', 10)} relevant companies.

User Profile:
- Role: {user_profile.get('role')}
- Experience: {user_profile.get('experience')} years
- Skills: {', '.join(user_profile.get('skills', []))}
- Location: {user_profile.get('location')}
- Salary Expectation: ${user_profile.get('salary', 'Not specified')}

For each company, provide:
1. Company Name
2. Website
3. Hiring Signal (e.g., "actively hiring", "possibly hiring", "unknown")
4. Brief reasoning

Format as JSON array with fields: name, website, hiring_signal, reasoning"""
        
        try:
            response = self.llm.invoke(prompt)
            # Parse response and extract companies
            companies = self._parse_companies(response.content)
            state["companies"] = companies
            logger.info(f"Found {len(companies)} companies")
        except Exception as e:
            logger.error(f"Error in CompanyFinderAgent: {e}")
            state["companies"] = []
        
        return state
    
    def _parse_companies(self, response_text: str) -> List[Dict]:
        """Parse companies from LLM response"""
        import json
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Error parsing companies: {e}")
        
        # Fallback: return empty list
        return []


class HiringClassifierAgent:
    """Agent for classifying company hiring status"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
    
    async def run(self, state: AgentState) -> AgentState:
        """Classify companies as actively hiring or not"""
        companies = state.get("companies", [])
        
        classified_companies = []
        
        for company in companies:
            hiring_signal = company.get("hiring_signal", "unknown").lower()
            
            if "active" in hiring_signal or "hiring" in hiring_signal:
                company["classification"] = "active"
            else:
                company["classification"] = "inactive"
            
            classified_companies.append(company)
        
        state["companies"] = classified_companies
        logger.info(f"Classified {len(classified_companies)} companies")
        
        return state


class CompanyResearchAgent:
    """Agent for researching companies"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, research_service):
        self.llm = llm
        self.research_service = research_service
    
    async def run(self, state: AgentState, company_index: int = 0) -> AgentState:
        """Research specific company"""
        companies = state.get("companies", [])
        
        if not companies or company_index >= len(companies):
            logger.warning("No companies to research")
            return state
        
        company = companies[company_index]
        
        try:
            # Extract company information
            company_info = await self.research_service.extract_company_info(
                company.get("name"),
                company.get("website")
            )
            
            # Check hiring signals
            hiring_check = await self.research_service.check_hiring_signals(
                company.get("website"),
                company.get("name")
            )
            
            # Summarize with LLM
            summary = await self._summarize_company(
                company.get("name"),
                company_info,
                hiring_check
            )
            
            state["research_data"] = {
                "company_info": company_info,
                "hiring_check": hiring_check,
                "summary": summary
            }
            
            logger.info(f"Researched company: {company.get('name')}")
        except Exception as e:
            logger.error(f"Error researching company: {e}")
            state["research_data"] = {"error": str(e)}
        
        return state
    
    async def _summarize_company(
        self,
        company_name: str,
        company_info: Dict,
        hiring_check: Dict
    ) -> str:
        """Summarize company using LLM"""
        prompt = f"""Based on the following information, provide a 2-3 sentence summary of {company_name}.

Information:
- Title: {company_info.get('title')}
- Description: {company_info.get('description')}
- Preview: {company_info.get('preview')}
- Hiring Status: {hiring_check.get('hiring_signal')}

Summary:"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error summarizing company: {e}")
            return company_info.get("description", "No summary available")


class OutreachStrategyAgent:
    """Agent for deciding outreach strategy"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
    
    async def run(self, state: AgentState) -> AgentState:
        """Decide outreach strategy"""
        research_data = state.get("research_data", {})
        company = state.get("current_company", {})
        
        prompt = f"""Based on the company information, decide the best outreach method.

Company: {company.get('name')}
Website: {company.get('website')}
Research: {research_data.get('summary', 'No research data')}

Choose one:
1. "email" - if you can find company email or support email
2. "linkedin" - if you should search for hiring manager on LinkedIn
3. "apply" - if there's an active careers page

Respond with JSON: {{"method": "...", "instructions": "..."}}"""
        
        try:
            response = self.llm.invoke(prompt)
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                strategy = json.loads(json_match.group())
            else:
                strategy = {"method": "linkedin", "instructions": "Search for hiring manager"}
            
            state["outreach_strategy"] = strategy
            logger.info(f"Strategy for {company.get('name')}: {strategy.get('method')}")
        except Exception as e:
            logger.error(f"Error determining strategy: {e}")
            state["outreach_strategy"] = {"method": "linkedin", "instructions": "Default strategy"}
        
        return state


def create_agent_graph(
    company_finder: CompanyFinderAgent,
    hiring_classifier: HiringClassifierAgent,
    research_agent: CompanyResearchAgent,
    strategy_agent: OutreachStrategyAgent
):
    """Create LangGraph workflow"""
    
    workflow = StateGraph(AgentState)
    
    # Define nodes
    workflow.add_node("company_finder", lambda state: company_finder.run(state))
    workflow.add_node("hiring_classifier", lambda state: hiring_classifier.run(state))
    workflow.add_node("research_agent", lambda state: research_agent.run(state))
    workflow.add_node("strategy_agent", lambda state: strategy_agent.run(state))
    
    # Define edges
    workflow.add_edge(START, "company_finder")
    workflow.add_edge("company_finder", "hiring_classifier")
    workflow.add_edge("hiring_classifier", "research_agent")
    workflow.add_edge("research_agent", "strategy_agent")
    workflow.add_edge("strategy_agent", END)
    
    return workflow.compile()
