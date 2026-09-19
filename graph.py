import json
import boto3

from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import (
    AnyMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from langchain_core.tools import tool
from langchain_aws import ChatBedrockConverse

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver


# =============================================================
# Multi-Agent LangGraph Application
#
# 1. Orchestrator Agent
#    - Uses Bedrock model
#    - Determines user intent
#    - Routes to worker
#
# 2. Recommendation Node
#    - Calls recommend-product Lambda
#
# 3. Order Management Node
#    - Calls place-orders Lambda
#
# 4. Order Tracking Node
#    - Calls order-status Lambda
#
# 5. AWS Lambda Handler
#    - Entry point for containerized Lambda deployment
# =============================================================


# =============================================================
# 1. AWS CLIENT
# =============================================================

lambda_client = boto3.client(
    "lambda",
    region_name="us-east-2"
)


# =============================================================
# 2. TOOLS
# =============================================================

@tool
def recommend_products(prompt: str) -> dict:
    """
    Suggest products for a shopper based on what they ask for.
    """

    response = lambda_client.invoke(
        FunctionName="recommend-product",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "prompt": prompt
        }).encode("utf-8"),
    )

    payload = json.loads(
        response["Payload"].read()
    )

    return payload


@tool
def place_order(product_id: str, quantity: int) -> dict:
    """
    Place an order for a product with the requested quantity.
    """

    response = lambda_client.invoke(
        FunctionName="place-orders",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "product_id": product_id,
            "quantity": quantity
        }).encode("utf-8"),
    )

    payload = json.loads(
        response["Payload"].read()
    )

    return payload


@tool
def get_order(order_id: str) -> dict:
    """
    Look up the status of an existing order by order ID.
    """

    response = lambda_client.invoke(
        FunctionName="order-status",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "order-id": order_id
        }).encode("utf-8"),
    )

    payload = json.loads(
        response["Payload"].read()
    )

    return payload


# =============================================================
# 3. MODEL
# =============================================================

model = ChatBedrockConverse(
    model="amazon.nova-lite-v1:0",
    region_name="us-east-2",
    temperature=0,
)


# =============================================================
# 4. STATE
# =============================================================

class State(TypedDict, total=False):
    messages: Annotated[
        list[AnyMessage],
        add_messages
    ]

    intent: str
    product_id: str
    quantity: int
    order_id: str


# =============================================================
# 5. ORCHESTRATOR NODE
# =============================================================

def orchestrator(state: State) -> dict:

    system_prompt = """
You are the orchestrator for an online shopping assistant.

Determine the user's intent.

Allowed intents:
- recommend
- order
- track

Return ONLY valid JSON using this exact structure:

{
  "intent": "recommend",
  "order_id": "",
  "product_id": "",
  "quantity": 1
}

Rules:

1. If the user wants product suggestions:
   intent = "recommend"

2. If the user wants to place an order:
   intent = "order"
   Extract product_id and quantity.

3. If the user wants to track or check an order:
   intent = "track"
   Extract order_id.

4. Do not include markdown.
5. Do not include explanations.
6. Return JSON only.
"""

    response = model.invoke(
        [
            SystemMessage(
                content=system_prompt
            ),
            *state["messages"],
        ]
    )

    try:
        parsed = json.loads(
            response.content
        )

    except json.JSONDecodeError:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I could not determine "
                        "the request type."
                    )
                )
            ],
            "intent": "recommend",
            "order_id": "",
            "product_id": "",
            "quantity": 1,
        }

    return {
        "intent": parsed.get(
            "intent",
            "recommend"
        ),
        "order_id": parsed.get(
            "order_id",
            ""
        ),
        "product_id": parsed.get(
            "product_id",
            ""
        ),
        "quantity": parsed.get(
            "quantity",
            1
        ),
    }


# =============================================================
# 6. ROUTER
# =============================================================

def route_to_worker(state: State) -> str:

    intent = state.get(
        "intent",
        "recommend"
    )

    if intent == "track":
        return "order_tracking"

    if intent == "order":
        return "order_management"

    return "recommendation"


# =============================================================
# 7. RECOMMENDATION NODE
# =============================================================

def recommendation_node(state: State) -> dict:

    user_message = (
        state["messages"][-1].content
    )

    result = recommend_products.invoke({
        "prompt": user_message
    })

    answer = result.get(
        "answer",
        "I could not find a recommendation."
    )

    return {
        "messages": [
            AIMessage(
                content=answer
            )
        ]
    }


