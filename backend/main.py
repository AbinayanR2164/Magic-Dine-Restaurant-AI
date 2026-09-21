from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv
import os
import mysql.connector
import json


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()


# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI()


# ==========================================
# MYSQL DATABASE CONNECTION
# ==========================================

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="magicdine"
    )


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# GROQ CLIENT
# ==========================================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "MagicDine AI backend is running!"
    }


# ==========================================
# GET ORDER DATA
# ==========================================

def get_order_data():

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            order_date,
            order_time,
            customer_id,
            order_amount,
            order_channel,
            order_status,
            payment_method
        FROM orders
        ORDER BY order_date, order_time
    """)

    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return orders


# ==========================================
# CALCULATE METRICS
# ==========================================

def calculate_metrics():

    orders = get_order_data()

    total_orders = len(orders)

    total_revenue = sum(
        float(order["order_amount"])
        for order in orders
    )

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0
        else 0
    )

    channel_counts = {}

    for order in orders:

        channel = order["order_channel"]

        channel_counts[channel] = (
            channel_counts.get(channel, 0) + 1
        )

    best_channel = (
        max(
            channel_counts,
            key=channel_counts.get
        )
        if channel_counts
        else "No data"
    )

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
        "channel_counts": channel_counts,
        "best_channel": best_channel
    }


# ==========================================
# METRICS API
# ==========================================

@app.get("/metrics")
def metrics():

    return calculate_metrics()


# ==========================================
# AI DATA HELPERS
# ==========================================

def get_customer_analytics_data():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            c.id,
            c.name,
            c.phone,
            c.email,
            COUNT(o.customer_id) AS order_count,
            COALESCE(SUM(o.order_amount), 0) AS total_spent,
            COALESCE(AVG(o.order_amount), 0) AS average_order_value
        FROM customers c
        LEFT JOIN orders o
            ON c.id = o.customer_id
        GROUP BY c.id, c.name, c.phone, c.email
        ORDER BY total_spent DESC
    """)

    customers = cursor.fetchall()
    cursor.close()
    db.close()
    return customers

def get_offer_data():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, offer_name, discount_percent, start_date, end_date, is_active
        FROM offers
        ORDER BY start_date DESC
    """)

    offers = cursor.fetchall()
    cursor.close()
    db.close()
    return offers


# ==========================================
# AI ASSISTANT
# ==========================================

@app.get("/ask")
def ask_ai(question: str):

    try:

        # ======================================
        # GET REAL DATABASE DATA
        # ======================================

        orders = get_order_data()

        restaurant_metrics = calculate_metrics()
        customer_data = get_customer_analytics_data()
        offer_data = get_offer_data()


        # ======================================
        # PREPARE ORDER DATA
        # ======================================

        order_data = "\n".join(
            [
                f"Date: {order['order_date']}, "
                f"Time: {order['order_time']}, "
                f"Customer ID: {order['customer_id']}, "
                f"Amount: ₹{order['order_amount']}, "
                f"Channel: {order['order_channel']}, "
                f"Status: {order['order_status']}, "
                f"Payment: {order['payment_method']}"
                for order in orders
            ]
        )

        customer_data_text = json.dumps(customer_data, default=str, ensure_ascii=False)
        offer_data_text = json.dumps(offer_data, default=str, ensure_ascii=False)


        # ======================================
        # AI SYSTEM PROMPT
        # ======================================

        system_prompt = """
You are MagicDine AI, an intelligent restaurant
growth assistant.

Analyze ONLY the real restaurant data provided.

You help restaurant owners understand:

orders
revenue
average order value
peak hours
customer behavior
repeat customers
order channels
offers
restaurant growth


IMPORTANT RULES:

1. Use only the provided restaurant data.

2. Never invent restaurant numbers.

3. Keep recommendations practical.

4. Give a maximum of 5 recommendations.

5. The dataset may be small.

6. Do not make unrealistic predictions.

7. Return ONLY valid JSON.

