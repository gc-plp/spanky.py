import datetime
from spanky.plugin import hook, permissions
from spanky.plugin.event import EventType
from spanky.plugin.permissions import Permission
from spanky.utils import time_utils
from plugins.log import get_msg_cnt_for_user

@hook.command(permissions=Permission.admin, format="user")
def kick(user_id_to_object, str_to_id, text):
    """
    <user> - Kick someone
    """
    user = user_id_to_object(str_to_id(text))
    user.kick()
    return "Okay."

@hook.command(permissions=Permission.admin, format="user")
def ban(user_id_to_object, str_to_id, text):
    """
    <user> - Ban someone
    """
    user = user_id_to_object(str_to_id(text))
    user.ban()
    return "Okay."

@hook.command(permissions=Permission.admin)
def add_join_event(storage, text):
    """
    <'type' 'option'> - Add action to be triggered on user join.
Possible actions:
 * message #channel blahblah -> send blahblah to #channel
 * role @role -> set @role on join).
The scripted message can contain special words that are replaced when the event is triggered:
 * {AGE} - Account age
 * {USER} - User that just joined
 * {USER_ID} - User ID
 * {SEEN_CNT} - How many times this user has been seen in servers shared with the bot

e.g. 'message #general {USER} / {USER_ID} just joined!' will send 'John / 12345678910 just joined!'
    """
    text = text.split()

    if text[0] == "message":
        if storage["on_join_message"] == None:
            storage["on_join_message"] = []

        if text[0] in storage["on_join_message"]:
            return "There already is a message with that content"

        storage["on_join_message"].append(" ".join(text[1:]))
        storage.sync()
    elif text[0] == "role":
        if storage["on_join_role"] == None:
            storage["on_join_role"] = []

        if text[0] in storage["on_join_role"]:
            return "There already is a message with that content"

        storage["on_join_role"].append(" ".join(text[1:]))
        storage.sync()
    else:
        return "Invalid type."
    return "Done."

@hook.event(EventType.join)
def do_join(event, storage, send_message, str_to_id, server):
    if storage["on_join_message"]:
        for msg in storage["on_join_message"]:
            creation_date = datetime.datetime.utcfromtimestamp(int((int(event.member.id) >> 22) + 1420070400000) / 1000)
            args = {
                "AGE":  time_utils.sec_to_human((datetime.datetime.now() - creation_date).total_seconds()),
                "USER": event.member.name,
                "USER_ID": event.member.id
            }
            if "{SEEN_CNT}" in msg:
                args["SEEN_CNT"] = get_msg_cnt_for_user(event.member.id)

            text = msg.split(" ", maxsplit=1)
            chanid = str_to_id(text[0])
            message = text[1].format(**args)

            send_message(target=chanid, text=message)


    if storage["on_join_role"]:
        for role in storage["on_join_role"]:
            role_id = str_to_id(role)

            for role in server.get_roles():
                if role.id == role_id:
                    event.member.add_role(role)

@hook.command(permissions=Permission.admin)
def list_join_events(storage):
    """
    List on-join events
    """
    msg = ""

    if storage["on_join_message"]:
        msg += "\nMessages:\n" + "\n".join("-" + i for i in storage["on_join_message"])

    if storage["on_join_role"]:
        msg += "\nRoles:\n" + "\n".join("-" + i for i in storage["on_join_role"])

    return msg

@hook.command(permissions=Permission.admin)
def del_join_event(storage, text):
    """
    <event> - delete a join event
    """
    to_delete = []
    if storage["on_join_message"]:
        for item in storage["on_join_message"]:
            if text in item:
                to_delete.append((storage["on_join_message"], item))

    if storage["on_join_role"]:
        for item in storage["on_join_role"]:
            if text == item:
                to_delete.append((storage["on_join_role"], item))

    if len(to_delete) > 1:
        return "Found too many matching entries. Try restricting the search criteria"
    elif len(to_delete) == 0:
        return "Entry not found"

    lst, item = to_delete[0]

    lst.remove(item)
    storage.sync()

    return "Done"
