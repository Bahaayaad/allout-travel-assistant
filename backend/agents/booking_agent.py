from google.adk.agents import Agent
from database import search_activities, get_activity, save_booking, save_escalation
from services.email_service import send_escalation_email


def find_activities(search_term: str = "", category: str = "") -> dict:
    """
    Search the activity catalog.

    Args:
        search_term: what the customer is looking for, e.g. 'desert', 'burj khalifa'
        category: Adventure, Landmark, Cruise, Culture, Family, Entertainment

    Returns:
        dict with matching activities
    """
    results = search_activities(
        term=search_term or None,
        category=category or None
    )

    if not results:
        return {"found": False, "message": f"Nothing matched '{search_term or category}'"}

    return {
        "found": True,
        "activities": [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "description": r["description"][:100]}
            for r in results
        ]
    }


def get_activity_details(activity_id: str) -> dict:
    """
    Get full details for an activity including all variations, timings and pricing.

    Args:
        activity_id: e.g. 'act_001'

    Returns:
        full activity dict or error
    """
    activity = get_activity(activity_id)
    if not activity:
        return {"error": f"Activity {activity_id} not found"}
    return activity


def check_availability(activity_id: str, variation_id: str, time_slot: str, group_size: int) -> dict:
    """
    Check if a specific time slot and group size are available for a variation.

    Args:
        activity_id: activity ID
        variation_id: specific variation ID, e.g. 'var_001_1'
        time_slot: e.g. '9:00 AM'
        group_size: number of people

    Returns:
        availability info and pricing
    """
    activity = get_activity(activity_id)
    if not activity:
        return {"available": False, "reason": "Activity not found"}

    variation = next((v for v in activity["variations"] if v["id"] == variation_id), None)
    if not variation:
        return {"available": False, "reason": "Variation not found"}

    if time_slot not in variation["timings"]:
        return {
            "available": False,
            "reason": f"{time_slot} is not offered for this option",
            "available_timings": variation["timings"]
        }

    if group_size > max(variation["group_sizes"]):
        return {
            "available": False,
            "reason": f"Max group size is {max(variation['group_sizes'])}",
            "available_group_sizes": variation["group_sizes"]
        }

    return {
        "available": True,
        "activity": activity["name"],
        "variation": variation["name"],
        "time_slot": time_slot,
        "group_size": group_size,
        "price_per_person": variation["price_per_person"],
        "total": variation["price_per_person"] * group_size,
        "currency": variation["currency"]
    }


def create_booking(
    activity_id: str,
    variation_id: str,
    user_name: str,
    user_email: str,
    booking_date: str,
    time_slot: str,
    group_size: int,
    notes: str = ""
) -> dict:
    """
    Save a booking to the database.

    Args:
        activity_id: activity ID
        variation_id: variation ID
        user_name: customer full name
        user_email: customer email
        booking_date: date in YYYY-MM-DD format
        time_slot: e.g. '9:00 AM'
        group_size: number of people
        notes: any special requests

    Returns:
        booking confirmation
    """
    activity = get_activity(activity_id)
    if not activity:
        return {"error": "Activity not found"}

    variation = next((v for v in activity["variations"] if v["id"] == variation_id), None)
    if not variation:
        return {"error": "Variation not found"}

    total = variation["price_per_person"] * group_size

    booking_id = save_booking({
        "activity_id": activity_id,
        "variation_id": variation_id,
        "user_name": user_name,
        "user_email": user_email,
        "booking_date": booking_date,
        "time_slot": time_slot,
        "group_size": group_size,
        "total_price": total,
        "currency": variation["currency"],
        "notes": notes
    })

    return {
        "confirmed": True,
        "booking_id": booking_id,
        "activity": activity["name"],
        "variation": variation["name"],
        "date": booking_date,
        "time": time_slot,
        "guests": group_size,
        "total": total,
        "currency": variation["currency"],
    }


def escalate_to_supervisor(conversation_id: str, activity_requested: str, user_message: str) -> dict:
    """
    Escalate to human supervisor when we can't fulfill a request.

    Args:
        conversation_id: current session ID
        activity_requested: what the customer wants
        user_message: the customer's original message

    Returns:
        escalation reference
    """
    esc_id = save_escalation({
        "conversation_id": conversation_id,
        "activity_requested": activity_requested,
        "user_message": user_message
    })

    send_escalation_email(
        escalation_id=esc_id,
        conversation_id=conversation_id,
        activity_requested=activity_requested,
        user_message=user_message
    )

    return {
        "escalated": True,
        "ref": esc_id,
        "message": f"I've flagged this to our team (ref: {esc_id}). Someone will get back to you here in the chat shortly."
    }


booking_agent = Agent(
    name="booking_agent",
    model="gemini-2.5-flash",
    description="Handles activity searches, availability checks, bookings, and escalations for unavailable requests.",
    instruction="""You handle bookings for Allout Travel's Dubai activities.

Flow for a booking:
1. Search for the activity using find_activities
2. Get full details with get_activity_details  
3. Check the specific time slot and group size with check_availability
4. Collect name, email, date, time, group size from the customer
5. Confirm the details back to them, then call create_booking

If something isn't available:
- Tell the customer clearly what the issue is
- Suggest alternative timings or variations if they exist
- If nothing works, use escalate_to_supervisor — never leave the customer stuck

Be warm but efficient. Always confirm booking details before creating the booking.
""",
    tools=[find_activities, get_activity_details, check_availability, create_booking, escalate_to_supervisor]
)
