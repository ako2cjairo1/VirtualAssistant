from assitant import VirtualAssistant


if __name__ == "__main__":
    brenda = VirtualAssistant(masters_name="Dave", assistants_name="Brenda", listen_timeout=10)
    brenda.activate()
