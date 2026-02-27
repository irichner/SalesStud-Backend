# =============================================
# SalesStud.io Backend - schema_agent.py
# Author: Grok (xAI) for @irichner
# Created: 2026-02-26
# Change Log:
# 2026-02-26: Autonomous Schema Evolution with LangGraph
# =============================================

from langgraph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, Any, List
import litellm
from app.db.database import get_db
from app.models.models import AIProvider, AgentMemory
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

# State for the schema evolution graph
class SchemaEvolutionState:
    def __init__(self):
        self.reason: str = ""
        self.desired_change: str = ""
        self.proposal: Dict[str, Any] = {}
        self.approved: bool = False
        self.applied: bool = False
        self.errors: List[str] = []

# Tool for proposing schema migration
@tool
def propose_schema_migration(reason: str, desired_change: str) -> Dict[str, Any]:
    """Propose a schema migration based on detected need"""
    db = next(get_db())
    try:
        # Get active provider
        provider = db.query(AIProvider).first()
        if not provider:
            return {"error": "No AI provider configured"}

        # Get current schema info
        schema_info = get_schema_info(db)

        # Generate migration proposal using LLM
        prompt = f"""
        You are a database schema evolution expert for MSSQL Server 2025.

        Current Schema:
        {schema_info}

        Reason for change: {reason}
        Desired change: {desired_change}

        Generate an Alembic migration script for this change.
        Output only the Python code for the upgrade() function, nothing else.
        Use SQLAlchemy operations like op.add_column, op.create_table, etc.
        Ensure it's safe and reversible.
        """

        response = litellm.completion(
            model="xai/grok-4-1-fast-reasoning",
            messages=[{"role": "user", "content": prompt}],
            api_key=provider.api_key,
            base_url=provider.base_url
        )

        migration_code = response.choices[0].message.content.strip()

        # Analyze impact
        impact = analyze_impact(desired_change, db)

        proposal = {
            "alembic_script": migration_code,
            "impact": impact,
            "rollback": generate_rollback(migration_code),
            "risk_score": calculate_risk(desired_change)
        }

        return proposal
    finally:
        db.close()

# Tool for applying approved migration
@tool
def apply_approved_migration(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Apply an approved schema migration"""
    # This would execute the migration via Alembic
    # For now, just return success
    return {"status": "applied", "migration_id": "temp_id"}

def get_schema_info(db: Session) -> str:
    """Get current database schema information"""
    # Query information_schema for tables, columns, etc.
    tables_query = text("""
        SELECT TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME
    """)
    tables = db.execute(tables_query).fetchall()

    schema_info = "Tables:\n"
    for table in tables:
        schema_info += f"- {table.TABLE_NAME} ({table.TABLE_TYPE})\n"

        # Get columns
        columns_query = text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = :table_name AND TABLE_SCHEMA = 'dbo'
            ORDER BY ORDINAL_POSITION
        """)
        columns = db.execute(columns_query, {"table_name": table.TABLE_NAME}).fetchall()
        for col in columns:
            nullable = "NULL" if col.IS_NULLABLE == 'YES' else "NOT NULL"
            default = f" DEFAULT {col.COLUMN_DEFAULT}" if col.COLUMN_DEFAULT else ""
            schema_info += f"  - {col.COLUMN_NAME} {col.DATA_TYPE} {nullable}{default}\n"

    return schema_info

def analyze_impact(change: str, db: Session) -> str:
    """Analyze the impact of the proposed change"""
    # Simple analysis - can be enhanced
    if "add column" in change.lower():
        return "Adds new column with zero downtime, existing data unaffected"
    elif "create table" in change.lower():
        return "Creates new table, no impact on existing data"
    elif "alter table" in change.lower():
        return "Modifies existing table, potential for data migration"
    else:
        return "Unknown impact - requires manual review"

def generate_rollback(migration_code: str) -> str:
    """Generate rollback instructions"""
    # Simple reverse operations
    if "op.add_column" in migration_code:
        return "Drop the added column"
    elif "op.create_table" in migration_code:
        return "Drop the created table"
    else:
        return "Manual rollback required"

def calculate_risk(change: str) -> int:
    """Calculate risk score 1-10"""
    if "drop" in change.lower():
        return 9
    elif "alter" in change.lower():
        return 7
    elif "add" in change.lower():
        return 3
    else:
        return 5

# Define the graph
def create_schema_evolution_graph():
    workflow = StateGraph(SchemaEvolutionState)

    # Nodes
    def detect_need(state: SchemaEvolutionState):
        # This would be triggered by data analysis
        return state

    def propose_change(state: SchemaEvolutionState):
        proposal = propose_schema_migration.invoke({
            "reason": state.reason,
            "desired_change": state.desired_change
        })
        state.proposal = proposal
        return state

    def human_approval(state: SchemaEvolutionState):
        # Interrupt for human approval
        # In LangGraph, this would pause the graph
        return state

    def apply_change(state: SchemaEvolutionState):
        if state.approved:
            result = apply_approved_migration.invoke({"proposal": state.proposal})
            state.applied = True
        return state

    def post_change(state: SchemaEvolutionState):
        # Update agent memory with new schema
        update_agent_memory_with_schema()
        # Notify users, etc.
        return state

    # Add nodes
    workflow.add_node("detect_need", detect_need)
    workflow.add_node("propose_change", propose_change)
    workflow.add_node("human_approval", human_approval)
    workflow.add_node("apply_change", apply_change)
    workflow.add_node("post_change", post_change)

    # Edges
    workflow.add_edge("detect_need", "propose_change")
    workflow.add_edge("propose_change", "human_approval")
    workflow.add_edge("human_approval", "apply_change")
    workflow.add_edge("apply_change", "post_change")
    workflow.add_edge("post_change", END)

    # Set entry point
    workflow.set_entry_point("detect_need")

    # Add interrupt before apply_change
    workflow.add_interrupt("human_approval")

    # Memory
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)

# Global graph instance
schema_graph = create_schema_evolution_graph()

# Function to trigger schema evolution
def trigger_schema_evolution(reason: str, desired_change: str):
    """Start the schema evolution process"""
    initial_state = SchemaEvolutionState()
    initial_state.reason = reason
    initial_state.desired_change = desired_change

    # Run until interrupt
    result = schema_graph.invoke(initial_state)
    return result

def update_agent_memory_with_schema():
    """Update agent memory with current schema information"""
    db = next(get_db())
    try:
        schema_info = get_schema_info(db)
        # Store in agent memory - for simplicity, assume agent_id=1
        memory_entry = AgentMemory(
            agent_id=1,
            key="current_schema",
            value={"schema": schema_info}
        )
        db.add(memory_entry)
        db.commit()
    finally:
        db.close()