8. Do NOT return Markdown.

9. Do NOT use ###.

10. Do NOT use **.

11. Do NOT use bullet symbols.

12. Do NOT put any explanation outside the JSON.

13. The "summary" must directly answer the
restaurant owner's question.

14. Metrics must use the actual restaurant data.

15. Recommendations must be practical actions.

16. Only make claims about peak hours, customer behavior,
repeat customers, or trends when the provided order data
clearly supports the claim.

17. If the dataset is too small to establish a trend,
explicitly say that there is insufficient data instead
of guessing.

18. Never invent a peak time, trend, customer behavior,
or performance pattern.

19. Recommendations must be based on observable data
from the provided dataset.

20. Match customer IDs to real customer names from customer_data.
Never call a customer "Customer 1" when a name is available.

21. Use customer_data for customer names, spending, order counts,
repeat customers, average order values, and zero-order customers.

22. Use offer_data for active offers, inactive offers, discounts,
and offer dates.

23. For peak-hour or time-based questions, use order times only.
With this small dataset, do not claim a reliable peak hour or trend.
If evidence is insufficient, say so explicitly.

24. For "customers with no orders", count customer_data records
where order_count is 0.

25. For "top customer by spending", use the highest total_spent
in customer_data and provide the customer's real name.

26. Never invent customer names, order times, offers, trends,
or performance patterns.


RETURN EXACTLY THIS JSON STRUCTURE:

{
    "summary": "Short answer directly addressing the user's question.",
    "metrics": [
        {
            "label": "Total orders",
            "value": "5"
        },
        {
            "label": "Total revenue",
            "value": "₹3,170"
        },
        {
            "label": "Average order value",
            "value": "₹634"
        },
        {
            "label": "Best channel",
            "value": "Dine-in"
        }
    ],
    "recommendations": [
        {
            "title": "Increase average order value",
            "description": "Add meal combos and suitable add-ons."
        },
        {
            "title": "Improve repeat customers",
            "description": "Introduce a simple loyalty program."
        }
    ]
}


The JSON must contain exactly these three
top-level fields:

summary
metrics
recommendations


"summary" must be a string.

"metrics" must be an array of objects.
Each metric object must contain:
label
value

"recommendations" must be an array of objects.
Each recommendation object must contain:
title
description


Never put Markdown inside any JSON value.

Never use ### inside any JSON value.

Never use ** inside any JSON value.
"""


        # ======================================
        # CALL GROQ
        # ======================================

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": f"""
Restaurant metrics:

{restaurant_metrics}


Restaurant order data:

{order_data}


Restaurant customer data:

{customer_data_text}


Restaurant offer data:

{offer_data_text}


Restaurant owner's question:

{question}
"""
                }

            ],

            response_format={
                "type": "json_object"
            }
        )


        # ======================================
        # GET RAW AI RESPONSE
        # ======================================

        raw_answer = (
            response.choices[0]
            .message
            .content
            .strip()
        )


        print("===================================")
        print("RAW GROQ RESPONSE:")
        print(raw_answer)
        print("===================================")


        # ======================================
        # PARSE JSON
        # ======================================

        answer = json.loads(raw_answer)


        # ======================================
        # VALIDATE RESPONSE STRUCTURE
        # ======================================

        if not isinstance(answer, dict):

            raise ValueError(
                "AI response is not a JSON object"
            )


        if "summary" not in answer:

            raise ValueError(
                "AI response missing summary"
            )


        if "metrics" not in answer:

            raise ValueError(
                "AI response missing metrics"
            )


        if "recommendations" not in answer:

            raise ValueError(
                "AI response missing recommendations"
            )


        if not isinstance(answer["metrics"], list):

            raise ValueError(
                "AI metrics is not an array"
            )


        if not isinstance(
            answer["recommendations"],
            list
        ):

            raise ValueError(
                "AI recommendations is not an array"
            )


        # ======================================
        # LIMIT RECOMMENDATIONS TO 5
        # ======================================

        answer["recommendations"] = (
            answer["recommendations"][:5]
        )


        # ======================================
        # RETURN STRUCTURED JSON
        # ======================================

        return {
            "question": question,
            "answer": answer
        }


    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except Exception as error:

        print("===================================")
        print("AI ERROR:")
        print(error)
        print("===================================")

        return {
            "question": question,
            "answer": {
                "summary":
                    "I couldn't process the AI response.",

                "metrics": [],

                "recommendations": []
            }
        }


# ==========================================
# DATABASE TEST
# ==========================================

@app.get("/db-test")
def db_test():

    db = get_db_connection()

    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )

    count = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return {
        "orders_count": count
    }


# ==========================================
# CUSTOMERS API
# ==========================================

@app.get("/customers")
def get_customers():

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            name,
            phone,
            email,
            created_at
        FROM customers
        ORDER BY created_at DESC
    """)

    customers = cursor.fetchall()

    cursor.close()
    db.close()

    return {
        "customers": customers
    }


