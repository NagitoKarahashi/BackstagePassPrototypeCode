from app.services.profiles_service import resolve_internal_user_id

PROFILE_SELECT = """
id,
external_auth_id,
username,
display_name,
city,
bio,
fan_points,
preferred_genres
"""

ORDER_SELECT = """
id,
user_id,
event_id,
event_uuid,
qty,
total_amount,
status,
created_at
"""

TICKET_SELECT = """
id,
user_id,
order_id,
event_id,
event_uuid,
status,
created_at
"""


def _safe_execute(builder, default):
    try:
        resp = builder.execute()
        return resp.data or default
    except Exception:
        return default


def get_me_overview_service(sb, external_auth_id: str):
    profile_rows = _safe_execute(
        sb.table("profiles")
        .select(PROFILE_SELECT)
        .eq("external_auth_id", external_auth_id)
        .limit(1),
        [],
    )

    if not profile_rows:
        profile = {
            "id": None,
            "external_auth_id": external_auth_id,
            "username": None,
            "display_name": None,
            "city": None,
            "bio": None,
            "fan_points": 0,
            "preferred_genres": [],
        }
        internal_user_id = None
    else:
        profile = profile_rows[0]
        internal_user_id = profile.get("id")

    if internal_user_id:
        orders = _safe_execute(
            sb.table("orders")
            .select(ORDER_SELECT)
            .eq("user_id", internal_user_id)
            .order("created_at", desc=True)
            .limit(5),
            [],
        )

        tickets = _safe_execute(
            sb.table("tickets")
            .select(TICKET_SELECT)
            .eq("user_id", internal_user_id)
            .order("created_at", desc=True)
            .limit(5),
            [],
        )

        badges = _safe_execute(
            sb.table("user_badges")
            .select("*")
            .eq("user_id", internal_user_id)
            .order("awarded_at", desc=True)
            .limit(6),
            [],
        )
    else:
        orders = []
        tickets = []
        badges = []

    stats = {
        "fan_points": profile.get("fan_points", 0) or 0,
        "orders_count": len(orders),
        "tickets_count": len(tickets),
        "badges_count": len(badges),
    }

    return {
        "profile": profile,
        "stats": stats,
        "recent_orders": orders,
        "recent_tickets": tickets,
        "badges": badges,
    }


def get_me_history_service(sb, external_auth_id: str, order_limit: int = 20, ticket_limit: int = 20):
    try:
        internal_user_id = resolve_internal_user_id(sb, external_auth_id)
    except Exception:
        return {
            "orders": [],
            "tickets": [],
        }

    orders = _safe_execute(
        sb.table("orders")
        .select(ORDER_SELECT)
        .eq("user_id", internal_user_id)
        .order("created_at", desc=True)
        .limit(order_limit),
        [],
    )

    tickets = _safe_execute(
        sb.table("tickets")
        .select(TICKET_SELECT)
        .eq("user_id", internal_user_id)
        .order("created_at", desc=True)
        .limit(ticket_limit),
        [],
    )

    return {
        "orders": orders,
        "tickets": tickets,
    }