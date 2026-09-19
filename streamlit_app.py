# =============================================================
# Streamlit shopping UI — AnyCart
#   - Category image gallery
#   - Product cards
#   - Chat window
#   - Talks to deployed LangGraph Lambda
#
# Run:
# uv run streamlit run ui/streamlit_app.py
# =============================================================

import os
import json
import re as _re
import ast as _ast

import boto3
import streamlit as st

from catalog import (
    PRODUCTS,
    FEATURED_PRODUCTS,
    format_price,
    all_categories,
)


# =============================================================
# Configuration
# =============================================================

IMG_DIR = os.path.join(
    os.path.dirname(__file__),
    "images",
)


LAMBDA_FUNCTION_NAME = "eCommernce-app"

AWS_REGION = "us-east-2"


# =============================================================
# Streamlit Page Configuration
# =============================================================

st.set_page_config(
    page_title="AnyCart",
    page_icon="🛒",
    layout="wide",
)


# =============================================================
# AWS Lambda Client
# =============================================================

lambda_client = boto3.client(
    "lambda",
    region_name=AWS_REGION,
)


# =============================================================
# Agent Integration
# =============================================================

def assistant_reply(text: str) -> str:
    """
    Invoke the deployed LangGraph Lambda function.
    """

    try:

        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "message": text
                }
            ).encode("utf-8"),
        )

        payload = json.loads(
            response["Payload"].read()
        )

        # -----------------------------------------
        # Lambda execution failure
        # -----------------------------------------

        if "FunctionError" in response:
            return (
                "Lambda execution failed:\n\n"
                f"{payload}"
            )

        # -----------------------------------------
        # Expected Lambda response
        #
        # {
        #   "statusCode": 200,
        #   "body": "{\"answer\": \"...\"}"
        # }
        # -----------------------------------------

        if isinstance(payload, dict):

            if "body" in payload:

                body = payload["body"]

                if isinstance(body, str):

                    try:
                        body = json.loads(body)

                    except json.JSONDecodeError:
                        return body

                status_code = payload.get(
                    "statusCode",
                    200,
                )

                if status_code != 200:

                    return (
                        "Error: "
                        + body.get(
                            "error",
                            "Request failed.",
                        )
                    )

                return body.get(
                    "answer",
                    "No answer returned.",
                )

            # -----------------------------------------
            # Direct response fallback
            # -----------------------------------------

            if "answer" in payload:
                return payload["answer"]

            if "response" in payload:
                return payload["response"]

            if "error" in payload:
                return (
                    f"Error: {payload['error']}"
                )

        return str(payload)

    except Exception as error:

        return (
            "Unable to contact the shopping "
            f"assistant.\n\n{error}"
        )


# =============================================================
# Custom CSS
# =============================================================

