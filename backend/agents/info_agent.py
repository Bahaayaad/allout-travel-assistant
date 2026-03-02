from google.adk.agents import Agent
from database import search_activities, get_activity


def list_activities() -> list:
    results = search_activities()
    return [{"id": r["id"], "name": r["name"], "category": r["category"]} for r in results]


def get_activity_image(activity_id: str = "", activity_name: str = "") -> dict:

    activity = None

    if activity_id:
        activity = get_activity(activity_id)
    elif activity_name:
        results = search_activities(term=activity_name)
        if results:
            activity = get_activity(results[0]["id"])

    if not activity:
        return {"error": "Activity not found"}

    return {
        "activity": activity["name"],
        "image_url": activity["image_url"],
        "description": activity["description"]
    }


def get_cancellation_policy(activity_id: str = "", activity_name: str = "") -> dict:
    """
    Get the cancellation policy for an activity.

    Args:
        activity_id: activity ID
        activity_name: search by name if ID not available
    """
    activity = _lookup(activity_id, activity_name)
    if not activity:
        return {"error": "Activity not found"}
    return {"activity": activity["name"], "policy": activity["cancellation_policy"]}


def get_reschedule_policy(activity_id: str = "", activity_name: str = "") -> dict:

    activity = _lookup(activity_id, activity_name)
    if not activity:
        return {"error": "Activity not found"}
    return {"activity": activity["name"], "policy": activity["reschedule_policy"]}


def get_pricing(activity_id: str = "", activity_name: str = "") -> dict:

    activity = _lookup(activity_id, activity_name)
    if not activity:
        return {"error": "Activity not found"}

    return {
        "activity": activity["name"],
        "variations": [
            {
                "id": v["id"],
                "name": v["name"],
                "price_per_person": v["price_per_person"],
                "currency": v["currency"],
                "timings": v["timings"],
                "max_group": max(v["group_sizes"])
            }
            for v in activity["variations"]
        ]
    }


def _lookup(activity_id, activity_name):
    if activity_id:
        return get_activity(activity_id)
    if activity_name:
        results = search_activities(term=activity_name)
        if results:
            return get_activity(results[0]["id"])
    return None


info_agent = Agent(
    name="info_agent",
    model="gemini-2.5-flash",
    description="Provides activity images, cancellation/reschedule policies, pricing details, and full activity listings.",
    instruction="""You handle information requests for Allout Travel.

You can help with:
- Listing all available Dubai activities
- Showing activity images (always include the image URL so the customer can see it)
- Cancellation and reschedule policies — explain them clearly
- Pricing across different variations and group sizes

When sharing an image, include the full URL as plain text like:
https://images.unsplash.com/photo-xxx?w=800

Don't use markdown image syntax. Just put the raw URL in your response.
""",
    tools=[list_activities, get_activity_image, get_cancellation_policy, get_reschedule_policy, get_pricing]
)