# =============================================================
# 8. ORDER MANAGEMENT NODE
# =============================================================

def order_management_node(state: State) -> dict:

    product_id = state.get(
        "product_id",
        ""
    )

    quantity = state.get(
        "quantity",
        1
    )

    if not product_id:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I need a product_id "
                        "before I can place the order."
                    )
                )
            ]
        }

    result = place_order.invoke({
        "product_id": product_id,
        "quantity": quantity,
    })

    if "error" in result:
        return {
            "messages": [
                AIMessage(
                    content=result["error"]
                )
            ]
        }

    order_id = result.get(
        "order-id"
    )

    status = result.get(
        "status",
        "Pending"
    )

    if not order_id:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Unable to place order. "
                        f"Response: {result}"
                    )
                )
            ]
        }

    return {
        "messages": [
            AIMessage(
                content=(
                    "Order placed successfully.\n"
                    f"Order ID: {order_id}\n"
                    f"Status: {status}"
                )
            )
        ]
    }


# =============================================================
# 9. ORDER TRACKING NODE
# =============================================================

def order_tracking_node(state: State) -> dict:

    order_id = state.get(
        "order_id",
        ""
    )

    if not order_id:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Please provide an order ID."
                    )
                )
            ]
        }

    result = get_order.invoke({
        "order_id": order_id
    })

    if "error" in result:
        return {
            "messages": [
                AIMessage(
                    content=result["error"]
                )
            ]
        }

    return {
        "messages": [
            AIMessage(
                content=(
                    f"Order ID: "
                    f"{result.get('order-id')}\n"
                    f"Status: "
                    f"{result.get('order-status')}\n"
                    f"Quantity: "
                    f"{result.get('quantity')}"
                )
            )
        ]
    }


# =============================================================
# 10. GRAPH
# =============================================================

builder = StateGraph(State)

builder.add_node(
    "orchestrator",
    orchestrator
)

builder.add_node(
    "recommendation",
    recommendation_node
)

builder.add_node(
    "order_management",
    order_management_node
)

builder.add_node(
    "order_tracking",
    order_tracking_node
)


builder.add_edge(
    START,
    "orchestrator"
)

builder.add_conditional_edges(
    "orchestrator",
    route_to_worker,
    {
        "recommendation": "recommendation",
        "order_management": "order_management",
        "order_tracking": "order_tracking",
    }
)

builder.add_edge(
    "recommendation",
    END
)

builder.add_edge(
    "order_management",
    END
)

builder.add_edge(
    "order_tracking",
    END
)


# =============================================================
# 11. COMPILE
# =============================================================

memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory
)


# =============================================================
# 12. AWS LAMBDA HANDLER
# =============================================================

def lambda_handler(event, context):
    """
    AWS Lambda entry point.

    Expected event:
    {
        "message": "Track order <order-id>"
    }
    """

    try:
        # -----------------------------------------------------
        # 1. Read input
        # -----------------------------------------------------

        user_input = event.get(
            "message",
            ""
        ).strip()

        if not user_input:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "message is required"
                })
            }

        # -----------------------------------------------------
        # 2. Create request-specific thread ID
        # -----------------------------------------------------

        request_id = getattr(
            context,
            "aws_request_id",
            "lambda-request"
        )

        config = {
            "configurable": {
                "thread_id": request_id
            }
        }

        # -----------------------------------------------------
        # 3. Run LangGraph
        # -----------------------------------------------------

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=user_input
                    )
                ]
            },
            config=config
        )

        # -----------------------------------------------------
        # 4. Extract final response
        # -----------------------------------------------------

        answer = (
            result["messages"][-1].content
        )

        # -----------------------------------------------------
        # 5. Return response
        # -----------------------------------------------------

        return {
            "statusCode": 200,
            "body": json.dumps({
                "answer": answer
            })
        }

    except Exception as error:

        print(
            f"Lambda execution error: {error}"
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": (
                    "Unable to process request."
                )
            })
        }


# =============================================================
# 13. LOCAL TEST
# =============================================================

if __name__ == "__main__":

    config = {
        "configurable": {
            "thread_id": "demo"
        }
    }

    user_input = (
        "Can you track order "
        "ac34e1b3-eb0b-4250-ba7e-2d2f4cde576f?"
    )

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ]
        },
        config=config
    )

    print(
        "\nFinal Answer:\n"
    )

    print(
        result["messages"][-1].content
    )