st.markdown(
    """
    <style>

      @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap'
      );

      html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
      }

      /* Hero banner */
      .hero-banner {
        background:
          linear-gradient(
            135deg,
            #232F3E 0%,
            #37475A 50%,
            #FF9900 100%
          );

        border-radius: 20px;
        padding: 36px 44px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
      }

      .hero-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: rgba(255,153,0,0.15);
        border-radius: 50%;
      }

      .hero-title {
        font-size: 42px;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
      }

      .hero-sub {
        color: #FFE0B2;
        font-size: 16px;
        margin-top: 0;
        opacity: 0.9;
      }

      /* Section headers */
      .category-header {
        font-size: 22px;
        font-weight: 700;
        color: #232F3E;
        margin-bottom: 16px;
      }

      /* Product cards */
      .prod-card {
        border: none;
        border-radius: 16px;
        padding: 22px;
        background: #FFFFFF;
        box-shadow:
          0 2px 8px rgba(0,0,0,0.06),
          0 1px 3px rgba(0,0,0,0.04);

        height: 280px;
        display: flex;
        flex-direction: column;

        transition:
          transform 0.2s ease,
          box-shadow 0.2s ease;

        border: 1px solid #F0F2F5;
      }

      .prod-card:hover {
        transform: translateY(-6px);

        box-shadow:
          0 12px 32px rgba(0,0,0,0.1);

        border-color: #FF9900;
      }

      .prod-id {
        background:
          linear-gradient(
            135deg,
            #FF9900,
            #FFB84D
          );

        color: #FFFFFF;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 10px;
      }

      .prod-name {
        font-weight: 700;
        color: #1B2638;
        font-size: 17px;
        margin: 4px 0;
        line-height: 1.3;
      }

      .prod-category {
        color: #7A8695;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
        font-weight: 600;
      }

      .prod-price {
        color: #232F3E;
        font-weight: 800;
        font-size: 22px;
      }

      .prod-desc {
        color: #5B6B7F;
        font-size: 13px;
        margin-top: auto;
        padding-top: 10px;
        line-height: 1.5;
      }

      /* Category buttons */
      .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: 1px solid #E0E4EA;
        transition: all 0.2s ease;
      }

      .stButton > button:hover {
        background: #FF9900;
        color: #FFFFFF;
        border-color: #FF9900;
      }

      /* Sidebar */
      [data-testid="stSidebar"] {
        background:
          linear-gradient(
            180deg,
            #232F3E 0%,
            #1A2433 100%
          );
      }

      [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
      }

      [data-testid="stSidebar"]
      .stRadio label {
        color: #FFE0B2 !important;
      }

      [data-testid="stSidebar"] hr {
        border-color:
          rgba(255,255,255,0.1);
      }

      /* Chat area */
      .chat-header {
        font-size: 20px;
        font-weight: 700;
        color: #232F3E;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 2px solid #FF9900;
        display: inline-block;
      }

      [data-testid="stChatInput"] {
        border-radius: 12px;
        border: 1px solid #E0E4EA;
        box-shadow:
          0 2px 8px rgba(0,0,0,0.04);

        transition: all 0.2s ease;
      }

      [data-testid="stChatInput"]:
      focus-within {
        border-color: #FF9900;

        box-shadow:
          0 0 0 3px
          rgba(255,153,0,0.12);
      }

      [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 12px 16px;
      }

      hr {
        border: none;
        border-top:
          1px solid #F0F2F5;

        margin: 20px 0;
      }

      #MainMenu {
        visibility: hidden;
      }

      footer {
        visibility: hidden;
      }

    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================
# Session State
# =============================================================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hey! I'm your AnyCart shopping "
                "assistant. I can recommend products, "
                "place orders, or track existing ones. "
                "How can I help?"
            ),
        }
    ]


if "category" not in st.session_state:
    st.session_state.category = "All"


# =============================================================
# Sidebar
# =============================================================

with st.sidebar:

    st.markdown("## 🛒 AnyCart")

    st.caption(
        "AI-powered multi-agent shopping"
    )

    st.markdown("---")

    cats = [
        "All"
    ] + all_categories()

    st.session_state.category = st.radio(
        "Browse categories",
        cats,
        index=cats.index(
            st.session_state.category
        ),
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    col1.metric(
        "Featured",
        len(FEATURED_PRODUCTS),
    )

    col2.metric(
        "Catalog",
        len(PRODUCTS),
    )

    st.markdown("---")

    st.markdown(
        "**Powered by**"
    )

    st.markdown(
        "Amazon Bedrock | "
        "LangGraph | "
        "DynamoDB"
    )


# =============================================================
# Hero Banner
# =============================================================

st.markdown(
    """
    <div class="hero-banner">

      <div class="hero-title">
        🛒 AnyCart
      </div>

      <div class="hero-sub">
        Your AI-powered shopping experience —
        browse, discover, and order with a
        conversational agent.
      </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================
# Main Layout
# =============================================================

left, right = st.columns(
    [2, 1],
    gap="large",
)


# =============================================================
# Product Catalog
# =============================================================

with left:

    st.markdown(
        '<div class="category-header">'
        'Shop by Category'
        '</div>',
        unsafe_allow_html=True,
    )

    cat_list = all_categories()

    cols = st.columns(
        len(cat_list)
    )

    for col, cat in zip(
        cols,
        cat_list,
    ):

        with col:

            img_path = os.path.join(
                IMG_DIR,
                f"{cat.lower()}.png",
            )

            if os.path.exists(
                img_path
            ):

                st.image(
                    img_path,
                    width="stretch",
                )

            if st.button(
                cat,
                key=f"cat_{cat}",
                width="stretch",
            ):

                st.session_state.category = cat

                st.rerun()

    st.markdown("---")


    # =========================================================
    # Featured Products
    # =========================================================

    st.markdown(
        '<div class="category-header">'
        'Featured Picks'
        '</div>',
        unsafe_allow_html=True,
    )

    per_row = 3

    shown = FEATURED_PRODUCTS

    for i in range(
        0,
        len(shown),
        per_row,
    ):

        row = st.columns(
            per_row
        )

        for col, product in zip(
            row,
            shown[i:i + per_row],
        ):

            with col:

                st.markdown(
                    f"""
                    <div class="prod-card">

                      <span class="prod-id">
                        {product['product_id']}
                      </span>

                      <div class="prod-name">
                        {product['name']}
                      </div>

                      <div class="prod-category">
                        {product['category']}
                      </div>

                      <div class="prod-price">
                        {format_price(product['price'])}
                      </div>

                      <div class="prod-desc">
                        {product['description']}
                      </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write("")


# =============================================================
# Chat Assistant
# =============================================================

with right:

    st.markdown(
        '<span class="chat-header">'
        '💬 AI Assistant'
        '</span>',
        unsafe_allow_html=True,
    )


    # =========================================================
    # Chat History
    # =========================================================

    chat_box = st.container(
        height=620
    )

    with chat_box:

        for msg in st.session_state.messages:

            avatar = (
                "🧑"
                if msg["role"] == "user"
                else "🤖"
            )

            with st.chat_message(
                msg["role"],
                avatar=avatar,
            ):

                raw_content = msg[
                    "content"
                ]

                # ---------------------------------------------
                # LangGraph list content support
                # ---------------------------------------------

                if isinstance(
                    raw_content,
                    list,
                ):

                    parts = []

                    for block in raw_content:

                        if (
                            isinstance(
                                block,
                                dict,
                            )
                            and "text" in block
                        ):

                            parts.append(
                                block["text"]
                            )

                        elif isinstance(
                            block,
                            str,
                        ):

                            parts.append(
                                block
                            )

                    content = "\n".join(
                        parts
                    )

                else:

                    content = str(
                        raw_content
                    )


                # ---------------------------------------------
                # Order confirmation formatting
                # ---------------------------------------------

                order_match = _re.search(
                    r"Order placed!\s*Details:\s*(\{.*\})",
                    content,
                )

                status_match = _re.search(
                    r"status:\s*(\{.*\})",
                    content,
                    _re.IGNORECASE,
                )


                if order_match:

                    try:

                        details = _ast.literal_eval(
                            order_match.group(1)
                        )

                        order_id = (
                            details.get("order_id")
                            or details.get("order-id")
                            or "N/A"
                        )

                        prefix = content[
                            :order_match.start()
                        ].strip()

                        if prefix:
                            st.markdown(
                                prefix
                            )

                        st.success(
                            "Order placed successfully!"
                        )

                        st.code(
                            order_id,
                            language=None,
                        )

                        st.caption(
                            "Order ID — save this to "
                            "track your order."
                        )

                    except Exception:

                        content = content.replace(
                            "$",
                            "\\$",
                        )

                        st.markdown(
                            content
                        )


                elif status_match:

                    try:

                        details = _ast.literal_eval(
                            status_match.group(1)
                        )

                        order_id = (
                            details.get("order_id")
                            or details.get("order-id")
                            or "N/A"
                        )

                        status = (
                            details.get("status")
                            or details.get(
                                "order-status"
                            )
                            or "Unknown"
                        )

                        quantity = details.get(
                            "quantity"
                        )

                        lines = [
                            f"**Status:** {status}",
                            f"**Order ID:** `{order_id}`",
                        ]

                        if quantity is not None:

                            lines.append(
                                f"**Quantity:** "
                                f"{quantity}"
                            )

                        st.markdown(
                            "\n\n".join(lines)
                        )

                    except Exception:

                        content = content.replace(
                            "$",
                            "\\$",
                        )

                        st.markdown(
                            content
                        )


                else:

                    content = content.replace(
                        "$",
                        "\\$",
                    )

                    st.markdown(
                        content
                    )


    # =========================================================
    # Chat Input
    # =========================================================

    prompt = st.chat_input(
        "Ask about products, place an order, "
        "or track one..."
    )

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.spinner(
            "Thinking..."
        ):

            reply = assistant_reply(
                prompt
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        st.rerun()