import json
import asyncio
from flask import Flask, jsonify
from telethon import TelegramClient
from telethon.tl.functions.channels import GetAdminLogRequest
from telethon.tl.types import (
    ChannelAdminLogEventsFilter,
    ChannelAdminLogEventActionParticipantJoin,
    ChannelAdminLogEventActionParticipantLeave,
    ChannelAdminLogEventActionParticipantJoinByInvite,
    ChannelAdminLogEventActionParticipantJoinByRequest
)
from telethon.sessions import StringSession

API_ID = 27634392
API_HASH = "c29325ca5de227dc611e54d355f76896"
STRING_SESSION = "1BVtsOIABu5KYzwSUb9AaSOTBd27u1nXRyzhz45UyvaiMAjvZ-Qvbo_abLVYryxRLhZkeSle0oARyaLhj_SgFeWxB3qEsIeEHbLu3Dot-ruj5p-IsYRdYSm5UjxRC-lrc-UsaprgmWVNgoMXj0042AjHEVUEfVlSw7hQlaMHyicFSpIsjICjsuPj5ZCllIybe3os4o2_pIBHO8YNmkLIvVmP9CkF3mCMi5OpkBL_M-IPCKsrjmqrIvLCY6HhKGcQgwJID0WkoQX_tHFZ8lBihT8wC-LZTxP7LQkoaeaN7f45BikkThuhdHxasTGizDqTLotjGKdRTlHZcLAfSzMFa6Wrfq_0Fmqk="
CHANNEL_ID = -1002163149728

app = Flask(__name__)

async def fetch_events_async():
    async with TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH) as client:
        channel = await client.get_entity(CHANNEL_ID)
        filters = ChannelAdminLogEventsFilter(join=True, leave=True, invite=True)
        result = await client(GetAdminLogRequest(
            channel=channel,
            q="",
            min_id=0,
            max_id=0,
            limit=30,
            events_filter=filters,
            admins=None
        ))

        events_list = []

        for event in result.events:
            user = await client.get_entity(event.user_id) if event.user_id else None
            if not user:
                continue

            user_info = {
                "id": user.id,
                "name": user.first_name or "Unknown",
                "username": user.username if user.username else None
            }

            action_type = None
            extra_info = {}

            if isinstance(event.action, ChannelAdminLogEventActionParticipantJoin):
                action_type = "join"

            elif isinstance(event.action, ChannelAdminLogEventActionParticipantLeave):
                action_type = "leave"

            elif isinstance(event.action, ChannelAdminLogEventActionParticipantJoinByInvite):
                action_type = "join_by_invite"
                inviter = await client.get_entity(event.action.invite.admin_id)
                extra_info = {
                    "invite_title": event.action.invite.title,
                    "inviter": {
                        "id": inviter.id,
                        "name": inviter.first_name,
                        "username": inviter.username
                    }
                }

            elif isinstance(event.action, ChannelAdminLogEventActionParticipantJoinByRequest):
                action_type = "join_by_request"
                approver = await client.get_entity(event.action.approved_by)
                extra_info = {
                    "invite_title": event.action.invite.title,
                    "approved_by": {
                        "id": approver.id,
                        "name": approver.first_name,
                        "username": approver.username
                    }
                }

            events_list.append({
                "event_id": event.id,
                "date": str(event.date),
                "user": user_info,
                "action": action_type,
                "extra_info": extra_info
            })

        return events_list

@app.route("/", methods=["GET"])
def get_events():
    try:
        events = asyncio.run(fetch_events_async())
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
