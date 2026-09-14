import time
from thespian.actors import *
from block_agent import BlockAgent
from messages import Message, MessageType


if __name__ == '__main__':
    actorSystem = ActorSystem()

    block_agent_1 = actorSystem.createActor(BlockAgent)
    block_agent_2 = actorSystem.createActor(BlockAgent)
    block_agent_3 = actorSystem.createActor(BlockAgent)
    block_agent_4 = actorSystem.createActor(BlockAgent)
    block_agent_5 = actorSystem.createActor(BlockAgent)

    chain_agent = [block_agent_1, block_agent_2, block_agent_3, block_agent_4, block_agent_5]

    for i, block in enumerate(chain_agent):
        init_message_data = {'name': f"Block{i+1}"}
        init_message = Message(MessageType.INITIALIZATION, init_message_data)
        actorSystem.tell(block, init_message)

    first_message_data = {
        'chain_address': chain_agent,
        'msg': '',
        'name': 'Block1',
        'start_time': time.perf_counter(),
    }
    first_message = Message(MessageType.NEXT_AGENT, first_message_data)
    actorSystem.tell(block_agent_1, first_message)
