from thespian.actors import *
from send_agent import SendAgent
from time_agent import TimeAgent
from messages import Message, MessageType


if __name__ == '__main__':
    actorSystem = ActorSystem()

    send_agent_1 = actorSystem.createActor(SendAgent)
    init_message_1_data = {'name': "Send1"}
    init_message_1 = Message(MessageType.INITIALIZATION, init_message_1_data)
    actorSystem.tell(send_agent_1, init_message_1)

    send_agent_2 = actorSystem.createActor(SendAgent)
    init_message_2_data = {'name': "Send2"}
    init_message_2 = Message(MessageType.INITIALIZATION, init_message_2_data)
    actorSystem.tell(send_agent_2, init_message_2)

    time_agent_1 = actorSystem.createActor(TimeAgent)
    init_message_3_data = {'name': "Time1"}
    init_message_3 = Message(MessageType.INITIALIZATION, init_message_3_data)
    actorSystem.tell(time_agent_1, init_message_3)

    time_agent_2 = actorSystem.createActor(TimeAgent)
    init_message_4_data = {'name': "Time2"}
    init_message_4 = Message(MessageType.INITIALIZATION, init_message_4_data)
    actorSystem.tell(time_agent_2, init_message_4)

    message_meeting_1 = Message(
        msg_type=MessageType.COUNT_SEND_MESSAGE,
        msg_body={'count_msg': 2,
                  'time_address': time_agent_1},
    )
    message_meeting_2 = Message(
        msg_type=MessageType.COUNT_SEND_MESSAGE,
        msg_body={'count_msg': 5,
                  'time_address': time_agent_2},
    )
    message_meeting_3 = Message(
        msg_type=MessageType.COUNT_SEND_MESSAGE,
        msg_body={'count_msg': 6,
                  'time_address': time_agent_1},
    )
    message_meeting_4 = Message(
        msg_type=MessageType.COUNT_SEND_MESSAGE,
        msg_body={'count_msg': 9,
                  'time_address': time_agent_2},
    )

    actorSystem.tell(send_agent_1, message_meeting_1)
    actorSystem.tell(send_agent_2, message_meeting_3)
    actorSystem.tell(send_agent_1, message_meeting_2)
    actorSystem.tell(send_agent_2, message_meeting_4)

    finish_message = Message(
        msg_type=MessageType.GET_RESULT,
        msg_body={},
    )
    actorSystem.tell(time_agent_1, finish_message)
    actorSystem.tell(time_agent_2, finish_message)