# ==========================================
# OFFERS API
# ==========================================

@app.get("/offers")
def get_offers():

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            offer_name,
            discount_percent,
            start_date,
            end_date,
            is_active
        FROM offers
        ORDER BY start_date DESC
    """)

    offers = cursor.fetchall()

    cursor.close()
    db.close()

    return {
        "offers": offers
    }


# ==========================================
# CREATE OFFER
# ==========================================

@app.post("/offers")
def create_offer(offer: dict):

    # ======================================
    # OFFER VALIDATION
    # ======================================

    if not offer.get("offer_name"):
        raise HTTPException(
            status_code=400,
            detail="Offer name is required."
        )


    discount = float(
        offer.get("discount_percent", 0)
    )


    if discount < 1 or discount > 100:
        raise HTTPException(
            status_code=400,
            detail="Discount percentage must be between 1 and 100."
        )


    if (
        not offer.get("start_date") or
        not offer.get("end_date")
    ):
        raise HTTPException(
            status_code=400,
            detail="Start date and end date are required."
        )


    if offer["end_date"] < offer["start_date"]:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date."
        )

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO offers
        (
            offer_name,
            discount_percent,
            start_date,
            end_date,
            is_active
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        offer["offer_name"],
        offer["discount_percent"],
        offer["start_date"],
        offer["end_date"],
        offer["is_active"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return {
        "message": "Offer created successfully"
    }

# ==========================================
# INSIGHTS API
# ==========================================

@app.get("/insights")
def get_insights():

    orders = get_order_data()

    if not orders:

        return {
            "insights": []
        }

    total_orders = len(orders)

    total_revenue = sum(
        float(order["order_amount"])
        for order in orders
    )

    average_order_value = (
        total_revenue / total_orders
    )

    channel_counts = {}

    for order in orders:

        channel = order["order_channel"]

        channel_counts[channel] = (
            channel_counts.get(channel, 0) + 1
        )

    best_channel = max(
        channel_counts,
        key=channel_counts.get
    )

    highest_order = max(
        orders,
        key=lambda order: float(
            order["order_amount"]
        )
    )

    insights = [

        {
            "title": "Best order channel",
            "description":
                f"{best_channel} has the highest number "
                f"of orders with "
                f"{channel_counts[best_channel]} orders."
        },

        {
            "title": "Average order value",
            "description":
                f"Your current average order value is "
                f"₹{average_order_value:.0f}."
        },

        {
            "title": "Highest-value order",
            "description":
                f"Your highest order was "
                f"₹{float(highest_order['order_amount']):.0f}."
        },

        {
            "title": "Revenue performance",
            "description":
                f"Your restaurant generated "
                f"₹{total_revenue:.0f} from "
                f"{total_orders} orders."
        }

    ]

    return {
        "insights": insights
    }


@app.get("/orders-analytics")
def orders_analytics(days: int = 7):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            order_date,
            COUNT(*) AS order_count,
            SUM(order_amount) AS revenue
        FROM orders
        WHERE order_date >= (
            SELECT MAX(order_date)
            FROM orders
        ) - INTERVAL %s DAY
        GROUP BY order_date
        ORDER BY order_date
    """, (days,))

    results = cursor.fetchall()

    cursor.close()
    db.close()

    return {
        "days": days,
        "orders": results
    }


