from PyQt6.QtCore import QObject, pyqtSignal
from chat.model.SwarmThread import SwarmThread
from util.Constants import MODEL_MESSAGE


class SwarmModel(QObject):
    thread_started_signal = pyqtSignal()
    thread_finished_signal = pyqtSignal()
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self):
        super().__init__()
        self.swarm_thread = None

    def run_agent(self, args):
        if self.swarm_thread is not None and self.swarm_thread.isRunning():
            print(f"{MODEL_MESSAGE.THREAD_RUNNING}")
            self.swarm_thread.wait()

        self.swarm_thread = SwarmThread(args)
        self.swarm_thread.started.connect(self.thread_started_signal.emit)
        self.swarm_thread.finished.connect(self.handle_thread_finished)
        self.swarm_thread.response_signal.connect(self.response_signal.emit)
        self.swarm_thread.response_finished_signal.connect(self.response_finished_signal.emit)
        self.swarm_thread.start()

    def handle_thread_finished(self):
        print(f"{MODEL_MESSAGE.THREAD_FINISHED}")
        self.thread_finished_signal.emit()
        self.swarm_thread = None

    def force_stop(self):
        if self.swarm_thread is not None:
            self.swarm_thread.set_force_stop(True)
