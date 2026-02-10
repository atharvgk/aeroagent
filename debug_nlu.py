from agent_llm import AgentLLM
import json

agent = AgentLLM()
query = "give pilots with dgca certificate"

import sys

with open("nlu_result.txt", "w") as f:
    sys.stdout = f
    print(f"Query: {query}")

    # 1. Test NLU
    tool_call = agent._nlu_layer(query)
    print(f"NLU Tool Call: {tool_call}")

    # 2. Test Execution
    if tool_call:
        result = agent._execute_tool(tool_call)
        print(f"Tool Result Type: {type(result)}")
        if isinstance(result, list) and len(result) > 0:
            print(f"First Pilot: {result[0]}")
        else:
            print(f"Result: {result}")
