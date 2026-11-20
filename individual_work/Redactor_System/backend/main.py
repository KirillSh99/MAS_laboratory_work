from fastapi import FastAPI
from database import engine, Base
from routers import agents
from thespian.actors import ActorSystem
from agents.dispatcher_agent import AgentsDispatcher
from agents.scene_agent import SceneAgent
from agents.messages import Message, MessageType


def create_app():
    app = FastAPI(title="Agent Editor Backend")
    Base.metadata.create_all(bind=engine)

    system = ActorSystem('multiprocTCPBase')
    scene_addr = system.createActor(SceneAgent)
    dispatcher_addr = system.createActor(AgentsDispatcher)

    system.tell(dispatcher_addr, Message(
        MessageType.INIT_DISPATCHER,
        {"scene_agent_address": scene_addr}
    ))

    app.state.dispatcher = dispatcher_addr
    app.include_router(agents.router)
    return app

app = create_app()