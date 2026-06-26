from app.db.supabase_client import supabase
from app.services.profiles_service import resolve_internal_user_id


def list_my_tickets(external_auth_id: str):
    internal_user_id = resolve_internal_user_id(supabase, external_auth_id)

    result = (
        supabase.table("tickets")
        .select("*")
        .eq("owner_user_id", internal_user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"items": result.data or []}


def get_ticket_detail(ticket_id: str):
    result = (
        supabase.table("tickets")
        .select("*")
        .eq("id", ticket_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


def check_in_ticket(ticket_id: str):
    ticket = get_ticket_detail(ticket_id)
    if not ticket:
        return {"ok": False, "message": "Ticket not found"}

    status = ticket.get("status")
    if status != "active":
        return {"ok": False, "message": f"Ticket is not active: {status}"}

    update_result = (
        supabase.table("tickets")
        .update({"status": "used"})
        .eq("id", ticket_id)
        .execute()
    )

    if not update_result.data:
        return {"ok": False, "message": "Failed to update ticket"}

    return {
        "ok": True,
        "message": "Check-in successful",
        "ticket_id": ticket_id,
        "new_status": "used",
    }