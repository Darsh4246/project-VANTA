class ConversationMemory:
    """Manages conversational history context window for the LangChain agent."""
    def __init__(self, max_messages: int = 12):
        self.max_messages = max_messages
        self.messages = []

    def add_user_message(self, text: str):
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant_message(self, text: str):
        self.messages.append({"role": "assistant", "content": text})
        self._trim()

    def clear(self):
        self.messages = []

    def get_messages(self) -> list:
        return self.messages

    def _trim(self):
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
