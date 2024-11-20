import time
from pprint import pprint

from PyQt6.QtCore import QThread, pyqtSignal
from openai import OpenAI
from swarm import Swarm, Agent
from tavily import TavilyClient

from util.Constants import Constants


class SwarmThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.openai = OpenAI(api_key=args['open_api_key'])
        self.client = Swarm(client=self.openai)
        self.search_tool_args = args['search_tool_args']
        self.query = self.search_tool_args['query']
        self.messages = args['messages']
        self.stream = args['stream']
        self.force_stop = False
        self.create_all_agents(args['agent_prompt_list'])
        pprint(args)

    def run(self):
        self.start_time = time.time()
        try:
            response = self.client.run(
                agent=self.orchestrator,
                messages=self.messages,
                stream=self.stream,
            )
            if self.stream:
                self.handle_stream_response(response)
            else:
                self.handle_response(response)
        except Exception as e:
            self.response_signal.emit(str(e), False)

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def handle_response(self, response):
        if self.force_stop:
            self.finish_run(response.agent.model, Constants.FORCE_STOP, self.stream)
        else:
            result = response.messages[-1]["content"]
            finish_reason = Constants.NORMAL_STOP
            self.response_signal.emit(result, self.stream)
            self.finish_run(response.agent.model, finish_reason, self.stream)

    def handle_stream_response(self, response):
        content = ""
        last_sender = ""

        for chunk in response:
            if self.force_stop:
                self.finish_run(chunk['response'].agent.model, Constants.FORCE_STOP, self.stream)
                break
            else:
                if "sender" in chunk:
                    last_sender = chunk["sender"]

                if "content" in chunk and chunk["content"] is not None:
                    if not content and last_sender:
                        last_sender = ""
                    content += chunk["content"]
                    self.response_signal.emit(chunk["content"], self.stream)

                if "tool_calls" in chunk and chunk["tool_calls"] is not None:
                    for tool_call in chunk["tool_calls"]:
                        f = tool_call["function"]
                        name = f["name"]
                        if not name:
                            continue

                if "response" in chunk:
                    self.finish_run(chunk['response'].agent.model, Constants.NORMAL_STOP, self.stream)

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)

    def create_all_agents(self, args):
        orchestrator_agent = args['orchestrator_agent']
        search_agent = args['search_agent']
        programmer_agent = args['programmer_agent']
        tester_agent = args['tester_agent']

        self.orchestrator = self.create_agent(
            orchestrator_agent['name'],
            orchestrator_agent['instructions'],
            [self.transfer_to_search_agent, self.transfer_to_programmer_agent, self.transfer_to_tester_agent],
        )

        self.search_agent = self.create_agent(
            search_agent['name'],
            search_agent['instructions'],
            [self.search_web, self.transfer_to_orchestrator_agent]
        )

        self.programmer_agent = self.create_agent(
            programmer_agent['name'],
            programmer_agent['instructions'],
            [self.transfer_to_orchestrator_agent]
        )

        self.tester_agent = self.create_agent(
            tester_agent['name'],
            tester_agent['instructions'],
            [self.transfer_to_orchestrator_agent]
        )

    def create_agent(self, agent_name, agent_instructions, agent_functions):
        return Agent(
            name=agent_name, instructions=agent_instructions, functions=agent_functions
        )

    def transfer_to_search_agent(self):
        """transfer to Search Agent for web search"""
        return self.search_agent

    def transfer_to_programmer_agent(self):
        """transfer to Programmer Agent for code generation and code refinement"""
        return self.programmer_agent

    def transfer_to_tester_agent(self):
        """transfer to Tester Agent to provide reliable feedback for the programmer agent to optimise the code iteratively"""
        return self.tester_agent

    def transfer_to_orchestrator_agent(self):
        """transfer to Orchestrator Agent for orchestrating the processes"""
        return self.orchestrator

    def search_web(self, query):
        """Search 'query' on the web and return the results"""
        if self.search_tool_args:
            tavily = TavilySearch(self.search_tool_args)
            return tavily.search(query)
        else:
            return None


class TavilySearch:

    def __init__(self, args):
        self.search_args = args
        self.client = TavilyClient(api_key=self.search_args['tavily_api_key'])

    def search(self, query):
        response = self.client.search(
            query=query,
            search_depth=self.search_args['search_depth'],
            topic=self.search_args['topic'],
            days=self.search_args['days'],
            max_results=self.search_args['max_results'],
            include_domains=self.search_args['include_domains'],
            exclude_domains=self.search_args['exclude_domains'],
            include_answer=self.search_args['include_answer'],
            include_raw_content=self.search_args['include_raw_content'],
            include_images=self.search_args['include_images'],
        )

        search_results = []
        for result in response["results"]:
            search_results.append({
                "title": result["title"],
                "url": result["url"],
                "content": result["content"],
                "score": result["score"],
                "raw_content": result["raw_content"],
            })

        return search_results
