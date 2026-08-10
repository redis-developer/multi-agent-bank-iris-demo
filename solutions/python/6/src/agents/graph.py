"""The multi-agent LangGraph: one supervisor, five specialists.

═══════════════════════════════════════════════════════════════════════
SECTION 4 - MULTI-AGENT: solved.
═══════════════════════════════════════════════════════════════════════

                       START
                         │
                    supervisor          ← trusts the semantic route when
                         │                present, else asks the LLM
      ┌─────────┬────────┼─────────┬───────────┐
  servicing  loan_docs  noc      sales      journey
      └─────────┴────────┴─────────┴───────────┘
                         │
                        END
"""

import json

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from src.agents import personas
from src.retrieval.rag import LoanDocsRetriever

MAX_TOOL_ROUNDS = 6

TOOL_AGENTS = [personas.SERVICING, personas.NOC, personas.SALES,
               personas.JOURNEY]
AGENT_NAMES = [p["name"] for p in personas.ALL_AGENTS]


class BotState(MessagesState):
    """Graph state shared by the supervisor and every specialist."""
    customer_id: str
    route: str | None
    agent: str
    memories: list[str]
    citations: list[dict]


def _system_prompt(persona: dict, state: BotState) -> str:
    """Persona prompt + the verified customer + long-term memories."""
    prompt = (persona["prompt"]
              + f"\nVerified customer_id: {state['customer_id']}")
    memories = state.get("memories") or []
    if memories:
        prompt += ("\nKnown about this customer from earlier conversations:\n- "
                   + "\n- ".join(memories))
    return prompt


def make_tool_agent_node(persona: dict, llm):
    """A specialist that reasons with tools: think → call tool → observe →
    answer. This hand-rolled loop is exactly what agent frameworks automate."""
    llm_with_tools = llm.bind_tools(persona["tools"])
    tools_by_name = {t.name: t for t in persona["tools"]}

    def node(state: BotState):
        messages = ([SystemMessage(content=_system_prompt(persona, state))]
                    + list(state["messages"]))
        for _ in range(MAX_TOOL_ROUNDS):
            response = llm_with_tools.invoke(messages)
            if not response.tool_calls:
                return {"messages": [response], "agent": persona["name"],
                        "citations": []}
            messages.append(response)
            for call in response.tool_calls:
                result = tools_by_name[call["name"]].invoke(call["args"])
                messages.append(ToolMessage(content=str(result),
                                            tool_call_id=call["id"]))
        return {"messages": [AIMessage(content=(
                    "I couldn't complete that in one go — could you rephrase "
                    "or break the request into smaller steps?"))],
                "agent": persona["name"], "citations": []}

    return node


def make_loan_docs_node(llm, retriever: LoanDocsRetriever):
    """The RAG specialist from Section 3, now living inside the graph:
    retrieve → augment → generate, with citations."""

    def node(state: BotState):
        question = state["messages"][-1].content
        chunks = retriever.search(question)
        system = (_system_prompt(personas.LOAN_DOCS, state)
                  + "\n\nContext passages:\n"
                  + retriever.format_context(chunks))
        response = llm.invoke([SystemMessage(content=system)]
                              + list(state["messages"]))
        citations = [{"doc_title": c["doc_title"], "section": c["section"]}
                     for c in chunks]
        return {"messages": [response], "agent": "loan_docs",
                "citations": citations}

    return node


def make_supervisor_node(llm):
    """Decide which specialist handles this turn. The semantic route from
    Section 2 (cheap, no LLM) wins when present; otherwise the supervisor
    asks the LLM to pick from the agent descriptions."""
    catalog = "\n".join(f"- {p['name']}: {p['description']}"
                        for p in personas.ALL_AGENTS)

    def node(state: BotState):
        route = state.get("route")
        if route in AGENT_NAMES:
            return {"agent": route}
        decision = llm.invoke([
            SystemMessage(content=(
                "Pick the one agent best suited to the customer's message. "
                f"Agents:\n{catalog}\n"
                'Reply with JSON only: {"agent": "<name>"}')),
            state["messages"][-1],
        ])
        try:
            choice = json.loads(decision.content).get("agent", "")
        except (json.JSONDecodeError, AttributeError):
            choice = ""
        return {"agent": choice if choice in AGENT_NAMES else "servicing"}

    return node


def build_agent_graph(llm, retriever: LoanDocsRetriever):
    """Assemble and compile the supervisor graph."""
    supervisor = make_supervisor_node(llm)
    agent_nodes = {p["name"]: make_tool_agent_node(p, llm)
                   for p in TOOL_AGENTS}
    agent_nodes["loan_docs"] = make_loan_docs_node(llm, retriever)

    graph = StateGraph(BotState)
    graph.add_node("supervisor", supervisor)
    for name, node in agent_nodes.items():
        graph.add_node(name, node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state["agent"],
        {name: name for name in agent_nodes},
    )
    for name in agent_nodes:
        graph.add_edge(name, END)

    return graph.compile()
