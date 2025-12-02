# Technical Architecture & AI Components

This document details the specific AI/ML technologies used in the Business Consultant Graph project, where they are implemented in the codebase, and how they function together.

## 1. Prompting 🎯
**Location:** `src/business_consultant_graph.py`
- **System Prompts:** Lines 96-120 (Persona definitions for Dan, Sam, Alex)
- **Prompt Construction:** Lines 261-298 (`build_coach_prompt_with_rag`)

**Usage:** 
We use **Persona-Based Prompting** to give each AI coach a distinct personality and expertise area (e.g., Dan Martell = Systems, Alex Hormozi = Offers/Leads). Prompts are dynamically constructed to include the user's business description, goal, and retrieved evidence.

## 2. Structured Output 📋
**Location:** `src/business_consultant_graph.py`
- **Schema Definition:** Lines 122-151 (`COACH_JSON_SCHEMA`)
- **Parsing Logic:** Lines 156-192 (`safe_parse_json`)
- **Validation:** Lines 194-227 (`validate_and_fix_json`)

**Usage:**
We enforce a strict **JSON Schema** for all LLM responses. This ensures that every coach returns data in a predictable format (Bottlenecks, Recommendations, KPIs) that can be programmatically merged and used to generate the final report. We use a "repair" mechanism to re-prompt the LLM if it generates invalid JSON.

## 3. Semantic Search 🔍
**Location:** 
- `scripts/ingest_chroma.py` (Embedding generation)
- `src/business_consultant_graph.py` (Retrieval logic)

**Usage:**
We use **OpenAI Embeddings** to convert text chunks from coach knowledge bases into vector representations. These are stored in **ChromaDB**. When a user asks for advice, we convert their business description into a query vector and find the most semantically similar advice from our knowledge base, even if the keywords don't match exactly.

## 4. Retrieval Augmented Generation (RAG) 🧠
**Location:** `src/business_consultant_graph.py`
- **Retrieval:** Lines 63-92 (`get_top_k_evidence_with_meta`)
- **Augmentation:** Lines 261-298 (`build_coach_prompt_with_rag`)

**Usage:**
RAG combines the retrieval of relevant documents with the generation capabilities of the LLM.
1. **Retrieve:** Find top-3 relevant advice chunks for the specific business problem.
2. **Augment:** Inject these chunks into the LLM's context window.
3. **Generate:** The LLM answers using its general knowledge + the specific retrieved evidence.

## 5. Tool Calling & MCP 🛠️
**Location:** `src/business_consultant_graph.py`
- **Tool Stub:** Lines 23-30 (`retrieval_tool`)

**Usage:**
The architecture is designed to support **Model Context Protocol (MCP)** style tool calling. The `retrieval_tool` function encapsulates the RAG logic, making it possible to expose this as a tool that an agent could autonomously decide to call. Currently, it is called deterministically within the graph nodes.

## 6. LangGraph: State, Nodes, Graph 🕸️
**Location:** `src/business_consultant_graph.py`
- **State:** Lines 32-40 (`BizState`)
- **Nodes:** Lines 300-332 (Coach nodes, Merge node)
- **Graph:** Lines 400-423 (`build_graph`)

**Usage:**
**LangGraph** orchestrates the entire workflow.
- **State:** A shared dictionary (`BizState`) that holds the data as it flows through the system.
- **Nodes:** Functions that perform work (e.g., `dan_node` calls the LLM).
- **Graph:** Defines the control flow. We use a **Parallel Flow** where all 3 coaches run simultaneously, followed by a **Merge Node** that consolidates their insights.

---

## Visual Workflow Diagram

```mermaid
graph TD
    User[User Input] -->|Business Desc, Goal, KPIs| State[LangGraph State (BizState)]
    
    subgraph "Parallel Execution (Coach Nodes)"
        State --> Dan[Dan Martell Node]
        State --> Sam[Sam Ovens Node]
        State --> Alex[Alex Hormozi Node]
        
        subgraph "RAG Pipeline (Inside Each Node)"
            Dan -->|Query| Chroma[(ChromaDB)]
            Sam -->|Query| Chroma
            Alex -->|Query| Chroma
            
            Chroma -->|Retrieved Evidence| Prompt[Prompt Construction]
            Prompt -->|Context + Evidence| LLM[LLM Generation]
            LLM -->|JSON Output| Validate[Structured Validation]
        end
    end
    
    Validate -->|Analysis + Provenance| Merge[Merge Node]
    
    Merge -->|Consolidated Data| FinalReport[Final Report JSON]
    FinalReport -->|Generate| DOCX[DOCX Document]
    
    style User fill:#f9f,stroke:#333,stroke-width:2px
    style State fill:#bbf,stroke:#333,stroke-width:2px
    style Merge fill:#bfb,stroke:#333,stroke-width:2px
    style DOCX fill:#ff9,stroke:#333,stroke-width:2px
```

### Text-Based Flow Representation

```text
User Input (business description, goal, KPIs)
    ↓
┌─────────────────────────────────────────┐
│  LangGraph State (BizState)             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Parallel Execution (3 Coach Nodes)     │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Dan Node │  │ Sam Node │  │Alex Node│ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │             │             │      │
│    [RAG]         [RAG]         [RAG]     │ ← Retrieval Augmented Generation
│       │             │             │      │
│  Semantic Search → ChromaDB ←───────────┘ │ ← Semantic Search
│       │             │             │      │
│  [Prompting] [Prompting] [Prompting]    │ ← Prompting
│       │             │             │      │
│  [Structured] [Structured] [Structured] │ ← Structured Output
│       ↓             ↓             ↓      │
└───────┼─────────────┼─────────────┼──────┘
        └─────────────┴─────────────┘
                      ↓
        ┌─────────────────────────┐
        │   Merge Node            │
        │  (Combines all analyses)│
        └─────────────┬───────────┘
                      ↓
        ┌─────────────────────────┐
        │   Final Report          │
        │   (JSON + DOCX)         │
        └─────────────────────────┘
```