# ==========================================
# DELETE OFFER
# ==========================================

@app.delete("/offers/{offer_id}")
def delete_offer(offer_id: int):

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM offers
        WHERE id = %s
    """, (offer_id,))

    db.commit()

    cursor.close()
    db.close()

    return {
        "message": "Offer deleted successfully"
    }

# ==========================================
# UPDATE OFFER
# ==========================================

@app.put("/offers/{offer_id}")
def update_offer(
    offer_id: int,
    offer: dict
):

    if not offer.get("offer_name"):
        raise HTTPException(status_code=400, detail="Offer name is required.")

    try:
        discount = float(offer.get("discount_percent", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Discount percentage must be a valid number.")

    if discount < 1 or discount > 100:
        raise HTTPException(status_code=400, detail="Discount percentage must be between 1 and 100.")

    if not offer.get("start_date") or not offer.get("end_date"):
        raise HTTPException(status_code=400, detail="Start date and end date are required.")

    if offer["end_date"] < offer["start_date"]:
        raise HTTPException(status_code=400, detail="End date cannot be before start date.")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE offers
        SET
            offer_name = %s,
            discount_percent = %s,
            start_date = %s,
            end_date = %s,
            is_active = %s
        WHERE id = %s
    """, (
        offer["offer_name"],
        offer["discount_percent"],
        offer["start_date"],
        offer["end_date"],
        offer["is_active"],
        offer_id
    ))

    db.commit()

    cursor.close()
    db.close()

    return {
        "message": "Offer updated successfully"
    }
    
# ==========================================
# ORDER CHANNEL ANALYTICS
# ==========================================

@app.get("/channel-analytics")
def channel_analytics():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            order_channel,
            COUNT(*) AS order_count,
            SUM(order_amount) AS revenue
        FROM orders
        GROUP BY order_channel
        ORDER BY order_count DESC
    """)

    results = cursor.fetchall()

    cursor.close()
    db.close()

    return {
        "channels": results
    }


# ==========================================
# CUSTOMER INTELLIGENCE
# ==========================================

@app.get("/customer-analytics")
def customer_analytics():

    return {
        "customers": get_customer_analytics_data()
    }


# ==========================================
# CUSTOMER ORDER HISTORY
# ==========================================

@app.get("/customer-orders/{customer_id}")
def customer_orders(customer_id: int):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            order_date,
            order_amount,
            order_channel
        FROM orders
        WHERE customer_id = %s
        ORDER BY order_date DESC
    """, (customer_id,))

    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return {
        "customer_id": customer_id,
        "orders": orders
    }  



    # ==========================================
# DASHBOARD AI INSIGHT API
# ==========================================

@app.get("/dashboard-insight")
def dashboard_insight():

    orders = get_order_data()

    if not orders:

        return {
            "title": "No order data",
            "description": "There are no orders available for analysis."
        }

    total_orders = len(orders)

    total_revenue = sum(
        float(order["order_amount"])
        for order in orders
    )

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0
        else 0
    )

    channel_counts = {}

    for order in orders:

        channel = order["order_channel"]

        channel_counts[channel] = (
            channel_counts.get(channel, 0) + 1
        )

    best_channel = max(
        channel_counts,
        key=channel_counts.get
    )

    best_channel_orders = channel_counts[best_channel]

    return {

        "title": "Orders insight",

        "description":
            f"{best_channel} currently has the highest "
            f"order count with {best_channel_orders} "
            f"out of {total_orders} orders. "
            f"Your current average order value is "
            f"₹{average_order_value:.0f}."
    }